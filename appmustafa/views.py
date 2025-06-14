from rest_framework import viewsets
from .models import Animal, Noticia, Comentario, Adopcion
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    AnimalSerializer, UsuarioSerializer, NoticiaSerializer,
    ComentarioSerializer, AdopcionSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import generics, serializers, status, viewsets
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str  # force_str para decode en Django 4+
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .throttles import CrearComentarioThrottle
from .throttles import UserRateThrottle, CrearAdopcionThrottle
from rest_framework.exceptions import Throttled
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsAdminOrReadOnly
from rest_framework.exceptions import PermissionDenied
from rest_framework import mixins, viewsets

# Obtener el modelo de usuario configurado en el proyecto
User = get_user_model()

# Instancia para generar tokens seguros para restablecer contraseñas
token_generator = PasswordResetTokenGenerator()


# ViewSet para manejar operaciones CRUD de Animales
class AnimalViewSet(viewsets.ModelViewSet):
    # Consulta todos los animales, ordenados por fecha de nacimiento descendente (más recientes primero)
    queryset = Animal.objects.all().order_by('-fecha_nacimiento')
    # Serializador que define cómo se representan los objetos Animal en JSON
    serializer_class = AnimalSerializer
    # Solo administradores pueden crear/modificar; usuarios no autenticados solo pueden leer
    permission_classes = [IsAdminOrReadOnly]


# ViewSet para manejar noticias
class NoticiaViewSet(viewsets.ModelViewSet):
    # Consulta todas las noticias ordenadas por fecha de publicación descendente (más recientes primero)
    queryset = Noticia.objects.all().order_by('-fecha_publicacion')
    # Serializador para noticias
    serializer_class = NoticiaSerializer
    # Permisos iguales que para animales: solo admins pueden modificar
    permission_classes = [IsAdminOrReadOnly]


# ViewSet para manejar comentarios
class ComentarioViewSet(viewsets.ModelViewSet):
    # Consulta todos los comentarios
    queryset = Comentario.objects.all()
    # Serializador para comentarios
    serializer_class = ComentarioSerializer
    # Permisos: usuarios autenticados pueden crear, modificar o eliminar; otros solo pueden leer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Definir throttling (limitación de tasa) para evitar spam de comentarios
    def get_throttles(self):
        if self.request.method == 'POST':
            # Aplicar throttling personalizado solo cuando se crean comentarios
            return [CrearComentarioThrottle()]
        # Para otras acciones (GET, PUT, DELETE) no se aplica throttling
        return []

    # Filtrar comentarios por noticia si se pasa parámetro 'noticia' en la query
    def get_queryset(self):
        noticia_id = self.request.query_params.get('noticia')
        if noticia_id:
            # Retornar solo comentarios asociados a esa noticia, ordenados por fecha descendente
            return Comentario.objects.filter(noticia_id=noticia_id).order_by('-fecha_hora')
        # Si no hay filtro, retornar todos los comentarios (comportamiento por defecto)
        return super().get_queryset()

    # Al crear un comentario, asociar el usuario autenticado automáticamente
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    # Al actualizar, permitir solo si el usuario dueño del comentario es el que hace la petición
    def perform_update(self, serializer):
        if serializer.instance.usuario != self.request.user:
            raise PermissionDenied("No puedes editar comentarios de otro usuario.")
        serializer.save()

    # Al eliminar, permitir solo si el usuario dueño del comentario es el que hace la petición
    def perform_destroy(self, instance):
        if instance.usuario != self.request.user:
            raise PermissionDenied("No puedes eliminar comentarios de otro usuario.")
        instance.delete()


# ViewSet para manejo de solicitudes de adopción
class AdopcionViewSet(viewsets.ModelViewSet):
    # Consulta todas las adopciones
    queryset = Adopcion.objects.all()
    # Serializador para adopciones
    serializer_class = AdopcionSerializer
    # Solo usuarios autenticados pueden acceder
    permission_classes = [IsAuthenticated]

    # Filtrado para obtener adopciones por usuario
    def get_queryset(self):
        user = self.request.user
        return (
            Adopcion.objects
            .filter(usuario=user)
            .select_related('animal', 'usuario')
            .order_by('-fecha_hora')
        )


    # Aplicar throttling en la creación de adopciones para limitar solicitudes
    def get_throttles(self):
        if self.request.method == 'POST':
            return [CrearAdopcionThrottle()]
        # Para otras peticiones usar el throttling definido por defecto
        return super().get_throttles()

    # Método que lanza excepción personalizada cuando se excede el límite de peticiones
    def throttled(self, request, wait):
        hours = wait // 3600
        minutes = (wait % 3600) // 60
        seconds = int(wait % 60)

        if hours > 0:
            time_str = f"{int(hours)}h {int(minutes)}min"
        elif minutes > 0:
            time_str = f"{int(minutes)}min {int(seconds)}s"
        else:
            time_str = f"{seconds}s"

        # Excepción con mensaje amigable indicando cuánto falta para poder hacer otra petición
        raise Throttled(detail={
            'message': f'Has alcanzado el límite de solicitudes de adopción. Inténtalo de nuevo en {time_str}.'
        })

    # Al crear una adopción, se validan reglas:
    def perform_create(self, serializer):
        animal = serializer.validated_data.get('animal')
        usuario = self.request.user

        # No permitir crear múltiples solicitudes para el mismo animal y usuario
        if Adopcion.objects.filter(animal=animal, usuario=usuario).exists():
            raise PermissionDenied("Ya has solicitado adoptar este animal antes.")

        # Verifica que el usuario de la adopción sea el que está haciendo la petición (no puede ser otro)
        if serializer.validated_data.get('usuario') != usuario:
            raise PermissionDenied("No puedes crear una adopción en nombre de otro usuario.")

        serializer.save()

    # Solo el usuario dueño puede modificar la adopción
    def perform_update(self, serializer):
        if serializer.instance.usuario != self.request.user:
            raise PermissionDenied("No puedes modificar esta adopción.")
        serializer.save()

    # Solo el usuario dueño puede eliminar la adopción
    def perform_destroy(self, instance):
        if instance.usuario != self.request.user:
            raise PermissionDenied("No puedes eliminar esta adopción.")
        instance.delete()


# ViewSet para manejo de usuarios, solo para creación (registro)
# Definimos una vista basada en ViewSet personalizada para manejar operaciones relacionadas con el modelo User.
class UsuarioViewSet(
    mixins.CreateModelMixin,         # Permite crear nuevos usuarios (POST).
    mixins.RetrieveModelMixin,      # Permite recuperar un usuario específico (GET /usuarios/<id>/).
    mixins.UpdateModelMixin,        # Permite actualizar información del usuario (PUT/PATCH).
    viewsets.GenericViewSet         # Provee la funcionalidad básica de un ViewSet sin CRUD completo.
):
    queryset = User.objects.all()  # Consulta base: todos los usuarios. (Spoiler: no todos podrán verse).
    serializer_class = UsuarioSerializer  # Serializador que define cómo se transforma el objeto User a JSON.

    def get_permissions(self):
        # Define permisos por acción: cualquiera puede crear usuario (registro), el resto requiere autenticación.
        if self.action == 'create':
            return [AllowAny()]  # Registro abierto. ¡Bienvenido, forastero!
        return [IsAuthenticated()]  # Para todo lo demás, necesitas mostrar tus credenciales.

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()  # Obtenemos el usuario solicitado.
        if user != request.user:
            # Intento de ver el perfil ajeno: denegado con elegancia.
            raise PermissionDenied("No puedes ver el perfil de otro usuario.")
        serializer = self.get_serializer(user)  # Serializamos la data del usuario.
        return Response(serializer.data)  # Devolvemos su perfil como respuesta (porque se portó bien).

    def update(self, request, *args, **kwargs):
        user = self.get_object()  # Obtenemos el usuario a actualizar.
        if user != request.user:
            # Nada de travesuras. Cada quien edita su perfil y punto.
            raise PermissionDenied("No puedes editar el perfil de otro usuario.")
        return super().update(request, *args, **kwargs)  # Si es su perfil, continúa con la actualización.



# Vista para obtener tokens JWT y enviarlos en cookies seguras HTTP-only
class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Llamar a la implementación original para obtener tokens
        resp = super().post(request, *args, **kwargs)
        # Extraer tokens de la respuesta
        access = resp.data.get('access')
        refresh = resp.data.get('refresh')

        # Guardar tokens en cookies con seguridad
        resp.set_cookie(
            key='access_token',
            value=access,
            httponly=True,    # No accesible vía JS (protección contra XSS)
            secure=True,      # Solo enviar por HTTPS (recomendado en producción)
            samesite='None',  # Permitir envío cross-site (depende de frontend)
            path='/',
            max_age=3600      # Duración igual que ACCESS_TOKEN_LIFETIME (1 hora)
        )
        resp.set_cookie(
            key='refresh_token',
            value=refresh,
            httponly=True,
            secure=True,
            samesite='None',
            max_age=86400     # Duración igual que REFRESH_TOKEN_LIFETIME (1 día)
        )

        # Respuesta simplificada sin tokens en body para seguridad
        resp.data = {'detail': 'Login exitoso'}
        return resp


# Vista que refresca el token JWT usando el token de refresco guardado en cookies
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Obtiene el token de refresco de las cookies de la petición
        refresh_token = request.COOKIES.get('refresh_token')
        
        # Si no hay token de refresco en cookies, responde con error 400
        if refresh_token is None:
            return Response({"error": "Refresh token not found in cookies"}, status=status.HTTP_400_BAD_REQUEST)

        # Añade el token de refresco al cuerpo de la petición para el método padre
        request.data['refresh'] = refresh_token
        
        # Llama al método post original para refrescar el token
        response = super().post(request, *args, **kwargs)

        # Si la respuesta fue exitosa y contiene el nuevo access_token, lo guarda en una cookie segura
        if response.status_code == 200 and 'access' in response.data:
            access_token = response.data['access']
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,     # Solo accesible por HTTP (no JS)
                secure=True,       # Solo enviar por HTTPS (en producción)
                samesite='None',   # Permitir cookies cross-site
                max_age=3600       # Tiempo de vida de la cookie (1 hora)
            )
            # Oculta el token en la respuesta JSON para mayor seguridad
            response.data = {'detail': 'Token refreshed'}

        return response


# Vista protegida de ejemplo que solo permite acceso a usuarios autenticados
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    # Responde con mensaje indicando que el token es válido y se concedió acceso
    return Response({'message': 'Acceso concedido: tu token es válido.'})


# Vista para obtener el perfil del usuario autenticado
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados

    def get(self, request):
        # Serializa los datos del usuario que hizo la petición
        serializer = UsuarioSerializer(request.user)
        # Devuelve los datos serializados en la respuesta
        return Response(serializer.data)


# Vista para solicitar el reseteo de contraseña
class RequestPasswordResetAPIView(generics.GenericAPIView):
    throttle_classes = [UserRateThrottle]  # Limita la cantidad de solicitudes para evitar abusos
    permission_classes = [AllowAny]  # Permite acceso público (no requiere autenticación)
    serializer_class = PasswordResetRequestSerializer    

    def post(self, request):
        # Valida los datos recibidos (espera un email)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Busca usuario por email
        user = User.objects.filter(email=email).first()
        if not user:
            # Por seguridad no indica si el email no existe para no filtrar usuarios
            return Response({"detail": "Si existe, recibirás un email."}, status=200)

        # Codifica el ID de usuario para incluirlo en el link
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        # Genera un token seguro para el restablecimiento de contraseña
        token = token_generator.make_token(user)

        # Construye el enlace completo para el frontend
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        reset_link = f"{frontend_url}/resetPassword/{uidb64}/{token}/"

        # Envía email con el enlace para restablecer la contraseña
        send_mail(
            subject="Recupera tu contraseña",
            message=f"Pulsa este enlace para restablecer tu contraseña:\n\n{reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        # Mensaje genérico para evitar revelar si el email existe o no
        return Response({"detail": "Si existe, recibirás un email."}, status=200)


# Vista para confirmar el reseteo de contraseña con el token y nueva contraseña
class PasswordResetConfirmAPIView(generics.GenericAPIView):
    permission_classes = []  # Permite acceso público (para que el usuario pueda resetear)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        # Valida el token, uid y nueva contraseña recibidos
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            # Decodifica el uid para obtener el usuario
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Link inválido."}, status=400)

        # Verifica que el token sea válido y no haya expirado
        if not token_generator.check_token(user, token):
            return Response({"detail": "Token inválido o expirado."}, status=400)

        # Establece la nueva contraseña y guarda el usuario
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Contraseña restablecida con éxito."}, status=200)


# Vista para cerrar sesión eliminando las cookies de acceso y refresco
class LogoutView(APIView):
    def post(self, request):
        # Crea una respuesta con mensaje de éxito
        response = Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)
        # Borra cookie de access_token
        response.delete_cookie(
            key='access_token',
            path='/',
            samesite='None',
        )
        # Borra cookie de refresh_token
        response.delete_cookie(
            key='refresh_token',
            path='/',
            samesite='None',
        )
        # Retorna la respuesta con cookies eliminadas
        return response


# Vista para recibir mensajes de contacto desde la web y enviarlos por email
@api_view(['POST'])
def contacto_view(request):
    # Obtiene datos del formulario enviado
    nombre = request.data.get('nombre')
    email = request.data.get('email')
    asunto = request.data.get('asunto')
    mensaje = request.data.get('mensaje')

    # Contexto para renderizar la plantilla HTML del email
    context = {
        'nombre': nombre,
        'email': email,
        'asunto': asunto,
        'mensaje': mensaje,
    }

    # Renderiza el contenido HTML del email usando plantilla
    html_content = render_to_string('email/contacto_recibido.html', context)

    # Prepara el email con asunto, texto plano y contenido HTML
    email_message = EmailMultiAlternatives(
        subject=f"[Contacto Web] {asunto}",
        body=mensaje,  # Texto plano como respaldo
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.DEFAULT_FROM_EMAIL]
    )
    # Adjunta la versión HTML
    email_message.attach_alternative(html_content, "text/html")
    # Envía el email
    email_message.send()

    # Respuesta JSON confirmando envío
    return Response({"mensaje": "Correo enviado correctamente"})


# Vista para que un usuario autenticado pueda eliminar su cuenta
class EliminarCuentaView(APIView):
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados

    def delete(self, request):
        user = request.user
        # Borra el usuario de la base de datos
        user.delete()
        # Responde con mensaje y código 204 No Content
        return Response({"mensaje": "Cuenta eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)

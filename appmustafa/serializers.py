from rest_framework import serializers
from .models import Animal, Noticia, Comentario, Adopcion
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.html import format_html
from django.contrib.auth import get_user_model

User = get_user_model()

class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = '__all__'
        
    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value

class NoticiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Noticia
        fields = '__all__'

MAX_NIVEL_RESPUESTA = 5  # Nivel máximo permitido
from rest_framework import serializers
from .models import Comentario

MAX_NIVEL_RESPUESTA = 3  # Ajusta según tu lógica

class ComentarioSerializer(serializers.ModelSerializer):
    respuestas = serializers.SerializerMethodField()
    usuario_username = serializers.SerializerMethodField()
    usuario_foto = serializers.SerializerMethodField()
    noticia_titulo = serializers.SerializerMethodField()
    parent_contenido = serializers.SerializerMethodField()
    noticia_id = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = [
            'id',
            'noticia',
            'noticia_titulo',
            'usuario',
            'usuario_username',
            'usuario_foto',
            'contenido',
            'fecha_hora',
            'parent',
            'parent_contenido',
            'respuestas',
            'noticia_id'
        ]
        read_only_fields = ['usuario']

    def validate(self, data):
        parent = data.get('parent')
        nivel = 1

        while parent:
            nivel += 1
            if nivel > MAX_NIVEL_RESPUESTA:
                raise serializers.ValidationError(
                    f"No se permite responder más allá del nivel {MAX_NIVEL_RESPUESTA}."
                )
            parent = parent.parent

        return data

    def get_respuestas(self, obj):
        if obj.respuestas.exists():
            return ComentarioSerializer(obj.respuestas.all().order_by('fecha_hora'), many=True).data
        return []

    def get_usuario_username(self, obj):
        return obj.usuario.username

    def get_usuario_foto(self, obj):
        request = self.context.get('request')
        if hasattr(obj.usuario, 'foto_perfil') and obj.usuario.foto_perfil:
            if request:
                return request.build_absolute_uri(obj.usuario.foto_perfil.url)
            return obj.usuario.foto_perfil.url  # fallback por si no hay request
        return None

    def get_noticia_titulo(self, obj):
        return obj.noticia.titulo if obj.noticia else None

    def get_parent_contenido(self, obj):
        return obj.parent.contenido if obj.parent else None
    
    def get_noticia_id(self, obj):
        return obj.noticia.id if obj.noticia else None
    
    def validate_contenido(self, value):
        if not value.strip():
            raise serializers.ValidationError("El comentario no puede estar vacío.")
        return value


class AdopcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adopcion
        fields = '__all__'

    def validate(self, data):
        usuario = data.get('usuario')
        animal = data.get('animal')

        if self.instance is None:  # Solo validar en creación
            if Adopcion.objects.filter(animal=animal, usuario=usuario).exists():
                raise serializers.ValidationError("Ya has enviado una solicitud para este animal.")
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'password', 'foto_perfil', 'recibir_novedades', 'is_staff'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'recibir_novedades': {'required': False},
            'foto_perfil': {'required': False},
        }

    def validate_username(self, value):
        if self.Meta.model.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value

    def validate_email(self, value):
        if self.Meta.model.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value
    
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("La contraseña debe contener al menos un número.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = self.Meta.model(**validated_data)
        user.set_password(password)
        user.save()

        # Envío de correo de bienvenida
        nombre_para_saludo = user.first_name or user.username
        email = EmailMessage(
            subject='¡Bienvenido a nuestra plataforma!',
            body=format_html(f"""
            <div style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 30px;">
                <div style="max-width: 600px; margin: auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
                        <h1>¡Bienvenido, {nombre_para_saludo}! 🌟</h1>
                    </div>
                    <div style="padding: 30px; color: #333;">
                        <p>Gracias por registrarte en nuestra plataforma. ¡Estamos encantados de tenerte con nosotros!</p>
                        <p>Esperamos que disfrutes de todas las funcionalidades y te animes a explorar todo lo que tenemos para ofrecer.</p>
                        <p style="margin-top: 30px;">— El equipo de <strong>Animales Masquefa</strong></p>
                    </div>
                    <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                        <p>Este correo ha sido enviado automáticamente. Por favor, no respondas a este mensaje.</p>
                    </div>
                </div>
            </div>
            """),
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],
        )
        email.content_subtype = "html"
        email.encoding = 'utf-8'
        email.send(fail_silently=False)

        return user
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("La contraseña debe contener al menos un número.")
        return value

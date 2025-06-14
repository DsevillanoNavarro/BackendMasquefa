# Importaciones necesarias para definir rutas (endpoints) y para servir archivos estáticos en modo desarrollo
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importa las vistas y viewsets definidas en la app para usarlas en las rutas
from .views import (
    AnimalViewSet, UsuarioViewSet, NoticiaViewSet, ComentarioViewSet, AdopcionViewSet,
    CookieTokenObtainPairView, CookieTokenRefreshView,
    protected_view, ProfileView,
    PasswordResetConfirmAPIView, RequestPasswordResetAPIView,
    LogoutView, contacto_view, EliminarCuentaView
)

from django.conf import settings
from django.conf.urls.static import static

# Importa vistas de la librería simplejwt por si se usan (aunque aquí no se usan directamente)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


# Crea un router por defecto para registrar automáticamente las rutas de los ViewSets (API REST)
router = DefaultRouter()
router.register(r'animales', AnimalViewSet)    # Rutas para operaciones CRUD de animales
router.register(r'usuarios', UsuarioViewSet)   # Rutas para usuarios
router.register(r'noticias', NoticiaViewSet)   # Rutas para noticias
router.register(r'comentarios', ComentarioViewSet) # Rutas para comentarios
router.register(r'adopciones', AdopcionViewSet)    # Rutas para adopciones


# Definición de las rutas URL de la API y sus vistas asociadas
urlpatterns = [
    # Ruta para obtener token JWT, usando vista personalizada que guarda token en cookies
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Ruta para refrescar token JWT usando token guardado en cookies
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),

    # Ruta para cerrar sesión, elimina las cookies de tokens
    path('logout/', LogoutView.as_view(), name='logout'),

    # Ruta protegida de ejemplo que requiere autenticación
    path('protected/', protected_view, name='api_protected'),

    # Ruta para obtener datos del perfil del usuario autenticado
    path('me/', ProfileView.as_view(), name='user-profile'),

    # Ruta para solicitar el reseteo de contraseña (envía email con link)
    path('password-reset/', RequestPasswordResetAPIView.as_view(), name='password-reset'),

    # Ruta para confirmar y cambiar la contraseña usando token recibido por email
    path('password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),

    # Ruta para enviar mensaje de contacto desde el frontend
    path('contacto/', contacto_view, name='contacto'),

    # Ruta para eliminar la cuenta del usuario autenticado
    path('usuarios/eliminar/', EliminarCuentaView.as_view(), name='eliminar-cuenta'),

    # Incluye todas las rutas generadas automáticamente por el router para los ViewSets
    path('', include(router.urls)),
]

# Si estamos en modo DEBUG (desarrollo), añade rutas para servir archivos multimedia (media)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

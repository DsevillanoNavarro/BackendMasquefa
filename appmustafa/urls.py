from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnimalViewSet, UsuarioViewSet, NoticiaViewSet, ComentarioViewSet, AdopcionViewSet, CookieTokenObtainPairView, CookieTokenRefreshView, protected_view, ProfileView, PasswordResetConfirmAPIView, RequestPasswordResetAPIView, LogoutView, contacto_view
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

router = DefaultRouter()
router.register(r'animales', AnimalViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'noticias', NoticiaViewSet)
router.register(r'comentarios', ComentarioViewSet)
router.register(r'adopciones', AdopcionViewSet)

urlpatterns = [
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('protected/', protected_view, name='api_protected'),
    path('me/', ProfileView.as_view(), name='user-profile'),
    path('password-reset/', RequestPasswordResetAPIView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),
    path('contacto/', contacto_view, name='contacto'),
    path('', include(router.urls)),
    
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
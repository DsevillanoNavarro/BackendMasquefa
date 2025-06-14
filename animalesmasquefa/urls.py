"""
Configuración de URLs para el proyecto 'animalesmasquefa'.

Define cómo se enrutan las URLs a las vistas correspondientes.
Más info: https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import IsAdminUser
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test


def admin_required(view_func):
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_staff,  # puedes usar is_superuser si prefieres
        login_url='/admin/login/',  # Redirección si no cumple
        redirect_field_name='next'  # Redirige de vuelta después de login
    )(view_func)
    return decorated_view_func


schema_view = get_schema_view(
   openapi.Info(
      title="API AnimalesMasquefa",
      default_version='v1',
      description="Solo para admins 👑",
      contact=openapi.Contact(email="admin@masquefa.com"),
      license=openapi.License(name="MIT"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),  # lo controlamos con decorador
)

urlpatterns = [
    # Ruta al panel de administración de Django
    path('admin/', admin.site.urls),

    # URLs para Jet Dashboard (interfaz de administración mejorada)
    path('jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),

    # URLs para Jet (interfaz base del admin mejorada)
    path('jet/', include('jet.urls', 'jet')),

    # Rutas de la API principal del proyecto (appmustafa)
    path('api/', include('appmustafa.urls')),
    
    # Swagger solo visible para admins
    path('swagger/', admin_required(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),

    # Opcional: también Redoc
    path('redoc/', admin_required(schema_view.with_ui('redoc', cache_timeout=0)), name='schema-redoc'),
    
]

# Configura la entrega de archivos multimedia en modo desarrollo
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

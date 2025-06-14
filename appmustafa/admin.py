from django.contrib import admin
from .models import *  # Importa todos los modelos definidos en la app
from auditlog.models import LogEntry  # Modelo de auditoría
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser  # Modelo de usuario personalizado
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# Define la URL del sitio visible en el panel de administración (por ejemplo, para redirigir al frontend)
admin.site.site_url = getattr(settings, 'FRONTEND_URL', '/')

# Registro de modelos en el panel de administración
admin.site.register(CustomUser, UserAdmin)  # Usa la interfaz estándar de Django para usuarios
admin.site.register(Animal)
admin.site.register(Noticia)
admin.site.register(Comentario)
admin.site.register(Adopcion)

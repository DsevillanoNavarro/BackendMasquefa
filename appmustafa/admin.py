from django.contrib import admin
from .models import *
from auditlog.models import LogEntry
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django import forms
from django.contrib import admin
from django.conf import settings

admin.site.site_url = getattr(settings, 'FRONTEND_URL', '/')

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Animal)
admin.site.register(Noticia)
admin.site.register(Comentario)
admin.site.register(Adopcion)


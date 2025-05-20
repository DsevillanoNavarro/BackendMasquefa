from django.contrib import admin
from .models import *
from auditlog.models import LogEntry

# Register your models here.
admin.site.register(Animal)
admin.site.register(Noticia)
admin.site.register(Comentario)
admin.site.register(Adopcion)


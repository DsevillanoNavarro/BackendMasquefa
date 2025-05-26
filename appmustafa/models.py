from django.db import models
from django.utils import timezone
from datetime import date
from django.core.exceptions import ValidationError
from auditlog.registry import auditlog
from django.contrib.auth.models import AbstractUser  # ✅ esto sí debe quedarse
from django.conf import settings  # ✅ para ForeignKey con AUTH_USER_MODEL

class Animal(models.Model):
    nombre = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField()
    edad = models.PositiveIntegerField(editable=False, null=True, blank=True)
    situacion = models.TextField(max_length=750)
    imagen = models.ImageField(upload_to='animales/')

    class Meta:
        verbose_name = 'Animal'
        verbose_name_plural = 'Animales'

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.fecha_nacimiento > date.today():
            raise ValidationError("La fecha de nacimiento no puede ser en el futuro.")
    
    def calcular_edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return (
                today.year - self.fecha_nacimiento.year
                - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
            )
        return None

    def save(self, *args, **kwargs):
        self.edad = self.calcular_edad()
        super().save(*args, **kwargs)
        


class Noticia(models.Model):
    titulo = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='noticias/')
    contenido = models.TextField(max_length=1000)
    fecha_publicacion = models.DateField()

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'

    def __str__(self):
        return self.titulo


class Comentario(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name="comentarios")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios")
    contenido = models.TextField(max_length=1000)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='respuestas')


    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        return f'{self.usuario.username} - {self.contenido[:20]}'

    def tiempo_transcurrido(self):
        delta = timezone.now() - self.fecha_hora
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        elif seconds < 86400:
            return f"{int(seconds // 3600)}h"
        elif seconds < 2592000:
            return f"{int(seconds // 86400)}d"
        else:
            return f"{int(seconds // 2592000)}mo"


def validate_pdf(file):
    if not file.name.endswith('.pdf'):
        raise ValidationError("Solo se permiten archivos PDF.")


def pdf_upload_path(instance, filename):
    return f'adopciones/{instance.usuario.id}/{filename}'


class Adopcion(models.Model):
    ESTADOS_ADOPCION = [
        ('Aceptada', 'Aceptada'),
        ('Rechazada', 'Rechazada'),
        ('Pendiente', 'Pendiente'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="adopciones")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="adopciones")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    aceptada = models.CharField(max_length=10, choices=ESTADOS_ADOPCION, default='Pendiente')
    contenido = models.FileField(upload_to=pdf_upload_path, validators=[validate_pdf])

    class Meta:
        verbose_name = 'Adopcion'
        verbose_name_plural = 'Adopciones'

    def __str__(self):
        return self.animal.nombre
    
    def clean(self):
        # No permitir múltiples adopciones aceptadas para un animal
        if self.aceptada == 'Aceptada':
            if Adopcion.objects.filter(animal=self.animal, aceptada='Aceptada').exclude(id=self.id).exists():
                raise ValidationError("Este animal ya fue adoptado.")

        # No permitir más de una solicitud por el mismo usuario al mismo animal
        if Adopcion.objects.filter(animal=self.animal, usuario=self.usuario).exclude(id=self.id).exists():
            raise ValidationError("Ya has enviado una solicitud para adoptar a este animal.")


class CustomUser(AbstractUser):
    foto_perfil = models.ImageField(upload_to='usuarios/perfiles/', null=True, blank=True)
    recibir_novedades = models.BooleanField(default=False)

    def __str__(self):
        return self.username

# ——— Después de definir **todas** tus clases, las registras: ———
auditlog.register(Animal)
auditlog.register(Noticia)
auditlog.register(Comentario)
auditlog.register(Adopcion)

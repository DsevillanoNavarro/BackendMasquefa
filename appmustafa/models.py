# Importaciones necesarias de Django, librerías de terceros y utilidades
from django.db import models
from django.utils import timezone
from datetime import date
from django.core.exceptions import ValidationError
from auditlog.registry import auditlog  # Para registrar auditorías (si se usa)
from django.contrib.auth.models import AbstractUser  # Modelo base para usuarios personalizados
from django.conf import settings  
from PIL import Image  # Pillow, para procesar imágenes
from io import BytesIO
from django.core.files.base import ContentFile  # Para crear archivos desde memoria

# Librerías de Cloudinary
import cloudinary
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from cloudinary.models import CloudinaryField

# ==============================
# Modelo Animal
# ==============================
class Animal(models.Model):
    nombre = models.CharField(max_length=50)  # Nombre del animal
    fecha_nacimiento = models.DateField()     # Fecha de nacimiento
    edad = models.PositiveIntegerField(editable=False, null=True, blank=True)  # Edad calculada automáticamente
    situacion = models.TextField(max_length=750)  # Descripción o situación actual del animal
    # Imagen en Cloudinary
    imagen = CloudinaryField('imagen', folder='animales', default='pexels-leonardo-de-oliveira-872270-1770918_yp2wtl', blank=False, null=False)

    class Meta:
        verbose_name = 'Animal'
        verbose_name_plural = 'Animales'

    def __str__(self):
        return self.nombre or "Animal sin nombre"

    # Validación para asegurar que la fecha de nacimiento no sea futura
    def clean(self):
        if self.fecha_nacimiento > date.today():
            raise ValidationError("La fecha de nacimiento no puede ser en el futuro.")
    
    # Calcula la edad actual en años
    def calcular_edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return (
                today.year - self.fecha_nacimiento.year
                - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
            )
        return None

    # Al guardar, se actualiza automáticamente la edad
    def save(self, *args, **kwargs):
        self.edad = self.calcular_edad()
        super().save(*args, **kwargs)


# ==============================
# Modelo Noticia
# ==============================
class Noticia(models.Model):
    titulo = models.CharField(max_length=100)              # Título de la noticia
    # Imagen en Cloudinary
    imagen = CloudinaryField('imagen', folder='noticias', default='pexels-bekka419-804475_gpv7j8')  # Imagen relacionada
    contenido = models.TextField(max_length=1000)          # Texto de la noticia
    fecha_publicacion = models.DateField()                 # Fecha de publicación

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'

    def __str__(self):
        return self.titulo or "Noticia sin título"


# ==============================
# Modelo Comentario
# ==============================
class Comentario(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name="comentarios")  # Noticia relacionada
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios")  # Usuario que comenta
    contenido = models.TextField(max_length=1000)  # Texto del comentario
    fecha_hora = models.DateTimeField(auto_now_add=True)  # Fecha y hora de creación
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='respuestas')  # Comentario padre para hilos

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        return f'{self.usuario.username} - {self.contenido[:20]}'

    # Calcula cuánto tiempo ha pasado desde que se creó el comentario
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


# ==============================
# Validación y path para PDF en adopciones
# ==============================
def validate_pdf(file):
    if not file.name.lower().endswith('.pdf'):
        raise ValidationError("Solo se permiten archivos PDF.")

# Define el path de subida del PDF usando el ID del usuario
def pdf_upload_path(instance, filename):
    return f'adopciones/{instance.usuario.id}/{filename}'


# ==============================
# Modelo Adopcion
# ==============================
class Adopcion(models.Model):
    ESTADOS_ADOPCION = [
        ('Aceptada', 'Aceptada'),
        ('Rechazada', 'Rechazada'),
        ('Pendiente', 'Pendiente'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="adopciones", db_index=True)  # Animal adoptado
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="adopciones", db_index=True)  # Usuario adoptante
    fecha_hora = models.DateTimeField(auto_now_add=True)  # Fecha de solicitud
    aceptada = models.CharField(max_length=10, choices=ESTADOS_ADOPCION, default='Pendiente')  # Estado actual
    # PDF con formulario o info en Cloudinary como recurso raw
    contenido = models.FileField(
        upload_to=pdf_upload_path,
        storage=RawMediaCloudinaryStorage(),
        validators=[validate_pdf]
    )

    class Meta:
        verbose_name = 'Adopcion'
        verbose_name_plural = 'Adopciones'

    def __str__(self):
        return f"{self.animal.nombre} por {self.usuario.username}"

    # Validaciones personalizadas
    def clean(self):
        if self.pk:  # Si la solicitud ya existe
            estado_original = Adopcion.objects.get(pk=self.pk).aceptada
        else:
            estado_original = None

        # No se puede aceptar más de una adopción por animal
        if self.aceptada == 'Aceptada' and estado_original != 'Aceptada':
            if Adopcion.objects.filter(animal=self.animal, aceptada='Aceptada').exclude(pk=self.pk).exists():
                raise ValidationError("Este animal ya fue adoptado.")

        # Un usuario no puede hacer más de una solicitud por el mismo animal
        if Adopcion.objects.filter(animal=self.animal, usuario=self.usuario).exclude(pk=self.pk).exists():
            raise ValidationError("Ya has enviado una solicitud para adoptar a este animal.")


# ==============================
# Modelo CustomUser
# ==============================
class CustomUser(AbstractUser):
    # Avatar o foto del perfil en Cloudinary
    foto_perfil = CloudinaryField(
        'foto_perfil',
        folder='usuarios/perfiles',
        default='default_wtx8r7', 
        blank=False, 
        null=False
        )
    recibir_novedades = models.BooleanField(default=False)  # Boletín de novedades, etc.

    def __str__(self):
        return self.username

# Registro para auditoría si se utiliza auditlog
auditlog.register(Animal, exclude_fields=['imagen'])
auditlog.register(Noticia, exclude_fields=['imagen'])
auditlog.register(Comentario)
auditlog.register(Adopcion, exclude_fields=['contenido'])
auditlog.register(CustomUser, exclude_fields=['foto_perfil'])
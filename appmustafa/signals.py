from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Animal, Noticia, Adopcion
from appmustafa.utils.email import enviar_email_html
import cloudinary.uploader

User = get_user_model()

DEFAULT_IMAGEN_ANIMAL = 'pexels-leonardo-de-oliveira-872270-1770918_yp2wtl'
DEFAULT_IMAGEN_USUARIO = 'default_wtx8r7'
DEFAULT_IMAGEN_NOTICIA = 'pexels-bekka419-804475_gpv7j8'

# -----------------------------
# MANEJO DE ARCHIVOS OBSOLETOS
# -----------------------------
@receiver(pre_save, sender=Animal)
def borrar_imagen_anterior_animal(sender, instance, **kwargs):
    # Si es creación, nada que hacer
    if not instance.pk:
        return
    try:
        anterior = Animal.objects.get(pk=instance.pk)
    except Animal.DoesNotExist:
        return

    # Si cambió la imagen (el public_id cambia cuando sube la nueva)
    if anterior.imagen and anterior.imagen.public_id != getattr(instance.imagen, 'public_id', None):
        if anterior.imagen.public_id != DEFAULT_IMAGEN_ANIMAL:
            cloudinary.uploader.destroy(anterior.imagen.public_id, invalidate=True)



@receiver(pre_save, sender=User)
def borrar_foto_anterior_usuario(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        anterior = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if anterior.foto_perfil and anterior.foto_perfil.public_id != getattr(instance.foto_perfil, 'public_id', None):
        if anterior.foto_perfil.public_id != DEFAULT_IMAGEN_USUARIO:
            cloudinary.uploader.destroy(anterior.foto_perfil.public_id, invalidate=True)


@receiver(pre_save, sender=Adopcion)
def borrar_pdf_anterior_adopcion(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        anterior = Adopcion.objects.get(pk=instance.pk)
    except Adopcion.DoesNotExist:
        return

    # Para archivos raw, el public_id es el nombre sin extensión
    old_name = anterior.contenido.name or ''
    new_name = getattr(instance.contenido, 'name', '')
    if old_name and old_name != new_name:
        public_id = old_name.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        cloudinary.uploader.destroy(public_id, resource_type='raw', invalidate=True)


# ----------------------------
# LIMPIEZA TRAS ELIMINACIONES
# ----------------------------
@receiver(post_delete, sender=Animal)
def eliminar_imagen_animal(sender, instance, **kwargs):
    if instance.imagen and instance.imagen.public_id != DEFAULT_IMAGEN_ANIMAL:
        cloudinary.uploader.destroy(instance.imagen.public_id, invalidate=True)


@receiver(post_delete, sender=User)
def eliminar_imagen_usuario(sender, instance, **kwargs):
    if instance.foto_perfil and instance.foto_perfil.public_id != DEFAULT_IMAGEN_USUARIO:
        cloudinary.uploader.destroy(instance.foto_perfil.public_id, invalidate=True)

@receiver(post_delete, sender=Noticia)
def eliminar_imagen_noticia(sender, instance, **kwargs):
    if instance.imagen and instance.imagen.public_id != DEFAULT_IMAGEN_NOTICIA:
        cloudinary.uploader.destroy(instance.imagen.public_id, invalidate=True)


@receiver(post_delete, sender=Adopcion)
def eliminar_pdf_adopcion(sender, instance, **kwargs):
    if instance.contenido:
        name = instance.contenido.name or ''
        public_id = name.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        cloudinary.uploader.destroy(public_id, resource_type='raw', invalidate=True)


# --------------------------------
# NOTIFICACIONES POR CORREO
# --------------------------------

@receiver(post_save, sender=Adopcion)
def gestionar_estado_adopcion(sender, instance, created, **kwargs):
    usuario = instance.usuario
    animal = instance.animal

    imagen_url = (
        f"{settings.CLOUDINARY_BASE_URL}{instance.imagen.public_id}.jpg"
        if hasattr(animal.imagen, 'public_id') else
        f"{settings.CLOUDINARY_BASE_URL}${DEFAULT_IMAGEN_ANIMAL}.jpg"
    )

    imagen_path = (
        f"{settings.CLOUDINARY_BASE_URL}{instance.imagen.public_id}.jpg"
        if hasattr(animal.imagen, 'public_id') else
        f"{settings.CLOUDINARY_BASE_URL}{DEFAULT_IMAGEN_ANIMAL}.jpg"
    )


    if not created and instance.aceptada == 'Aceptada':
        contexto = {
            'usuario': usuario,
            'animal': animal.nombre,
            'imagen_url': imagen_url,
            'frontend_url': settings.FRONTEND_URL,
        }
        enviar_email_html(
            destinatario=usuario.email,
            asunto=f"¡Tu adopción de {animal.nombre} ha sido aceptada! 🐾",
            plantilla="email/adopcion_aceptada.html",
            contexto=contexto,
            imagenes_inline={'imagen_animal': imagen_path}
        )

        otras = Adopcion.objects.filter(animal=animal, aceptada='Pendiente').exclude(pk=instance.pk)
        for pet in otras:
            pet.aceptada = 'Rechazada'
            pet.save()

    elif not created and instance.aceptada == 'Rechazada':
        contexto = {
            'usuario': usuario,
            'animal': animal.nombre,
            'imagen_url': imagen_url,
            'frontend_url': settings.FRONTEND_URL,
        }
        enviar_email_html(
            destinatario=usuario.email,
            asunto=f"Adopción de {animal.nombre} - No has sido seleccionado 😿",
            plantilla="email/adopcion_rechazada.html",
            contexto=contexto,
            imagenes_inline={'imagen_animal': imagen_path}
        )


@receiver(post_save, sender=Adopcion)
def notificar_adopcion_admin(sender, instance, created, **kwargs):
    if created:
        contexto = {
            "usuario": instance.usuario,
            "animal": instance.animal.nombre,
            "fecha": instance.fecha_hora.strftime("%d/%m/%Y %H:%M"),
        }
        enviar_email_html(
            destinatario=settings.EMAIL_HOST_USER,
            asunto="🐾 Nueva adopción registrada",
            plantilla="email/nueva_adopcion.html",
            contexto=contexto
        )


@receiver(post_save, sender=Animal)
def notificar_nuevo_animal(sender, instance, created, **kwargs):
    if created:
        usuarios = User.objects.filter(recibir_novedades=True)

        imagen_url = (
            f"{settings.CLOUDINARY_BASE_URL}{instance.imagen.public_id}.jpg"
            if hasattr(instance.imagen, 'public_id') else
            f"{settings.CLOUDINARY_BASE_URL}{DEFAULT_IMAGEN_ANIMAL}.jpg"
        )
        imagen_path = imagen_url  # Cloudinary no usa paths locales

        for user in usuarios:
            contexto = {
                'usuario': user,
                'animal': instance,
                'animal_url': f"{settings.FRONTEND_URL}/animales",
                'imagen_url': imagen_url,
            }
            enviar_email_html(
                destinatario=user.email,
                asunto="🐾 Nuevo animal disponible para adopción",
                plantilla="email/nuevo_animal.html",
                contexto=contexto,
                imagenes_inline={'imagen_animal': imagen_path}
            )



@receiver(post_save, sender=Noticia)
def notificar_nueva_noticia(sender, instance, created, **kwargs):
    if created:
        usuarios = User.objects.filter(recibir_novedades=True)

        imagen_url = (
            f"{settings.CLOUDINARY_BASE_URL}{instance.imagen.public_id}.jpg"
            if hasattr(instance.imagen, 'public_id') else
            f"{settings.CLOUDINARY_BASE_URL}{DEFAULT_IMAGEN_NOTICIA}.jpg"
        )
        imagen_path = imagen_url  # Cloudinary no usa paths locales

        for user in usuarios:
            contexto = {
                'usuario': user,
                'noticia': instance,
                'noticia_url': f"{settings.FRONTEND_URL}/noticias",
                'imagen_url': imagen_url,
            }
            enviar_email_html(
                destinatario=user.email,
                asunto="📰 Nueva noticia publicada",
                plantilla="email/nueva_noticia.html",
                contexto=contexto,
                imagenes_inline={'imagen_noticia': imagen_path}
            )
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Animal, Noticia, Adopcion
from appmustafa.utils.email import enviar_email_html  # 🆕 función reutilizable

User = get_user_model()


@receiver(post_save, sender=Adopcion)
def enviar_email_adopcion_aceptada(sender, instance, created, **kwargs):
    if not created and instance.aceptada == 'Aceptada':
        usuario = instance.usuario
        animal = instance.animal

        imagen_path = animal.imagen.path if animal.imagen else "media/default-cat.jpg"
        imagen_url = f"{settings.BACKEND_URL}{animal.imagen.url}" if animal.imagen else f"{settings.BACKEND_URL}/media/default-cat.jpg"

        contexto = {
            'usuario': usuario,
            'animal': animal.nombre,
            'imagen_url': imagen_url,
            'frontend_url': settings.FRONTEND_URL,
        }

        # Email de aceptación
        enviar_email_html(
            destinatario=usuario.email,
            asunto=f"¡Tu adopción de {animal.nombre} ha sido aceptada! 🐾",
            plantilla="email/adopcion_aceptada.html",
            contexto=contexto,
            imagenes_inline={'imagen_animal': imagen_path}
        )

        # Rechazar automáticamente otras solicitudes
        otras = Adopcion.objects.filter(animal=animal, aceptada='Pendiente').exclude(id=instance.id)
        for pet in otras:
            pet.aceptada = 'Rechazada'
            pet.save()

            contexto_rech = {
                'usuario': pet.usuario,
                'animal': animal.nombre,
                'imagen_url': imagen_url,
                'frontend_url': settings.FRONTEND_URL,
            }

            enviar_email_html(
                destinatario=pet.usuario.email,
                asunto=f"Adopción de {animal.nombre} - No has sido seleccionado 😿",
                plantilla="email/adopcion_rechazada.html",
                contexto=contexto_rech,
                imagenes_inline={'imagen_animal': imagen_path}
            )


@receiver(post_save, sender=Adopcion)
def notificar_adopcion_admin(sender, instance, created, **kwargs):
    if created:
        usuario = instance.usuario
        animal = instance.animal
        fecha = instance.fecha_hora.strftime("%d/%m/%Y %H:%M")

        contexto = {
            "usuario": usuario,
            "animal": animal,
            "fecha": fecha,
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

        imagen_url = f"{settings.BACKEND_URL}{instance.imagen.url}" if instance.imagen else f"{settings.BACKEND_URL}/media/default-cat.jpg"
        imagen_path = instance.imagen.path if instance.imagen else "media/default-cat.jpg"

        contexto_base = {
            'animal': instance,
            'animal_url': f"{settings.FRONTEND_URL}/animales",
            'imagen_url': imagen_url,
        }

        for user in usuarios:
            contexto = {
                'usuario': user,
                **contexto_base
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

        imagen_url = f"{settings.BACKEND_URL}{instance.imagen.url}" if instance.imagen else f"{settings.BACKEND_URL}/media/default-news.jpg"
        imagen_path = instance.imagen.path if instance.imagen else "media/default-news.jpg"

        contexto_base = {
            'noticia': instance,
            'noticia_url': f"{settings.FRONTEND_URL}/noticias",
            'imagen_url': imagen_url,
        }

        for user in usuarios:
            contexto = {
                'usuario': user,
                **contexto_base
            }
            enviar_email_html(
                destinatario=user.email,
                asunto="📰 Nueva noticia publicada",
                plantilla="email/nueva_noticia.html",
                contexto=contexto,
                imagenes_inline={'imagen_noticia': imagen_path}
            )

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Adopcion
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

@receiver(post_save, sender=Adopcion)
def enviar_email_adopcion_aceptada(sender, instance, created, **kwargs):
    if not created and instance.aceptada == 'Aceptada':
        usuario = instance.usuario
        email = usuario.email
        animal = instance.animal.nombre

        # URL de imagen del animal
        if instance.animal.imagen and hasattr(instance.animal.imagen, 'url'):
            imagen_url = f"{settings.FRONTEND_URL}{settings.MEDIA_URL}{instance.animal.imagen}"
        else:
            imagen_url = f"{settings.FRONTEND_URL}/default-cat.jpg"

        context = {
            'usuario': usuario,
            'animal': animal,
            'imagen_url': imagen_url,
            'frontend_url': settings.FRONTEND_URL,
        }

        # Email de aceptación
        html_content = render_to_string('email/adopcion_aceptada.html', context)
        text_content = strip_tags(html_content)
        email_message = EmailMultiAlternatives(
            subject=f"¡Tu adopción de {animal} ha sido aceptada! 🐾",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        # Otras adopciones rechazadas
        otras_adopciones = Adopcion.objects.filter(
            animal=instance.animal,
            aceptada='Pendiente'
        ).exclude(id=instance.id)

        for adopcion in otras_adopciones:
            adopcion.aceptada = 'Rechazada'
            adopcion.save()

            # Email de rechazo
            contexto_rechazo = {
                'usuario': adopcion.usuario,
                'animal': animal,
                'imagen_url': imagen_url,
                'frontend_url': settings.FRONTEND_URL,
            }

            html_rechazo = render_to_string('email/adopcion_rechazada.html', contexto_rechazo)
            texto_rechazo = strip_tags(html_rechazo)

            mensaje_rechazo = EmailMultiAlternatives(
                subject=f"Adopción de {animal} - No has sido seleccionado 😿",
                body=texto_rechazo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[adopcion.usuario.email],
            )
            mensaje_rechazo.attach_alternative(html_rechazo, "text/html")
            mensaje_rechazo.send()

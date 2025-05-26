from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Adopcion
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Animal, Noticia, Adopcion
from django.contrib.auth import get_user_model
from email.mime.image import MIMEImage
from django.core.mail import EmailMessage

User = get_user_model()

@receiver(post_save, sender=Adopcion)
def enviar_email_adopcion_aceptada(sender, instance, created, **kwargs):
    if not created and instance.aceptada == 'Aceptada':
        usuario = instance.usuario
        email = usuario.email
        animal = instance.animal.nombre

        # Construir URL de la imagen (BACKEND)
        if instance.animal.imagen and hasattr(instance.animal.imagen, 'url'):
            imagen_url = f"{settings.BACKEND_URL}{instance.animal.imagen.url}"
        else:
            imagen_url = f"{settings.BACKEND_URL}/media/default-cat.jpg"

        context = {
            'usuario': usuario,
            'animal': animal,
            'imagen_url': imagen_url,
            'frontend_url': settings.FRONTEND_URL,
        }

        # Enviar email de aceptación
        html_content = render_to_string('email/adopcion_aceptada.html', context)
        text_content = strip_tags(html_content)
        mensaje = EmailMultiAlternatives(
            subject=f"¡Tu adopción de {animal} ha sido aceptada! 🐾",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        mensaje.attach_alternative(html_content, 'text/html')
        mensaje.send()

        # Rechazar y notificar otras peticiones pendientes
        otras = Adopcion.objects.filter(animal=instance.animal, aceptada='Pendiente').exclude(id=instance.id)
        for pet in otras:
            pet.aceptada = 'Rechazada'
            pet.save()
            context_rech = {
                'usuario': pet.usuario,
                'animal': animal,
                'imagen_url': imagen_url,
                'frontend_url': settings.FRONTEND_URL,
            }
            html_rech = render_to_string('email/adopcion_rechazada.html', context_rech)
            text_rech = strip_tags(html_rech)
            noti = EmailMultiAlternatives(
                subject=f"Adopción de {animal} - No has sido seleccionado 😿",
                body=text_rech,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[pet.usuario.email],
            )
            noti.attach_alternative(html_rech, 'text/html')
            noti.send()
            
def enviar_email_novedad(usuarios, asunto, plantilla, contexto_base):
    for user in usuarios:
        contexto = {
            'usuario': user,
            **contexto_base
        }
        html_content = render_to_string(plantilla, contexto)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")

        # Adjuntar imagen animal (si aplica)
        animal = contexto_base.get('animal')
        if animal and animal.imagen:
            try:
                with open(animal.imagen.path, 'rb') as f:
                    img_data = f.read()
                image = MIMEImage(img_data)
                image.add_header('Content-ID', '<imagen_animal>')
                image.add_header('Content-Disposition', 'inline', filename=animal.imagen.name)
                email.attach(image)
            except Exception as e:
                print(f"No se pudo adjuntar imagen del animal: {e}")

        # Adjuntar imagen noticia (si aplica)
        noticia = contexto_base.get('noticia')
        if noticia and hasattr(noticia, 'imagen') and noticia.imagen:
            try:
                with open(noticia.imagen.path, 'rb') as f:
                    img_data = f.read()
                image = MIMEImage(img_data)
                image.add_header('Content-ID', '<imagen_noticia>')
                image.add_header('Content-Disposition', 'inline', filename=noticia.imagen.name)
                email.attach(image)
            except Exception as e:
                print(f"No se pudo adjuntar imagen de la noticia: {e}")

        email.send()


@receiver(post_save, sender=Animal)
def notificar_nuevo_animal(sender, instance, created, **kwargs):
    if created:
        usuarios = User.objects.filter(recibir_novedades=True)

        if instance.imagen and hasattr(instance.imagen, 'url'):
            imagen_url = f"{settings.BACKEND_URL}{instance.imagen.url}"  # Combina el dominio con la ruta de imagen
        else:
            imagen_url = f"{settings.BACKEND_URL}/media/default-cat.jpg"

        contexto = {
            'animal': instance,
            'animal_url': f"{settings.FRONTEND_URL}/animales/{instance.id}",
            'imagen_url': imagen_url,
        }

        enviar_email_novedad(usuarios, "🐾 Nuevo animal disponible para adopción", "email/nuevo_animal.html", contexto)




@receiver(post_save, sender=Noticia)
def notificar_nueva_noticia(sender, instance, created, **kwargs):
    if created:
        usuarios = User.objects.filter(recibir_novedades=True)
        contexto = {
            'noticia': instance,
            'noticia_url': f"{settings.FRONTEND_URL}/noticias/{instance.id}",
        }
        enviar_email_novedad(usuarios, "📰 Nueva noticia publicada", "email/nueva_noticia.html", contexto)
        
@receiver(post_save, sender=Adopcion)
def notificar_adopcion_admin(sender, instance, created, **kwargs):
    if created:
        usuario = instance.usuario
        animal = instance.animal
        fecha = instance.fecha_hora.strftime("%d/%m/%Y %H:%M")

        html_content = render_to_string("email/nueva_adopcion.html", {
            "usuario": usuario,
            "animal": animal,
            "fecha": fecha
        })
        plain_text = strip_tags(html_content)

        from django.core.mail import EmailMultiAlternatives

        email = EmailMultiAlternatives(
            subject="🐾 Nueva adopción registrada",
            body=plain_text,
            from_email=settings.EMAIL_HOST_USER,
            to=[settings.EMAIL_HOST_USER],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
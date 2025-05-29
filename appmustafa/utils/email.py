# appmustafa/utils/email.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
from django.conf import settings

def enviar_email_html(destinatario, asunto, plantilla, contexto, imagenes_inline=None):
    """
    Envía un correo HTML con posibilidad de adjuntar imágenes inline.
    
    - destinatario: str o lista con correos
    - asunto: str
    - plantilla: nombre de la plantilla ej. "email/bienvenida.html"
    - contexto: diccionario para renderizar plantilla
    - imagenes_inline: dict { 'cid_nombre': ruta_a_imagen }
    """
    html_content = render_to_string(plantilla, contexto)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=asunto,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destinatario] if isinstance(destinatario, str) else destinatario
    )
    email.attach_alternative(html_content, "text/html")

    if imagenes_inline:
        for cid, ruta in imagenes_inline.items():
            try:
                with open(ruta, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=ruta.split('/')[-1])
                    email.attach(img)
            except Exception as e:
                print(f"No se pudo adjuntar {cid}: {e}")

    email.send(fail_silently=False)

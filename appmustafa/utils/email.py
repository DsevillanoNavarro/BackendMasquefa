from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
from django.conf import settings

def enviar_email_html(destinatario, asunto, plantilla, contexto, imagenes_inline=None):
    """
    Envía un correo en formato HTML, con soporte para imágenes embebidas (inline).

    Parámetros:
    - destinatario: dirección de correo (str) o lista de correos
    - asunto: título del correo
    - plantilla: ruta de la plantilla HTML (ej. "email/bienvenida.html")
    - contexto: diccionario con variables para renderizar la plantilla
    - imagenes_inline: diccionario opcional { 'cid_nombre': 'ruta/a/imagen.png' } para incluir imágenes dentro del HTML
    """

    # Renderiza el contenido HTML desde la plantilla y el contexto proporcionado
    html_content = render_to_string(plantilla, contexto)
    text_content = strip_tags(html_content)  # Versión sin HTML, como respaldo

    # Crea el objeto del correo
    email = EmailMultiAlternatives(
        subject=asunto,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destinatario] if isinstance(destinatario, str) else destinatario
    )

    # Adjunta la versión HTML como alternativa
    email.attach_alternative(html_content, "text/html")

    # Si hay imágenes inline, se adjuntan con su respectivo Content-ID
    if imagenes_inline:
        for cid, ruta in imagenes_inline.items():
            try:
                with open(ruta, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{cid}>')  # Para referenciar en el HTML
                    img.add_header('Content-Disposition', 'inline', filename=ruta.split('/')[-1])
                    email.attach(img)
            except Exception as e:
                print(f"No se pudo adjuntar {cid}: {e}")  # Manejo básico de errores al adjuntar

    # Envía el correo (lanzará excepción si falla)
    email.send(fail_silently=False)

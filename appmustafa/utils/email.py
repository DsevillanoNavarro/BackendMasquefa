from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
from django.conf import settings
from urllib.request import urlopen
import mimetypes

def enviar_email_html(destinatario, asunto, plantilla, contexto, imagenes_inline=None):
    """
    Envía un correo en formato HTML, con soporte para imágenes embebidas (inline).
    Soporta rutas locales y URLs remotas (Cloudinary, etc.)
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
                if ruta.startswith('http://') or ruta.startswith('https://'):
                    # Descargar desde URL remota
                    response = urlopen(ruta)
                    img_data = response.read()
                    content_type = response.info().get_content_type()
                    main_type, sub_type = content_type.split('/')
                else:
                    # Leer desde archivo local
                    with open(ruta, 'rb') as f:
                        img_data = f.read()
                    mime_type, _ = mimetypes.guess_type(ruta)
                    if mime_type:
                        main_type, sub_type = mime_type.split('/')
                    else:
                        main_type, sub_type = 'image', 'png'

                img = MIMEImage(img_data, _subtype=sub_type)
                img.add_header('Content-ID', f'<{cid}>')
                img.add_header('Content-Disposition', 'inline', filename=cid)
                email.attach(img)

            except Exception as e:
                print(f"[Email] No se pudo adjuntar imagen '{cid}': {e}")

    email.send(fail_silently=False)

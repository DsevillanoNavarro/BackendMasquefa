from django.core.management.base import BaseCommand
from django.core.files.storage import FileSystemStorage
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.core.files.base import ContentFile
from django.core.files import File  # ¡IMPORTANTE!
from django.conf import settings
from pathlib import Path
from appmustafa.models import CustomUser, Animal, Noticia, Adopcion
import os

class Command(BaseCommand):
    help = "Migra archivos locales a Cloudinary"

    def handle(self, *args, **kwargs):
        local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        cloudinary_storage = MediaCloudinaryStorage()

        total_migrados = 0
        total_omitidos = 0

        modelos = [
            (CustomUser, 'foto_perfil'),
            (Animal, 'imagen'),
            (Noticia, 'imagen'),
            (Adopcion, 'contenido'),
        ]

        for Modelo, campo in modelos:
            objetos = Modelo.objects.exclude(**{f"{campo}": ""})
            for obj in objetos:
                archivo = getattr(obj, campo)
                ruta_relativa = archivo.name
                ruta_local = Path(settings.MEDIA_ROOT) / ruta_relativa

                if archivo and hasattr(archivo, 'url') and "res.cloudinary.com" in archivo.url:
                    self.stdout.write(f"⏩ Ya migrado: {archivo.url}")
                    continue

                if ruta_local.exists():
                    try:
                        with local_storage.open(ruta_relativa, 'rb') as f:
                            content = ContentFile(f.read())

                        # Subida a Cloudinary y reapertura como archivo
                        nombre_archivo = os.path.basename(ruta_relativa)
                        nuevo_nombre = cloudinary_storage.save(nombre_archivo, content)
                        archivo_cloudinary = cloudinary_storage.open(nuevo_nombre)

                        # Guardar en el campo como archivo completo (File)
                        setattr(obj, campo, File(archivo_cloudinary, name=nuevo_nombre))
                        obj.save()

                        # Mostrar URL Cloudinary final
                        nuevo_archivo = getattr(obj, campo)
                        self.stdout.write(self.style.SUCCESS(f"✅ Migrado a Cloudinary: {nuevo_archivo.url}"))

                        total_migrados += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Error en {ruta_relativa}: {e}"))
                        total_omitidos += 1
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  No encontrado: {ruta_local}"))
                    total_omitidos += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n📦 Migración finalizada: {total_migrados} subidos, {total_omitidos} omitidos."
        ))

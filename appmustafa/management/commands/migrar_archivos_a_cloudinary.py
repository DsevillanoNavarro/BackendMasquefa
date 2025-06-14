from django.core.management.base import BaseCommand
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
from appmustafa.models import CustomUser, Animal, Noticia, Adopcion
import os

class Command(BaseCommand):
    help = "Migra archivos locales (imágenes y PDFs) a Cloudinary"

    def handle(self, *args, **kwargs):
        local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
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

                if ruta_local.exists():
                    try:
                        f = local_storage.open(ruta_relativa, 'rb')
                        content = ContentFile(f.read())
                        f.close()  # 👈 Evita PermissionError en Windows
                        archivo.save(os.path.basename(archivo.name), content, save=True)
                        self.stdout.write(f"✅ Migrado: {archivo.name}")
                        total_migrados += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Error migrando {archivo.name}: {e}"))
                        total_omitidos += 1
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  Archivo no encontrado: {ruta_local} — se omite."))
                    total_omitidos += 1

        self.stdout.write(self.style.SUCCESS(
            f"📦 Migración finalizada — {total_migrados} archivos migrados, {total_omitidos} omitidos."
        ))

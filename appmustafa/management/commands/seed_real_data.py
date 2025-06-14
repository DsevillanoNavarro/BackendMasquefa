# appmustafa/management/commands/seed_real_data.py

from django.core.management.base import BaseCommand
from faker import Faker
from datetime import timedelta, date
from django.utils.timezone import now
import random
import os
import cloudinary.uploader

from django.db.models.signals import pre_save, post_save, post_delete
from appmustafa import signals
from appmustafa.models import Animal, Noticia, CustomUser, Adopcion, Comentario

# Importa auditlog para desregistrar temporalmente
from auditlog.registry import auditlog

fake = Faker('es_ES')

IMG_DIR = 'media/dummy_animales'
PDF_DUMMY = 'media/dummy_adopcion.pdf'
IMAGENES = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

class Command(BaseCommand):
    help = 'Genera datos falsos y sube a Cloudinary (sin auditar)'

    def handle(self, *args, **kwargs):
        # 0) Desregistrar modelos de Auditlog durante el seed
        for model in [Animal, Noticia, Comentario, Adopcion, CustomUser]:
            try:
                auditlog.unregister(model)
            except Exception:
                pass

        # 1) Desconexión de tus propias señales (igual que antes)
        for sig, sender in [
            (signals.borrar_imagen_anterior_animal, Animal),
            (signals.borrar_foto_anterior_usuario, CustomUser),
            (signals.borrar_pdf_anterior_adopcion, Adopcion),
        ]:
            try: pre_save.disconnect(sig, sender=sender)
            except: pass
        for sig, sender in [
            (signals.eliminar_imagen_animal, Animal),
            (signals.eliminar_imagen_usuario, CustomUser),
            (signals.eliminar_pdf_adopcion, Adopcion),
        ]:
            try: post_delete.disconnect(sig, sender=sender)
            except: pass
        for sig, sender in [
            (signals.gestionar_estado_adopcion, Adopcion),
            (signals.notificar_adopcion_admin, Adopcion),
            (signals.notificar_nuevo_animal, Animal),
            (signals.notificar_nueva_noticia, Noticia),
        ]:
            try: post_save.disconnect(sig, sender=sender)
            except: pass

        # 2) Crear usuarios
        usuarios = []
        for _ in range(10):
            u = CustomUser.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='Kilobyte1',
                recibir_novedades=random.choice([True, False])
            )
            usuarios.append(u)

        # 3) Crear animales y subir a Cloudinary
        for _ in range(30):
            fecha_nac = date.today() - timedelta(days=random.randint(100, 5000))
            fichero = random.choice(IMAGENES)
            ani = Animal.objects.create(
                nombre=fake.first_name(),
                fecha_nacimiento=fecha_nac,
                situacion=fake.paragraph(nb_sentences=15)
            )
            res = cloudinary.uploader.upload(
                os.path.join(IMG_DIR, fichero),
                folder="animales"
            )
            ani.imagen = res["public_id"]
            ani.save()

        # 4) Crear noticias
        for _ in range(8):
            fichero = random.choice(IMAGENES)
            noti = Noticia.objects.create(
                titulo=fake.sentence(nb_words=6),
                contenido=fake.paragraph(nb_sentences=5),
                fecha_publicacion=now().date()
            )
            res = cloudinary.uploader.upload(
                os.path.join(IMG_DIR, fichero),
                folder="noticias"
            )
            noti.imagen = res["public_id"]
            noti.save()

        # 5) Crear comentarios
        for noti in Noticia.objects.all():
            for _ in range(random.randint(2, 6)):
                usr = random.choice(usuarios)
                c = Comentario.objects.create(
                    noticia=noti,
                    usuario=usr,
                    contenido=fake.paragraph(nb_sentences=random.randint(2, 4))
                )
                if random.random() < 0.5:
                    Comentario.objects.create(
                        noticia=noti,
                        usuario=random.choice(usuarios),
                        contenido=fake.paragraph(nb_sentences=2),
                        parent=c
                    )

        # 6) Crear adopciones y subir PDF a Cloudinary
        for _ in range(10):
            usr = random.choice(usuarios)
            ani = random.choice(list(Animal.objects.all()))
            if Adopcion.objects.filter(animal=ani, usuario=usr).exists():
                continue

            ad = Adopcion.objects.create(
                usuario=usr,
                animal=ani,
                aceptada=random.choice(['Pendiente', 'Aceptada'])
            )
            res = cloudinary.uploader.upload(
                PDF_DUMMY,
                resource_type="raw",
                folder=f"adopciones/{usr.id}"
            )
            ad.contenido = res["public_id"] + ".pdf"
            try:
                ad.full_clean()
                ad.save()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Adopción inválida: {e}"))

        # 7) Reconectar tus señales
        pre_save.connect(signals.borrar_imagen_anterior_animal, sender=Animal)
        pre_save.connect(signals.borrar_foto_anterior_usuario, sender=CustomUser)
        pre_save.connect(signals.borrar_pdf_anterior_adopcion, sender=Adopcion)
        post_delete.connect(signals.eliminar_imagen_animal, sender=Animal)
        post_delete.connect(signals.eliminar_imagen_usuario, sender=CustomUser)
        post_delete.connect(signals.eliminar_pdf_adopcion, sender=Adopcion)
        post_save.connect(signals.gestionar_estado_adopcion, sender=Adopcion)
        post_save.connect(signals.notificar_adopcion_admin, sender=Adopcion)
        post_save.connect(signals.notificar_nuevo_animal, sender=Animal)
        post_save.connect(signals.notificar_nueva_noticia, sender=Noticia)

        self.stdout.write(self.style.SUCCESS("✅ Seed completado correctamente (auditlog desactivado)"))

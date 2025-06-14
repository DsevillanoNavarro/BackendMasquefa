# appmustafa/management/commands/seed_real_data.py

from django.core.management.base import BaseCommand
from django.core.files import File
from appmustafa.models import Animal, Noticia, CustomUser, Adopcion, Comentario
from faker import Faker
from datetime import timedelta, date
from django.utils.timezone import now
import random
from appmustafa import signals
from django.db.models.signals import pre_save, post_save, post_delete
import os

fake = Faker('es_ES')  # Faker configurado en español

# Directorio de imágenes dummy y PDF de ejemplo para solicitudes
IMG_DIR = 'media/dummy_animales'
PDF_DUMMY = 'media/dummy_adopcion.pdf'

# Lista de nombres de archivos de imagen
IMAGENES = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

class Command(BaseCommand):
    help = 'Genera datos falsos realistas usando Faker'

    def handle(self, *args, **kwargs):
        # 🔌 Desactiva señales automáticas para evitar efectos colaterales
        pre_save.disconnect(signals.borrar_imagen_anterior_animal, sender=Animal)
        pre_save.disconnect(signals.borrar_foto_anterior_usuario, sender=CustomUser)
        pre_save.disconnect(signals.borrar_pdf_anterior_adopcion, sender=Adopcion)
        post_delete.disconnect(signals.eliminar_imagen_animal, sender=Animal)
        post_delete.disconnect(signals.eliminar_imagen_usuario, sender=CustomUser)
        post_delete.disconnect(signals.eliminar_pdf_adopcion, sender=Adopcion)
        post_save.disconnect(signals.gestionar_estado_adopcion, sender=Adopcion)
        post_save.disconnect(signals.notificar_adopcion_admin, sender=Adopcion)
        post_save.disconnect(signals.notificar_nuevo_animal, sender=Animal)
        post_save.disconnect(signals.notificar_nueva_noticia, sender=Noticia)

        # 👤 Crea 10 usuarios falsos
        usuarios = []
        for _ in range(10):
            user = CustomUser.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='Kilobyte1',
                recibir_novedades=random.choice([True, False])
            )
            usuarios.append(user)

        # 🐶 Crea 30 animales falsos con imágenes
        for _ in range(30):
            fecha_nacimiento = date.today() - timedelta(days=random.randint(100, 5000))
            imagen_file = random.choice(IMAGENES)

            animal = Animal(
                nombre=fake.first_name(),
                fecha_nacimiento=fecha_nacimiento,
                situacion=fake.paragraph(nb_sentences=15)
            )
            animal.save()
            with open(os.path.join(IMG_DIR, imagen_file), 'rb') as f:
                animal.imagen.save(imagen_file, File(f), save=True)

        # 📰 Crea 8 noticias con imágenes
        for _ in range(8):
            imagen_file = random.choice(IMAGENES)
            noticia = Noticia(
                titulo=fake.sentence(nb_words=6),
                contenido=fake.paragraph(nb_sentences=5),
                fecha_publicacion=now().date()
            )
            noticia.save()
            with open(os.path.join(IMG_DIR, imagen_file), 'rb') as f:
                noticia.imagen.save(imagen_file, File(f), save=True)

        # 💬 Genera comentarios
        for noticia in Noticia.objects.all():
            for _ in range(random.randint(2, 6)):
                usuario = random.choice(usuarios)
                comentario = Comentario.objects.create(
                    noticia=noticia,
                    usuario=usuario,
                    contenido=fake.paragraph(nb_sentences=random.randint(2,4))
                )
                if random.random() < 0.5:
                    Comentario.objects.create(
                        noticia=noticia,
                        usuario=random.choice(usuarios),
                        contenido=fake.paragraph(nb_sentences=2),
                        parent=comentario
                    )

        # 📝 Crea 10 adopciones con PDFs
        for _ in range(10):
            usuario = random.choice(usuarios)
            animal = random.choice(list(Animal.objects.all()))
            if Adopcion.objects.filter(animal=animal, usuario=usuario).exists():
                continue

            adopcion = Adopcion(
                usuario=usuario,
                animal=animal,
                aceptada=random.choice(['Pendiente', 'Aceptada'])
            )
            adopcion.save()
            with open(PDF_DUMMY, 'rb') as f:
                adopcion.contenido.save('solicitud.pdf', File(f), save=True)
            try:
                adopcion.full_clean()
                adopcion.save()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Error al crear adopción: {e}"))

        # 🔌 Reconecta las señales
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

        self.stdout.write(self.style.SUCCESS("✅ Datos falsos realistas creados con éxito"))
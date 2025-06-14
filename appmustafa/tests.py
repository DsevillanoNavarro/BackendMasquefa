# Importaciones necesarias para pruebas, autenticación y manejo de archivos
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

# Modelos del sistema relacionados con animales, adopciones, comentarios y noticias
from .models import Animal, Adopcion, Comentario, Noticia

# Obtener el modelo de usuario activo del proyecto
User = get_user_model()

# Clase de pruebas automatizadas usando APITestCase (de DRF)
class AnimalesMasquefaTests(APITestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        # Obtener token JWT para autenticación en las pruebas
        login_url = reverse('token_obtain_pair')
        login_resp = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'password123'
        })
        self.token = login_resp.data.get('access')
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'} if self.token else {}

        # Crear una imagen simulada para asociar con un animal
        image = SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')

        # Crear un animal de prueba en la base de datos
        self.animal = Animal.objects.create(
            nombre='Pelusa',
            fecha_nacimiento=date(2020, 1, 1),
            situacion='En acogida',
            imagen=image
        )

        # Crear una noticia para asociar comentarios en pruebas
        noticia_image = SimpleUploadedFile('none.jpg', b'img', content_type='image/jpeg')
        self.noticia = Noticia.objects.create(
            titulo='Noticia Test',
            contenido='Contenido de prueba',
            fecha_publicacion=date.today(),
            imagen=noticia_image
        )

    def test_crear_adopcion_valida(self):
        # Prueba que una adopción válida se cree correctamente (HTTP 201)
        url = reverse('adopcion-list')
        pdf = SimpleUploadedFile('solicitud.pdf', b'%PDF-1.4 pdf content', content_type='application/pdf')

        # ⚠️ El backend espera 'animal_id' y 'usuario'
        data = {
            'animal_id': self.animal.id,
            'usuario': self.user.id,
            'contenido': pdf
        }

        response = self.client.post(url, data, format='multipart', **self.auth_header)
        print("Respuesta del servidor:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_prevenir_adopcion_duplicada(self):
        # Verifica que un usuario no pueda enviar dos solicitudes de adopción para el mismo animal
        url = reverse('adopcion-list')
        contenido = SimpleUploadedFile("testfile.pdf", b"file_content", content_type="application/pdf")

        data = {
            'animal_id': self.animal.id,
            'usuario': self.user.id,
            'contenido': contenido,
        }

        # Primer intento: debe ser exitoso
        response1 = self.client.post(url, data, format='multipart', **self.auth_header)
        print("Primer respuesta:", response1.data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Segundo intento con otro archivo PDF para el mismo animal y usuario: debe fallar
        contenido2 = SimpleUploadedFile("testfile2.pdf", b"otro_contenido", content_type="application/pdf")
        data['contenido'] = contenido2
        response2 = self.client.post(url, data, format='multipart', **self.auth_header)
        print("Segunda respuesta:", response2.data)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ya has enviado una solicitud", str(response2.content))

    def test_comentario_vacio_rechazado(self):
        # Verifica que no se permita crear un comentario sin contenido
        url = reverse('comentario-list')
        data = {'noticia': self.noticia.id, 'contenido': ''}
        response = self.client.post(url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comentario_correcto(self):
        # Verifica que se pueda crear un comentario válido correctamente
        url = reverse('comentario-list')
        data = {'noticia': self.noticia.id, 'contenido': '¡Muy bonito el gato!'}
        response = self.client.post(url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_jwt(self):
        # Prueba que el login con credenciales correctas devuelva un mensaje personalizado
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': 'testuser', 'password': 'password123'})
        print("Login JWT response:", response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'detail': 'Login exitoso'})

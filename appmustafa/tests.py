from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from .models import Animal, Adopcion, Comentario, Noticia

User = get_user_model()

class AnimalesMasquefaTests(APITestCase):

    def setUp(self):
        # Crear usuario de prueba y token JWT
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        login_url = reverse('token_obtain_pair')
        login_resp = self.client.post(login_url, {
            'username': 'testuser', 'password': 'password123'
        })
        self.token = login_resp.data.get('access')
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'} if self.token else {}

        # Crear imagen simulada
        image = SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')

        # Crear animal de prueba
        self.animal = Animal.objects.create(
            nombre='Pelusa',
            fecha_nacimiento=date(2020, 1, 1),
            situacion='En acogida',
            imagen=image
        )

        # Crear noticia de prueba para comentarios
        noticia_image = SimpleUploadedFile('none.jpg', b'img', content_type='image/jpeg')
        self.noticia = Noticia.objects.create(
            titulo='Noticia Test',
            contenido='Contenido de prueba',
            fecha_publicacion=date.today(),
            imagen=noticia_image
        )

    def test_crear_adopcion_valida(self):
        url = reverse('adopcion-list')
        pdf = SimpleUploadedFile('solicitud.pdf', b'%PDF-1.4 pdf content', content_type='application/pdf')
        data = {
            'animal': self.animal.id,
            'usuario': self.user.id,
            'contenido': pdf
        }
        response = self.client.post(url, data, format='multipart', **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_prevenir_adopcion_duplicada(self):
        url = '/api/adopciones/'  # o usa reverse si lo tienes
        contenido = SimpleUploadedFile("testfile.pdf", b"file_content", content_type="application/pdf")

        data = {
            'animal': self.animal.id,
            'usuario': self.user.id,
            'contenido': contenido,
        }

        response1 = self.client.post(url, data, format='multipart', **self.auth_header)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Segundo intento para probar duplicación
        contenido2 = SimpleUploadedFile("testfile2.pdf", b"otro_contenido", content_type="application/pdf")
        data['contenido'] = contenido2
        response2 = self.client.post(url, data, format='multipart', **self.auth_header)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b"Ya has enviado una solicitud", response2.content)

        

    def test_comentario_vacio_rechazado(self):
        url = reverse('comentario-list')
        data = {'noticia': self.noticia.id, 'contenido': ''}
        response = self.client.post(url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comentario_correcto(self):
        url = reverse('comentario-list')
        data = {'noticia': self.noticia.id, 'contenido': '¡Muy bonito el gato!'}
        response = self.client.post(url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_jwt(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': 'testuser', 'password': 'password123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'detail': 'Login exitoso'})
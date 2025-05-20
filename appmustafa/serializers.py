from rest_framework import serializers
from .models import Animal, Noticia, Comentario, Adopcion
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.utils.html import format_html
from rest_framework import generics
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = '__all__'
        
class NoticiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Noticia
        fields = '__all__'

class ComentarioSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField(read_only=True)
    tiempo_transcurrido = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = ['id', 'noticia', 'usuario', 'contenido', 'fecha_hora', 'tiempo_transcurrido']

    def get_tiempo_transcurrido(self, obj):
        return obj.tiempo_transcurrido()
        
class AdopcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adopcion
        fields = '__all__'        
        
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # encripta la contraseña
        user.save()
        
        email = EmailMessage(
        subject='¡Bienvenido a nuestra plataforma!',
        body=format_html("""
        <div style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 30px;">
            <div style="max-width: 600px; margin: auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
                    <h1>¡Bienvenido, {}! 🌟</h1>
                </div>
                <div style="padding: 30px; color: #333;">
                    <p>Gracias por registrarte en nuestra plataforma. ¡Estamos encantados de tenerte con nosotros!</p>
                    <p>Esperamos que disfrutes de todas las funcionalidades y te animes a explorar todo lo que tenemos para ofrecer.</p>
                    <p style="margin-top: 30px;">— El equipo de <strong>Animales Masquefa</strong></p>
                </div>
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                    <p>Este correo ha sido enviado automáticamente. Por favor, no respondas a este mensaje.</p>
                </div>
            </div>
        </div>
    """, user.first_name or user.username),
        
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
        )
        email.content_subtype = "html"  # para enviar HTML
        email.encoding = 'utf-8'        # <--- esta línea es la clave
        email.send(fail_silently=False)

        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
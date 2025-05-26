from jet.dashboard import modules
from jet.dashboard.dashboard import Dashboard
from appmustafa.models import CustomUser as User
from django.urls import reverse
from appmustafa.models import Adopcion, Comentario, Animal, Noticia
from jet.dashboard.models import UserDashboardModule
from django.utils import translation

translation.activate('es')

class CustomIndexDashboard(Dashboard):
    columns = 2

    def init_with_context(self, context):
        
        user = context['request'].user
        UserDashboardModule.objects.filter(user=user).delete()

        button_html = lambda url, text: (
            f'<a href="{url}" '
            f'style="display:inline-block;margin:20px 0;padding:20px 40px;background-color:#4170E8;color:white;'
            'font-family:Poppins,sans-serif;font-size:20px;font-weight:900;border:none;text-decoration:none;'
            'transition:background-color 0.5s ease;border-radius:0;" '
            'onmouseover="this.style.backgroundColor=\'#000000\'" '
            'onmouseout="this.style.backgroundColor=\'#4170E8\'">'
            f'{text}</a>'
        )

        self.children.append(
            modules.LinkList(
                title='⚡ Tareas rápidas',
                children=[
                    {'title': 'Añadir Animal', 'url': reverse('admin:appmustafa_animal_add')},
                    {'title': 'Añadir Noticia', 'url': reverse('admin:appmustafa_noticia_add')},
                    {'title': 'Añadir Comentario', 'url': reverse('admin:appmustafa_comentario_add')},
                    {'title': 'Añadir Adopción', 'url': reverse('admin:appmustafa_adopcion_add')},
                ],
            )
        )

        adopciones = Adopcion.objects.order_by('-fecha_hora')[:10]
        self.children.append(
            modules.LinkList(
                title='🐾 Adopciones recientes',
                children=[
                    {'title': f'{a.animal.nombre} por {a.usuario.username} - {a.fecha_hora:%Y-%m-%d}',
                     'url': reverse('admin:appmustafa_adopcion_change', args=(a.id,))}
                    for a in adopciones
                ],
                pre_content='<p style="font-size:18px;">Últimas adopciones registradas:</p>',
                post_content=button_html(reverse('admin:appmustafa_adopcion_changelist'), 'Ver más')
            )
        )

        pendientes = Adopcion.objects.filter(aceptada='Pendiente').order_by('-fecha_hora')[:10]
        self.children.append(
            modules.LinkList(
                title='⏳ Adopciones pendientes',
                children=[
                    {'title': f'{p.animal.nombre} por {p.usuario.username}',
                     'url': reverse('admin:appmustafa_adopcion_change', args=(p.id,))}
                    for p in pendientes
                ],
                pre_content='<p style="font-size:18px;">Solicitudes de adopción pendientes:</p>',
                post_content=button_html(reverse('admin:appmustafa_adopcion_changelist') + "?aceptada__exact=Pendiente", 'Ver más')
            )
        )

        nuevos_usuarios = User.objects.order_by('-date_joined')[:10]
        self.children.append(
            modules.LinkList(
                title='👤 Usuarios recientes',
                children=[
                    {'title': f'{u.username} ({u.email}) - {u.date_joined:%Y-%m-%d}',
                     'url': reverse('admin:appmustafa_customuser_change', args=(u.id,))}
                    for u in nuevos_usuarios
                ],
                pre_content='<p style="font-size:18px;">Últimos usuarios registrados:</p>',
                post_content=button_html(reverse('admin:appmustafa_customuser_changelist'), 'Ver más')
            )
        )

        comentarios = Comentario.objects.order_by('-fecha_hora')[:10]
        self.children.append(
            modules.LinkList(
                title='💬 Comentarios recientes',
                children=[
                    {'title': f'{c.usuario.username}: {c.contenido[:40]}',
                     'url': reverse('admin:appmustafa_comentario_change', args=(c.id,))}
                    for c in comentarios
                ],
                pre_content='<p style="font-size:18px;">Comentarios más recientes:</p>',
                post_content=button_html(reverse('admin:appmustafa_comentario_changelist'), 'Ver más')
            )
        )

        animales = Animal.objects.order_by('-id')[:10]
        self.children.append(
            modules.LinkList(
                title='🐶 Animales registrados',
                children=[
                    {'title': f'{an.nombre} - {an.edad} años',
                     'url': reverse('admin:appmustafa_animal_change', args=(an.id,))}
                    for an in animales
                ],
                pre_content='<p style="font-size:18px;">Últimos animales registrados:</p>',
                post_content=button_html(reverse('admin:appmustafa_animal_changelist'), 'Ver más')
            )
        )

        noticias = Noticia.objects.order_by('-fecha_publicacion')[:10]
        self.children.append(
            modules.LinkList(
                title='📰 Noticias publicadas',
                children=[
                    {'title': n.titulo, 'url': reverse('admin:appmustafa_noticia_change', args=(n.id,))}
                    for n in noticias
                ],
                pre_content='<p style="font-size:18px;">Últimas noticias publicadas:</p>',
                post_content=button_html(reverse('admin:appmustafa_noticia_changelist'), 'Ver más')
            )
        )

        self.children.append(
            modules.LinkList(
                title='📊 Estadísticas del sitio',
                children=[
                    {'title': f'👤 Usuarios registrados: {User.objects.count()}', 'url': '/admin/appmustafa/customuser/'},
                    {'title': f'🐕 Animales registrados: {Animal.objects.count()}', 'url': '/admin/appmustafa/animal/'},
                    {'title': f'📰 Noticias registradas: {Noticia.objects.count()}', 'url': '/admin/appmustafa/noticia/'},
                    {'title': f'📁 Adopciones registradas: {Adopcion.objects.count()}', 'url': '/admin/appmustafa/adopcion/'},
                    {'title': f'💬 Comentarios registrados: {Comentario.objects.count()}', 'url': '/admin/appmustafa/comentario/'},
                ]
            )
        )

        self.children.append(
            modules.LinkList(
                title='🛡️ Registro de auditoría',
                pre_content='<p style="font-size:18px;">Accede al registro completo de auditoría:</p>',
                children=[
                    {'title': 'Ver log de auditoría', 'url': '/admin/auditlog/logentry/'},
                ],
            )
        )

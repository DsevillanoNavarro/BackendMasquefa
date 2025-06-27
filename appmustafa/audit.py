# appmustafa/audit.py

# Importa el objeto 'auditlog' que permite registrar modelos para auditoría
from auditlog.registry import auditlog

# Importa los modelos de la aplicación que se desean auditar
from .models import Animal, Noticia, Comentario, Adopcion, CustomUser

# Función encargada de registrar los modelos en el sistema de auditoría
def register_auditlog_models():
    auditlog.register(Animal, exclude_fields=['imagen'])
    auditlog.register(Noticia, exclude_fields=['imagen'])
    auditlog.register(Comentario)
    auditlog.register(Adopcion, exclude_fields=['contenido'])
    auditlog.register(CustomUser, exclude_fields=['foto_perfil'])
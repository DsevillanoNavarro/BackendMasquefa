# appmustafa/audit.py

# Importa el objeto 'auditlog' que permite registrar modelos para auditoría
from auditlog.registry import auditlog

# Importa los modelos de la aplicación que se desean auditar
from .models import Animal, Noticia, Comentario, Adopcion, CustomUser

# Función encargada de registrar los modelos en el sistema de auditoría
def register_auditlog_models():
    # Registrar el modelo Animal para que sus cambios sean auditados
    auditlog.register(Animal)
    
    # Registrar el modelo Noticia para auditoría de cambios
    auditlog.register(Noticia)
    
    # Registrar el modelo Comentario para rastrear sus modificaciones
    auditlog.register(Comentario)
    
    # Registrar el modelo Adopcion para auditar cambios de estado, usuario, etc.
    auditlog.register(Adopcion)
    
    # Registrar el modelo de usuario personalizado para auditar creación, edición, etc.
    auditlog.register(CustomUser)

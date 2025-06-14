# Importa la clase base AppConfig que se utiliza para configurar apps en Django
from django.apps import AppConfig

# Define la configuración específica para la aplicación "appmustafa"
class AppmustafaConfig(AppConfig):
    # Especifica el tipo de campo por defecto para claves primarias automáticas
    default_auto_field = 'django.db.models.BigAutoField'

    # Nombre interno de la aplicación (debe coincidir con la carpeta o el nombre en INSTALLED_APPS)
    name = 'appmustafa'
    
    # Este método se ejecuta automáticamente cuando Django carga esta app
    def ready(self):
        # Importa los signals para que estén activos al arrancar la app (handlers de eventos como post_save, post_delete, etc.)
        import appmustafa.signals

        # Importa la función que registra los modelos en el sistema de auditoría (auditlog)
        from .audit import register_auditlog_models

        # Ejecuta el registro de modelos para que los cambios queden auditados automáticamente
        register_auditlog_models()

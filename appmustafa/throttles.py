from rest_framework.throttling import UserRateThrottle

# Limita la cantidad de comentarios que un usuario puede crear
class CrearComentarioThrottle(UserRateThrottle):
    scope = "comentario_creacion"

# Limita cuántas solicitudes de adopción puede hacer un usuario
class CrearAdopcionThrottle(UserRateThrottle):
    scope = "adopcion_creacion"

# Restringe la cantidad de intentos de inicio de sesión para evitar abusos
class LoginThrottle(UserRateThrottle):
    scope = "login"

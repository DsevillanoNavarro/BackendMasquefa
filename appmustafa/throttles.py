from rest_framework.throttling import UserRateThrottle


class CrearComentarioThrottle(UserRateThrottle):
    scope = "comentario_creacion"


class CrearAdopcionThrottle(UserRateThrottle):
    scope = "adopcion_creacion"


class LoginThrottle(UserRateThrottle):
    scope = "login"
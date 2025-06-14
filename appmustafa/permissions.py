# Importa las clases base para permisos desde Django REST Framework
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que permite:
    - Acceso de solo lectura (GET, HEAD, OPTIONS) a cualquier usuario, autenticado o no.
    - Acceso de escritura (POST, PUT, PATCH, DELETE) solo a usuarios con privilegios de staff (admin).
    """

    def has_permission(self, request, view):
        # Si la petición es de tipo seguro (GET, HEAD, OPTIONS), se permite siempre
        if request.method in permissions.SAFE_METHODS:
            return True

        # Para métodos de escritura (POST, PUT, DELETE, etc.), se requiere que el usuario sea staff
        # `request.user` debe existir y `is_staff` debe ser True
        return request.user and request.user.is_staff

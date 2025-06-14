# Importa la clase base para autenticación JWT
from rest_framework_simplejwt.authentication import JWTAuthentication

# Clase personalizada para autenticar usando JWT almacenado en cookies
class CookieJWTAuthentication(JWTAuthentication):
    
    # Sobrescribe el método 'authenticate' para usar cookies en lugar de headers
    def authenticate(self, request):
        # Intenta obtener el token JWT desde la cookie llamada "access_token"
        raw_token = request.COOKIES.get("access_token")
        
        # Si no existe la cookie, no se puede autenticar
        if raw_token is None:
            return None
        
        try:
            # Valida que el token no esté vencido ni malformado
            validated_token = self.get_validated_token(raw_token)
            
            # Obtiene el usuario asociado al token y lo retorna junto al token
            return self.get_user(validated_token), validated_token
        
        except Exception:
            # Si ocurre cualquier error (token inválido, expirado, etc.), retorna None
            return None

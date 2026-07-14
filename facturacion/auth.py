from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Contribuyente


class ApiKeyAuthentication(BaseAuthentication):
    """Autenticación por API key en el header Authorization: Bearer <key>.

    Si el header no está presente devuelve None (deja pasar a otros
    authenticators). Si está presente pero la key es inválida lanza 401.
    """

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None

        api_key = auth[len('Bearer '):]
        try:
            contribuyente = Contribuyente.objects.get(api_key=api_key, is_active=True)
        except Contribuyente.DoesNotExist:
            raise AuthenticationFailed('API key inválida o inactiva.')

        # DRF espera (user, token). Usamos el Contribuyente como "user".
        return (contribuyente, None)

    def authenticate_header(self, request):
        return 'Bearer realm="sri-facturacion"'

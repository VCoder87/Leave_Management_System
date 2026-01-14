import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from core.models import User

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = AnonymousUser()

        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = payload.get('user_id')
                request.user = User.objects.get(id=user_id)
            except Exception:
                request.user = AnonymousUser()

        return self.get_response(request)

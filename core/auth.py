import jwt
from datetime import datetime, timedelta
from django.conf import settings

SECRET = settings.SECRET_KEY

def generate_tokens(user):
    access = jwt.encode({
        'user_id': user.id,
        'role': user.role.role_name,
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }, SECRET, algorithm='HS256')

    refresh = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET, algorithm='HS256')

    return {'access': access, 'refresh': refresh}

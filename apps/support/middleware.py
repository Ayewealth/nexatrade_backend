import jwt
from django.conf import settings
from urllib.parse import parse_qs
from apps.authentication.models import User
from channels.middleware import BaseMiddleware
from asgiref.sync import sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


@sync_to_async
def get_user(token):
    try:
        UntypedToken(token)  # Verifies token
        decoded_data = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects.get(id=decoded_data["user_id"])
        return user
    except (InvalidToken, TokenError, jwt.DecodeError, User.DoesNotExist):
        return None


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        print("Chat Auth token:", token)

        if token:
            scope["user"] = await get_user(token)
        else:
            scope["user"] = None

        return await super().__call__(scope, receive, send)

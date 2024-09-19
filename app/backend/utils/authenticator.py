import datetime
import secrets
import jwt

from models.payload import Payload
from quart import request, jsonify, current_app
from config import CONFIG_USER_DATABASE
from utils.user_database import UserDatabase


class Authenticator:
    def __init__(self) -> None:
        self.SECRET_KEY = secrets.token_hex()
        self.ALGORITHM = "HS256"
        self.EXPIRATION_DELTA = datetime.timedelta(hours=1)
    
    def generate_jwt_token(self, payload: Payload) -> str:
        """
        Generate a JWT token for the authenticated user
        """
        payload.exp = datetime.datetime.now(datetime.timezone.utc) + self.EXPIRATION_DELTA
        token = jwt.encode(payload.model_dump(), self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
    
    def get_jwt_from_request(self):
        """
        Retrieve the JWT token from the request header (Authorization)
        """
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            return None
        
        parts = auth_header.split()

        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

        return None
    
    def decode_jwt(self,token):
        """
        Decode the JWT to get payload
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return Payload(**payload)
        except jwt.exceptions.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.exceptions.InvalidTokenError:
            raise ValueError("Invalid token")
        




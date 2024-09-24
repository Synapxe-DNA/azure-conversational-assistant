import datetime
import logging
import secrets

import jwt
from azure.keyvault.secrets.aio import SecretClient
from config import CONFIG_KEYVAULT_CLIENT
from models.payload import Payload
from quart import current_app, request


class Authenticator:
    def __init__(self, secret_key) -> None:
        self.ALGORITHM = "HS256"
        self.EXPIRATION_DELTA = datetime.timedelta(hours=1)
        self.SECRET_KEY = secret_key

    @classmethod
    async def setup(cls):
        keyvault_client: SecretClient = current_app.config[CONFIG_KEYVAULT_CLIENT]
        try:
            secretKeyObj = await keyvault_client.get_secret("secretKey")
            secret_key = secretKeyObj.value
            logging.info("Secret key has been retrieved from keyvault")
        except Exception as e:
            secret_key = secrets.token_hex()
            logging.warning(e)
            logging.warning("Secret key will be generated randomly")
        return cls(secret_key)

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

    def decode_jwt(self, token):
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

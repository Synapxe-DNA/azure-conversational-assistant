import datetime

import jwt
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.keyvault.secrets.aio import SecretClient
from config import CONFIG_KEYVAULT_CLIENT
from models.account import Account
from models.payload import Payload
from quart import current_app, request


class Authenticator:
    def __init__(self) -> None:
        self.ALGORITHM = "HS256"
        self.EXPIRATION_DELTA = datetime.timedelta(hours=1)
        self.keyvault_client: SecretClient = current_app.config[CONFIG_KEYVAULT_CLIENT]

    async def get_secret_key(self):
        try:
            secretKeyObj = await self.keyvault_client.get_secret("secretKey")  # Gets latest version
            secret_key = secretKeyObj.value
            return secret_key
        except ResourceNotFoundError:
            raise ValueError("Secret key has not been set. Please contact the administrator.")
        except HttpResponseError:
            raise ValueError("Secret key has been disabled. Please contact the administrator.")

    async def generate_jwt_token(self, account: Account) -> str:
        """
        Generate a JWT token for the authenticated user
        """
        secret_key = await self.get_secret_key()
        expiry = datetime.datetime.now(datetime.timezone.utc) + self.EXPIRATION_DELTA
        payload = Payload(username=account.username, exp=expiry)
        token = jwt.encode(payload.model_dump(), secret_key, algorithm=self.ALGORITHM)
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

    async def decode_jwt(self, token) -> None:
        """
        Decode the JWT to get payload
        """
        try:
            secret_key = await self.get_secret_key()
            jwt.decode(token, secret_key, algorithms=[self.ALGORITHM])
        except jwt.exceptions.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.exceptions.InvalidTokenError:
            raise ValueError("Invalid token")
        except Exception as error:
            raise (error)

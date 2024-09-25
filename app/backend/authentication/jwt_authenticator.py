import datetime

import jwt
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.keyvault.secrets.aio import SecretClient
from config import CONFIG_KEYVAULT_CLIENT
from models.account import Account
from models.payload import Payload
from quart import current_app, request


class JWTAuthenticator:
    '''
    A JWT Authenticator that generates and decodes JWT tokens for the user

    Attributes:
        ALGORITHM (str): The algorithm used for encoding the JWT token
        EXPIRATION_DELTA (datetime.timedelta): The expiration time used when generating a JWT token
        keyvault_client (SecretClient): The keyvault client used to retrieve the secret key
    '''

    def __init__(self) -> None:
        self.ALGORITHM = "HS256"
        self.EXPIRATION_DELTA = datetime.timedelta(hours=1)
        self.keyvault_client: SecretClient = current_app.config[CONFIG_KEYVAULT_CLIENT]

    async def get_secret_key(self) -> str:
        '''
        Function to get the secret key from the keyvault

        Raises:
            ResourceNotFoundError: If the secret key has not been created/does not exist
            HttpResponseError: If the secret key has been disabled

        Returns:
            secret_key (str): The secret key
        '''
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
        Generate a JWT token for the authenticated user with the given account username, secret key and expiration time

        Args:
            account (Account): The account object of the user
        
        Returns:
            token (str): The JWT token generated
        """
        secret_key = await self.get_secret_key()
        expiry = datetime.datetime.now(datetime.timezone.utc) + self.EXPIRATION_DELTA
        payload = Payload(username=account.username, exp=expiry)
        token = jwt.encode(payload.model_dump(), secret_key, algorithm=self.ALGORITHM)
        return token

    def get_jwt_from_request(self):
        """
        Retrieve the JWT token from the request header (Authorization)

        Returns: 
            token (str): The JWT token
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

        Args: 
            token (str): The JWT token to decode

        Raises:
            ValueError: If the token has expired or is invalid
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

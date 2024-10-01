from typing import Tuple

from azure.core.exceptions import ResourceNotFoundError
from azure.keyvault.secrets.aio import SecretClient
from config import CONFIG_KEYVAULT_CLIENT
from models.account import Account
from quart import current_app


class AccountAuthenticator:
    """
    An Account Authenticator that checks the user login credentials

    Attributes:
        keyvault_client (SecretClient): The keyvault client used to retrieve the username and password
    """

    def __init__(self):
        self.keyvault_client: SecretClient = current_app.config[CONFIG_KEYVAULT_CLIENT]

    async def verify_user(self, account: Account) -> Tuple[bool, str]:
        """
        Function to verify the user login credentials against the stored username and password from keyvault

        Args:
            account (Account): The account object of the user

        Raises:
            ResourceNotFoundError: If the username or password has not been created/does not exist

        Returns:
            Tuple[bool, str]: A tuple containing a boolean value if both username and password is correct and a message indicating the result
        """
        try:
            found_password = await self.check_secret("password", account.password)
            found_username = await self.check_secret("username", account.username)
            if found_password and found_username:
                return True, "Login successful"
            else:
                return False, "Username or password is incorrect"

        except ResourceNotFoundError:
            return False, "Username or password has not been set. Please contact the administrator."

    async def check_secret(self, secret_name: str, user_input: str) -> bool:
        """
        Function to check if the user username/password matches the stored username/password in keyvault

        Args:
            secret_name (str): The secret name to query from keyvault
            user_input (str): The user's username/password

        Returns:
            bool: A boolean value indicating if the user username/password matches the stored username/password in keyvault

        """
        async for ver in self.keyvault_client.list_properties_of_secret_versions(secret_name):
            if ver.enabled:
                secret = await self.keyvault_client.get_secret(secret_name, ver.version)
                if secret.value == user_input:
                    return True
        return False

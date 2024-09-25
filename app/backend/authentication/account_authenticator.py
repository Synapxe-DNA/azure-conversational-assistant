from typing import Tuple

from azure.core.exceptions import ResourceNotFoundError
from azure.keyvault.secrets.aio import SecretClient
from config import CONFIG_KEYVAULT_CLIENT
from models.account import Account
from quart import current_app


class AccountAuthenticator:

    def __init__(self):
        self.keyvault_client: SecretClient = current_app.config[CONFIG_KEYVAULT_CLIENT]

    async def verify_user(self, account: Account) -> Tuple[bool, str]:
        try:
            found_password = await self.check_secret("password", account.password)
            found_username = await self.check_secret("username", account.username)
            if found_password and found_username:
                return True, "Login successful"
            else:
                return False, "Username or password is incorrect"

        except ResourceNotFoundError:
            return False, "Username or password has not been set. Please contact the administrator."

    async def check_secret(self, secret_name: str, expected_value: str) -> bool:
        async for ver in self.keyvault_client.list_properties_of_secret_versions(secret_name):
            if ver.enabled:
                secret = await self.keyvault_client.get_secret(secret_name, ver.version)
                if secret.value == expected_value:
                    return True
        return False

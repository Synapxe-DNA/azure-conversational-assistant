import logging
import sqlite3

import bcrypt
from azure.keyvault.secrets.aio import SecretClient
from config import CONFIG_KEYVAULT_CLIENT
from models.account import Account
from quart import current_app


class UserDatabase:

    def __init__(self, cursor):
        self.cursor = cursor

    @classmethod
    async def setup(cls):

        connection = sqlite3.connect("authorised_users.db")
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS authorised_users")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS authorised_users (
                            username TEXT PRIMARY KEY,
                            password BLOB)
                            """
        )

        keyvault_client: SecretClient = current_app.config[CONFIG_KEYVAULT_CLIENT]
        try:
            username = await keyvault_client.get_secret("username")
            password = await keyvault_client.get_secret("password")
            hashed_password = UserDatabase.hash_password(password.value)
            add_account = "INSERT INTO authorised_users (username, password) VALUES (?, ?)"
            cursor.execute(add_account, (username.value, hashed_password))
            logging.info("Username and password has been retrieved from keyvault")
        except Exception as e:
            logging.warning(e)
            logging.warning("Username and password will not be inserted")
        connection.commit()
        return cls(cursor)

    def verify_user(self, account: Account) -> bool:
        password = account.password.encode("utf-8")
        command = "SELECT password FROM authorised_users WHERE username = ? LIMIT 1"
        self.cursor.execute(command, (account.username,))  # parameters must be tuple
        result = self.cursor.fetchone()  # return type is tuple
        return bcrypt.checkpw(password, result[0]) if result else False

    @staticmethod
    def hash_password(password: str) -> bytes:
        hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hash_password

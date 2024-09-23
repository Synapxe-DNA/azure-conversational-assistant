import logging
import sqlite3

import bcrypt
from azure.keyvault.secrets.aio import SecretClient
from config import CONFIG_KEYVAULT_CLIENT
from models.payload import Payload
from quart import current_app


class UserDatabase:

    def __init__(self):

        self.connection = sqlite3.connect("authorised_users.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute("DROP TABLE IF EXISTS authorised_users")
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS authorised_users (
                            username TEXT PRIMARY KEY,
                            password BLOB)
                            """
        )
        self.keyvault_client: SecretClient = current_app.config[CONFIG_KEYVAULT_CLIENT]

    def verify_user(self, payload: Payload) -> bool:
        password = payload.password.encode("utf-8")
        command = "SELECT password FROM authorised_users WHERE username = ? LIMIT 1"
        self.cursor.execute(command, (payload.username,))  # parameters must be tuple
        result = self.cursor.fetchone()  # return type is tuple
        return bcrypt.checkpw(password, result[0]) if result else False

    def hash_password(self, password: str) -> bytes:
        hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hash_password

    async def setup(self):
        try:
            username = await self.keyvault_client.get_secret("username")
            password = await self.keyvault_client.get_secret("password")
            hashed_password = self.hash_password(password.value)
            add_account = "INSERT INTO authorised_users (username, password) VALUES (?, ?)"
            self.cursor.execute(add_account, (username.value, hashed_password))
        except Exception as e:
            print(e)
            logging.info("Username and password not set in keyvault")
        self.connection.commit()
        return self

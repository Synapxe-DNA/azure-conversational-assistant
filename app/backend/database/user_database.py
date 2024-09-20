import json
import sqlite3

import bcrypt
from models.payload import Payload


class UserDatabase:

    def __init__(self, accounts: str) -> None:

        connection = sqlite3.connect("authorised_users.db")
        self.cursor = connection.cursor()
        self.cursor.execute("DROP TABLE IF EXISTS authorised_users")
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS authorised_users (
                            username TEXT PRIMARY KEY,
                            password BLOB)
                            """
        )
        if not accounts == "":
            accounts = json.loads(accounts.replace('\\"', '"'))

            for account in accounts:
                for username, password in account.items():
                    hashed_password = self.hash_password(password)
                    add_account = "INSERT INTO authorised_users (username, password) VALUES (?, ?)"
                    self.cursor.execute(add_account, (username, hashed_password))
        connection.commit()

    def verify_user(self, payload: Payload) -> bool:
        password = payload.password.encode("utf-8")
        command = "SELECT password FROM authorised_users WHERE username = ? LIMIT 1"
        self.cursor.execute(command, (payload.username,))  # parameters must be tuple
        result = self.cursor.fetchone()  # return type is tuple
        if result:
            if bcrypt.checkpw(password, result[0]):
                return True
            else:
                return False
        else:
            return False

    def hash_password(self, password: str) -> bytes:
        hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hash_password

import sqlite3

import bcrypt
from models.payload import Payload


class UserDatabase:

    def __init__(self, username, password) -> None:

        connection = sqlite3.connect("authorised_users.db")
        self.cursor = connection.cursor()
        self.cursor.execute("DROP TABLE IF EXISTS authorised_users")
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS authorised_users (
                            username TEXT PRIMARY KEY,
                            password BLOB)
                            """
        )
        if not username == "" and not password == "":
            hashed_password = self.hash_password(password)
            add_account = "INSERT INTO authorised_users (username, password) VALUES (?, ?)"
            self.cursor.execute(add_account, (username, hashed_password))
        connection.commit()

    def verify_user(self, payload: Payload) -> bool:
        password = payload.password.encode("utf-8")
        command = "SELECT password FROM authorised_users WHERE username = ? LIMIT 1"
        self.cursor.execute(command, (payload.username,))  # parameters must be tuple
        result = self.cursor.fetchone()  # return type is tuple
        return bcrypt.checkpw(password, result[0]) if result else False

    def hash_password(self, password: str) -> bytes:
        hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hash_password

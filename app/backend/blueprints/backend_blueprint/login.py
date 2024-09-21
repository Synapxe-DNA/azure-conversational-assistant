from authentication.authenticator import Authenticator
from config import CONFIG_AUTHENTICATOR, CONFIG_USER_DATABASE
from database.user_database import UserDatabase
from models.payload import Payload
from quart import Blueprint, current_app, jsonify, request

login = Blueprint("login", __name__, url_prefix="/login")


@login.route("", methods=["POST"])
async def login_endpoint():
    data = await request.get_json()

    payload = Payload(username=data.get("username"), password=data.get("password"))

    authenticator: Authenticator = current_app.config[CONFIG_AUTHENTICATOR]
    user_database: UserDatabase = current_app.config[CONFIG_USER_DATABASE]

    if user_database.verify_user(payload):
        token = authenticator.generate_jwt_token(payload)
        return jsonify(token=token, token_type="Bearer")

    return jsonify(error="Invalid credentials"), 401

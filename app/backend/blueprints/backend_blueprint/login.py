from quart import Blueprint, current_app, jsonify, request
from config import CONFIG_AUTHENTICATOR, CONFIG_USER_DATABASE
from utils.authenticator import Authenticator
from utils.user_database import UserDatabase
from models.payload import Payload

login = Blueprint("login", __name__, url_prefix="/login")


@login.route("", methods=["POST"])
async def login_endpoint():
    data = await request.get_json()

    payload = Payload(username=data.get("username"), password=data.get("password"))

    authenticator:Authenticator = current_app.config[CONFIG_AUTHENTICATOR]
    user_database:UserDatabase = current_app.config[CONFIG_USER_DATABASE]

    # TODO: Password, SQLite
    # Verify user credentials (this should be replaced with actual verification logic)
    if user_database.verify_user(payload):
        # Generate a JWT token for the authenticated user
        token = authenticator.generate_jwt_token(payload)
        return jsonify(token=token)

    return jsonify(error="Invalid credentials"), 401
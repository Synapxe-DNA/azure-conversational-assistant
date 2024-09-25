from authentication.account_authenticator import AccountAuthenticator
from authentication.jwt_authenticator import JWTAuthenticator
from config import CONFIG_AUTHENTICATOR, CONFIG_USER_DATABASE
from models.account import Account
from quart import Blueprint, current_app, jsonify, request

login = Blueprint("login", __name__, url_prefix="/login")


@login.route("", methods=["POST"])
async def login_endpoint():
    data = await request.get_json()

    account = Account(username=data.get("username"), password=data.get("password"))

    authenticator: JWTAuthenticator = current_app.config[CONFIG_AUTHENTICATOR]
    user_database: AccountAuthenticator = current_app.config[CONFIG_USER_DATABASE]

    is_verified, message = await user_database.verify_user(account)
    if is_verified:
        try:
            token = await authenticator.generate_jwt_token(account)
            return jsonify(token=token, token_type="Bearer"), 200
        except Exception as error:
            return jsonify(error=str(error)), 500
    else:
        return jsonify(error=message), 401

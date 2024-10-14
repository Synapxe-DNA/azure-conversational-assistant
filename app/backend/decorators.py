from functools import wraps

from authentication.jwt_authenticator import JWTAuthenticator
from config import CONFIG_AUTHENTICATOR
from quart import current_app, jsonify


def require_authentication(func):
    """
    Decorator for routes that require authentication
    """

    @wraps(func)
    async def verify():
        authenticator: JWTAuthenticator = current_app.config[CONFIG_AUTHENTICATOR]
        token = authenticator.get_jwt_from_request()
        if token:
            try:
                await authenticator.decode_jwt(token)
                return await func()
            except ValueError as e:
                return jsonify({"error": str(e)}), 401
        else:
            return jsonify({"error": "Access token required"}), 401

    return verify

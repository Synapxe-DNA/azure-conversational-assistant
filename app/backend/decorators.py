import logging
from functools import wraps
from typing import Any, Callable, Dict

from authentication.jwt_authenticator import JWTAuthenticator
from config import CONFIG_AUTH_CLIENT, CONFIG_AUTHENTICATOR, CONFIG_SEARCH_CLIENT
from core.authentication import AuthError
from error import error_response
from quart import abort, current_app, jsonify, request


def authenticated_path(route_fn: Callable[[str, Dict[str, Any]], Any]):
    """
    Decorator for routes that request a specific file that might require access control enforcement
    """

    @wraps(route_fn)
    async def auth_handler(path=""):
        # If authentication is enabled, validate the user can access the file
        auth_helper = current_app.config[CONFIG_AUTH_CLIENT]
        search_client = current_app.config[CONFIG_SEARCH_CLIENT]
        authorized = False
        try:
            auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)
            authorized = await auth_helper.check_path_auth(path, auth_claims, search_client)
        except AuthError:
            abort(403)
        except Exception as error:
            logging.exception("Problem checking path auth %s", error)
            return error_response(error, route="/content")

        if not authorized:
            abort(403)

        return await route_fn(path, auth_claims)

    return auth_handler


def authenticated(route_fn: Callable[[Dict[str, Any]], Any]):
    """
    Decorator for routes that might require access control. Unpacks Authorization header information into an auth_claims dictionary
    """

    @wraps(route_fn)
    async def auth_handler():
        auth_helper = current_app.config[CONFIG_AUTH_CLIENT]
        try:
            auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)
        except AuthError:
            abort(403)

        return await route_fn(auth_claims)

    return auth_handler


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

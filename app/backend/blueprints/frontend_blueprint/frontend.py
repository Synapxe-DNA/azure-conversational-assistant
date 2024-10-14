import os
import uuid

from quart import Blueprint, request, send_from_directory

static_folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "browser")
frontend = Blueprint("app", __name__, static_folder=static_folder_path, url_prefix="/app")


@frontend.after_request
async def set_permissions_policy_header(response):
    response.headers["Permissions-Policy"] = "autoplay=()"
    return response


@frontend.route("/")
async def index():
    response = await frontend.send_static_file("index.html")
    response = await set_session_cookie(response)
    return response


@frontend.route("/<path:path>")
async def resources(path):
    try:
        response = await send_from_directory(static_folder_path, path)
    except Exception:
        response = await frontend.send_static_file("index.html")
    response = await set_session_cookie(response)
    return response


async def set_session_cookie(response):
    if "session" not in request.cookies:
        response.set_cookie("session", str(uuid.uuid4()), httponly=True)
    return response

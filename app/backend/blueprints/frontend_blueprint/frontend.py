import os

from quart import Blueprint, send_from_directory

static_folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "browser")
frontend = Blueprint("app", __name__, static_folder=static_folder_path, url_prefix="/app")


@frontend.route("/")
async def index():
    return await frontend.send_static_file("index.html")


@frontend.route("/<path:path>")
async def resources(path):
    try:
        return await send_from_directory(static_folder_path, path)
    except Exception:
        return await frontend.send_static_file("index.html")

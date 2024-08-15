import json
from datetime import datetime

from azure.storage.blob.aio import ContainerClient
from config import CONFIG_BLOB_FEEDBACK_CONTAINER_CLIENT
from quart import Blueprint, current_app, jsonify, request

feedback = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback.route("/", methods=["POST"])
async def feedback_endpoint():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    data = json.dumps(request_json)

    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

    feedback_client: ContainerClient = current_app.config[CONFIG_BLOB_FEEDBACK_CONTAINER_CLIENT]
    try:
        await feedback_client.upload_blob(name=f"{formatted_datetime}.json", data=data)
    except Exception as error:
        return str(error), 500

    return "Feedback sent!", 200

from azure.cosmos import ContainerProxy
from config import CONFIG_FEEDBACK_CONTAINER_CLIENT
from models.feedback import Feedback
from quart import Blueprint, current_app, jsonify, request

feedback = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback.route("/", methods=["POST"])
async def feedback_endpoint():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    data = await request.get_json()

    containerClient: ContainerProxy = current_app.config[CONFIG_FEEDBACK_CONTAINER_CLIENT]

    try:
        feedback = Feedback(**data)
        await containerClient.create_item(feedback.model_dump(), enable_automatic_id_generation=True)

    except Exception as error:
        print(error)
        return str(error), 500

    return "Feedback sent!", 200

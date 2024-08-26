from azure.cosmos import ContainerProxy
from config import CONFIG_FEEDBACK_CONTAINER_CLIENT
from models.feedback import FeedbackRequest
from quart import Blueprint, current_app, jsonify, request
from utils.utils import Utils

feedback = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback.route("/", methods=["POST"])
async def feedback_endpoint():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415

    data = await request.get_json()
    containerClient: ContainerProxy = current_app.config[CONFIG_FEEDBACK_CONTAINER_CLIENT]

    try:
        feedback_request = FeedbackRequest(**data)
        feedback_store = await Utils.construct_feedback_for_storing(feedback_request)
        await containerClient.create_item(feedback_store.model_dump(), enable_automatic_id_generation=True)
        return "Feedback sent!", 200

    except Exception as error:
        print(error)
        return str(error), 500

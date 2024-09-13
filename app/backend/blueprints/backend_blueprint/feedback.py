from azure.cosmos import ContainerProxy
from config import CONFIG_FEEDBACK_CONTAINER_CLIENT
from quart import Blueprint, current_app, jsonify, request
from utils.utils import Utils

feedback = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback.route("/stream", methods=["POST"])
async def feedback_endpoint():
    data = await request.form
    containerClient: ContainerProxy = current_app.config[CONFIG_FEEDBACK_CONTAINER_CLIENT]

    try:
        feedback_request = Utils.form_feedback_request(data)
        feedback_store = await Utils.construct_feedback_for_storing(feedback_request)
        await containerClient.create_item(feedback_store.model_dump(), enable_automatic_id_generation=True)
        return jsonify({"message": "Feedback sent!"}), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500

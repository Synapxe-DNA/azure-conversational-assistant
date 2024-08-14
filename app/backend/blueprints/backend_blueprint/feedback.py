from quart import Blueprint, jsonify, request


feedback = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback.route("/feedback", methods=["POST"])
async def feedback_endpoint():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    return request_json, 200 #placeholder

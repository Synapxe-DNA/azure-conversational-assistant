
import json

from typing import (
    Dict,
    Any,
    cast,
)
from quart import (
    Blueprint,
    current_app,
    request,
    jsonify,
)
from models.profile import Profile
from config import (
    CONFIG_CHAT_APPROACH, 
    CONFIG_CHAT_VISION_APPROACH,
    )
from approaches.approach import Approach
from utils.utils import Utils
from error import error_response

chat = Blueprint("chat", __name__, url_prefix="/chat")


@chat.route("/stream", methods=["POST"])
async def chat_stream_endpoint(auth_claims: Dict[str, Any] = None):

    # Receive data from the client
    data = await request.form

    context = data.get("context", {})
    # Extract data from the JSON message
    # profile = json.loads(data.get("profile"))
    chat_history = json.loads(data.get("chat_history", "[]"))
    query_text = json.loads(data["query"])
    profile = json.loads(data.get("profile", "{}"))
    profile = Profile(**profile)
    context["auth_claims"] = auth_claims

    messages = chat_history + [query_text]

    try:
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

        result = await approach.run_stream(
            messages=messages,
            context=context,
            profile=profile,
        )

        response = await Utils.construct_streaming_chat_response(result)
        return response, 200
    except Exception as error:
        return error_response(error, "/chat/stream")
    

# Not in use
@chat.route("/", methods=["POST"])
async def chat_endpoint(auth_claims: Dict[str, Any]):
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    context = request_json.get("context", {})
    context["auth_claims"] = auth_claims
    try:
        use_gpt4v = context.get("overrides", {}).get("use_gpt4v", False)
        approach: Approach
        if use_gpt4v and CONFIG_CHAT_VISION_APPROACH in current_app.config:
            approach = cast(Approach, current_app.config[CONFIG_CHAT_VISION_APPROACH])
        else:
            approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

        result = await approach.run(
            request_json["messages"],
            context=context,
            session_state=request_json.get("session_state"),
        )
        return jsonify(result)
    except Exception as error:
        return error_response(error, "/chat")
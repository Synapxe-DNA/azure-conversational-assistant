import json
from typing import Any, Dict, cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH, CONFIG_CHAT_VISION_APPROACH
from error import error_response
from models.chat import TextChatRequest
from models.profile import Profile
from quart import Blueprint, current_app, jsonify, request
from utils.utils import Utils

chat = Blueprint("chat", __name__, url_prefix="/chat")


@chat.route("/stream", methods=["POST"])
async def chat_stream_endpoint():

    # Receive data from the client
    data = await request.form

    context = data.get("context", {})  # for overrides

    textChatRequest = TextChatRequest(
        chat_history=json.loads(data.get("chat_history", "[]")),
        query=json.loads(data["query"]),
        profile=Profile(**json.loads(data.get("profile", "{}"))),
    )

    messages = [chat_history.model_dump() for chat_history in textChatRequest.chat_history] + [textChatRequest.query]

    try:
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

        result = await approach.run_stream(
            messages=messages,
            context=context,
            profile=textChatRequest.profile,
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

from typing import Any, Dict, cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH, CONFIG_CHAT_VISION_APPROACH
from error import error_response
from models.chat import TextChatRequest
from models.request_type import RequestType
from opentelemetry import trace
from quart import Blueprint, current_app, jsonify, request
from utils.utils import Utils

# Get the global tracer provider
tracer = trace.get_tracer(__name__)

chat = Blueprint("chat", __name__, url_prefix="/chat")


@chat.route("/stream", methods=["POST"])
async def chat_stream_endpoint():
    with tracer.start_as_current_span("chat_stream") as span:
        try:
            # Receive data from the client
            data = await request.form
            textChatRequest = TextChatRequest(**Utils.form_request(data).model_dump())

            approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

            result = await approach.run_stream(
                messages=Utils.form_message(textChatRequest.chat_history, textChatRequest.query),
                profile=textChatRequest.profile,
                language=textChatRequest.language,
            )

            response = await Utils.construct_streaming_response(result, RequestType.CHAT)
            span.set_attribute("http.url", "testing from local")
            span.set_attribute("token_count", "12")
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

import logging
from typing import cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH
from decorators import require_authentication
from error.error import error_response
from models.chat import TextChatRequest
from models.request_type import RequestType
from quart import Blueprint, current_app, jsonify, request
from utils.request_handler import RequestHandler
from utils.response_handler import ResponseHandler

chat = Blueprint("chat", __name__, url_prefix="/chat")


@chat.route("/stream", methods=["POST"])
async def chat_stream_endpoint():
    try:
        # Receive data from the client
        data = await request.get_json()
        textChatRequest = TextChatRequest(**RequestHandler.form_query_request(data).model_dump())
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

        result = await approach.run_stream(
            messages=RequestHandler.form_message(textChatRequest.chat_history, textChatRequest.query),
            profile=textChatRequest.profile,
            language=textChatRequest.language.lower(),
        )
        response = await ResponseHandler.construct_streaming_response(
            result, RequestType.CHAT, textChatRequest.language.lower()
        )
        return response, 200
    except Exception as error:
        logging.error(f"Exception in /chat/stream. {error}")
        return jsonify(error_response(error)), 500


@chat.route("", methods=["POST"])
@require_authentication
async def chat_endpoint():
    try:
        data = await request.get_json()
        textChatRequest = TextChatRequest(**RequestHandler.form_query_request(data).model_dump())
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

        result = await approach.run(
            messages=RequestHandler.form_message(textChatRequest.chat_history, textChatRequest.query),
            profile=textChatRequest.profile,
            language=textChatRequest.language,
        )

        response = ResponseHandler.construct_non_streaming_response(result)

        return response, 200
    except Exception as error:
        logging.error(f"Exception in /chat. {error}")
        return jsonify(error_response(error)), 500

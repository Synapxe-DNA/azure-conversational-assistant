import logging
from typing import cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH
from decorators import require_authentication
from error import error_response
from models.chat import TextChatRequest
from models.request_type import RequestType
from quart import Blueprint, current_app, request
from utils.utils import Utils

chat = Blueprint("chat", __name__, url_prefix="/chat")


@chat.route("/stream", methods=["POST"])
async def chat_stream_endpoint():
    try:
        # Receive data from the client
        data = await request.get_json()
        textChatRequest = TextChatRequest(**Utils.form_query_request(data).model_dump())
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

        result = await approach.run_stream(
            messages=Utils.form_message(textChatRequest.chat_history, textChatRequest.query),
            profile=textChatRequest.profile,
            language=textChatRequest.language,
        )

        response = await Utils.construct_streaming_response(result, RequestType.CHAT)
        return response, 200
    except Exception as error:
        logging.error("Exception in /chat/stream. ", error)
        return error_response(error, "/chat/stream")


@chat.route("", methods=["POST"])
@require_authentication
async def chat_endpoint():
    try:
        data = await request.get_json()
        textChatRequest = TextChatRequest(**Utils.form_query_request(data).model_dump())
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])

        result = await approach.run(
            messages=Utils.form_message(textChatRequest.chat_history, textChatRequest.query),
            profile=textChatRequest.profile,
            language=textChatRequest.language,
        )

        response = Utils.construct_non_streaming_response(result)

        return response, 200
    except Exception as error:
        logging.error("Exception in /chat. ", error)
        return error_response(error, "/chat")

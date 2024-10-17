import logging
import time
from typing import cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH
from error.error import error_response
from models.request_type import RequestType
from models.voice import VoiceChatRequest
from quart import Blueprint, current_app, request
from utils.request_handler import RequestHandler
from utils.response_handler import ResponseHandler

voice = Blueprint("voice", __name__, url_prefix="/voice")


@voice.route("/stream", methods=["POST"])
async def voice_endpoint():

    try:
        # Get the start time
        start_time = time.time()

        # Receive data from the client
        data = await request.get_json()
        # Extract data from the JSON message
        voiceChatRequest = VoiceChatRequest(**RequestHandler.form_query_request(data).model_dump())

        # Send transcribed text and data to LLM
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])
        result = await approach.run_stream(
            messages=RequestHandler.form_message(voiceChatRequest.chat_history, voiceChatRequest.query),
            profile=voiceChatRequest.profile,
            language=voiceChatRequest.language.lower(),
        )

        response = await ResponseHandler.construct_streaming_response(
            result, RequestType.VOICE, voiceChatRequest.language.lower(), start_time
        )
        return response, 200
    except Exception as error:
        logging.error(f"Exception in /voice/stream. {error}")
        return error_response(error)

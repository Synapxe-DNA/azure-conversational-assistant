from typing import cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH
from error import error_response
from models.request_type import RequestType
from models.voice import VoiceChatRequest
from quart import Blueprint, current_app, request
from utils.utils import Utils

voice = Blueprint("voice", __name__, url_prefix="/voice")


@voice.route("/", methods=["POST"])
async def voice_endpoint():

    try:
        # Receive data from the client
        data = await request.form
        # Extract data from the JSON message
        voiceChatRequest = VoiceChatRequest(**Utils.form_request(data).model_dump())

        # Send transcribed text and data to LLM
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])
        result = await approach.run_stream(
            messages=Utils.form_message(voiceChatRequest.chat_history, voiceChatRequest.query),
            profile=voiceChatRequest.profile,
            language=voiceChatRequest.language,
        )

        response = await Utils.construct_streaming_response(result, RequestType.VOICE)
        return response, 200
    except Exception as error:
        return error_response(error, "/voice")

import json
from typing import cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH
from error import error_response
from models.profile import Profile
from models.voice import VoiceChatRequest
from quart import Blueprint, current_app, request
from utils.utils import Utils

voice = Blueprint("voice", __name__, url_prefix="/voice")


@voice.route("/", methods=["POST"])
async def voice_endpoint():

    # Receive data from the client
    data = await request.form

    # Extract data from the JSON message
    query_text = data["query"]

    context = data.get("context", {})

    voiceChatRequest = VoiceChatRequest(
        chat_history=json.loads(data.get("chat_history", "[]")),
        profile=Profile(**json.loads(data.get("profile", "{}"))),
        query=data["query"],
    )

    # Detect language if default
    # if profile.language == "default":
    #     languages = [Language.ENGLISH, Language.CHINESE, Language.TAMIL, Language.MALAY]
    #     detector = LanguageDetectorBuilder.from_languages(*languages).build()
    #     language = detector.detect_language_of(query_text)
    #     language = str(language).split(".")[1].lower()  # get language name from enum
    #     profile.language = language

    # Form message
    messages = [chat_history.model_dump() for chat_history in voiceChatRequest.chat_history] + [
        {"content": query_text, "role": "user"}
    ]

    # Send transcribed text and data to LLM
    try:
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])
        result = await approach.run_stream(
            messages=messages,
            context=context,
            profile=voiceChatRequest.profile,
        )

        response = await Utils.construct_streaming_response(result, "voice")
        return response, 200
    except Exception as error:
        return error_response(error, "/voice")

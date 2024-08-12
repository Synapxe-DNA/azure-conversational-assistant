import json
from io import BytesIO
from typing import Any, Dict, cast

from approaches.approach import Approach
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from config import CONFIG_CHAT_APPROACH
from error import error_response
from lingua import Language, LanguageDetectorBuilder
from models.profile import Profile
from openai import AsyncOpenAI
from quart import Blueprint, current_app, request
from utils.utils import Utils

# print(lang)
voice = Blueprint("voice", __name__, url_prefix="/voice")


@voice.route("/", methods=["POST"])
async def voice_endpoint(auth_claims: Dict[str, Any] = None):

    # Receive data from the client
    data = await request.form
    audio = await request.files

    # Extract data from the JSON message
    context = data.get("context", {})

    profile_json = json.loads(data.get("profile"))
    profile = Profile(**profile_json)

    chat_history = json.loads(data.get("chat_history", "[]"))
    context["auth_claims"] = auth_claims

    # Convert audio to text
    config: ChatReadRetrieveReadApproach = current_app.config[CONFIG_CHAT_APPROACH]
    client: AsyncOpenAI = config.openai_client_2
    audio_file = audio["query"]
    buffer = BytesIO(audio_file.read())
    buffer.name = f"file.{audio_file.filename.split('.')[-1]}"  # Required to indicate file type for whisper

    query_text = await client.audio.transcriptions.create(
        file=buffer, model=config.whisiper_deployment, response_format="text"
    )

    # Detect language if default
    if profile.language == "default":
        languages = [Language.ENGLISH, Language.CHINESE, Language.TAMIL, Language.MALAY]
        detector = LanguageDetectorBuilder.from_languages(*languages).build()
        language = detector.detect_language_of(query_text)
        language = str(language).split(".")[1].lower()  # get language name from enum
        profile.language = language

    # Form message
    messages = chat_history + [{"content": query_text, "role": "user"}]

    # Send transcribed text and data to LLM
    try:
        approach = cast(Approach, current_app.config[CONFIG_CHAT_APPROACH])
        result = await approach.run_stream(
            messages=messages,
            context=context,
            profile=profile,
        )

        response = await Utils.construct_streaming_voice_response(result, query_text)
        return response, 200
    except Exception as error:
        return error_response(error, "/voice")

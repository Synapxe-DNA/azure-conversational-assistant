import json
from typing import cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH
from error import error_response
from models.profile import Profile
from quart import Blueprint, current_app, request
from utils.utils import Utils

# print(lang)
voice = Blueprint("voice", __name__, url_prefix="/voice")


@voice.route("/", methods=["POST"])
async def voice_endpoint():

    # Receive data from the client
    data = await request.form

    # Extract data from the JSON message
    query_text = data["query"]

    context = data.get("context", {})

    profile_json = json.loads(data.get("profile"))
    profile = Profile(**profile_json)

    chat_history = json.loads(data.get("chat_history", "[]"))

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

        response = await Utils.construct_streaming_voice_response(result)
        return response, 200
    except Exception as error:
        return error_response(error, "/voice")

import logging

from config import CONFIG_TEXT_TO_SPEECH_SERVICE
from models.speech import SpeechRequest
from quart import Blueprint, current_app, jsonify, request

speech = Blueprint("speech", __name__, url_prefix="/speech")


@speech.route("", methods=["POST"])
async def speech_endpoint():
    try:
        request_json = await request.get_json()
        speech_request = SpeechRequest(**request_json)
        tts = current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE]
        audio_data = tts.readText(speech_request.text, False)
        return audio_data, 200, {"Content-Type": "audio/mp3"}
    except Exception as e:
        logging.error(f"Exception in /speech. {e}")
        return jsonify({"error": str(e)}), 500

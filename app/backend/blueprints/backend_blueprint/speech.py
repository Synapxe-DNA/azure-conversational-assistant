import logging

from quart import (
    Blueprint,
    request,
    jsonify,
)
from speech.text_to_speech import TextToSpeech

speech = Blueprint("speech", __name__, url_prefix="/speech")


@speech.route("/", methods=["POST"])
async def speech_endpoint():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    text = request_json["text"]
    try:
        tts = await TextToSpeech.create()
        audio_data = tts.readText(text)
        return audio_data, 200, {"Content-Type": "audio/mp3"}
    except Exception as e:
        logging.exception("Exception in /speech")
        return jsonify({"error": str(e)}), 500
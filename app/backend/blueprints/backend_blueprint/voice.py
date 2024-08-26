import json
from io import BytesIO
from typing import Any, Dict, cast

from approaches.approach import Approach
from config import CONFIG_CHAT_APPROACH, CONFIG_SPEECH_TO_TEXT_SERVICE
from error import error_response
from models.profile import Profile
from pydub import AudioSegment
from quart import Blueprint, current_app, request
from utils.utils import Utils

voice = Blueprint("voice", __name__, url_prefix="/voice")


@voice.route("/", methods=["POST"])
async def voice_endpoint(auth_claims: Dict[str, Any] = None):

    # Receive data from the client

    data = await request.form
    audio = await request.files

    context = data.get("context", {})

    # Process audio
    target_sample_rate = 16000  # 16 kHz
    target_channels = 1  # Mono
    target_bit_depth = 16  # 16-bit

    # Resample audio
    audio_seg = AudioSegment.from_file(audio["query"], format="webm")
    audio_seg = audio_seg.set_frame_rate(target_sample_rate)
    audio_seg = audio_seg.set_channels(target_channels)
    audio_seg = audio_seg.set_sample_width(target_bit_depth // 8)
    wav_io = BytesIO()
    audio_seg.export(wav_io, format="wav")

    # Extract data from the JSON message
    profile_json = json.loads(data.get("profile"))
    profile = Profile(**profile_json)

    chat_history = json.loads(data.get("chat_history", "[]"))
    audio_blob = wav_io.getvalue()
    context["auth_claims"] = auth_claims

    wav_io.close()

    # Convert audio to text

    stt = current_app.config[CONFIG_SPEECH_TO_TEXT_SERVICE]
    transcription = stt.transcribe(audio_blob)

    # language = Utils.get_mode_language(transcription['language'])
    query_text = " ".join(transcription["text"])

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

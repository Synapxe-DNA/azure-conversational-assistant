import base64
import re
import time

from azure.cognitiveservices.speech import (
    ResultReason,
    SpeechConfig,
    SpeechSynthesisOutputFormat,
    SpeechSynthesisResult,
    SpeechSynthesizer,
)
from config import (
    CONFIG_CREDENTIAL,
    CONFIG_SPEECH_SERVICE_ID,
    CONFIG_SPEECH_SERVICE_LOCATION,
    CONFIG_SPEECH_SERVICE_TOKEN,
)
from models.language import LanguageBCP47
from quart import current_app
from utils.utils import Utils


class TextToSpeech:

    def __init__(self, speech_token) -> None:
        self.resource_id = current_app.config.get(CONFIG_SPEECH_SERVICE_ID)
        self.region = current_app.config[CONFIG_SPEECH_SERVICE_LOCATION]
        self.speech_token = speech_token
        self.auth_token = self.getAuthToken()
        self.speech_config = SpeechConfig(auth_token=self.auth_token, region=self.region)
        self.speech_config.speech_synthesis_output_format = SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        self.speech_synthesizer = SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)

    @classmethod
    async def create(cls):
        speech_token = await cls.getCredential()
        return cls(speech_token)

    @staticmethod
    async def getCredential():
        speech_token = current_app.config.get(CONFIG_SPEECH_SERVICE_TOKEN)
        if speech_token is None or speech_token.expires_on < time.time() + 60:
            speech_token = await current_app.config[CONFIG_CREDENTIAL].get_token(
                "https://cognitiveservices.azure.com/.default"
            )
        current_app.config[CONFIG_SPEECH_SERVICE_TOKEN] = speech_token
        return speech_token

    def getAuthToken(self):
        return "aad#" + self.resource_id + "#" + self.speech_token.token

    def readText(self, text, encode: bool, language=None):
        if language is None:
            language = Utils.get_language(text)

        # Force output language for /voice endpoint
        self.speech_config.speech_synthesis_voice_name = LanguageBCP47.voice_mapping[language]
        self.speech_synthesizer = SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)

        text = re.sub(r"[*#]", "", text)  # remove * and # from markdown
        text = re.sub(r"-{2,}", "", text)  # remove 2 or more consecutive `-` from markdown
        result: SpeechSynthesisResult = self.speech_synthesizer.speak_text_async(text).get()
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            if encode:
                return base64.b64encode(result.audio_data).decode("utf-8")
            else:
                return result.audio_data
        elif result.reason == ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            current_app.logger.error(
                "Speech synthesis canceled: %s %s", cancellation_details.reason, cancellation_details.error_details
            )
            raise Exception("Speech synthesis canceled. Check logs for details.")
        else:
            current_app.logger.error("Unexpected result reason: %s", result.reason)
            raise Exception("Speech synthesis failed. Check logs for details.")

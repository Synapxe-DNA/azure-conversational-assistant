import time

import azure.cognitiveservices.speech as speechsdk
from config import (
    CONFIG_CREDENTIAL,
    CONFIG_SPEECH_SERVICE_ID,
    CONFIG_SPEECH_SERVICE_LOCATION,
    CONFIG_SPEECH_SERVICE_TOKEN,
)
from quart import current_app


class SpeechToText:
    def __init__(self, speech_token):
        # set up config variables
        resource_id = current_app.config.get(CONFIG_SPEECH_SERVICE_ID)
        region = current_app.config[CONFIG_SPEECH_SERVICE_LOCATION]
        speech_token = speech_token
        auth_token = self.getAuthToken(resource_id, speech_token.token)

        # create recognizer
        self.speech_config = speechsdk.SpeechConfig(auth_token=auth_token, region=region)
        self.auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
            languages=["en-SG", "zh-CN", "ta-IN", "ms-MY"]
        )
        self.stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=self.stream)
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config=self.auto_detect_source_language_config,
        )

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

    def getAuthToken(self, resource_id, token):
        return "aad#" + resource_id + "#" + token

    def getSpeechRecognizer(self) -> speechsdk.SpeechRecognizer:
        return self.speech_recognizer

    def getStream(self):
        return self.stream

    def resetStream(self):
        self.stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=self.stream)
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config=self.auto_detect_source_language_config,
        )

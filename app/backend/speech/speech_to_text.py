import io
import threading
import time

import azure.cognitiveservices.speech as speechsdk
from config import (
    CONFIG_CREDENTIAL,
    CONFIG_SPEECH_SERVICE_ID,
    CONFIG_SPEECH_SERVICE_LOCATION,
    CONFIG_SPEECH_SERVICE_TOKEN,
)
from quart import current_app


class SpeechRecognition:
    def __init__(self, speech_token):

        self.resource_id = current_app.config.get(CONFIG_SPEECH_SERVICE_ID)
        self.region = current_app.config[CONFIG_SPEECH_SERVICE_LOCATION]
        self.speech_token = speech_token
        self.auth_token = self.getAuthToken()

        self.speech_config = speechsdk.SpeechConfig(auth_token=self.auth_token, region=self.region)
        self.audio_blob = None
        self.recognition_done = threading.Event()

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

    def setup_speech_recognizer(self):
        speech_config = self.speech_config
        speech_config.set_property(
            property_id=speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
            value="Continuous",
        )

        audio_stream = speechsdk.audio.PushAudioInputStream()
        # audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

        auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
            languages=["en-SG", "zh-CN", "ta-IN", "ms-MY"]
        )
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_source_language_config,
        )

        all_results = {"text": [], "language": []}

        speech_recognizer.recognized.connect(self.handle_final_result(all_results))
        speech_recognizer.session_started.connect(lambda evt: print(f"SESSION STARTED: {evt}"))
        speech_recognizer.session_stopped.connect(lambda evt: self.recognition_done.set())
        speech_recognizer.canceled.connect(lambda evt: self.recognition_done.set())

        self.push_audio(audio_stream)

        return speech_recognizer, all_results

    def push_audio(self, audio_stream):
        with io.BytesIO(self.audio_blob) as audio_file:
            chunk_size = 1024
            while True:
                chunk = audio_file.read(chunk_size)
                if not chunk:
                    break
                audio_stream.write(chunk)
            audio_stream.close()

    @staticmethod
    def handle_final_result(all_results):
        def inner(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                detected_language = evt.result.properties[
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
                ]
                all_results["text"].append(evt.result.text)
                all_results["language"].append(detected_language)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                print(f"No speech could be recognized: {evt.result.no_match_details}")

        return inner

    def transcribe(self, audio_blob):
        self.audio_blob = audio_blob
        self.speech_recognizer, all_results = self.setup_speech_recognizer()
        self.speech_recognizer.start_continuous_recognition()
        self.recognition_done.wait()
        self.speech_recognizer.stop_continuous_recognition()
        return all_results

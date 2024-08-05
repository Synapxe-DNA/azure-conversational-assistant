from .text_to_speech import TextToSpeech
from .translate import Translator


class TTSPipeline:

    def __init__(self):
        self.text_to_speech = None
        self.translator = Translator()

    @classmethod
    async def create(cls):
        pipeline = cls()
        pipeline.text_to_speech = await TextToSpeech.create()
        return pipeline

    async def process_and_stream_audio(self, chunk, language):
        if language == "en":
            translated_chunk = chunk
        else:
            translated_chunk = await self.translator.translate(chunk, language)
        audio_data = await self.text_to_speech.readText(translated_chunk)
        if audio_data:
            return audio_data
            # return {audio_data: audio_data, translated_chunk: translated_chunk}

    # async def generate_speech_stream(self, chunks, language):
    #     '''
    #     This function processes input streamed by word. It accumulates words into sentences,
    #     using a full stop as the sentence delimiter. Each complete sentence is then processed
    #     and streamed as audio.
    #     '''
    #     current_sentence = []
    #     for word in chunks:
    #         if word in [".", " ."]:
    #             if current_sentence:
    #                 sentence = " ".join(current_sentence) + "."
    #                 data = await self.process_and_stream_audio(sentence, language)
    #                 if data:
    #                     return data
    #                 current_sentence = []
    #         else:
    #             current_sentence.append(word)

    #     # Process any remaining words if the last sentence doesn't end with a period
    #     if current_sentence:
    #         sentence = "".join(current_sentence)
    #         data = await self.process_and_stream_audio(sentence, language)
    #         if data:
    #             return data

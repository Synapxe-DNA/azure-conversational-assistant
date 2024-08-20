import base64
import dataclasses
import json
import logging
import re
from collections import Counter
from typing import Any, AsyncGenerator, List

from config import CONFIG_TEXT_TO_SPEECH_SERVICE
from error import error_dict
from models.source import Source
from models.voice import VoiceChatResponse
from quart import current_app, stream_with_context


class Utils:

    async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
        try:
            async for event in r:
                yield json.dumps(event, ensure_ascii=False, cls=JSONEncoder) + "\n"
        except Exception as error:
            logging.exception("Exception while generating response stream: %s", error)
            yield json.dumps(error_dict(error))

    @staticmethod
    def get_mode_language(languages: List[str]):
        counter = Counter(languages)
        max_count = max(counter.values())
        mode = [string for string, count in counter.items() if count == max_count]

        return mode[0]  # Tiebreaker: Language that comes first in the list

    @staticmethod
    async def construct_streaming_voice_response(
        result: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[str, None]:
        @stream_with_context
        async def generator() -> AsyncGenerator[str, None]:
            text_response = ""
            tts = current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE]

            async for res in Utils.format_as_ndjson(result):
                print("====================================")
                print(res)
                print("====================================")
                # Extract sources
                res = json.loads(res)
                thoughts = res.get("context", {}).get("thoughts", [])
                followup_question = res.get("context", {}).get("followup_questions", [])
                if not thoughts == []:
                    sources = extract_sources_from_thoughts(thoughts)
                    response = VoiceChatResponse(
                        response_message="",
                        sources=sources,
                        additional_question_1="",
                        additional_question_2="",
                        audio_base64="",
                    )
                    yield response.model_dump_json()
                elif not followup_question == []:
                    response = VoiceChatResponse(
                        response_message="",
                        sources=[],
                        additional_question_1=followup_question[0],
                        additional_question_2=followup_question[1],
                        audio_base64="",
                    )
                    yield response.model_dump_json()
                else:
                    # Extract text response
                    text_response_chunk = res.get("delta", {}).get("content", "")

                    if text_response_chunk is None:
                        break

                    text_response += text_response_chunk
                    if bool(re.search(r"[.,!?。，！？]", text_response_chunk)):
                        audio_data = tts.readText(text_response)
                        response = VoiceChatResponse(
                            response_message=text_response,
                            sources=[],
                            additional_question_1="",
                            additional_question_2="",
                            audio_base64=base64.b64encode(audio_data).decode("utf-8"),
                        )
                        yield response.model_dump_json()
                        text_response = ""

        return generator()

    @staticmethod
    async def construct_streaming_chat_response(
        result: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[str, None]:
        @stream_with_context
        async def generator() -> AsyncGenerator[str, None]:
            async for res in Utils.format_as_ndjson(result):
                print("====================================")
                print(res)
                print("====================================")
                # Extract sources
                res = json.loads(res)
                thoughts = res.get("context", {}).get("thoughts", [])
                followup_question = res.get("context", {}).get("followup_questions", [])
                if not thoughts == []:
                    pass
                    # sources = extract_data_from_stream(thoughts)
                    # response = TextChatResponse(
                    #     response_message="",
                    #     sources=sources,
                    #     additional_question_1="",
                    #     additional_question_2="",
                    # )
                    # yield response.model_dump_json()
                elif not followup_question == []:
                    pass
                    # response = TextChatResponse(
                    #     response_message="",
                    #     sources=[],
                    #     additional_question_1=followup_question[0],
                    #     additional_question_2=followup_question[1],
                    # )
                    # yield response.model_dump_json()
                else:
                    # Extract text response
                    text_response_chunk = res.get("delta", {}).get("content", "")
                    if text_response_chunk is None:
                        break
                    # response = TextChatResponse(
                    #     response_message=text_response_chunk,
                    #     sources=[],
                    #     additional_question_1="",
                    #     additional_question_2="",
                    # )
                    yield text_response_chunk
                    # yield response.model_dump_json()
                    print("====================================")
                    print(text_response_chunk)
                    print("====================================")

        return generator()


def extract_sources_from_thoughts(thoughts: List[dict[str, Any]]):
    sources_desc = thoughts[2].get("description", [])
    sources = []
    for source in sources_desc:  # sources[2] is search results
        src = Source(
            id=str(source.get("id")),
            title=str(source.get("title")),
            cover_image_url=str(source.get("cover_image_url")),
            full_url=str(source.get("full_url")),
            content_category=str(source.get("content_category")),
            chunks=str(source.get("chunks")),
        )
        sources.append(src)
    return sources


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        return super().default(o)

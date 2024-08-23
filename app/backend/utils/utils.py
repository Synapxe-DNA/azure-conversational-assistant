import json
import logging
import re
from typing import Any, AsyncGenerator, List, Literal

from config import CONFIG_TEXT_TO_SPEECH_SERVICE
from error import error_dict
from models.chat import TextChatResponse
from models.source import Source
from models.voice import VoiceChatResponse
from quart import current_app, stream_with_context
from utils.json_encoder import JSONEncoder


class Utils:

    @staticmethod
    async def construct_streaming_response(
        result: AsyncGenerator[dict[str, Any], None],
        request_type: Literal["chat", "voice"],
    ) -> AsyncGenerator[str, None]:
        """
        Reconstructing the generator response from LLM to a new generator response in our format
        """

        @stream_with_context
        async def generator() -> AsyncGenerator[str, None]:
            response_message = ""
            tts = current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE]

            async for res in format_as_ndjson(result):
                # Extract sources
                res = json.loads(res)
                error_msg = res.get("error", None)
                thoughts = res.get("context", {}).get("thoughts", [])
                text_response_chunk = ""
                sources = []

                if error_msg is not None:
                    if request_type == "chat":
                        response = TextChatResponse(
                            response_message=error_msg,
                            sources=[],
                        )
                        yield response.model_dump_json()
                    else:
                        audio_data = tts.readText(error_msg)
                        response = VoiceChatResponse(
                            response_message=error_msg,
                            sources=[],
                            audio_base64=audio_data,
                        )
                        yield response.model_dump_json()
                elif not thoughts == []:
                    sources = extract_sources_from_thoughts(thoughts)

                    if request_type == "chat":
                        response = TextChatResponse(
                            response_message="",
                            sources=sources,
                        )
                        yield response.model_dump_json()

                    else:
                        response = VoiceChatResponse(
                            response_message="",
                            sources=sources,
                            audio_base64="",
                        )
                        yield response.model_dump_json()
                else:
                    # Extract text response
                    text_response_chunk = res.get("delta", {}).get("content", "")

                    if text_response_chunk is None:
                        break

                    if request_type == "chat":
                        response = TextChatResponse(
                            response_message=text_response_chunk,
                            sources=[],
                        )
                        yield response.model_dump_json()

                    else:
                        response_message += text_response_chunk
                        if bool(
                            re.search(r"[.,!?。，！？]", text_response_chunk)
                        ):  # Transcribe text only when punctuation is detected
                            audio_data = tts.readText(response_message)
                            response = VoiceChatResponse(
                                response_message=response_message,
                                sources=[],
                                audio_base64=audio_data,
                            )
                            yield response.model_dump_json()
                            response_message = ""

        return generator()


# Helper functions


def extract_sources_from_thoughts(thoughts: List[dict[str, Any]]):
    sources_desc = thoughts[2].get("description", [])  # thoughts[2] is search results
    sources = []
    for source in sources_desc:
        src_instance = Source(
            id=[str(source.get("id"))],
            title=str(source.get("title")),
            cover_image_url=str(source.get("cover_image_url")),
            full_url=str(source.get("full_url")),
            content_category=str(source.get("content_category")),
        )

        if src_instance.full_url in [s.full_url for s in sources]:
            for s in sources:
                if s.full_url == src_instance.full_url:
                    s.id.extend(src_instance.id)
        else:
            sources.append(src_instance)

    return sources


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    try:
        async for event in r:
            yield json.dumps(event, ensure_ascii=False, cls=JSONEncoder) + "\n"
    except Exception as error:
        logging.exception("Exception while generating response stream: %s", error)
        yield json.dumps(error_dict(error))

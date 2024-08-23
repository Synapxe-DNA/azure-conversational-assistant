import json
import logging
import re
from typing import Any, AsyncGenerator, List

from azure.search.documents.aio import SearchClient
from config import CONFIG_SEARCH_CLIENT, CONFIG_TEXT_TO_SPEECH_SERVICE
from error import error_dict
from lingua import Language, LanguageDetectorBuilder
from models.chat import TextChatResponse
from models.chat_history import ChatHistory
from models.feedback import FeedbackRequest, FeedbackStore
from models.language import LanguageSelected
from models.profile import Profile
from models.request import Request
from models.request_type import RequestType
from models.source import Source, SourceWithChunk
from models.voice import VoiceChatResponse
from quart import current_app, stream_with_context
from utils.json_encoder import JSONEncoder
from werkzeug.datastructures import MultiDict


class Utils:

    @staticmethod
    async def construct_streaming_response(
        result: AsyncGenerator[dict[str, Any], None],
        request_type: RequestType,
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

                if error_msg is not None:
                    yield construct_error_response(error_msg, request_type)
                elif not thoughts == []:
                    yield construct_source_response(thoughts, request_type)
                else:
                    # Extract text response
                    text_response_chunk = res.get("delta", {}).get("content", "")

                    if text_response_chunk is None:
                        break

                    if request_type == RequestType.CHAT:
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
                            audio_data = tts.readText(response_message, True)  # remove * from markdown
                            response = VoiceChatResponse(
                                response_message=response_message,
                                sources=[],
                                audio_base64=audio_data,
                            )
                            yield response.model_dump_json()
                            response_message = ""

        return generator()

    @staticmethod
    async def construct_feedback_for_storing(feedback_request: FeedbackRequest) -> FeedbackStore:
        search_client: SearchClient = current_app.config[CONFIG_SEARCH_CLIENT]
        sources: List[SourceWithChunk] = []
        for source in feedback_request.retrieved_sources:
            for id in source.ids:
                result = await search_client.get_document(id)  # Retrieve text chunks via id
                sources.append(
                    SourceWithChunk(
                        id=id,
                        title=source.title,
                        cover_image_url=source.cover_image_url,
                        full_url=source.full_url,
                        content_category=source.content_category,
                        chunk=result["chunks"],
                    )  # Attribute name may change based on data
                )

        feedback_store = FeedbackStore(
            date_time=feedback_request.date_time,
            feedback_type=feedback_request.feedback_type,
            feedback_category=feedback_request.feedback_category,
            feedback_remarks=feedback_request.feedback_remarks,
            user_profile=feedback_request.user_profile,
            chat_history=feedback_request.chat_history,
            retrieved_sources=sources,
        )

        return feedback_store

    @staticmethod
    def form_message(chat_history_list: List[ChatHistory], query: dict[str, str]) -> list[dict[str, Any]]:
        messages = [chat_history.model_dump() for chat_history in chat_history_list] + [query]
        return messages

    @staticmethod
    def form_request(data: MultiDict) -> Request:

        language = json.loads(data["language"])
        print("CHOSEN LANGUAGE: ", language)
        query = json.loads(data["query"])
        language = get_language(query["content"]) if language == LanguageSelected.SPOKEN.value else data["language"]
        print("DETECTED LANGUAGE: ", language)

        request = Request(
            chat_history=json.loads(data.get("chat_history", "[]")),
            profile=Profile(**json.loads(data.get("profile", "{}"))),
            query=query,
            language=language,
        )
        return request


# Helper functions


def extract_sources_from_thoughts(thoughts: List[dict[str, Any]]):
    sources_desc = thoughts[2].get("description", [])  # thoughts[2] is search results
    sources = []
    for source in sources_desc:
        src_instance = Source(
            ids=[str(source.get("id"))],
            title=str(source.get("title")),
            cover_image_url=str(source.get("cover_image_url")),
            full_url=str(source.get("full_url")),
            content_category=str(source.get("content_category")),
        )

        if src_instance.full_url in [s.full_url for s in sources]:
            for s in sources:
                if s.full_url == src_instance.full_url:
                    s.ids.extend(src_instance.ids)
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


def construct_error_response(error_msg: str, request_type: RequestType) -> str:
    tts = current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE]

    if request_type == RequestType.CHAT:
        response = TextChatResponse(
            response_message=error_msg,
            sources=[],
        )
    else:
        audio_data = tts.readText(error_msg)
        response = VoiceChatResponse(
            response_message=error_msg,
            sources=[],
            audio_base64=audio_data,
        )
    return response.model_dump_json()


def construct_source_response(thoughts: List[dict[str, Any]], request_type: RequestType) -> str:
    sources = extract_sources_from_thoughts(thoughts)

    if request_type == RequestType.CHAT:
        response = TextChatResponse(
            response_message="",
            sources=sources,
        )
    else:
        response = VoiceChatResponse(
            response_message="",
            sources=sources,
            audio_base64="",
        )
    return response.model_dump_json()


def get_language(query_text: str):
    languages = [Language.ENGLISH, Language.CHINESE, Language.TAMIL, Language.MALAY]
    detector = LanguageDetectorBuilder.from_languages(*languages).build()
    language = detector.detect_language_of(query_text)
    if language is None:
        language = "english"
        print("Language not detected. Defaulting to English.")
    else:
        language = str(language).split(".")[1].lower()  # get language name from enum
    return language

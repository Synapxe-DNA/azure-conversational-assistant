import json
import logging
import re
from typing import Any, AsyncGenerator, List

from azure.search.documents.aio import SearchClient
from config import CONFIG_SEARCH_CLIENT, CONFIG_TEXT_TO_SPEECH_SERVICE
from error import error_dict
from lingua import Language, LanguageDetectorBuilder
from models.chat import TextChatResponse, TextChatResponseWtihChunk
from models.chat_history import ChatHistory
from models.feedback import FeedbackRequest, FeedbackStore
from models.language import LanguageSelected
from models.logstore import LogStore
from models.profile import Profile
from models.request import Request
from models.request_type import RequestType
from models.source import Source, SourceWithChunk
from models.voice import VoiceChatResponse
from quart import current_app, stream_with_context
from utils.json_encoder import JSONEncoder
from werkzeug.datastructures import MultiDict


class Utils:
    """
    Construct a streaming response from the LLM response that will be returned to the frontend
    """

    @staticmethod
    async def construct_streaming_response(
        result: AsyncGenerator[dict[str, Any], None],
        request_type: RequestType,
        language: str = None,
    ) -> AsyncGenerator[str, None]:
        """
        Reconstructing the generator response from LLM to a new generator response in our format
        """

        @stream_with_context
        async def generator() -> AsyncGenerator[str, None]:

            response_message = ""
            tts = current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE]
            # logStore = LogStore()

            async for res in format_as_ndjson(result):
                # Extract sources
                res = json.loads(res)
                error_msg = res.get("error", None)
                thoughts = res.get("context", {}).get("thoughts", [])
                text_response_chunk = ""
                if error_msg is not None:
                    yield construct_error_response(error_msg, request_type, language)
                elif not thoughts == []:
                    yield construct_source_response(thoughts, request_type)
                    # logStore = extract_thoughts_for_logging(thoughts, logStore)
                else:
                    # Extract text response
                    text_response_chunk = res.get("delta", {}).get("content", "")

                    if text_response_chunk is None:
                        if not response_message == "":
                            audio_data = tts.readText(response_message, True, language)
                            response = VoiceChatResponse(
                                response_message=response_message,
                                sources=[],
                                audio_base64=audio_data,
                            )
                            yield response.model_dump_json()
                            response_message = ""
                        break

                    # logStore.response_message += text_response_chunk

                    if request_type == RequestType.CHAT:
                        response = TextChatResponse(
                            response_message=text_response_chunk,
                            sources=[],
                        )
                        yield response.model_dump_json()

                    else:
                        response_message += text_response_chunk
                        if bool(
                            re.search(r"[.,!?。，！？]\s", text_response_chunk)
                        ):  # Transcribe text only when punctuation is detected
                            audio_data = tts.readText(response_message, True, language)
                            response = VoiceChatResponse(
                                response_message=response_message,
                                sources=[],
                                audio_base64=audio_data,
                            )
                            yield response.model_dump_json()
                            response_message = ""
            # await Utils.send_log(logStore)

        return generator()

    """
    Construct a non-streaming response from the LLM response that will be returned to the frontend
    Note: This function is only used for chat endpoint and not for voice
    """

    @staticmethod
    def construct_non_streaming_response(data: dict) -> dict[str, Any]:
        data = json.loads(json.dumps(data, ensure_ascii=False, cls=JSONEncoder) + "\n")
        thoughts = data.get("context", {}).get("thoughts", [])
        sources = extract_sources_with_chunks_from_thoughts(thoughts)
        response = TextChatResponseWtihChunk(
            response_message=data["message"]["content"],
            sources=sources,
        )
        return response.model_dump()

    """
    Construct a response from client feedback that will be stored in the database
    """

    @staticmethod
    async def construct_feedback_for_storing(feedback_request: FeedbackRequest) -> FeedbackStore:
        search_client: SearchClient = current_app.config[CONFIG_SEARCH_CLIENT]
        for chatHistory in feedback_request.chat_history:
            sources: List[SourceWithChunk] = []
            for source in chatHistory.sources:
                for id in source.ids:
                    try:
                        result = await search_client.get_document(id)  # Retrieve text chunks via id
                    except Exception:
                        result = {"chunks": "Chunk for source cannot be found"}
                    src = SourceWithChunk(
                        id=id,
                        title=source.title,
                        cover_image_url=source.cover_image_url,
                        full_url=source.full_url,
                        content_category=source.content_category,
                        chunk=result["chunks"],
                    )
                    sources.append(src)
            chatHistory.sources = sources

        return feedback_request

    """
    Utility function to form a message from the chat history and query into the specified LLM input format
    """

    @staticmethod
    def form_message(chat_history_list: List[ChatHistory], query: dict[str, str]) -> list[dict[str, Any]]:
        messages = [chat_history.model_dump() for chat_history in chat_history_list] + [query]
        return messages

    """
    Utility function to form a Request object from formdata
    """

    @staticmethod
    def form_formdata_request(data: MultiDict) -> Request:
        print(f"CHOSEN LANGUAGE: {data['language']}")
        language = (
            Utils.get_language(data["query"]) if data["language"] == LanguageSelected.SPOKEN.value else data["language"]
        )
        print(f"DETECTED LANGUAGE: {language}")
        request = Request(
            chat_history=json.loads(data["chat_history"]),
            profile=Profile(**json.loads(data["profile"])),
            query=json.loads(data["query"]),
            language=language,
        )

        return request

    """
    Utility function to form a Request object from json
    """

    @staticmethod
    def form_json_request(data: dict) -> Request:
        print(f"CHOSEN LANGUAGE: {data['language']}")
        language = (
            Utils.get_language(data["query"]) if data["language"] == LanguageSelected.SPOKEN.value else data["language"]
        )
        print(f"DETECTED LANGUAGE: {language}")

        request = Request(
            chat_history=data["chat_history"],
            profile=Profile(**data["profile"]),
            query=data["query"],
            language=language,
        )

        return request

    """
    Utility function to form a FeedbackRequest object from formdata
    """

    @staticmethod
    def form_feedback_request(data: MultiDict) -> FeedbackRequest:

        feedback_request = FeedbackRequest(
            date_time=data["date_time"],
            feedback_type=data["feedback_type"],
            feedback_category=json.loads(data["feedback_category"]),
            feedback_remarks=data.get("feedback_remarks", ""),
            user_profile=Profile(**json.loads(data["user_profile"])),
            chat_history=json.loads(data["chat_history"]),
        )
        return feedback_request

    """
    Utility function to get the language of the query text if language selected is "spoken"
    """

    @staticmethod
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

    # @staticmethod
    # async def send_log(logStore: LogStore):
    #     logStore.date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     containerClient = current_app.config[CONFIG_LOGGING_CONTAINER_CLIENT]
    #     try:
    #         await containerClient.create_item(logStore.model_dump(), enable_automatic_id_generation=True)
    #         logging.info("Log sent successfully")
    #     except Exception as error:
    #         logging.error("Error while sending log", error)
    #         pass


# Helper functions

"""
Utility function to extract sources without chunks from the ThoughtStep returned by the LLM
"""


def extract_sources_from_thoughts(thoughts: List[dict[str, Any]]) -> List[Source]:
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

        sources.append(src_instance)

    return sources


"""
Utility function to extract sources with chunks from the ThoughtStep returned by the LLM
"""


def extract_sources_with_chunks_from_thoughts(thoughts: List[dict[str, Any]]) -> List[SourceWithChunk]:
    sources_desc = thoughts[2].get("description", [])  # thoughts[2] is search results
    sources = []
    for source in sources_desc:
        src_instance = SourceWithChunk(
            id=str(source.get("id")),
            title=str(source.get("title")),
            cover_image_url=str(source.get("cover_image_url")),
            full_url=str(source.get("full_url")),
            content_category=str(source.get("content_category")),
            chunk=str(source.get("chunks")),
        )
        sources.append(src_instance)

    return sources


"""
Utility function to extract time taken, user query and sources with chunks from the ThoughtStep returned by the LLM
"""


def extract_thoughts_for_logging(thoughts: List[dict[str, Any]], logStore: LogStore) -> LogStore:
    logStore.time_taken = thoughts[4].get("description", -1)  # thoughts[4] is time taken
    logStore.user_query = thoughts[5].get("description", "")  # thoughts[5] is user query
    logStore.retrieved_sources = extract_sources_with_chunks_from_thoughts(thoughts)

    return logStore


"""
Utility function to format the LLM response into a json string
"""


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    try:
        async for event in r:
            yield json.dumps(event, ensure_ascii=False, cls=JSONEncoder) + "\n"
    except Exception as error:
        logging.exception("Exception while generating response stream: %s", error)
        yield json.dumps(error_dict(error))


"""
Utility function to construct error response from LLM into a json string
"""


def construct_error_response(error_msg: str, request_type: RequestType, language: str) -> str:
    tts = current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE]

    if request_type == RequestType.CHAT:
        response = TextChatResponse(
            response_message=error_msg,
            sources=[],
        )
    else:
        audio_data = tts.readText(error_msg, True, language)
        response = VoiceChatResponse(
            response_message=error_msg,
            sources=[],
            audio_base64=audio_data,
        )
    return response.model_dump_json()


"""
Utility function to construct source response from LLM into a json string
Note: This function is only used for voice endpoint and not for chat as sources will be streamed back first before the text response
"""


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

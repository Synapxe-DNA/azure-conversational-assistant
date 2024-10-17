import datetime
import json
import logging
import re
import time
from typing import Any, AsyncGenerator, List

import pytz
from azure.cosmos import ContainerProxy
from azure.cosmos.exceptions import CosmosHttpResponseError
from config import CONFIG_CHAT_HISTORY_CONTAINER_CLIENT, CONFIG_TEXT_TO_SPEECH_SERVICE
from models.apilog import APILog
from models.chat import TextChatResponse, TextChatResponseWithChunk
from models.chat_history import ChatHistory
from models.chat_message import ChatMessageWithSource
from models.request_type import RequestType
from models.source import Source, SourceWithChunk
from models.voice import VoiceChatResponse
from opentelemetry import trace
from quart import current_app, request, stream_with_context
from utils.json_encoder import JSONEncoder

# Get the global tracer provider
tracer = trace.get_tracer(__name__)


class ResponseHandler:

    @staticmethod
    async def construct_streaming_response(
        result: AsyncGenerator[dict[str, Any], None], request_type: RequestType, language: str, start_time: int
    ) -> AsyncGenerator[str, None]:
        """
        Reconstructing the generator response from LLM to a new generator response in our format
        """

        @stream_with_context
        async def generator() -> AsyncGenerator[str, None]:
            tts = current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE]
            apiLog = APILog()
            response_message = ""
            count = 0
            async for res in JSONEncoder.format_as_ndjson(result, language):
                res = json.loads(res)
                error_msg = res.get("error", None)
                thoughts = res.get("context", {}).get("thoughts", [])
                text_response_chunk = ""
                if error_msg is not None:
                    yield construct_error_response(error_msg, request_type, language)
                elif not thoughts == []:
                    yield construct_source_response(thoughts, request_type)
                    apiLog = extract_thoughts_for_logging(thoughts, apiLog)
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

                    apiLog.response_message += text_response_chunk
                    apiLog.output_token_count += 1

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

                    # Get time of first stream
                    if not count:
                        apiLog.first_stream_time_taken = time.time() - start_time
                        count += 1

            await send_custom_logs(apiLog)  # Send custom logs to app insights
            await store_chat_history(request.cookies.get("session"), apiLog)  # Store chat history in Cosmos DB

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
        response = TextChatResponseWithChunk(
            response_message=data["message"]["content"],
            sources=sources,
        )
        return response.model_dump()


# Helper functions

"""
Utility function to extract sources without chunks from the ThoughtStep returned by the LLM
"""


def extract_sources_from_thoughts(thoughts: List[dict[str, Any]]) -> List[Source]:
    sources_desc = thoughts[2].get("description", [])  # thoughts[2] is search results
    sources = {}
    sources_url = set()
    for source in sources_desc:

        src_instance = Source(
            ids=[str(source.get("id"))],
            title=str(source.get("title")),
            cover_image_url=str(source.get("cover_image_url")),
            full_url=str(source.get("full_url")),
            content_category=str(source.get("content_category")),
            category_description=str(source.get("category_description")),
            pr_name=str(source.get("pr_name")),
            date_modified=str(source.get("date_modified")),
        )

        if src_instance.full_url in sources_url:
            source_obj = sources[src_instance.full_url]
            source_obj.ids.extend(src_instance.ids)
        else:
            sources[src_instance.full_url] = src_instance
            sources_url.add(src_instance.full_url)

    return list(sources.values())


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
            category_description=str(source.get("category_description")),
            pr_name=str(source.get("pr_name")),
            date_modified=str(source.get("date_modified")),
        )
        sources.append(src_instance)
    return sources


"""
Utility function to extract time taken, user query and sources with chunks from the ThoughtStep returned by the LLM
"""


def extract_thoughts_for_logging(thoughts: List[dict[str, Any]], log: APILog) -> APILog:
    log.user_query = thoughts[5].get("description", "")  # thoughts[5] is user query
    log.input_token_count = thoughts[6].get("description", 0)  # thoughts[6] is input token count
    log.output_token_count = thoughts[7].get("description", 0)  # thoughts[7] is output token count
    log.retrieved_sources = extract_sources_with_chunks_from_thoughts(thoughts)

    return log


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


@staticmethod
async def send_custom_logs(apiLog: APILog):
    span = trace.get_current_span()
    # sending custom logs to app insights
    span.set_attribute("Query", apiLog.user_query)
    if apiLog.retrieved_sources:
        for i, source in enumerate(apiLog.retrieved_sources, start=1):
            span.set_attribute(f"Chunk {i} ID", source.id)
            span.set_attribute(f"Chunk {i} title", source.title)
            span.set_attribute(f"Chunk {i} cover image url", source.cover_image_url)
            span.set_attribute(f"Chunk {i} full url", source.full_url)
            span.set_attribute(f"Chunk {i} content category", source.content_category)
            span.set_attribute(f"Chunk {i} content", source.chunk)
    span.set_attribute("Response", apiLog.response_message)
    span.set_attribute("Session id", request.cookies.get("session"))
    span.set_attribute("First stream time taken", apiLog.first_stream_time_taken)
    span.set_attribute("Total input tokens", apiLog.input_token_count)
    span.set_attribute("Total output tokens", apiLog.output_token_count)
    span.set_attribute("Total tokens", apiLog.input_token_count + apiLog.output_token_count)


@staticmethod
async def store_chat_history(session_id, apiLog: APILog):
    chat_history_client: ContainerProxy = current_app.config[CONFIG_CHAT_HISTORY_CONTAINER_CLIENT]
    response_message = ChatMessageWithSource(
        role="assistant", content=apiLog.response_message, sources=apiLog.retrieved_sources
    )
    query_message = ChatMessageWithSource(role="user", content=apiLog.user_query, sources=[])
    chat_message = [query_message, response_message]

    date_time = str(datetime.datetime.now(pytz.timezone("Asia/Singapore")))

    try:
        try:
            chat_history_item = await chat_history_client.read_item(item=session_id, partition_key=session_id)
            chat_history = ChatHistory(**chat_history_item)
            chat_history.chat_messages.extend(chat_message)
            chat_history.last_modified = date_time
        except CosmosHttpResponseError:  # If the chat history does not exist
            chat_history = ChatHistory(
                id=session_id,
                session_id=session_id,
                created_at=date_time,
                last_modified=date_time,
                chat_messages=chat_message,
            )
        await chat_history_client.upsert_item(chat_history.model_dump())
    except Exception as e:
        logging.info("Error storing chat history: ", e)

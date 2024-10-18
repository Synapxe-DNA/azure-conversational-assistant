from typing import Any, List

from azure.search.documents.aio import SearchClient
from config import CONFIG_SEARCH_CLIENT
from models.chat_message import ChatMessage
from models.feedback import FeedbackRequest
from models.language import LanguageSelected
from models.profile import Profile
from models.request import Request
from models.source import SourceWithChunk
from quart import current_app
from utils.utils import Utils


class RequestHandler:
    """
    A class to handle request from client and reconstruct it to our own format
    """

    @staticmethod
    async def construct_feedback_for_storing(feedback_request: FeedbackRequest) -> FeedbackRequest:
        """
        Function to retrieve the text chunks for the sources in the chat history

        Args:
            feedback_request (FeedbackRequest): FeedbackRequest object to add the retrieved text chunks to

        Returns:
            FeedbackRequest object with the text chunks added to the sources
        """
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
                        category_description=source.category_description,
                        pr_name=source.pr_name,
                        date_modified=source.date_modified,
                    )
                    sources.append(src)
            chatHistory.sources = sources

        return feedback_request

    @staticmethod
    def form_message(chat_history_list: List[ChatMessage], query: ChatMessage) -> List[dict[str, Any]]:
        """
        Utility function to form a message from the chat history and query into the specified LLM input format

        Args:
            chat_history_list (List[ChatMessage]): List of ChatMessage objects which represent the chat history between the user and LLM
            query (ChatMessage): The ChatMessage object which represents the user query

        Returns:
            List[dict[str, Any]]: A list of dictionaries where each dictionary represents a message by the user or LLM
        """

        messages = [chat_history.model_dump() for chat_history in chat_history_list] + [query.model_dump()]
        return messages

    @staticmethod
    def form_query_request(data: dict) -> Request:
        """
        Utility function to form a Request object from json

        Args:
            data (dict): The json data received from the client

        Returns:
            Request: The Request object formed from the json data
        """
        language = (
            Utils.get_language(data["query"]["content"])
            if data["language"] == LanguageSelected.SPOKEN.value
            else data["language"]
        )

        request = Request(
            chat_history=data["chat_history"],
            profile=Profile(**data["profile"]),
            query=data["query"],
            language=language,
        )
        return request

    @staticmethod
    def form_feedback_request(data: dict) -> FeedbackRequest:
        """
        Utility function to form a FeedbackRequest object from json

        Args:
            data (dict): The json data received from the client

        Returns:
            FeedbackRequest: The FeedbackRequest object formed from the json data
        """
        feedback_request = FeedbackRequest(
            date_time=data["date_time"],
            feedback_type=data["feedback_type"],
            feedback_category=data["feedback_category"],
            feedback_remarks=data.get("feedback_remarks", ""),
            user_profile=Profile(**data["user_profile"]),
            chat_history=data["chat_history"],
        )
        return feedback_request

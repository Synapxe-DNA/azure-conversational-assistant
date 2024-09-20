import dataclasses
import json
import logging
import mimetypes
import os
from typing import AsyncGenerator

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.retrievethenread import RetrieveThenReadApproach
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from blueprints.backend_blueprint.chat import chat
from blueprints.backend_blueprint.feedback import feedback
from blueprints.backend_blueprint.login import login
from blueprints.backend_blueprint.speech import speech
from blueprints.backend_blueprint.transcription import transcription
from blueprints.backend_blueprint.voice import voice
from blueprints.frontend_blueprint.frontend import frontend
from config import (
    CONFIG_ASK_APPROACH,
    CONFIG_AUTH_CLIENT,
    CONFIG_AUTHENTICATOR,
    CONFIG_CHAT_APPROACH,
    CONFIG_CREDENTIAL,
    CONFIG_FEEDBACK_CONTAINER_CLIENT,
    CONFIG_OPENAI_CLIENT,
    CONFIG_SEARCH_CLIENT,
    CONFIG_SPEECH_SERVICE_ID,
    CONFIG_SPEECH_SERVICE_LOCATION,
    CONFIG_SPEECH_SERVICE_TOKEN,
    CONFIG_SPEECH_TO_TEXT_SERVICE,
    CONFIG_TEXT_TO_SPEECH_SERVICE,
    CONFIG_USER_DATABASE,
)
from core.authentication import AuthenticationHelper
from error import error_dict
from openai import AsyncAzureOpenAI, AsyncOpenAI
from quart import Blueprint, Quart, current_app, redirect
from quart_cors import cors
from speech.speech_to_text import SpeechToText
from speech.text_to_speech import TextToSpeech
from utils.authenticator import Authenticator
from utils.user_database import UserDatabase

bp = Blueprint("routes", __name__, static_folder="static/browser")
# Fix Windows registry issue with mimetypes
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


# region Not used functions
@bp.route("/")
async def serve_app():
    return redirect("/app")


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        return super().default(o)


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    try:
        async for event in r:
            yield json.dumps(event, ensure_ascii=False, cls=JSONEncoder) + "\n"
    except Exception as error:
        logging.exception("Exception while generating response stream: %s", error)
        yield json.dumps(error_dict(error))


# endregion


@bp.before_app_serving
async def setup_clients():
    # Replace these with your own values, either in environment variables or directly here
    AZURE_COSMOS_DB_NAME = os.environ["AZURE_COSMOS_DB_NAME"]
    AZURE_DATABASE_ID = os.environ["AZURE_DATABASE_ID"]
    AZURE_CONTAINER_ID = os.environ["AZURE_CONTAINER_ID"]
    AZURE_SEARCH_SERVICE = os.environ["AZURE_SEARCH_SERVICE"]
    AZURE_SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]
    # Shared by all OpenAI deployments
    OPENAI_HOST = os.getenv("OPENAI_HOST", "azure")
    OPENAI_CHATGPT_MODEL = os.environ["AZURE_OPENAI_CHATGPT_MODEL"]
    OPENAI_EMB_MODEL = os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002")
    OPENAI_EMB_DIMENSIONS = int(os.getenv("AZURE_OPENAI_EMB_DIMENSIONS", 1536))
    # Used with Azure OpenAI deployments
    APIM_GATEWAY_URL = os.getenv("APIM_GATEWAY_URL")
    AZURE_OPENAI_CHATGPT_DEPLOYMENT = (
        os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT") if OPENAI_HOST.startswith("azure") else None
    )
    AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT") if OPENAI_HOST.startswith("azure") else None
    # Used only with non-Azure OpenAI deployments

    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
    AZURE_USE_AUTHENTICATION = os.getenv("AZURE_USE_AUTHENTICATION", "").lower() == "true"
    AZURE_ENFORCE_ACCESS_CONTROL = os.getenv("AZURE_ENFORCE_ACCESS_CONTROL", "").lower() == "true"
    AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS = os.getenv("AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS", "").lower() == "true"
    AZURE_ENABLE_UNAUTHENTICATED_ACCESS = os.getenv("AZURE_ENABLE_UNAUTHENTICATED_ACCESS", "").lower() == "true"
    AZURE_SERVER_APP_ID = os.getenv("AZURE_SERVER_APP_ID")
    AZURE_SERVER_APP_SECRET = os.getenv("AZURE_SERVER_APP_SECRET")
    AZURE_CLIENT_APP_ID = os.getenv("AZURE_CLIENT_APP_ID")
    AZURE_AUTH_TENANT_ID = os.getenv("AZURE_AUTH_TENANT_ID", AZURE_TENANT_ID)

    KB_FIELDS_CONTENT = os.getenv("KB_FIELDS_CONTENT", "content")
    KB_FIELDS_SOURCEPAGE = os.getenv("KB_FIELDS_SOURCEPAGE", "sourcePage")

    AZURE_SEARCH_QUERY_LANGUAGE = os.getenv("AZURE_SEARCH_QUERY_LANGUAGE", "en-us")
    AZURE_SEARCH_QUERY_SPELLER = os.getenv("AZURE_SEARCH_QUERY_SPELLER", "lexicon")

    AZURE_SPEECH_SERVICE_ID = os.getenv("AZURE_SPEECH_SERVICE_ID")
    AZURE_SPEECH_SERVICE_LOCATION = os.getenv("AZURE_SPEECH_SERVICE_LOCATION")

    # Use the current user identity to authenticate with Azure OpenAI, AI Search and Blob Storage (no secrets needed,
    # just use 'az login' locally, and managed identity when deployed on Azure). If you need to use keys, use separate AzureKeyCredential instances with the
    # keys for each service
    # If you encounter a blocking error during a DefaultAzureCredential resolution, you can exclude the problematic credential by using a parameter (ex. exclude_shared_token_cache_credential=True)
    azure_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

    # Set up clients for AI Search and Storage
    search_client = SearchClient(
        endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
        index_name=AZURE_SEARCH_INDEX,
        credential=azure_credential,
    )

    cosmos_client = CosmosClient(
        url=f"https://{AZURE_COSMOS_DB_NAME}.documents.azure.com:443/", credential=azure_credential
    )
    feedback_database_client = cosmos_client.get_database_client(AZURE_DATABASE_ID)
    feedback_container_client = feedback_database_client.get_container_client(AZURE_CONTAINER_ID)
    current_app.config[CONFIG_FEEDBACK_CONTAINER_CLIENT] = feedback_container_client

    # Set up authentication helper
    search_index = None
    if AZURE_USE_AUTHENTICATION:
        search_index_client = SearchIndexClient(
            endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
            credential=azure_credential,
        )
        search_index = await search_index_client.get_index(AZURE_SEARCH_INDEX)
        await search_index_client.close()
    auth_helper = AuthenticationHelper(
        search_index=search_index,
        use_authentication=AZURE_USE_AUTHENTICATION,
        server_app_id=AZURE_SERVER_APP_ID,
        server_app_secret=AZURE_SERVER_APP_SECRET,
        client_app_id=AZURE_CLIENT_APP_ID,
        tenant_id=AZURE_AUTH_TENANT_ID,
        require_access_control=AZURE_ENFORCE_ACCESS_CONTROL,
        enable_global_documents=AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS,
        enable_unauthenticated_access=AZURE_ENABLE_UNAUTHENTICATED_ACCESS,
    )

    # Used by the OpenAI SDK
    openai_client: AsyncOpenAI

    if not AZURE_SPEECH_SERVICE_ID or AZURE_SPEECH_SERVICE_ID == "":
        raise ValueError("Azure speech resource not configured correctly, missing AZURE_SPEECH_SERVICE_ID")
    if not AZURE_SPEECH_SERVICE_LOCATION or AZURE_SPEECH_SERVICE_LOCATION == "":
        raise ValueError("Azure speech resource not configured correctly, missing AZURE_SPEECH_SERVICE_LOCATION")
    current_app.config[CONFIG_SPEECH_SERVICE_ID] = AZURE_SPEECH_SERVICE_ID
    current_app.config[CONFIG_SPEECH_SERVICE_LOCATION] = AZURE_SPEECH_SERVICE_LOCATION
    # Wait until token is needed to fetch for the first time
    current_app.config[CONFIG_SPEECH_SERVICE_TOKEN] = None
    current_app.config[CONFIG_CREDENTIAL] = azure_credential

    if OPENAI_HOST.startswith("azure"):
        api_version = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-03-01-preview"
        if not APIM_GATEWAY_URL:
            raise ValueError("APIM_GATEWAY_URL must be set when OPENAI_HOST is azure")
        endpoint = APIM_GATEWAY_URL

        token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
        openai_client = AsyncAzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
        )
    else:
        raise ValueError("OPENAI_HOST must be 'azure")

    current_app.config[CONFIG_OPENAI_CLIENT] = openai_client
    current_app.config[CONFIG_SEARCH_CLIENT] = search_client
    current_app.config[CONFIG_AUTH_CLIENT] = auth_helper

    # Various approaches to integrate GPT and external knowledge, most applications will use a single one of these patterns
    # or some derivative, here we include several for exploration purposes
    current_app.config[CONFIG_ASK_APPROACH] = RetrieveThenReadApproach(
        search_client=search_client,
        openai_client=openai_client,
        auth_helper=auth_helper,
        chatgpt_model=OPENAI_CHATGPT_MODEL,
        chatgpt_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        embedding_model=OPENAI_EMB_MODEL,
        embedding_deployment=AZURE_OPENAI_EMB_DEPLOYMENT,
        embedding_dimensions=OPENAI_EMB_DIMENSIONS,
        sourcepage_field=KB_FIELDS_SOURCEPAGE,
        content_field=KB_FIELDS_CONTENT,
        query_language=AZURE_SEARCH_QUERY_LANGUAGE,
        query_speller=AZURE_SEARCH_QUERY_SPELLER,
    )

    current_app.config[CONFIG_CHAT_APPROACH] = ChatReadRetrieveReadApproach(
        search_client=search_client,
        openai_client=openai_client,
        auth_helper=auth_helper,
        chatgpt_model=OPENAI_CHATGPT_MODEL,
        chatgpt_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        embedding_model=OPENAI_EMB_MODEL,
        embedding_deployment=AZURE_OPENAI_EMB_DEPLOYMENT,
        embedding_dimensions=OPENAI_EMB_DIMENSIONS,
        sourcepage_field=KB_FIELDS_SOURCEPAGE,
        content_field=KB_FIELDS_CONTENT,
        query_language=AZURE_SEARCH_QUERY_LANGUAGE,
        query_speller=AZURE_SEARCH_QUERY_SPELLER,
    )

    tts = await TextToSpeech.create()
    stt = await SpeechToText.create()
    current_app.config[CONFIG_TEXT_TO_SPEECH_SERVICE] = tts
    current_app.config[CONFIG_SPEECH_TO_TEXT_SERVICE] = stt

    current_app.config[CONFIG_USER_DATABASE] = UserDatabase(os.getenv("USER_ACCOUNTS", ""))
    current_app.config[CONFIG_AUTHENTICATOR] = Authenticator()


@bp.after_app_serving
async def close_clients():
    await current_app.config[CONFIG_SEARCH_CLIENT].close()


def create_app():
    app = Quart(__name__)
    app.register_blueprint(bp)
    app.register_blueprint(frontend)
    app.register_blueprint(voice)
    app.register_blueprint(chat)
    app.register_blueprint(speech)
    app.register_blueprint(feedback)
    app.register_blueprint(transcription)
    app.register_blueprint(login)
    app = cors(app, allow_origin="*")  # For local testing

    default_level = "INFO"  # In development, log more verbosely
    logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", default_level))
    if allowed_origin := os.getenv("ALLOWED_ORIGIN"):
        app.logger.info("CORS enabled for %s", allowed_origin)
        cors(app, allow_origin=allowed_origin, allow_methods=["GET", "POST"])
    return app

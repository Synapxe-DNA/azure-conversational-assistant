import asyncio
import dataclasses
import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from types import CoroutineType
from typing import Any, AsyncGenerator, Optional, TypedDict, cast

import pandas as pd
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import AzureDeveloperCliCredential, get_bearer_token_provider
from azure.search.documents.aio import AsyncSearchItemPaged, SearchClient
from azure.search.documents.models import (
    QueryCaptionResult,
    QueryType,
    VectorizedQuery,
    VectorQuery,
)
from openai import APIError, AsyncAzureOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from openai_messages_token_helper import build_messages, get_token_limit
from pydantic import BaseModel


class Language(Enum):
    en: str = "English"
    zh: str = "Chinese"
    ms: str = "Malay"
    ta: str = "Tamil"

    @classmethod
    def from_iso_code(cls, code):
        try:
            return cls[code]
        except KeyError:
            raise ValueError(f"Invalid ISO code: {code}")


class Profile(BaseModel):
    profile_type: str
    user_age: int | None
    user_gender: str | None
    user_condition: str | None


class Prompts(dict):
    """
    A dictionary that supports dot notation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Prompts(value)
            elif isinstance(value, list):
                self[key] = [Prompts(x) if isinstance(x, dict) else x for x in value]

    def __getattr__(self, attr):
        value = self.get(attr)
        if isinstance(value, dict):
            value = Prompts(value)
        return value

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = Prompts(value)
        self.__setitem__(key, value)

    def __delattr__(self, key):
        self.__delitem__(key)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        return super().default(o)


@dataclass
class Document:
    id: Optional[str]
    parent_id: Optional[str]
    title: Optional[str]
    cover_image_url: Optional[str]
    full_url: Optional[str]
    content_category: Optional[str]
    chunks: Optional[str]
    embedding: Optional[list[float]]
    captions: list[QueryCaptionResult]
    score: Optional[float] = None
    reranker_score: Optional[float] = None

    def serialize_for_results(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "title": self.title,
            "cover_image_url": self.cover_image_url,
            "full_url": self.full_url,
            "content_category": self.content_category,
            "chunks": self.chunks,
            "embedding": Document.trim_embedding(self.embedding),
            "captions": (
                [
                    {
                        "additional_properties": caption.additional_properties,
                        "text": caption.text,
                        "highlights": caption.highlights,
                    }
                    for caption in self.captions
                ]
                if self.captions
                else []
            ),
            "score": self.score,
            "reranker_score": self.reranker_score,
        }

    @classmethod
    def trim_embedding(cls, embedding: Optional[list[float]]) -> Optional[list[float]]:
        """Returns a trimmed list of floats from the vector embedding."""
        if embedding:
            if len(embedding) > 2:
                # Format the embedding list to show the first 2 items followed by the count of the remaining items."""
                return f"[{embedding[0]}, {embedding[1]} ...+{len(embedding) - 2} more]"
            else:
                return str(embedding)

        return None


async def generate_search_query_or_response(
    azure_openai_model: str,
    system_prompt: str,
    chat_history: list[dict[str, str]],
    user_query: str,
    chatgpt_token_limit: int,
    token_limit: int,
    openai_client: AsyncAzureOpenAI,
    azure_openai_deployment: str,
    seed: int,
    temperature: float = 0.0,
    tools: list[dict[str, Any]] = "",
    few_shots_examples: list[dict[str, str]] = "",
    purpose: str = "query",
) -> ChatCompletion | CoroutineType:

    assert purpose in ["query", "response"], "Invalid purpose. Must be 'query' or 'response'."

    query_messages = build_messages(
        model=azure_openai_model,
        system_prompt=system_prompt,
        tools=tools,
        few_shots=few_shots_examples,
        past_messages=chat_history,
        new_user_content=user_query,
        max_tokens=chatgpt_token_limit - token_limit,
    )

    if purpose == "query":
        logging.info("Generating search query...")
        chat_completion: ChatCompletion = await openai_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            # Azure OpenAI takes the deployment name as the model name
            model=azure_openai_deployment if azure_openai_deployment else azure_openai_model,
            temperature=temperature,  # Minimize creativity for search query generation
            max_tokens=token_limit,  # Setting too low risks malformed JSON, setting too high may affect performance
            n=1,
            tools=tools,
            seed=seed,
        )
        logging.info("Generated search query")
        return chat_completion

    elif purpose == "response":
        logging.info("Generating response...")
        chat_coroutine = openai_client.chat.completions.create(
            # Azure OpenAI takes the deployment name as the model name
            model=azure_openai_deployment if azure_openai_deployment else azure_openai_model,
            messages=query_messages,
            temperature=temperature,
            max_tokens=token_limit,
            n=1,
            stream=True,
            seed=seed,
        )

        logging.info("Generated response")
        return chat_coroutine


def get_search_query(chat_completion: ChatCompletion, user_query: str, no_response: str = "0") -> str:
    response_message = chat_completion.choices[0].message

    if response_message.tool_calls:
        for tool in response_message.tool_calls:
            if tool.type != "function":
                continue
            function = tool.function
            if function.name == "search_sources":
                arg = json.loads(function.arguments)
                search_query = arg.get("search_query", no_response)
                if search_query != no_response:
                    return search_query
    elif query_text := response_message.content:
        if query_text.strip() != no_response:
            return query_text

    return user_query


async def compute_text_embedding(
    q: str,
    embedding_dimensions: int,
    embedding_model: str,
    embedding_deployment: str,
    openai_client: AsyncAzureOpenAI,
    weight: float,
) -> VectorizedQuery:
    SUPPORTED_DIMENSIONS_MODEL = {
        "text-embedding-ada-002": False,
        "text-embedding-3-small": True,
        "text-embedding-3-large": True,
    }

    class ExtraArgs(TypedDict, total=False):
        dimensions: int

    dimensions_args: ExtraArgs = (
        {"dimensions": embedding_dimensions} if SUPPORTED_DIMENSIONS_MODEL[embedding_model] else {}
    )

    logging.info("Computing text embedding...")
    embedding = await openai_client.embeddings.create(
        # Azure OpenAI takes the deployment name as the model name
        model=embedding_deployment if embedding_deployment else embedding_model,
        input=q,
        **dimensions_args,
    )
    query_vector = embedding.data[0].embedding
    logging.info("Computed text embedding")

    # See: https://github.com/Azure/azure-search-vector-samples/blob/main/demo-python/code/e2e-demos/azure-ai-search-e2e-build-demo.ipynb
    return VectorizedQuery(vector=query_vector, k_nearest_neighbors=50, fields="embedding", weight=weight)


def nonewlines(s: str) -> str:
    return s.replace("\n", " ").replace("\r", " ")


def get_sources_content(results: list[Document], use_semantic_captions: bool, use_image_citation: bool) -> list[str]:
    if use_semantic_captions:
        logging.info("Getting sources content (semantic captions)...")
        return [
            (get_citation((doc.title or ""), use_image_citation))
            + ": "
            + nonewlines(" . ".join([cast(str, c.text) for c in (doc.captions or [])]))
            for doc in results
        ]
    else:
        logging.info("Getting sources content (chunks)...")
        return [
            (get_citation((doc.title or ""), use_image_citation)) + ": " + nonewlines(doc.chunks or "")
            for doc in results
        ]


def get_citation(sourcepage: str, use_image_citation: bool) -> str:
    if use_image_citation:
        return sourcepage
    else:
        path, ext = os.path.splitext(sourcepage)
        if ext.lower() == ".png":
            page_idx = path.rfind("-")
            page_number = int(path[page_idx + 1 :])
            return f"{path[:page_idx]}.pdf#page={page_number}"

        return sourcepage


async def perform_search_and_fetch_documents(
    endpoint: str,
    index_name: str,
    azure_credential: AsyncTokenCredential,
    query_text: str,
    vectors: list[VectorQuery],
    usetextsearch: bool,
    usevectorsearch: bool,
    usesemanticranker: bool,
    top: int,
    usesemanticcaptions: bool,
    query_language: str,
    query_speller: str,
) -> list[Document]:

    async with SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=azure_credential,
    ) as search_client:
        search_text = query_text if usetextsearch else ""
        search_vectors = vectors if usevectorsearch else []
        if usesemanticranker:
            logging.info("Performing semantic search (with semantic ranking)...")
            results: AsyncSearchItemPaged = await search_client.search(
                search_text=search_text,
                filter=None,
                top=top,
                query_caption="extractive|highlight-false" if usesemanticcaptions else None,
                vector_queries=search_vectors,
                query_type=QueryType.SEMANTIC,
                query_language=query_language,
                query_speller=query_speller,
                semantic_configuration_name="default",
                semantic_query=query_text,
            )
        else:
            logging.info("Performing semantic search (without semantic ranking)...")
            results: AsyncSearchItemPaged = await search_client.search(
                search_text=search_text,
                filter=None,
                top=top,
                vector_queries=search_vectors,
            )

        documents = []
        async for page in results.by_page():
            # print(type(page))  # AsyncIterator
            async for document in page:
                documents.append(
                    Document(
                        id=document.get("id"),
                        parent_id=document.get("parent_id"),
                        title=document.get("title"),
                        cover_image_url=document.get("cover_image_url"),
                        full_url=document.get("full_url"),
                        content_category=document.get("content_category"),
                        chunks=document.get("chunks"),
                        embedding=document.get("embedding"),
                        captions=cast(list[QueryCaptionResult], document.get("@search.captions")),
                        score=document.get("@search.score"),
                        reranker_score=document.get("@search.reranker_score"),
                    )
                )

        logging.info(f"Fetched {len(documents)} documents")
        return documents


def filter_for_qualified_documents(
    documents: list[Document], minimum_search_score: float, minimum_reranker_score: float
) -> list[Document]:
    logging.info("Filtering for qualified documents...")
    qualified_documents = [
        doc
        for doc in documents
        if ((doc.score or 0) >= minimum_search_score or 0)
        and ((doc.reranker_score or 0) >= (minimum_reranker_score or 0))
    ]
    logging.info(f"Found {len(qualified_documents)} qualified documents")

    return qualified_documents


def extract_followup_questions(content: str):
    return content.split("<<")[0], re.findall(r"<<([^>>]+)>>", content)


async def run_with_streaming(
    chat_coroutine: CoroutineType,
    messages: list[ChatCompletionMessageParam],
    profile: Profile,
    auth_claims: dict[str, Any],
    session_state: Any = None,
) -> AsyncGenerator[dict[str, Any], None]:

    followup_questions_started = False
    followup_content = ""

    logging.debug("Starting run_with_streaming...")
    async for event_chunk in await chat_coroutine:
        # "2023-07-01-preview" API version has a bug where first response has empty choices
        event = event_chunk.model_dump()  # Convert pydantic model to dict
        logging.debug(f"Event chunk received: {event}")
        if event["choices"]:
            completion = {"delta": event["choices"][0]["delta"]}
            # if event contains << and not >>, it is start of follow-up question, truncate
            content = completion["delta"].get("content")
            content = content or ""  # content may either not exist in delta, or explicitly be None
            if "<<" in content:
                followup_questions_started = True
                earlier_content = content[: content.index("<<")]
                if earlier_content:
                    completion["delta"]["content"] = earlier_content
                    yield completion
                followup_content += content[content.index("<<") :]
            elif followup_questions_started:
                followup_content += content
            else:
                yield completion
    if followup_content:
        _, followup_questions = extract_followup_questions(followup_content)
        yield {"delta": {"role": "assistant"}, "context": {"followup_questions": followup_questions}}


async def run_stream(
    messages: list[ChatCompletionMessageParam],
    chat_coroutine: CoroutineType,
    profile: Profile,
    session_state: Any = None,
    context: dict[str, Any] = {},
) -> AsyncGenerator[dict[str, Any], None]:
    logging.debug("Starting run_stream...")
    # overrides = context.get("overrides", {})
    auth_claims = context.get("auth_claims", {})
    return run_with_streaming(chat_coroutine, messages, profile, auth_claims, session_state)


def error_dict(error: Exception) -> dict:
    if isinstance(error, APIError) and error.code == "content_filter":
        return {"error": ERROR_MESSAGE_FILTER}
    if isinstance(error, APIError) and error.code == "context_length_exceeded":
        return {"error": ERROR_MESSAGE_LENGTH}
    return {"error": ERROR_MESSAGE.format(error_type=type(error))}


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    try:
        async for event in r:
            logging.debug(f"format_as_ndjson input: {event}")  # Debug: Log input to format_as_ndjson
            yield json.dumps(event, ensure_ascii=False, cls=JSONEncoder) + "\n"
    except Exception as error:
        logging.exception("Exception while generating response stream: %s", error)
        yield json.dumps(error_dict(error))


async def construct_streaming_chat_response(result: AsyncGenerator[dict[str, Any], None]) -> AsyncGenerator[str, None]:
    async def generator() -> AsyncGenerator[str, None]:
        async for res in format_as_ndjson(result):
            logging.debug(f"Received from format_as_ndjson: {res}")  # Debug: Log received data
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
                    # logging.info("No content received in delta")
                    break
                # response = TextChatResponse(
                #     response_message=text_response_chunk,
                #     sources=[],
                #     additional_question_1="",
                #     additional_question_2="",
                # )
                yield text_response_chunk
                # logging.debug(f"Generator yielding: {text_response_chunk}")  # Debug: Log what is being yielded
                # # yield response.model_dump_json()
                # logging.debug("====================================")
                # logging.debug(text_response_chunk)
                # logging.debug("====================================")

    return generator()


# Consume the async generator
async def display_content(async_gen):
    response = []  # Accumulator for the response chunks
    async for item in async_gen:
        logging.debug(f"Consumer received: {item}")  # Debug: Track what is being consumed
        print(item, end="", flush=True)  # print the current token to console
        response.append(item)  # Collect each item
    print()

    full_response = "".join(response)  # Concatenate all collected chunks
    return full_response  # Return the full concatenated response if needed


def ensure_directory_exists(file_path: str):
    """
    Ensures that the directory for the given file path exists.
    If the directory does not exist, it is created.

    :param file_path: The path to the file.
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_or_append_csv(file_path: str, row_data: dict[str, str]):
    """
    Writes a new row to the CSV file specified by file_path.

    If the file does not exist, it is created. If it does exist, the row is appended.

    :param file_path: Path to the CSV file.
    :param row_data: Dictionary of data items to write as a new row.
    """
    # Ensure the directory exists
    ensure_directory_exists(file_path)

    file_exists = os.path.isfile(file_path)

    # Convert the row_data dictionary to a DataFrame
    df = pd.DataFrame([row_data])  # The DataFrame constructor expects an iterable of rows

    if file_exists:
        # Append to existing CSV file
        logging.info("Appending to existing CSV file...")
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        # Write a new CSV file with the header
        logging.info("Writing to new CSV file...")
        df.to_csv(file_path, mode="w", header=True, index=False)


async def run(user_query: str, file_path: str, result: AsyncGenerator[dict[str, Any], None]):
    response = await construct_streaming_chat_response(result)
    full_response = await display_content(response)  # Run the coroutine to display content
    data = {
        "user_query": user_query,
        "full_response": full_response,
    }
    # Function call to write or append row data to the CSV file
    write_or_append_csv(file_path, data)
    logging.info("====================================")
    logging.info(f"Full Response:\n{full_response}")
    logging.info("====================================")


if __name__ == "__main__":
    import argparse

    import yaml

    parser = argparse.ArgumentParser(
        description="Generate chat completion with Azure OpenAI and Azure Search for rapid RAG evaluation and testing.",
        epilog="""
        Example:
            .venv/bin/python ragas/ragas.py ragas/prompts.yml --usevectorsearch --usetextsearch --usesemanticranker --weight 1.0 --responsetokenlimit 1024 --userquery 'What is the meaning of life?'
        """,
    )

    parser.add_argument("prompts", type=str, nargs="?", help="The file path containing the prompts")
    parser.add_argument(
        "--selectedlanguage",
        type=str,
        default="en",
        choices=["en", "zh", "ms", "ta"],
        help="The selected language. Only 'en', 'zh', 'ms', 'ta' are allowed",
    )
    # Azure OpenAI service
    parser.add_argument("--openaimodelname", type=str, default="gpt-4o", help="Azure OpenAI GPT model")
    parser.add_argument("--openaiservicename", type=str, default="cog-zicuh2lqrbb2s", help="Azure OpenAI service name")
    parser.add_argument("--apiversion", type=str, default="2024-03-01-preview", help="Azure API version")
    parser.add_argument("--openaideploymentname", type=str, default="chat", help="Azure OpenAI deployment name")
    parser.add_argument("--embeddingdimensions", type=int, default=1536, help="Embedding dimensions")
    parser.add_argument("--embeddingmodelname", type=str, default="text-embedding-3-small", help="Embedding model name")
    parser.add_argument("--embeddingdeploymentname", type=str, default="embedding", help="Embedding deployment name")
    # Azure AI Search service
    parser.add_argument("--searchservice", type=str, default="gptkb-zicuh2lqrbb2s", help="Azure Search service name")
    parser.add_argument("--searchindex", type=str, default="gptkbindex5000200v4", help="Azure Search index name")
    parser.add_argument("--usevectorsearch", action="store_true", help="Use vector search (dense retrieval)")
    parser.add_argument("--usetextsearch", action="store_true", help="Use text search (sparse retrieval)")
    parser.add_argument("--usesemanticranker", action="store_true", help="Use semantic ranking")
    parser.add_argument("--usesemanticcaptions", action="store_true", help="Use semantic captions")
    parser.add_argument("--topn", type=int, default=3, help="The top N documents to retrieve")
    parser.add_argument("--weight", type=float, default=1.0, help="Weightage on vector search against text search")
    parser.add_argument("--querylanguage", type=str, default="en-us", help="The query language")
    parser.add_argument("--queryspeller", type=str, default="lexicon", help="The query speller")
    parser.add_argument("--minsearchscore", type=float, default=0.0, help="Threshold for minimum search score")
    parser.add_argument("--minrerankerscore", type=float, default=0.0, help="Threshold for minimum re-ranker score")

    # Miscellaneous
    parser.add_argument("--queryresponsetokenlimit", type=int, default=100, help="The query response token limit")
    parser.add_argument("--responsetokenlimit", type=int, default=512, help="The response token limit")
    parser.add_argument("--userquery", type=str, nargs=1, help="The user query you'd like to evaluate")
    parser.add_argument(
        "--filepath",
        type=str,
        default="./ragas/eval/results.csv",
        help="The file path where evaluation results will be saved",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--seed", type=int, default=1234, help="Set seed for reproducibility")

    args = parser.parse_args()

    # Prompts
    with open(args.prompts) as f:
        data = yaml.safe_load(f)
    prompts = Prompts(data)

    QUERY_PROMPT = prompts.categories[0].subcategories[0].prompts[0].text
    GENERAL_PROMPT = prompts.categories[0].subcategories[1].prompts[0].text
    SELECTED_LANGUAGE = Language.from_iso_code(args.selectedlanguage).value
    ANSWER_GENERATION_PROMPT = GENERAL_PROMPT.format(selected_language=SELECTED_LANGUAGE)
    QUERY_PROMPT_FEW_SHOTS: list[ChatCompletionMessageParam] = prompts.categories[1].subcategories[0].prompts[0].text
    CHAT_HISTORY = prompts.categories[2].subcategories[0].prompts[0].text
    if args.userquery is not None:
        ORIGINAL_USER_QUERY = [Prompts({"role": "user", "content": args.userquery[0]})]
        USER_QUERY_REQUEST = "Generate search query for: " + args.userquery[0]
    else:
        ORIGINAL_USER_QUERY = prompts.categories[2].subcategories[1].prompts[0].text
        USER_QUERY_REQUEST = "Generate search query for: " + ORIGINAL_USER_QUERY[0].content
    MESSAGES = CHAT_HISTORY + ORIGINAL_USER_QUERY

    # Error messages
    ERROR_MESSAGE = prompts.categories[3].subcategories[0].prompts[0].text
    ERROR_MESSAGE_FILTER = prompts.categories[3].subcategories[1].prompts[0].text
    ERROR_MESSAGE_LENGTH = prompts.categories[3].subcategories[2].prompts[0].text

    # Azure OpenAI service
    AZURE_OPENAI_CHATGPT_MODEL = args.openaimodelname
    CHATGPT_TOKEN_LIMIT = get_token_limit(AZURE_OPENAI_CHATGPT_MODEL)
    AZURE_OPENAI_SERVICE = args.openaiservicename
    AZURE_OPENAI_ENDPOINT = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
    AZURE_OPENAI_API_VERSION = args.apiversion
    AZURE_OPENAI_CHATGPT_DEPLOYMENT = args.openaideploymentname
    TOOLS: list[ChatCompletionToolParam] = [
        {
            "type": "function",
            "function": {
                "name": "search_sources",
                "description": "Retrieve sources from the Azure AI Search index",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "Query string to retrieve documents from azure search eg: 'Health care plan'",
                        }
                    },
                    "required": ["search_query"],
                },
            },
        }
    ]
    EMBEDDING_DIMENSIONS = args.embeddingdimensions
    EMBEDDING_MODEL = args.embeddingmodelname
    EMBEDDING_DPELOYMENT = args.embeddingdeploymentname

    # Azure AI Search
    AZURE_SEARCH_SERVICE = args.searchservice
    AZURE_SEARCH_INDEX = args.searchindex
    AZURE_SEARCH_ENDPOINT = f"https://{AZURE_SEARCH_SERVICE}.search.windows.net"
    TOP = args.topn
    WEIGHT = args.weight
    AZURE_SEARCH_QUERY_LANGUAGE = args.querylanguage
    AZURE_SEARCH_QUERY_SPELLER = args.queryspeller
    MINIMUM_SEARCH_SCORE = args.minsearchscore
    MINIMUM_RERANKER_SCORE = args.minrerankerscore

    QUERY_RESPONSE_TOKEN_LIMIT = args.queryresponsetokenlimit
    RESPONSE_TOKEN_LIMIT = args.responsetokenlimit
    FILE_PATH = args.filepath
    SEED = args.seed
    NO_RESPONSE = "0"

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    async def main():
        async with AzureDeveloperCliCredential(process_timeout=60) as azure_credential:
            token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
            async with AsyncAzureOpenAI(
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                azure_ad_token_provider=token_provider,
            ) as openai_client:
                chat_completion = await generate_search_query_or_response(
                    azure_openai_model=AZURE_OPENAI_CHATGPT_MODEL,
                    system_prompt=QUERY_PROMPT,
                    tools=TOOLS,
                    few_shots_examples=QUERY_PROMPT_FEW_SHOTS,
                    chat_history=CHAT_HISTORY,
                    user_query=USER_QUERY_REQUEST,
                    chatgpt_token_limit=CHATGPT_TOKEN_LIMIT,
                    token_limit=QUERY_RESPONSE_TOKEN_LIMIT,
                    openai_client=openai_client,
                    azure_openai_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                    seed=SEED,
                    purpose="query",
                )
                query_text = get_search_query(chat_completion, ORIGINAL_USER_QUERY, NO_RESPONSE)
                logging.info(f"Query text: {query_text}")

                # If retrieval mode includes vectors, compute an embedding for the query
                vectors: list[VectorQuery] = []
                if args.usevectorsearch:
                    vectors.append(
                        await compute_text_embedding(
                            query_text,
                            EMBEDDING_DIMENSIONS,
                            EMBEDDING_MODEL,
                            EMBEDDING_DPELOYMENT,
                            openai_client,
                            weight=WEIGHT,
                        )
                    )

                documents = await perform_search_and_fetch_documents(
                    endpoint=AZURE_SEARCH_ENDPOINT,
                    index_name=AZURE_SEARCH_INDEX,
                    azure_credential=azure_credential,
                    query_text=query_text,
                    vectors=vectors,
                    usetextsearch=args.usetextsearch,
                    usevectorsearch=args.usevectorsearch,
                    usesemanticranker=args.usesemanticranker,
                    top=TOP,
                    usesemanticcaptions=args.usesemanticcaptions,
                    query_language=AZURE_SEARCH_QUERY_LANGUAGE,
                    query_speller=AZURE_SEARCH_QUERY_SPELLER,
                )

                assert (
                    len(documents) == TOP
                ), "Number of retrieved documents is not equal to top n. "  # has to be same as top n

                qualified_documents = filter_for_qualified_documents(
                    documents, MINIMUM_SEARCH_SCORE, MINIMUM_RERANKER_SCORE
                )

                sources_content = get_sources_content(
                    qualified_documents, args.usesemanticcaptions, use_image_citation=False
                )

                content = "\n".join(sources_content)
                logging.info(content[:100])

                chat_coroutine = await generate_search_query_or_response(
                    azure_openai_model=AZURE_OPENAI_CHATGPT_MODEL,
                    system_prompt=ANSWER_GENERATION_PROMPT,
                    chat_history=CHAT_HISTORY,
                    user_query=ORIGINAL_USER_QUERY[0].content + "\n\nSources:\n" + content,
                    chatgpt_token_limit=CHATGPT_TOKEN_LIMIT,
                    token_limit=RESPONSE_TOKEN_LIMIT,
                    openai_client=openai_client,
                    azure_openai_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                    seed=SEED,
                    purpose="response",
                )

                profile = {
                    "profile_type": "general",
                    "user_age": None,
                    "user_gender": None,
                    "user_condition": None,
                }

                result: AsyncGenerator[dict[str, Any], None] = await run_stream(
                    messages=MESSAGES, chat_coroutine=chat_coroutine, context={}, profile=Profile(**profile)
                )

                await run(ORIGINAL_USER_QUERY[0].content, FILE_PATH, result)

    # Run the main async function
    asyncio.run(main())

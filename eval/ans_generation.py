import asyncio
import dataclasses
import json
import logging
import os
import pandas as pd
import re
import argparse
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

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))
from app.backend.approaches.prompts import general_prompt, general_query_prompt, query_prompt_few_shots

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
    pr_name: Optional[str]
    date_modified: Optional[str]
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

    if purpose == "query":
        query_messages = build_messages(
            model=azure_openai_model,
            system_prompt=system_prompt,
            tools=tools,
            few_shots=few_shots_examples,
            past_messages=chat_history,
            new_user_content=user_query,
            max_tokens=chatgpt_token_limit - token_limit,
        )

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
        messages = build_messages(
            model=azure_openai_model,
            system_prompt=system_prompt,
            past_messages=chat_history,
            new_user_content=user_query,
            max_tokens=chatgpt_token_limit - token_limit,
        )

        chat_completion: ChatCompletion = await openai_client.chat.completions.create(
            # Azure OpenAI takes the deployment name as the model name
            model=azure_openai_deployment if azure_openai_deployment else azure_openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=token_limit,
            n=1,
            stream=False,
            seed=seed,
        )

        logging.info("Generated response")
        return chat_completion


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


def get_sources_content(
    results: list[Document], use_semantic_captions: bool, use_image_citation: bool
) -> list[str]:
    if use_semantic_captions:
        return [
            {
                "index_id": doc.id or "",
                "article_id": doc.parent_id or "",
                "title": doc.title or "",
                "pr_name": doc.pr_name or "",
                "url": get_citation((doc.full_url or ""), use_image_citation)+ " [" + (doc.date_modified or "no date") + "]",
                "captions": nonewlines(" . ".join([cast(str, c.text) for c in (doc.captions or [])])),
                "search_score": doc.score or "",
                "reranker_score": doc.reranker_score or "",
            }
            for doc in results
        ]
    else:
        return [
            {
                "index_id": doc.id or "",
                "article_id": doc.parent_id or "",
                "title": doc.title or "",
                "pr_name": doc.pr_name or "",
                "url": get_citation((doc.full_url or ""), use_image_citation)+ " [" + (doc.date_modified or "no date") + "]",
                "chunk": (get_citation((doc.title or ""), use_image_citation)) + ": " + nonewlines(doc.chunks or ""),
                "search_score": doc.score or "",
                "reranker_score": doc.reranker_score or "",
            }
            for doc in results
        ]

def concat_sources(sources_content, start_idx, end_idx):
    combined = {
        'index_ids': [],
        'article_ids': [],
        'titles': [],
        'pr_names': [],
        'urls': [],
        'chunks': [],
        'search_scores': [],
        'reranker_scores': []
    }

    for item in sources_content[start_idx:end_idx]:
        combined['index_ids'].append(item['index_id'])
        combined['article_ids'].append(item['article_id'])
        combined['titles'].append(item['title'])
        combined['pr_names'].append(item['pr_name'])
        combined['urls'].append(item['url'])
        combined['chunks'].append(item['chunk'])
        combined['search_scores'].append(round(float(item['search_score']),5))
        combined['reranker_scores'].append(round(float(item['reranker_score']),3))

    return combined

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

def clean_text(df):
    df = df.apply(lambda col: col.map(lambda x: x.replace('\\u200b', '').replace('’', "'") if isinstance(x, str) else x))
    return df

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
            async for document in page:
                documents.append(
                    Document(
                        id=document.get("id"),
                        parent_id=document.get("parent_id"),
                        title=document.get("title"),
                        pr_name=document.get("pr_name"),
                        date_modified=document.get("date_modified"),
                        cover_image_url=document.get("cover_image_url"),
                        full_url=document.get("full_url"),
                        content_category=document.get("content_category"),
                        chunks=document.get("chunks"),
                        embedding=document.get("embedding"),
                        captions=cast(list[QueryCaptionResult], document.get("@search.captions")),
                        score=document.get("@search.score"),
                        reranker_score=document.get("@search.reranker_score")
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


def ensure_directory_exists(file_path: str):
    """
    Ensures that the directory for the given file path exists.
    If the directory does not exist, it is created.

    :param file_path: The path to the file.
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_or_append_csv(file_path: str, row_data: dict[str, str]): ####
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
    df = clean_text(df)

    if file_exists:
        # Append to existing CSV file
        logging.info("Appending to existing CSV file...")
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        # Write a new CSV file with the header
        logging.info("Writing to new CSV file...")
        df.to_csv(file_path, mode="w", header=True, index=False)


async def run(user_query: str, file_path: str, response: str, combined_sources: dict[str, str], total_input_tokens: int, total_output_tokens: int):
    data = {
        "user_query": user_query,
        "generated_response": response,
        "tokens_input": total_input_tokens,
        "tokens_output": total_output_tokens,
        "source_index_ids": combined_sources['index_ids'],
        "source_article_ids": list(set(combined_sources["article_ids"])),
        "source_titles": list(set(combined_sources["titles"])),
        "source_urls": list(set(combined_sources["urls"])),
        "source_contributors": list(set(combined_sources["pr_names"])),
        "source_chunks": "\n+++\n".join(combined_sources['chunks']),
        "source_search_scores": combined_sources['search_scores'],
        "source_reranker_scores": combined_sources['reranker_scores']
    }
    # Function call to write or append row data to the CSV file
    write_or_append_csv(file_path, data)
    logging.info("====================================")
    logging.info(f"Response output:\n{response}")
    logging.info("====================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate chat completion with Azure OpenAI and Azure Search for rapid RAG evaluation and testing.",
        epilog="""
        Example:
            python ans_generation.py --readfilepath input/sample_question_bank_5.csv --usevectorsearch --usetextsearch --usesemanticranker
        """,
    )
    parser.add_argument(
        "--readfilepath",
        type=str,
        default="./input/sample_question_bank_5.csv",
        help="The file path to read questions bank input file",
    )
    parser.add_argument(
        "--selectedlanguage",
        type=str,
        default="en",
        choices=["en", "zh", "ms", "ta"],
        help="The selected language. Only 'en', 'zh', 'ms', 'ta' are allowed",
    )
    # Azure OpenAI service
    parser.add_argument("--openaimodelname", type=str, default="gpt-4o", help="Azure OpenAI GPT model")
    parser.add_argument("--openaiservicename", type=str, default="cog-jisfkas7teqvm-000", help="Azure OpenAI service name")
    parser.add_argument("--apiversion", type=str, default="2024-06-01", help="Azure API version")
    parser.add_argument("--openaideploymentname", type=str, default="chat", help="Azure OpenAI deployment name")
    parser.add_argument("--embeddingdimensions", type=int, default=1536, help="Embedding dimensions")
    parser.add_argument("--embeddingmodelname", type=str, default="text-embedding-3-small", help="Embedding model name")
    parser.add_argument("--embeddingdeploymentname", type=str, default="embedding", help="Embedding deployment name")

    # Azure AI Search service
    parser.add_argument("--searchservice", type=str, default="gptkb-jisfkas7teqvm", help="Azure Search service name")
    parser.add_argument("--searchindex", type=str, default="gptkbindex5000200v7", help="Azure Search index name")
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
    parser.add_argument(
        "--savefilepath",
        type=str,
        default="./output/generated_answers_for_eval.csv",
        help="The file path where evaluation results will be saved",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--seed", type=int, default=1234, help="Set seed for reproducibility")

    args = parser.parse_args()

    QUERY_PROMPT = general_query_prompt
    SELECTED_LANGUAGE = Language.from_iso_code(args.selectedlanguage).value
    ANSWER_GENERATION_PROMPT = general_prompt.format(language=SELECTED_LANGUAGE)
    QUERY_PROMPT_FEW_SHOTS: list[ChatCompletionMessageParam] = json.loads(query_prompt_few_shots)
    CHAT_HISTORY = []

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
    EMBEDDING_DEPLOYMENT = args.embeddingdeploymentname

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
    SEED = args.seed
    NO_RESPONSE = "0"

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    SAVE_FILE_PATH = args.savefilepath
    OPEN_FILE_PATH = args.readfilepath
    qns_bank_df = pd.read_csv(OPEN_FILE_PATH)

    for index,row in qns_bank_df.iterrows():
        INPUT_QUERY = row["question"]
        print(f"INPUT_QUERY: {INPUT_QUERY}")
        ORIGINAL_USER_QUERY = [Prompts({"role": "user", "content": INPUT_QUERY})]
        USER_QUERY_REQUEST = "Generate search query for: " + str(INPUT_QUERY)
        MESSAGES = CHAT_HISTORY + ORIGINAL_USER_QUERY

        async def main():
            async with AzureDeveloperCliCredential(process_timeout=60) as azure_credential:
                token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
                async with AsyncAzureOpenAI(
                    api_version=AZURE_OPENAI_API_VERSION,
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    azure_ad_token_provider=token_provider,
                ) as openai_client:
                    try:                
                        total_input_tokens = 0
                        total_output_tokens = 0

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
                        total_input_tokens += chat_completion.usage.prompt_tokens
                        total_output_tokens += chat_completion.usage.completion_tokens

                        query_text = get_search_query(chat_completion, INPUT_QUERY, NO_RESPONSE)
                        logging.info(f"Query text: {query_text}")

                        # If retrieval mode includes vectors, compute an embedding for the query
                        vectors: list[VectorQuery] = []
                        if args.usevectorsearch:
                            vectors.append(
                                await compute_text_embedding(
                                    query_text,
                                    EMBEDDING_DIMENSIONS,
                                    EMBEDDING_MODEL,
                                    EMBEDDING_DEPLOYMENT,
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

                        combined_sources = concat_sources(sources_content, 0, len(sources_content))
                        content = "\n".join(combined_sources['chunks'])

                        chat_completion = await generate_search_query_or_response(
                            azure_openai_model=AZURE_OPENAI_CHATGPT_MODEL,
                            system_prompt=ANSWER_GENERATION_PROMPT,
                            chat_history=CHAT_HISTORY,
                            user_query=str(INPUT_QUERY) + "\n\nSources:\n" + content,
                            chatgpt_token_limit=CHATGPT_TOKEN_LIMIT,
                            token_limit=RESPONSE_TOKEN_LIMIT,
                            openai_client=openai_client,
                            azure_openai_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                            seed=SEED,
                            purpose="response",
                        )
                        total_input_tokens += chat_completion.usage.prompt_tokens
                        total_output_tokens += chat_completion.usage.completion_tokens

                        response = chat_completion.choices[0].message.content

                        await run(INPUT_QUERY, SAVE_FILE_PATH, response, combined_sources, total_input_tokens, total_output_tokens)
                    
                    except Exception as e:
                        logging.info("Logging error")
                        print(f"Error: {e}")

        # Run the main async function
        asyncio.run(main())
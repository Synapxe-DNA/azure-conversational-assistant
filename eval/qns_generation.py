import ast
import asyncio
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Optional, TypedDict, cast

import nest_asyncio
import pandas as pd
import pyarrow.parquet as pq
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import (
    QueryCaptionResult,
    QueryType,
    VectorizedQuery,
    VectorQuery,
)
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from openai.types.chat import ChatCompletion
from openai_messages_token_helper import build_messages, get_token_limit

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))
from app.backend.approaches.prompts import general_prompt  # noqa: E402

load_dotenv(dotenv_path=r"..\.azure\hhgai-prod-eastasia-001\.env")

# Azure OpenAI and search service
AZURE_SEARCH_SERVICE = os.environ["AZURE_SEARCH_SERVICE"]
AZURE_SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]
OPENAI_HOST = os.getenv("OPENAI_HOST", "azure")
OPENAI_CHATGPT_MODEL = os.environ["AZURE_OPENAI_CHATGPT_MODEL"]
OPENAI_EMB_MODEL = os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002")
OPENAI_EMB_DIMENSIONS = int(os.getenv("AZURE_OPENAI_EMB_DIMENSIONS", 1536))
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
AZURE_OPENAI_CHATGPT_DEPLOYMENT = (
    os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT") if OPENAI_HOST.startswith("azure") else None
)
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-03-01-preview"
AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT") if OPENAI_HOST.startswith("azure") else None
AZURE_SEARCH_QUERY_LANGUAGE = os.getenv("AZURE_SEARCH_QUERY_LANGUAGE", "en-us")
AZURE_SEARCH_QUERY_SPELLER = os.getenv("AZURE_SEARCH_QUERY_SPELLER", "lexicon")
CHATGPT_TOKEN_LIMIT = get_token_limit(OPENAI_CHATGPT_MODEL)

print(AZURE_OPENAI_SERVICE)


class Document:
    id: Optional[str]
    parent_id: Optional[str]
    title: Optional[str]
    pr_name: Optional[str]
    cover_image_url: Optional[str]
    full_url: Optional[str]
    content_category: Optional[str]
    chunks: Optional[str]
    embedding: Optional[list[float]]
    captions: list[QueryCaptionResult]
    score: Optional[float] = None
    reranker_score: Optional[float] = None


def create_df():
    df = pd.DataFrame(
        columns=[
            "content_category",
            "subpage",
            "keywords",
            "source_num",
            "index_ids",
            "article_ids_unique",
            "titles_unique",
            "content_contributors",
            "urls_unique",
            "chunks",
            "question",
            # "answer",
        ]
    )
    return df


def build_filter_by_content_category(filter_category):
    filters = []
    filters.append("content_category eq '{}'".format(filter_category.replace("'", "''")))
    return None if len(filters) == 0 else " and ".join(filters)


def build_filter_by_parent_id(id):
    filters = []
    id_content = f"{id}_content"
    id_table = f"{id}_table"
    id_js = f"{id}_js"
    filters.append("parent_id eq '{}'".format(id_content.replace("'", "''")))
    filters.append("parent_id eq '{}'".format(id_table.replace("'", "''")))
    filters.append("parent_id eq '{}'".format(id_js.replace("'", "''")))
    return None if len(filters) == 0 else " or ".join(filters)


async def compute_text_embedding(q: str, openai_client: AsyncAzureOpenAI):
    SUPPORTED_DIMENSIONS_MODEL = {
        "text-embedding-ada-002": False,
        "text-embedding-3-small": True,
        "text-embedding-3-large": True,
    }

    class ExtraArgs(TypedDict, total=False):
        dimensions: int

    dimensions_args: ExtraArgs = (
        {"dimensions": OPENAI_EMB_DIMENSIONS} if SUPPORTED_DIMENSIONS_MODEL[OPENAI_EMB_MODEL] else {}
    )
    embedding = await openai_client.embeddings.create(
        # Azure OpenAI takes the deployment name as the model name
        model=AZURE_OPENAI_EMB_DEPLOYMENT if AZURE_OPENAI_EMB_DEPLOYMENT else OPENAI_EMB_MODEL,
        input=q,
        **dimensions_args,
    )
    query_vector = embedding.data[0].embedding
    return VectorizedQuery(vector=query_vector, k_nearest_neighbors=50, fields="embedding")


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


def nonewlines(s: str) -> str:
    return s.replace("\n", " ").replace("\r", " ")


async def get_sources_content(
    results: list[Document], use_semantic_captions: bool, use_image_citation: bool
) -> list[str]:
    if use_semantic_captions:
        return [
            {
                "id": doc["id"] or "",
                "article_id": doc["parent_id"] or "",
                "title": doc["title"] or "",
                "pr_name": doc["pr_name"] or "",
                "url": get_citation((doc["full_url"] or ""), use_image_citation),
                "chunk": nonewlines(" . ".join([cast(str, c.text) for c in (doc["captions"] or [])])),
            }
            async for doc in results
        ]
    else:
        return [
            {
                "index_id": doc["id"] or "",
                "article_id": doc["parent_id"] or "",
                "title": doc["title"] or "",
                "pr_name": doc["pr_name"] or "",
                "url": get_citation((doc["full_url"] or ""), use_image_citation),
                "chunk": nonewlines(doc["chunks"] or ""),
            }
            async for doc in results
        ]


def concat_sources(sources_content, start_idx, end_idx):
    combined = {"index_ids": [], "article_ids": [], "titles": [], "pr_names": [], "urls": [], "chunks": []}

    for item in sources_content[start_idx:end_idx]:
        combined["index_ids"].append(item["index_id"])
        combined["article_ids"].append(item["article_id"])
        combined["titles"].append(item["title"])
        combined["pr_names"].append(item["pr_name"])
        combined["urls"].append(item["url"])
        combined["chunks"].append(item["chunk"])

    return combined


def get_combined_sources(sources_content, step=5, total_combined=3):
    combined_sources = []
    for n in range(0, (total_combined + 1) * step, 5):
        combined_source = concat_sources(sources_content, n, min(n + step, len(sources_content)))
        combined_sources.append(combined_source)

        # Stop when reach total_combined iterations
        if len(combined_sources) >= total_combined:
            break
    return combined_sources


def get_articles_df(content_category, percentile):
    merged_data = pq.read_table("./input/merged_data.parquet")
    merged_data = merged_data.to_pandas()
    merged_data_filtered = merged_data[merged_data["content_category"] == content_category]
    remove_type_list = [
        "No Extracted Content",
        "NaN",
        "No relevant content and mainly links",
        "Table of Contents",
        "No HTML Tags",
    ]
    merged_data_filtered = merged_data_filtered[~merged_data_filtered["remove_type"].isin(remove_type_list)]
    percentile_value = merged_data_filtered["page_views"].quantile(percentile)
    df_percentile = merged_data_filtered[merged_data_filtered["page_views"] > percentile_value]
    return df_percentile


async def retrieve_sources_content(keywords, num_search_results, filter, openai_client, search_client):
    vectors: list[VectorQuery] = []
    if USE_VECTOR_SEARCH:
        vectors.append(await compute_text_embedding(keywords, openai_client))

    if USE_SEMANTIC_RANKER:
        results = await search_client.search(
            search_text=keywords,
            filter=filter,
            top=num_search_results,
            query_caption="extractive|highlight-false" if USE_SEMANTIC_CAPTIONS else None,
            vector_queries=vectors,
            query_type=QueryType.SEMANTIC,
            query_language=AZURE_SEARCH_QUERY_LANGUAGE,
            query_speller=AZURE_SEARCH_QUERY_SPELLER,
            semantic_configuration_name="default",
            semantic_query=keywords,
        )
    else:
        results = await search_client.search(
            search_text=keywords,
            filter=filter,
            top=num_search_results,
            vector_queries=vectors,
        )

    sources_content = await get_sources_content(results, USE_SEMANTIC_CAPTIONS, use_image_citation=False)
    return sources_content


async def run_chat_completion(input, content, purpose, openai_client):
    if purpose == "generate_question":
        SYSTEM_PROMPT = qns_generation_prompt.format(keyword=input)
        NEW_USER_CONTENT = f"Please generate 3 unique questions on keywords '{input}' using the following provided source. \n\nSource:\n {content}"
        TEMPERATURE = TEMPERATURE_QNS
    elif purpose == "generate_answer":
        SYSTEM_PROMPT = general_prompt.format(language="ENGLISH")
        NEW_USER_CONTENT = input + "\n\nSources:\n" + content
        TEMPERATURE = TEMPERATURE_ANS

    messages = build_messages(
        model=OPENAI_CHATGPT_MODEL,
        system_prompt=SYSTEM_PROMPT,
        new_user_content=NEW_USER_CONTENT,
        max_tokens=CHATGPT_TOKEN_LIMIT - RESPONSE_TOKEN_LIMIT,
    )
    chat_completion: ChatCompletion = await openai_client.chat.completions.create(
        # Azure OpenAI takes the deployment name as the model name
        model=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=RESPONSE_TOKEN_LIMIT,
        n=1,
        stream=False,
        seed=SEED,
    )

    input_tokens_log = chat_completion.usage.prompt_tokens
    output_tokens_log = chat_completion.usage.completion_tokens

    return chat_completion, input_tokens_log, output_tokens_log


async def generate_by_content_category(keywords, filter, content_category, subpage, openai_client, search_client):
    logging.info("Generating question by content category")
    input_tokens = 0
    output_tokens = 0
    df = create_df()

    sources_content = await retrieve_sources_content(keywords, SEARCH_MAX_RESULTS, filter, openai_client, search_client)
    combined_sources = get_combined_sources(sources_content, step=5, total_combined=3)

    for n in range(len(combined_sources)):
        content = "\n".join(combined_sources[n]["chunks"])

        chat_coroutine, input_tokens_log_q, output_tokens_log_q = await run_chat_completion(
            keywords, content, "generate_question", openai_client
        )
        response_text_qns = chat_coroutine.choices[0].message.content
        questions_list = ast.literal_eval(response_text_qns)

        input_tokens += input_tokens_log_q
        output_tokens += output_tokens_log_q

        data = []
        for question in questions_list:
            # chat_coroutine, input_tokens_log_a, output_tokens_log_a = await run_chat_completion(question, content, "generate_answer", openai_client)
            # input_tokens += input_tokens_log_a
            # output_tokens += output_tokens_log_a

            # response_text_ans = chat_coroutine.choices[0].message.content
            data.append(
                {
                    "content_category": content_category,
                    "subpage": subpage,
                    "keywords": keywords,
                    "source_num": f"source_{n+1}",
                    "index_ids": combined_sources[n]["index_ids"],
                    "article_ids_unique": list(set(combined_sources[n]["article_ids"])),
                    "titles_unique": list(set(combined_sources[n]["titles"])),
                    "content_contributors": list(set(combined_sources[n]["pr_names"])),
                    "urls_unique": list(set(combined_sources[n]["urls"])),
                    "chunks": content,
                    "question": question,
                    # "answer": response_text_ans,
                }
            )
        df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
    return df, input_tokens, output_tokens


async def generate_by_page_views(df_percentile, keywords, content_category, subpage, openai_client, search_client):
    logging.info("Generating question by page views")
    input_tokens = 0
    output_tokens = 0
    df = create_df()
    cnt = 1
    for index, row in df_percentile.iterrows():
        # title = row["title"]
        id = row["id"]
        logging.info("Building filter")
        filter = build_filter_by_parent_id(id)

        sources_content = await retrieve_sources_content(
            keywords, SEARCH_MAX_RESULTS_ARTICLE, filter, openai_client, search_client
        )
        combined = concat_sources(sources_content, 0, len(sources_content))
        content = "\n".join(combined["chunks"])

        chat_coroutine, input_tokens_log_q, output_tokens_log_q = await run_chat_completion(
            keywords, content, "generate_question", openai_client
        )
        response_text_qns = chat_coroutine.choices[0].message.content
        questions_list = ast.literal_eval(response_text_qns)

        input_tokens += input_tokens_log_q
        output_tokens += output_tokens_log_q

        data = []
        for question in questions_list:
            # chat_coroutine, input_tokens_log_a, output_tokens_log_a = await run_chat_completion(question, content, "generate_answer", openai_client)
            # response_text_ans = chat_coroutine.choices[0].message.content

            # input_tokens += input_tokens_log_a
            # output_tokens += output_tokens_log_a

            data.append(
                {
                    "content_category": content_category,
                    "subpage": subpage,
                    "keywords": keywords,
                    "source_num": f"source_{cnt}",
                    "index_ids": list(set(combined["index_ids"])),
                    "article_ids_unique": list(set(combined["article_ids"])),
                    "titles_unique": list(set(combined["titles"])),
                    "content_contributors": list(set(combined["pr_names"])),
                    "urls_unique": list(set(combined["urls"])),
                    "chunks": content,
                    "question": question,
                    # "answer": response_text_ans,
                }
            )
        df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
        cnt += 1
    return df, input_tokens, output_tokens


qns_generation_prompt = """Your task is to formulate a set of 3 unique questions from given context, satisfying the rules given below:
1. All generated questions should precisely pertain to the keywords {keyword}, and it is imperative that the topic is explicitly included as an integral part of each question.
2. The generated questions should be straightforward, using simple language that is accessible to a broad audience.
3. The generated questions should make sense to humans even when read without the given context.
4. Prioritize clarity and brevity, ensuring that the questions are formulated in a way that reflect common language and would be easily comprehensible to the general public.
5. Ensure that the questions generated are meaningful and relevant to the general public in understanding or exploring more about the given topic.
7. Only generate questions that can be derived from the given context, including text and tables.
8. Importantly, ensure uniqueness and non-repetition in the questions.
9. Additionally, all questions must have answers found within the given context.
10. Do not use phrases like 'provided context', etc in the generated questions.
11. A generated question should contain less than 15 words.
12. Use simple language in the questions generated that are accessible to a broad audience.
13. The question should be in first-person perspective.
13. Each question should be enclosed in " ".
14. Output as a list of questions separated by , and enclosed by [ ].

Example of output:
["How can MediSave be used for outpatient treatments for newborns?", "What are the MediSave withdrawal limits for assisted conception procedures?", "How does MediShield Life help with payments for costly outpatient treatments?"]
"""

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate question bank with Azure OpenAI and Azure Search for RAG evaluation.",
        epilog="""
        Example:
            python qns_generation.py --readfilepath input/final_kws_for_qns_generation.xlsx --usevectorsearch --usetextsearch --usesemanticranker
        """,
    )
    parser.add_argument(
        "--readfilepath",
        type=str,
        default="./input/final_kws_for_qns_generation.xlsx",
        help="The file path to read input file with topic keywords",
    )
    parser.add_argument(
        "--searchmaxresults", type=int, default=30, help="Number of search results for generation by content category"
    )
    parser.add_argument(
        "--searchmaxresultspgviews",
        type=int,
        default=10,
        help="Number of search results for generation by top page views",
    )
    parser.add_argument("--temperatureqns", type=float, default=0.3, help="Temperature for question generation")
    parser.add_argument("--temperatureans", type=float, default=0.0, help="Temperature for answer generation")
    parser.add_argument("--usevectorsearch", action="store_true", help="Use vector search (dense retrieval)")
    parser.add_argument("--usetextsearch", action="store_true", help="Use text search (sparse retrieval)")
    parser.add_argument("--usesemanticranker", action="store_true", help="Use semantic ranking")
    parser.add_argument("--usesemanticcaptions", action="store_true", help="Use semantic captions")
    parser.add_argument("--minsearchscore", type=float, default=0.0, help="Threshold for minimum search score")
    parser.add_argument("--minrerankerscore", type=float, default=0.0, help="Threshold for minimum re-ranker score")
    parser.add_argument("--responsetokenlimit", type=int, default=512, help="The response token limit")
    parser.add_argument("--seed", type=int, default=1234, help="Set seed for reproducibility")

    args = parser.parse_args()

    input_file_path = args.readfilepath
    SEARCH_MAX_RESULTS = args.searchmaxresults
    SEARCH_MAX_RESULTS_ARTICLE = args.searchmaxresultspgviews
    TEMPERATURE_QNS = args.temperatureqns
    TEMPERATURE_ANS = args.temperatureans
    USE_VECTOR_SEARCH = args.usevectorsearch
    USE_TEXT_SEARCH = args.usetextsearch
    USE_SEMANTIC_RANKER = args.usesemanticranker
    USE_SEMANTIC_CAPTIONS = args.usesemanticcaptions
    MINIMUM_SEARCH_SCORE = args.minsearchscore
    MINIMUM_RERANKER_SCORE = args.minrerankerscore
    RESPONSE_TOKEN_LIMIT = args.responsetokenlimit
    SEED = args.seed

    df_kws = pd.read_excel(input_file_path)

    nest_asyncio.apply()

    async def main():
        azure_credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
        token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")

        async with AsyncAzureOpenAI(
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint="https://apim-jisfkas7teqvm.azure-api.net",  # https://{AZURE_OPENAI_SERVICE}.openai.azure.com
            azure_ad_token_provider=token_provider,
        ) as openai_client, SearchClient(
            endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
            index_name=AZURE_SEARCH_INDEX,
            credential=azure_credential,
        ) as search_client:

            total_input_tokens = 0
            total_output_tokens = 0

            results_final = create_df()
            for index, row in df_kws.iterrows():
                method = row["method"]
                content_category = row["content_category"]
                subpage = row["subpage"]
                keywords = row["final_keywords"]
                logging.info(f"Reading row {index}, {content_category}")

                error_log = defaultdict(list)  # to log rows with errors
                try:
                    if method == "by_content_category":
                        logging.info("Building filter")
                        if content_category.strip() == "[programs, program-sub-pages]":
                            if subpage == "vaccinate":
                                filter = build_filter_by_parent_id(
                                    1434610
                                )  # article_id of Vaccinate programs page with js
                            else:
                                filter = "content_category eq 'programs' or content_category eq 'program-sub-pages'"
                        else:
                            filter = build_filter_by_content_category(content_category)

                        results_kws, input_tokens_log, output_tokens_log = await generate_by_content_category(
                            keywords, filter, content_category, subpage, openai_client, search_client
                        )

                    elif method == "by_pg_views":
                        if content_category == "health-statistics":
                            percentile = 0.75  # 4 out of 15 articles
                        elif content_category == "medications":
                            percentile = 0.95  # 29 out of 579 articles

                        df_percentile = get_articles_df(content_category, percentile)

                        results_kws, input_tokens_log, output_tokens_log = await generate_by_page_views(
                            df_percentile, keywords, content_category, subpage, openai_client, search_client
                        )

                    results_final = pd.concat([results_final, results_kws], ignore_index=True)
                    total_input_tokens += input_tokens_log
                    total_output_tokens += output_tokens_log

                except Exception as e:
                    print(f"Error processing row {index} ({content_category}, {subpage}): {e}")
                    error_log["row"].append(index)
                    error_log["content_category"].append(content_category)
                    error_log["subpage"].append(subpage)
                    error_log["error"].append(e)
                    logging.info("Logging error")

            # Check cost of run
            # rates from https://openai.com/api/pricing/
            cost_per_million_input_tokens = 5
            cost_per_million_output_tokens = 15
            cost_input = (total_input_tokens / 1000000) * cost_per_million_input_tokens
            cost_output = (total_output_tokens / 1000000) * cost_per_million_output_tokens

            print("Number of tokens")
            print(f"total_input_tokens: {total_input_tokens}")
            print(f"total_output_tokens: {total_output_tokens}")
            print("\nTotal cost")
            print(f"input: ${round(cost_input,4)}")
            print(f"output: ${round(cost_output,4)}")
            print(f"total: ${round(cost_input+cost_output,4)}")

            # Drop duplicate questions
            results_final = results_final.drop_duplicates(subset="question")

            # Export in parquet and csv
            logging.info("Exporting files")
            now = datetime.now()

            output_dir = "input"
            os.makedirs(output_dir, exist_ok=True)

            save_filename = f"{output_dir}/question_bank_{now.strftime('%Y-%m-%d')}_{now.strftime('%H-%M')}"
            # results_final.to_parquet(f"{save_filename}.parquet",index=False)
            results_final.to_excel(f"{save_filename}.xlsx", index=False)
            print("File saved in input folder.")

            error_log_df = pd.DataFrame(error_log)
            if error_log_df.shape[0] >= 1:
                save_filename_error_log = f"{output_dir}/error_log_{now.strftime("%Y-%m-%d")}_{now.strftime("%H-%M")}"
                # results_final.to_parquet(f"{save_filename_error_log}.parquet",index=False)
                results_final.to_excel(f"{save_filename_error_log}.xlsx", index=False)
                print("Error log file saved in input folder.")

    # Run the main async function
    asyncio.run(main())

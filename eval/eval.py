import argparse
import asyncio
import os
import time
import warnings
from datetime import datetime

import pandas as pd
from azure.identity.aio import DefaultAzureCredential
from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

warnings.filterwarnings("ignore")


class AzureOpenAI(DeepEvalBaseLLM):
    def __init__(self, model):
        self.model = model

        if not hasattr(self, "last_input_tokens"):
            self.last_input_tokens = 0
        else:
            self.last_input_tokens = self.last_input_tokens

        if not hasattr(self, "last_output_tokens"):
            self.last_output_tokens = 0
        else:
            self.last_output_tokens = self.last_output_tokens

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        response = chat_model.invoke(prompt)
        output = response.content

        self.last_input_tokens += response.response_metadata["token_usage"]["prompt_tokens"]
        self.last_output_tokens += response.response_metadata["token_usage"]["completion_tokens"]

        return output

    async def a_generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        response = await chat_model.ainvoke(prompt)
        output = response.content

        self.last_input_tokens += response.response_metadata["token_usage"]["prompt_tokens"]
        self.last_output_tokens += response.response_metadata["token_usage"]["completion_tokens"]

        return output

    def get_model_name(self):
        return "GPT model"


async def get_azure_ad_token(resource_url):
    credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
    token = await credential.get_token(resource_url)
    return token.token


async def initialize_azure_openai(use_model):
    token = await get_azure_ad_token("https://cognitiveservices.azure.com/.default")

    if use_model == "gpt-4o":
        load_dotenv(dotenv_path=r"..\.azure\hhgai-prod-eastasia-001\.env")
    elif use_model == "gpt-4o-mini":
        load_dotenv(dotenv_path=r".env")

    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-03-01-preview"
    OPENAI_HOST = os.getenv("OPENAI_HOST", "azure")
    AZURE_OPENAI_CHATGPT_DEPLOYMENT = (
        os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT") if OPENAI_HOST.startswith("azure") else None
    )
    AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
    AZURE_ENDPOINT = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com/"

    llm_model = AzureChatOpenAI(
        openai_api_version=AZURE_OPENAI_API_VERSION,
        azure_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        azure_endpoint=AZURE_ENDPOINT,
        azure_ad_token=token,
    )
    return llm_model


def process_text(text):
    text_split = text.split("\n\n")
    text_processed = "\n\n".join(text_split[:-1])
    return text_processed


def create_metrics(model, use_mode, threshold=0.7):
    ARmetric = AnswerRelevancyMetric(threshold=threshold, model=model, include_reason=True, async_mode=use_mode)
    Fmetric = FaithfulnessMetric(threshold=threshold, model=model, include_reason=True, async_mode=use_mode)
    CRmetric = ContextualRelevancyMetric(threshold=threshold, model=model, include_reason=True, async_mode=use_mode)
    return ARmetric, Fmetric, CRmetric


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run deepeval to evaluate retrieval and generation performance of conversational assistant",
        epilog="""
        Example:
            python eval.py --readfilepath output/generated_answers_for_eval_test.csv --model gpt-4o-mini --asyncmode
        """,
    )

    parser.add_argument(
        "--readfilepath",
        type=str,
        default="./output/generated_answers_for_eval_test.csv",
        help="The file path to read input file",
    )
    parser.add_argument("--model", type=str, default="gpt-4o", help="Azure OpenAI GPT model for evaluation")
    parser.add_argument("--asyncmode", action="store_true", help="Use async programming")

    args = parser.parse_args()

    use_model = args.model
    use_mode = args.asyncmode

    df = pd.read_csv(args.readfilepath)
    df["retrieval_context"] = df["source_chunks"].apply(
        lambda x: x.split("\n+++\n")
    )  # convert chunks into list of chunks

    async def main():
        llm_model = await initialize_azure_openai(use_model)
        azure_model = AzureOpenAI(model=llm_model)

        retries = 5
        if use_mode:
            test_cases = []
            for index, row in df.iterrows():
                test_case = LLMTestCase(
                    input=row["user_query"],
                    actual_output=process_text(row["generated_response"]),  # Remove follow-up question
                    retrieval_context=row["retrieval_context"],
                )
                test_cases.append(test_case)

            metrics_list = []
            metrics_list.extend(create_metrics(azure_model, use_mode))

            for attempt in range(retries):
                try:
                    start_time = time.time()

                    results_df = pd.DataFrame()
                    results = evaluate(test_cases, metrics_list)

                    for result in results:
                        data = {
                            "input": [result.input],
                            "processed_output": [result.actual_output],
                            "retrieval_context": ["\n+++\n".join(result.retrieval_context)],
                        }

                        for metric_results in result.metrics_data:
                            if metric_results.name == "Answer Relevancy":
                                metric_name = "AR"
                            elif metric_results.name == "Faithfulness":
                                metric_name = "F"
                            elif metric_results.name == "Contextual Relevancy":
                                metric_name = "CR"

                            data[f"{metric_name}_score"] = [metric_results.score]
                            data[f"{metric_name}_reason"] = [metric_results.reason]
                            data[f"{metric_name}_verboselogs"] = [metric_results.verbose_logs]
                        data_df = pd.DataFrame(data)
                        results_df = pd.concat([results_df, data_df], ignore_index=True)

                    end_time = time.time()
                    print(f"Time taken: {round(end_time - start_time,2)}")
                    print(f"Total input tokens: {azure_model.last_input_tokens}")
                    print(f"Total output tokens: {azure_model.last_output_tokens}")

                    # save file
                    now = datetime.now()
                    output_dir = "output"
                    os.makedirs(output_dir, exist_ok=True)
                    results_df.to_excel(
                        f"{output_dir}/deepeval_results_{use_model}_{now.strftime('%Y-%m-%d')}_{now.strftime('%H-%M')}.xlsx",
                        index=False,
                    )
                    print(f"Output file saved in {output_dir} folder.")
                    break  # Exit retry loop if successful

                except Exception as e:
                    if "429" in str(e):  # Check if the error is a rate limit error
                        wait_time = 2**attempt  # Exponential backoff
                        print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying...")
                        time.sleep(wait_time)  # Wait before retrying
                    elif "content filter" in str(e):
                        print(f"Error: {e}")
                        continue
                    else:
                        print(f"Error: {e}")
                        break  # Exit loop on other errors

        else:
            results_df = pd.DataFrame()
            start_time = time.time()
            for index, row in df.iterrows():
                for attempt in range(retries):
                    try:
                        test_case = LLMTestCase(
                            input=row["user_query"],
                            actual_output=process_text(row["generated_response"]),  # Remove follow-up question
                            retrieval_context=row["retrieval_context"],
                        )
                        data = {
                            "input": [row["user_query"]],
                            "processed_output": [process_text(row["generated_response"])],
                            "retrieval_context": [row["retrieval_context"]],
                        }

                        metrics_list = []
                        metrics_list.extend(create_metrics(azure_model, use_mode))

                        for metric in metrics_list:
                            metric.measure(test_case)
                            if metric.__class__.__name__ == "AnswerRelevancyMetric":
                                metric_name = "AR"
                            elif metric.__class__.__name__ == "FaithfulnessMetric":
                                metric_name = "F"
                            elif metric.__class__.__name__ == "ContextualRelevancyMetric":
                                metric_name = "CR"

                            data[f"{metric_name}_score"] = [metric.score]
                            data[f"{metric_name}_reason"] = [metric.reason]
                            data[f"{metric_name}_verbose_logs"] = [metric.verbose_logs]

                        data_df = pd.DataFrame(data)
                        results_df = pd.concat([results_df, data_df], ignore_index=True)
                        break  # Exit retry loop if successful

                    except Exception as e:
                        if "429" in str(e):
                            wait_time = 2**attempt
                            print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying...")
                            time.sleep(wait_time)  # Wait before retrying
                        elif "content filter" in str(e):
                            data = {
                                "input": [row["user_query"]],
                                "processed_output": [process_text(row["generated_response"])],
                                "retrieval_context": [row["retrieval_context"]],
                                "error_log": [e],
                            }
                            data_df = pd.DataFrame(data)
                            results_df = pd.concat([results_df, data_df], ignore_index=True)
                            break  # Exit if it's a content filter error
                        else:
                            if attempt == retries - 1:
                                print(f"Error after {retries} attempts: {e}")
                                data = {
                                    "input": [row["user_query"]],
                                    "processed_output": [process_text(row["generated_response"])],
                                    "retrieval_context": [row["retrieval_context"]],
                                    "error_log": [f"Error after {attempt} attempts: {e}"],
                                }
                                data_df = pd.DataFrame(data)
                                results_df = pd.concat([results_df, data_df], ignore_index=True)

            end_time = time.time()
            print(f"Time taken: {round(end_time - start_time,2)}")
            print(f"Total input tokens: {azure_model.last_input_tokens}")
            print(f"Total output tokens: {azure_model.last_output_tokens}")

            # save file
            now = datetime.now()
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            results_df.to_excel(
                f"{output_dir}/deepeval_results_{use_model}_{now.strftime('%Y-%m-%d')}_{now.strftime('%H-%M')}.xlsx",
                index=False,
            )
            print(f"Output file saved in {output_dir} folder.")

    # Run the main async function
    asyncio.run(main())

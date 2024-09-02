import time
from typing import Any, Coroutine, List, Literal, Optional, Union, overload

from approaches import config
from approaches.approach import ThoughtStep
from approaches.chatapproach import ChatApproach
from approaches.prompts import (
    general_prompt,
    general_query_prompt,
    profile_prompt,
    profile_query_prompt,
)
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorQuery
from core.authentication import AuthenticationHelper
from models.profile import Profile
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from openai_messages_token_helper import build_messages, get_token_limit


class ChatReadRetrieveReadApproach(ChatApproach):
    """
    A multi-step approach that first uses OpenAI to turn the user's question into a search query,
    then uses Azure AI Search to retrieve relevant documents, and then sends the conversation history,
    original user question, and search results to OpenAI to generate a response.
    """

    def __init__(
        self,
        *,
        search_client: SearchClient,
        auth_helper: AuthenticationHelper,
        openai_client: AsyncOpenAI,
        chatgpt_model: str,
        chatgpt_deployment: Optional[str],  # Not needed for non-Azure OpenAI
        embedding_deployment: Optional[str],  # Not needed for non-Azure OpenAI or for retrieval_mode="text"
        embedding_model: str,
        embedding_dimensions: int,
        sourcepage_field: str,
        content_field: str,
        query_language: str,
        query_speller: str,
    ):
        self.search_client = search_client
        self.openai_client = openai_client
        self.auth_helper = auth_helper
        self.chatgpt_model = chatgpt_model
        self.chatgpt_deployment = chatgpt_deployment
        self.embedding_deployment = embedding_deployment
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.query_language = query_language
        self.query_speller = query_speller
        # See: https://github.com/pamelafox/openai-messages-token-helper/issues/16
        self.chatgpt_token_limit = get_token_limit(chatgpt_model)  # gpt-4o-mini not yet supported

    @property
    def system_message_chat_conversation(self):
        return """Assistant helps the company employees with their healthcare plan questions, and questions about the employee handbook. Be brief in your answers.
        Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
        For tabular information return it as an html table. Do not return markdown format. If the question is not in English, answer in the language used in the question.
        Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. Use square brackets to reference the source, for example [info1.txt]. Don't combine sources, list each source separately, for example [info1.txt][info2.pdf].
        {follow_up_questions_prompt}
        {injected_prompt}
        """

    @overload
    async def run_until_final_call(
        self,
        messages: list[ChatCompletionMessageParam],
        profile: Profile,
        language: str,
        # overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        should_stream: Literal[False],
    ) -> tuple[dict[str, Any], Coroutine[Any, Any, ChatCompletion], List[dict[str, Any]]]: ...

    @overload
    async def run_until_final_call(
        self,
        messages: list[ChatCompletionMessageParam],
        profile: Profile,
        language: str,
        # overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        should_stream: Literal[True],
    ) -> tuple[dict[str, Any], Coroutine[Any, Any, AsyncStream[ChatCompletionChunk]], List[dict[str, Any]]]: ...

    async def run_until_final_call(
        self,
        messages: list[ChatCompletionMessageParam],
        profile: Profile,
        language: str,
        # overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        should_stream: bool = False,
    ) -> tuple[
        dict[str, Any],
        Coroutine[Any, Any, Union[ChatCompletion, AsyncStream[ChatCompletionChunk]]],
        List[dict[str, Any]],
    ]:
        start_time = time.time()

        seed = config.SEED
        temperature = config.TEMPERATURE
        use_text_search = config.USE_TEXT_SEARCH
        use_vector_search = config.USE_VECTOR_SEARCH
        use_semantic_ranker = config.USE_SEMANTIC_RANKER
        use_semantic_captions = config.USE_SEMANTIC_CAPTIONS
        top = config.SEARCH_MAX_RESULTS
        minimum_search_score = config.MINIMUM_SEARCH_SCORE
        minimum_reranker_score = config.MINIMUM_RERANKER_SCORE
        response_token_limit = config.CHAT_RESPONSE_MAX_TOKENS

        selected_language = language.upper()
        print(f"Selected language: {selected_language}")
        print(f"Profile Type: {profile.profile_type}")

        if profile.user_age < 1:
            age_group = "Infant"
        elif profile.user_age <= 2:
            age_group = "Toddler"
        elif profile.user_age <= 6:
            age_group = "Preschool"
        elif profile.user_age <= 12:
            age_group = "Child"
        elif profile.user_age <= 17:
            age_group = "Teen"
        elif profile.user_age <= 64:
            age_group = "Adult"
        else:
            age_group = "Senior"

        original_user_query = messages[-1]["content"]
        if not isinstance(original_user_query, str):
            raise ValueError("The most recent message content must be a string.")

        if profile.profile_type == "general":
            user_query_request = "Generate search query for: " + original_user_query
        else:
            stripped_text_check = original_user_query.replace(" ", "")  # check if user input is an empty string
            if not stripped_text_check:
                user_query_request = "Generate search query for: " + original_user_query
            else:
                user_query_request = f"Generate search query for: {original_user_query}, user profile: {age_group}, {profile.user_gender}, age {profile.user_age}, {profile.user_condition}"

        tools: List[ChatCompletionToolParam] = [
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

        if profile.profile_type == "general":
            query_prompt = general_query_prompt
            answer_generation_prompt = general_prompt.format(language=selected_language)
        else:
            query_prompt = profile_query_prompt.format(
                gender=profile.user_gender,
                age_group=age_group,
                age=profile.user_age,
                pre_conditions=profile.user_condition,
            )
            answer_generation_prompt = profile_prompt.format(
                language=selected_language,
                gender=profile.user_gender,
                age_group=age_group,
                age=profile.user_age,
                pre_conditions=profile.user_condition,
            )

        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
        query_response_token_limit = 100
        query_messages = build_messages(
            model=self.chatgpt_model,
            system_prompt=query_prompt,
            tools=tools,
            few_shots=self.query_prompt_few_shots,
            past_messages=messages[:-1],
            new_user_content=user_query_request,
            max_tokens=self.chatgpt_token_limit - query_response_token_limit,
        )

        chat_completion: ChatCompletion = await self.openai_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            # Azure OpenAI takes the deployment name as the model name
            model=self.chatgpt_deployment if self.chatgpt_deployment else self.chatgpt_model,
            temperature=0.0,  # Minimize creativity for search query generation
            max_tokens=query_response_token_limit,  # Setting too low risks malformed JSON, setting too high may affect performance
            n=1,
            tools=tools,
            seed=seed,
        )

        query_text = self.get_search_query(chat_completion, original_user_query)

        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query

        # If retrieval mode includes vectors, compute an embedding for the query
        vectors: list[VectorQuery] = []
        if use_vector_search:
            vectors.append(await self.compute_text_embedding(query_text))

        results = await self.search(
            top,
            query_text,
            None,
            vectors,
            use_text_search,
            use_vector_search,
            use_semantic_ranker,
            use_semantic_captions,
            minimum_search_score,
            minimum_reranker_score,
        )

        sources_content = self.get_sources_content(results, use_semantic_captions, use_image_citation=False)

        content = "\n".join(sources_content)

        # STEP 3: Generate a contextual and content specific answer using the search results and chat history

        messages = build_messages(
            model=self.chatgpt_model,
            system_prompt=answer_generation_prompt,
            past_messages=messages[:-1],
            # Model does not handle lengthy system messages well. Moving sources to latest user conversation to solve follow up questions prompt.
            new_user_content=original_user_query + "\n\nSources:\n" + content,
            max_tokens=self.chatgpt_token_limit - response_token_limit,
        )

        # data_points = {"text": sources_content}

        chat_coroutine = self.openai_client.chat.completions.create(
            # Azure OpenAI takes the deployment name as the model name
            model=self.chatgpt_deployment if self.chatgpt_deployment else self.chatgpt_model,
            messages=messages,
            temperature=temperature,
            max_tokens=response_token_limit,
            n=1,
            stream=should_stream,
            seed=seed,
        )

        end_time = time.time()

        extra_info = {
            # "data_points": data_points,
            "thoughts": [
                ThoughtStep(
                    "Prompt to generate search query",
                    [str(message) for message in query_messages],
                    (
                        {"model": self.chatgpt_model, "deployment": self.chatgpt_deployment}
                        if self.chatgpt_deployment
                        else {"model": self.chatgpt_model}
                    ),
                ),
                ThoughtStep(
                    "Search using generated search query",
                    query_text,
                    {
                        "use_semantic_captions": use_semantic_captions,
                        "use_semantic_ranker": use_semantic_ranker,
                        "top": top,
                        "filter": None,
                        "use_vector_search": use_vector_search,
                        "use_text_search": use_text_search,
                    },
                ),
                ThoughtStep(
                    "Search results",
                    [result.serialize_for_results() for result in results],
                ),
                ThoughtStep(
                    "Prompt to generate answer",
                    [str(message) for message in messages],
                    (
                        {"model": self.chatgpt_model, "deployment": self.chatgpt_deployment}
                        if self.chatgpt_deployment
                        else {"model": self.chatgpt_model}
                    ),
                ),
                ThoughtStep(
                    "Time taken",
                    end_time - start_time,
                ),
            ],
        }

        return (extra_info, chat_coroutine)

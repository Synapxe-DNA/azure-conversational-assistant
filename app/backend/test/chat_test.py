import json
import os

import pytest
import pytest_asyncio
import requests
from lingua import Language, LanguageDetectorBuilder

"""
File paths
"""
valid_json_general_profile = "json_test_files/chat/valid_json_general_profile.json"
valid_json_other_profile = "json_test_files/chat/valid_json_other_profile.json"

valid_json_spoken_english = "json_test_files/chat/valid_json_spoken_english.json"
valid_json_spoken_chinese = "json_test_files/chat/valid_json_spoken_chinese.json"
valid_json_spoken_malay = "json_test_files/chat/valid_json_spoken_malay.json"
valid_json_spoken_tamil = "json_test_files/chat/valid_json_spoken_tamil.json"

valid_json_english_in_english_out = "json_test_files/chat/valid_json_english_in_english_out.json"
valid_json_english_in_chinese_out = "json_test_files/chat/valid_json_english_in_chinese_out.json"
valid_json_english_in_malay_out = "json_test_files/chat/valid_json_english_in_malay_out.json"
valid_json_english_in_tamil_out = "json_test_files/chat/valid_json_english_in_tamil_out.json"

valid_json_chinese_in_english_out = ""
valid_json_chinese_in_chinese_out = ""
valid_json_chinese_in_malay_out = ""
valid_json_chinese_in_tamil_out = ""

valid_json_malay_in_english_out = ""
valid_json_malay_in_chinese_out = ""
valid_json_malay_in_malay_out = ""
valid_json_malay_in_tamil_out = ""

valid_json_tamil_in_english_out = ""
valid_json_tamil_in_chinese_out = ""
valid_json_tamil_in_malay_out = ""
valid_json_tamil_in_tamil_out = ""

"""
Response file path
"""

response_folder_path = "responses/chat/"

"""
Test cases for the feedback endpoint
"""


@pytest_asyncio.fixture
async def chat_endpointURL(endpointURL):
    yield f"{endpointURL}/chat/stream"


"""
Test chat endpoint with valid json general profile
"""


@pytest.mark.asyncio
async def test_valid_json_general_profile_request(chat_endpointURL):
    response, _ = await post_valid_json_request(valid_json_general_profile, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


"""
Test chat endpoint with valid json other profile
"""


@pytest.mark.asyncio
async def test_valid_json_other_profile_request(chat_endpointURL):
    response, _ = await post_valid_json_request(valid_json_other_profile, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


"""
Test chat endpoint with valid json spoken english
"""


@pytest.mark.asyncio
async def test_valid_json_spoken_english_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_spoken_english, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.ENGLISH, f"Expected {Language.ENGLISH}, got {response_language}"


"""
Test chat endpoint with valid json spoken chinese
"""


@pytest.mark.asyncio
async def test_valid_json_spoken_chinese_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_spoken_chinese, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.CHINESE, f"Expected {Language.CHINESE}, got {response_language}"


"""
Test chat endpoint with valid json spoken malay
"""


@pytest.mark.asyncio
async def test_valid_json_spoken_malay_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_spoken_malay, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.MALAY, f"Expected {Language.MALAY}, got {response_language}"


"""
Test chat endpoint with valid json spoken tamil
"""


@pytest.mark.asyncio
async def test_valid_json_spoken_tamil_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_spoken_tamil, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.TAMIL, f"Expected {Language.TAMIL}, got {response_language}"


"""
Test chat endpoint with valid json english in english out
"""


@pytest.mark.asyncio
async def test_valid_json_english_in_english_out_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_english_in_english_out, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.ENGLISH, f"Expected {Language.ENGLISH}, got {response_language}"


"""
Test chat endpoint with valid json english in chinese out
"""


@pytest.mark.asyncio
async def test_valid_json_english_in_chinese_out_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_english_in_chinese_out, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.CHINESE, f"Expected {Language.CHINESE}, got {response_language}"


"""
Test chat endpoint with valid json english in malay out
"""


@pytest.mark.asyncio
async def test_valid_json_english_in_malay_out_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_english_in_malay_out, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.MALAY, f"Expected {Language.MALAY}, got {response_language}"


"""
Test chat endpoint with valid json english in tamil out
"""


@pytest.mark.asyncio
async def test_valid_json_english_in_tamil_out_request(chat_endpointURL):
    response, combined_json = await post_valid_json_request(valid_json_english_in_tamil_out, chat_endpointURL)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.TAMIL, f"Expected {Language.TAMIL}, got {response_language}"


"""
Helper function
"""


async def merge_streaming_response(response):
    combined_json = {}
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            json_object = json.loads(chunk)

            for key, value in json_object.items():
                if key in combined_json:
                    if isinstance(combined_json[key], list):
                        combined_json[key].extend(value if isinstance(value, list) else [value])
                    else:
                        combined_json[key] = combined_json[key] + value
                else:
                    combined_json[key] = value
    return combined_json


async def save_streaming_response(response_file_path, combined_json):
    if not os.path.exists(response_folder_path):
        os.makedirs(response_folder_path)

    with open(response_file_path, "w") as json_response:
        json.dump(combined_json, json_response, indent=4, ensure_ascii=False)


async def check_response_language(combined_json):
    response_message = combined_json["response_message"]
    languages = [Language.ENGLISH, Language.CHINESE, Language.TAMIL, Language.MALAY]
    detector = LanguageDetectorBuilder.from_languages(*languages).build()
    language = detector.detect_language_of(response_message)
    return language


async def post_valid_json_request(file_path, chat_endpointURL):
    with open(file_path) as json_request:
        data = json.load(json_request)

    response = requests.post(chat_endpointURL, json=data, stream=True)

    response_file_path = os.path.join(response_folder_path, os.path.basename(json_request.name))

    combined_json = await merge_streaming_response(response)
    await save_streaming_response(response_file_path, combined_json)

    return response, combined_json

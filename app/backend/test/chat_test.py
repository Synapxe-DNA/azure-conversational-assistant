import json
import os

import pytest
import pytest_asyncio
import requests

"""
File paths
"""
valid_json_general_profile = "json_test_files/chat/valid_json_general_profile.json"
valid_json_other_profile = "json_test_files/chat/valid_json_other_profile.json"

valid_json_spoken_english = "json_test_files/chat/valid_json_spoken_english.json"
valid_json_spoken_chinese = "json_test_files/chat/valid_json_spoken_chinese.json"
valid_json_spoken_malay = "json_test_files/chat/valid_json_spoken_malay.json"
valid_json_spoken_tamil = "json_test_files/chat/valid_json_spoken_tamil.json"

valid_json_english_in_english_out = ""
valid_json_english_in_chinese_out = ""
valid_json_english_in_malay_out = ""
valid_json_english_in_tamil_out = ""

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
Test feedback endpoint with valid json positive feedback
"""


@pytest.mark.asyncio
async def test_valid_json_general_profile_request(chat_endpointURL):
    with open(valid_json_general_profile) as json_request:
        data = json.load(json_request)

    response = requests.post(chat_endpointURL, json=data, stream=True)

    response_file_path = os.path.join(response_folder_path, os.path.basename(json_request.name))

    await save_streaming_response(response_file_path, response)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


"""
Helper function
"""


async def merge_streaming_response(response):
    combined_json = {}
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            json_object = json.loads(chunk.decode("utf-8"))

            for key, value in json_object.items():
                if key in combined_json:
                    if isinstance(combined_json[key], list):
                        combined_json[key].extend(value if isinstance(value, list) else [value])
                    else:
                        combined_json[key] = combined_json[key] + value
                else:
                    combined_json[key] = value
    return combined_json


async def save_streaming_response(response_file_path, response):
    if not os.path.exists(response_folder_path):
        os.makedirs(response_folder_path)

    combined_json = await merge_streaming_response(response)

    with open(response_file_path, "w") as json_response:
        json.dump(combined_json, json_response, indent=4)

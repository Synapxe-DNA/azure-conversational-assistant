import json
import os

import pytest
import io
from pydub import AudioSegment
import base64
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

valid_json_chinese_in_english_out = "json_test_files/chat/valid_json_chinese_in_english_out.json"
valid_json_chinese_in_chinese_out = "json_test_files/chat/valid_json_chinese_in_chinese_out.json"
valid_json_chinese_in_malay_out = "json_test_files/chat/valid_json_chinese_in_malay_out.json"
valid_json_chinese_in_tamil_out = "json_test_files/chat/valid_json_chinese_in_tamil_out.json"

valid_json_malay_in_english_out = "json_test_files/chat/valid_json_malay_in_english_out.json"
valid_json_malay_in_chinese_out = "json_test_files/chat/valid_json_malay_in_chinese_out.json"
valid_json_malay_in_malay_out = "json_test_files/chat/valid_json_malay_in_malay_out.json"
valid_json_malay_in_tamil_out = "json_test_files/chat/valid_json_malay_in_tamil_out.json"

valid_json_tamil_in_english_out = "json_test_files/chat/valid_json_tamil_in_english_out.json"
valid_json_tamil_in_chinese_out = "json_test_files/chat/valid_json_tamil_in_chinese_out.json"
valid_json_tamil_in_malay_out = "json_test_files/chat/valid_json_tamil_in_malay_out.json"
valid_json_tamil_in_tamil_out = "json_test_files/chat/valid_json_tamil_in_tamil_out.json"

"""
Response file path
"""

response_folder_path = "responses/voice/"

@pytest_asyncio.fixture
async def voice_endpointURL(endpointURL):
    """
    URL for voice endpoint
    """

    yield f"{endpointURL}/voice/stream"


@pytest.mark.asyncio
async def test_valid_json_general_profile_request(voice_endpointURL):
    """
    Test chat endpoint with valid json general profile
    """

    response, _ = await post_valid_json_request(valid_json_general_profile, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_valid_json_other_profile_request(voice_endpointURL):
    """
    Test chat endpoint with valid json other profile
    """

    response, _ = await post_valid_json_request(valid_json_other_profile, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_valid_json_spoken_english_request(voice_endpointURL):
    """
    Test chat endpoint with valid json spoken english
    """

    response, combined_json = await post_valid_json_request(valid_json_spoken_english, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.ENGLISH, f"Expected {Language.ENGLISH}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_spoken_chinese_request(voice_endpointURL):
    """
    Test chat endpoint with valid json spoken chinese
    """

    response, combined_json = await post_valid_json_request(valid_json_spoken_chinese, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.CHINESE, f"Expected {Language.CHINESE}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_spoken_malay_request(voice_endpointURL):
    """
    Test chat endpoint with valid json spoken malay
    """

    response, combined_json = await post_valid_json_request(valid_json_spoken_malay, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.MALAY, f"Expected {Language.MALAY}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_spoken_tamil_request(voice_endpointURL):
    """
    Test chat endpoint with valid json spoken tamil
    """

    response, combined_json = await post_valid_json_request(valid_json_spoken_tamil, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.TAMIL, f"Expected {Language.TAMIL}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_english_in_english_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json english in english out
    """

    response, combined_json = await post_valid_json_request(valid_json_english_in_english_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.ENGLISH, f"Expected {Language.ENGLISH}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_english_in_chinese_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json english in chinese out
    """

    response, combined_json = await post_valid_json_request(valid_json_english_in_chinese_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.CHINESE, f"Expected {Language.CHINESE}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_english_in_malay_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json english in malay out
    """

    response, combined_json = await post_valid_json_request(valid_json_english_in_malay_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.MALAY, f"Expected {Language.MALAY}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_english_in_tamil_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json english in tamil out
    """

    response, combined_json = await post_valid_json_request(valid_json_english_in_tamil_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.TAMIL, f"Expected {Language.TAMIL}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_chinese_in_english_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json chinese in english out
    """

    response, combined_json = await post_valid_json_request(valid_json_chinese_in_english_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.ENGLISH, f"Expected {Language.ENGLISH}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_chinese_in_chinese_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json chinese in chinese out
    """

    response, combined_json = await post_valid_json_request(valid_json_chinese_in_chinese_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.CHINESE, f"Expected {Language.CHINESE}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_chinese_in_malay_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json chinese in malay out
    """

    response, combined_json = await post_valid_json_request(valid_json_chinese_in_malay_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.MALAY, f"Expected {Language.MALAY}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_chinese_in_tamil_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json chinese in tamil out
    """

    response, combined_json = await post_valid_json_request(valid_json_chinese_in_tamil_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.TAMIL, f"Expected {Language.TAMIL}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_malay_in_english_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json malay in english out
    """

    response, combined_json = await post_valid_json_request(valid_json_malay_in_english_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.ENGLISH, f"Expected {Language.ENGLISH}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_malay_in_chinese_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json malay in chinese out
    """

    response, combined_json = await post_valid_json_request(valid_json_malay_in_chinese_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.CHINESE, f"Expected {Language.CHINESE}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_malay_in_malay_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json malay in malay out
    """

    response, combined_json = await post_valid_json_request(valid_json_malay_in_malay_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.MALAY, f"Expected {Language.MALAY}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_malay_in_tamil_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json malay in tamil out
    """

    response, combined_json = await post_valid_json_request(valid_json_malay_in_tamil_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.TAMIL, f"Expected {Language.TAMIL}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_tamil_in_english_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json tamil in english out
    """

    response, combined_json = await post_valid_json_request(valid_json_tamil_in_english_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.ENGLISH, f"Expected {Language.ENGLISH}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_tamil_in_chinese_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json tamil in chinese out
    """

    response, combined_json = await post_valid_json_request(valid_json_tamil_in_chinese_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.CHINESE, f"Expected {Language.CHINESE}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_tamil_in_malay_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json tamil in malay out
    """

    response, combined_json = await post_valid_json_request(valid_json_tamil_in_malay_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.MALAY, f"Expected {Language.MALAY}, got {response_language}"


@pytest.mark.asyncio
async def test_valid_json_tamil_in_tamil_out_request(voice_endpointURL):
    """
    Test chat endpoint with valid json tamil in tamil out
    """

    response, combined_json = await post_valid_json_request(valid_json_tamil_in_tamil_out, voice_endpointURL)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

    response_language = await check_response_language(combined_json)
    assert response_language == Language.TAMIL, f"Expected {Language.TAMIL}, got {response_language}"


"""
Helper functions
"""


async def merge_streaming_response(response):
    combined_json = {}
    audio_list = []
    response_decode = response.content.decode('utf-8')
    list_of_json = json.loads("[{}]".format(response_decode.replace("}{", "},{")))
    for chunk in list_of_json: # TODO fix ChunkedEncodingError due to large response
        for key, value in chunk.items():
            if key in combined_json:
                if isinstance(combined_json[key], list):
                    combined_json[key].extend(value if isinstance(value, list) else [value])
                else:
                    combined_json[key] = combined_json[key] + value
            else:
                combined_json[key] = value 

            if key == "audio_base64" and value != "":
                audio_list.append(base64.b64decode(value))

    return combined_json, audio_list


async def save_streaming_response(response_file_path, combined_json, audio_list):
    if not os.path.exists(response_folder_path):
        os.makedirs(response_folder_path)

    with open(response_file_path, "w") as json_response:
        json.dump(combined_json, json_response, indent=4, ensure_ascii=False)

    await combine_audio_with_pydub(audio_list, response_file_path)

async def combine_audio_with_pydub(audio_list, response_file_path):
    audio_response_file_path = response_file_path.replace(".json", ".mp3")
    combined = AudioSegment.empty()

    for audio_bytes in audio_list:

        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        combined += audio_segment

    combined.export(audio_response_file_path, format='mp3', bitrate="32k")


async def check_response_language(combined_json):
    response_message = combined_json["response_message"]
    languages = [Language.ENGLISH, Language.CHINESE, Language.TAMIL, Language.MALAY]
    detector = LanguageDetectorBuilder.from_languages(*languages).build()
    language = detector.detect_language_of(response_message)
    return language


async def post_valid_json_request(file_path, voice_endpointURL):
    with open(file_path) as json_request:
        data = json.load(json_request)

    response = requests.post(voice_endpointURL, json=data, stream=True)
    response_file_path = os.path.join(response_folder_path, os.path.basename(json_request.name))
    combined_json, audio_list = await merge_streaming_response(response)
    await save_streaming_response(response_file_path, combined_json, audio_list)

    return response, combined_json

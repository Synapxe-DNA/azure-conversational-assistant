import pytest
import pytest_asyncio
import requests

"""
Test cases for the speech endpoint
"""


@pytest_asyncio.fixture
async def speech_endpointURL(endpointURL):
    yield f"{endpointURL}/speech"


"""
Test speech endpoint with valid json and valid data request
"""


@pytest.mark.asyncio
async def test_valid_json_valid_data_request(speech_endpointURL):
    data = {"text": "Hello world"}
    response = requests.post(speech_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


"""
Test speech endpoint with valid json but invalid data request
"""


@pytest.mark.asyncio
async def test_valid_json_invalid_data_request(speech_endpointURL):
    data = {"INVALID": "Invalid data"}
    response = requests.post(speech_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"


"""
Test speech endpoint with invalid json request
"""


@pytest.mark.asyncio
async def test_invalid_json_request(speech_endpointURL):
    data = "Not a json"
    response = requests.post(speech_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"

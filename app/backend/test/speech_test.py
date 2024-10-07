import pytest
import pytest_asyncio
import requests


@pytest_asyncio.fixture
async def speech_endpointURL(endpointURL):
    """
    URL for speech endpoint
    """

    yield f"{endpointURL}/speech"


@pytest.mark.asyncio
async def test_valid_json_valid_data_request(speech_endpointURL):
    """
    Test speech endpoint with valid json and valid data request
    """

    data = {"text": "Hello world"}
    response = requests.post(speech_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_valid_json_invalid_data_request(speech_endpointURL):
    """
    Test speech endpoint with valid json but invalid data request
    """

    data = {"INVALID": "Invalid data"}
    response = requests.post(speech_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_invalid_json_request(speech_endpointURL):
    """
    Test speech endpoint with invalid json request
    """

    data = "Not a json"
    response = requests.post(speech_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"

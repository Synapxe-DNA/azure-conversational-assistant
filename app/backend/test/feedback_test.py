import datetime
import json

import pytest
import pytest_asyncio
import requests

"""
File paths
"""
valid_json_positive = "backend/test/json_test_files/feedback/valid_json_positive.json"
valid_json_negative = "backend/test/json_test_files/feedback/valid_json_negative.json"
valid_json_invalid_source_id = "backend/test/json_test_files/feedback/valid_json_invalid_source_id.json"
valid_json_no_source = "backend/test/json_test_files/feedback/valid_json_no_source.json"


@pytest_asyncio.fixture
async def feedback_endpointURL(endpointURL):
    """
    URL for feedback endpoint
    """

    yield f"{endpointURL}/feedback"


@pytest.mark.asyncio
async def test_valid_json_positive_request(feedback_endpointURL):
    """
    Test feedback endpoint with valid json positive feedback
    """
    with open(valid_json_positive) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_valid_json_negative_request(feedback_endpointURL):
    """
    Test feedback endpoint with valid json negative feedback
    """
    with open(valid_json_negative) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_valid_json_invalid_source_id_request(feedback_endpointURL):
    """
    Test feedback endpoint with valid json but invalid source id
    """

    with open(valid_json_invalid_source_id) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_valid_json_no_sources_request(feedback_endpointURL):
    """
    Test feedback endpoint with valid json but no sources
    """

    with open(valid_json_no_source) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_valid_json_invalid_data_request(feedback_endpointURL):
    """
    Test feedback endpoint with valid json invalid data
    """

    data = {"INVALID": "Invalid data"}
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"


@pytest.mark.asyncio
async def test_invalid_json_request(feedback_endpointURL):
    """
    Test feedback endpoint with invalid json
    """

    data = "Not a json"
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"

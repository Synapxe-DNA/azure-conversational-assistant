import pytest
import pytest_asyncio
import requests
import json
import datetime
'''
File paths
'''
valid_json_positive = "json_test_files/feedback/valid_json_positive.json" 
valid_json_negative = "json_test_files/feedback/valid_json_negative.json"
valid_json_invalid_source_id = "json_test_files/feedback/valid_json_invalid_source_id.json"
valid_json_no_source = "json_test_files/feedback/valid_json_no_source.json"


"""
Test cases for the feedback endpoint
"""

@pytest_asyncio.fixture
async def feedback_endpointURL(endpointURL):
    yield f"{endpointURL}/feedback"


"""
Test feedback endpoint with valid json positive feedback
"""

@pytest.mark.asyncio
async def test_valid_json_positive_request(feedback_endpointURL):
    with open(valid_json_positive) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

"""
Test feedback endpoint with valid json negative feedback
"""

@pytest.mark.asyncio
async def test_valid_json_negative_request(feedback_endpointURL):
    with open(valid_json_negative) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"


"""
Test feedback endpoint with valid json but invalid source id
"""

@pytest.mark.asyncio
async def test_valid_json_invalid_source_id_request(feedback_endpointURL):
    with open(valid_json_invalid_source_id) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

"""
Test feedback endpoint with valid json but no sources
"""

@pytest.mark.asyncio
async def test_valid_json_no_sources_request(feedback_endpointURL):
    with open(valid_json_no_source) as f:
        data = json.load(f)
    data["date_time"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.json()}"

"""
Test feedback endpoint with valid json invalid data
"""

@pytest.mark.asyncio
async def test_valid_json_invalid_data_request(feedback_endpointURL):
    data = {"INVALID": "Invalid data"}
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"

"""
Test feedback endpoint with invalid json
"""

@pytest.mark.asyncio
async def test_invalid_json_request(feedback_endpointURL):
    data = "Not a json"
    response = requests.post(feedback_endpointURL, json=data)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}, {response.json()}"


import os

import pytest_asyncio
from dotenv import load_dotenv


def pytest_addoption(parser):
    parser.addoption("--local", action="store_true", help="Run test for local development")


def pytest_configure(config):
    config.addinivalue_line(
        "filterwarnings", "ignore::DeprecationWarning:pydub.utils"
    )  # to ignore audioop deprecation as pydub does not have an alternative yet


@pytest_asyncio.fixture
async def endpointURL(request):
    load_dotenv("../../../.azure/hhgai-dev-eastasia-002/.env")
    local = request.config.getoption("--local")
    url = "http://localhost:50505" if local else os.getenv("BACKEND_URI")
    yield url

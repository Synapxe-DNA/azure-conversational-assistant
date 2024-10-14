import asyncio
import io
import json
import os

import pytest
import pytest_asyncio
import websockets
from pydub import AudioSegment

"""
File paths
"""
english_query = "backend/test/audio_test_files/english_query.mp3"
chinese_query = "backend/test/audio_test_files/chinese_query.mp3"
malay_query = "backend/test/audio_test_files/malay_query.mp3"
tamil_query = "backend/test/audio_test_files/tamil_query.mp3"

"""
Response file path
"""

RESPONSE_FOLDER_PATH = "backend/test/responses/transcription/"


@pytest_asyncio.fixture
async def transcription_endpointURL(request, endpointURL):
    """
    URL for transcription endpoint
    """

    if endpointURL.startswith("http://"):
        ws_endpointURL = endpointURL.replace("http://", "ws://")
    else:
        ws_endpointURL = endpointURL.replace("https://", "wss://")

    yield f"{ws_endpointURL}/ws/transcribe"


@pytest.mark.asyncio
async def test_english_query(transcription_endpointURL, endpointURL):
    """
    Test transcription endpoint with english query
    """

    await send_audio_file(english_query, transcription_endpointURL, endpointURL)


@pytest.mark.asyncio
async def test_chinese_query(transcription_endpointURL, endpointURL):
    """
    Test transcription endpoint with chinese query
    """

    await send_audio_file(chinese_query, transcription_endpointURL, endpointURL)


@pytest.mark.asyncio
async def test_malay_query(transcription_endpointURL, endpointURL):
    """
    Test transcription endpoint with malay query
    """

    await send_audio_file(malay_query, transcription_endpointURL, endpointURL)


@pytest.mark.asyncio
async def test_tamil_query(transcription_endpointURL, endpointURL):
    """
    Test transcription endpoint with tamil query
    """

    await send_audio_file(tamil_query, transcription_endpointURL, endpointURL)


async def convert_mp3_to_pcm(mp3_file_path):
    audio = AudioSegment.from_mp3(mp3_file_path)

    # Set the sample width to 2 bytes (16 bits)
    audio = audio.set_sample_width(2)

    # Export the audio to an in-memory buffer
    pcm_buffer = io.BytesIO()
    audio.export(pcm_buffer, format="raw")

    return pcm_buffer.getvalue()


async def send_audio_file(audio_file_path, transcription_endpointURL, endpointURL):
    if not os.path.exists(RESPONSE_FOLDER_PATH):
        try:
            os.makedirs(RESPONSE_FOLDER_PATH)
        except Exception:
            pass  # Directory already created by another test

    response_file_path = os.path.join(RESPONSE_FOLDER_PATH, os.path.basename(audio_file_path).replace(".mp3", ".txt"))

    state = {"is_final": False, "completed": False}
    pcm_data = await convert_mp3_to_pcm(audio_file_path)

    with open(response_file_path, "w") as f:
        f.write("")  # Clear the file

    async with websockets.connect(transcription_endpointURL, origin=endpointURL) as websocket:
        print("Websocket connection open")
        # Create tasks for each function
        receive_task = asyncio.create_task(on_message(websocket, state, response_file_path))
        send_task = asyncio.create_task(send_messages(websocket, state, pcm_data))
        check_task = asyncio.create_task(check_and_close(websocket, state))

        # Wait for the tasks to complete
        await asyncio.gather(receive_task, send_task, check_task)


async def check_and_close(websocket, state, timeout=60):
    try:
        await asyncio.wait_for(_check_and_close(websocket, state), timeout)
    except asyncio.TimeoutError:
        pytest.fail("Transcription took too long to complete")


async def _check_and_close(websocket, state):
    while True:
        await asyncio.sleep(1)  # Check every second
        if state["completed"] and state["is_final"]:
            await websocket.close()
            print("WebSocket connection closed.")
            break


async def on_message(websocket, state, response_file_path):
    while True:
        try:
            message = await websocket.recv()
            json_message = json.loads(message)
            print(f"Message received: {json_message}")
            state["is_final"] = json_message["is_final"]
            with open(response_file_path, "a") as f:
                json.dump(json_message, f, ensure_ascii=False)
                f.write("\n")
        except websockets.exceptions.ConnectionClosed:
            break


async def send_messages(websocket, state, pcm_data):
    chunk_size = 1024
    for i in range(0, len(pcm_data), chunk_size):
        chunk = pcm_data[i : i + chunk_size]
        await websocket.send(chunk)
        await asyncio.sleep(0.01)  # to simulate real-time audio streaming
    # await websocket.send(pcm_data)
    await websocket.send("completed")
    state["completed"] = True

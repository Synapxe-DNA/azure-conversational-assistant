import asyncio
import logging
import queue

import azure.cognitiveservices.speech as speechsdk
from config import CONFIG_SPEECH_TO_TEXT_SERVICE
from quart import Blueprint, current_app, websocket

transcription = Blueprint("transcription", __name__, url_prefix="/ws")


@transcription.websocket("/transcribe")
async def ws_transcribe():
    asyncio.get_running_loop().slow_callback_duration = 1

    # create stt object and get recognizer and stream
    stt = current_app.config[CONFIG_SPEECH_TO_TEXT_SERVICE]
    recognizer: speechsdk.SpeechRecognizer = stt.getSpeechRecognizer()
    stream = stt.getStream()

    # Start continuous recognition
    recognizer.start_continuous_recognition_async()

    # Function to handle sending results
    async def send_results():
        while True:
            try:
                result = stt.getQueue().get(timeout=0.1)
                logging.info(f"Sending result: {result}")
                await websocket.send_json(result)
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logging.error(f"Error sending result: {e}")
                break

    # Start the result sending task
    send_task = asyncio.create_task(send_results())

    try:
        while True:
            data = await websocket.receive()
            stream.write(data)
    except asyncio.CancelledError:
        # Handle WebSocket disconnection
        logging.info("WebSocket connection closed")
    finally:
        recognizer.stop_continuous_recognition_async()
        send_task.cancel()
        try:
            await send_task  # Wait for the task to be cancelled
        except asyncio.CancelledError:
            pass  # Task was cancelled successfully
        stt.reset()

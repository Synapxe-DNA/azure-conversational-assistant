import asyncio
import logging
import queue

from quart import Blueprint, websocket
from speech.speech_to_text import SpeechToText

transcription = Blueprint("transcription", __name__, url_prefix="/ws")


@transcription.websocket("/transcribe")
async def ws_transcribe():
    asyncio.get_running_loop().slow_callback_duration = 1

    # Set up queue for communication between threads
    result_queue = queue.Queue()

    # create stt object and get recognizer and speech
    stt = await SpeechToText.create()
    recognizer = stt.getSpeechRecognizer()
    stream = stt.getStream()

    # Set up callbacks
    def recognizing_cb(evt):
        logging.info(f"Recognizing: {evt.result.text}")
        result_queue.put({"text": evt.result.text, "is_final": False})

    def recognized_cb(evt):
        logging.info(f"Recognized: {evt.result.text}")
        result_queue.put({"text": evt.result.text, "is_final": True})

    def canceled_cb(evt):
        logging.warning(f"Recognition canceled: {evt.result.reason}")
        result_queue.put({"error": f"Recognition canceled: {evt.result.reason}"})

    # Connect callbacks
    recognizer.recognizing.connect(recognizing_cb)
    recognizer.recognized.connect(recognized_cb)
    recognizer.canceled.connect(canceled_cb)

    # Start continuous recognition
    recognizer.start_continuous_recognition()

    # Function to handle sending results
    async def send_results():
        while True:
            try:
                result = result_queue.get(timeout=0.1)
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
        recognizer.stop_continuous_recognition()
        send_task.cancel()
        try:
            await send_task  # Wait for the task to be cancelled
        except asyncio.CancelledError:
            pass  # Task was cancelled successfully
        stream.close()

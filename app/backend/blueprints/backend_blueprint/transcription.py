import asyncio
import logging
import queue
import signal

from config import CONFIG_SPEECH_TO_TEXT_SERVICE
from quart import Blueprint, current_app, websocket

transcription = Blueprint("transcription", __name__, url_prefix="/ws")


@transcription.websocket("/transcribe")
async def ws_transcribe():
    logging.info("Websocket connection open")

    asyncio.get_running_loop().slow_callback_duration = 1

    # create stt object
    stt = current_app.config[CONFIG_SPEECH_TO_TEXT_SERVICE]
    start_transcription = False
    send_task = None

    # Function to handle sending results
    async def send_results():
        while True:
            try:
                result = stt.getQueue().get(timeout=0.1)
                await websocket.send_json(result)
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logging.error(f"Error sending result: {e}")
                break

    async def stop_transcription():
        nonlocal start_transcription
        nonlocal send_task

        stt.getSpeechRecognizer().stop_continuous_recognition_async()
        if send_task is not None:
            send_task.cancel()
            try:
                await send_task  # Wait for the task to be cancelled
            except asyncio.CancelledError:
                send_task = None
        stt.reset()
        start_transcription = False
        logging.info("Transcribed audio successfully")

    def handler(signum, frame):
        loop = asyncio.get_event_loop()
        for task in asyncio.all_tasks(loop):
            task.cancel()

    # Set the signal handler for local development
    signal.signal(signal.SIGINT, handler)

    try:
        while True:
            data = await asyncio.wait_for(websocket.receive(), timeout=1800)  # 30 minutes timeout
            if not start_transcription:
                logging.info("Starting transcription")
                send_task = asyncio.create_task(send_results())  # Start the result sending task
                stt.getSpeechRecognizer().start_continuous_recognition_async()
                start_transcription = True

            if isinstance(data, str) and data == "completed":  # wait for frontend to send completed message
                while not stt.finished_recognising:
                    stt.getStream().write(b"")  # empty bytes needed to trigger recognition if audio too short
                while not stt.getQueue().empty():  # Ensure all results are sent before stopping transcription
                    await asyncio.sleep(0.1)
                await stop_transcription()
                continue
            stt.getStream().write(data)
    except asyncio.TimeoutError:
        logging.info("WebSocket connection timed out")
    except asyncio.CancelledError:
        logging.info("WebSocket connection closed")
    finally:
        await websocket.close(1000)
        await stop_transcription()

# recording.py
import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import io
import requests
import traceback
import RPi.GPIO as GPIO
import time
import openai

def callback(indata, frames, time_, status, audio_queue):
    """
    Callback for sounddevice; puts audio data into a queue.
    """
    audio_queue.put(indata.copy())

def record_audio_while_button_held(button_pin=17, samplerate=44100):
    """
    Records audio while the given GPIO pin is LOW (button pressed),
    and stops once the button is released.
    Returns a NumPy array of the recorded audio data, or None if no audio was captured.
    """

    # Clear any leftover data
    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time_, status):
        callback(indata, frames, time_, status, audio_queue)

    # Start recording
    stream = sd.InputStream(
        samplerate=samplerate,
        channels=1,
        callback=audio_callback
    )
    stream.start()
    print("Recording... (press and hold the button)")

    # Wait until button goes HIGH again
    while GPIO.input(button_pin) == GPIO.LOW:
        time.sleep(0.01)

    # Stop and close stream
    stream.stop()
    stream.close()
    print("Recording stopped.")

    # Gather frames from the queue
    frames = []
    while not audio_queue.empty():
        frames.append(audio_queue.get())

    if not frames:
        return None

    return np.concatenate(frames, axis=0)

def process_with_whisper(audio_data, samplerate=44100):
    """
    Sends audio data to OpenAI's Whisper API and returns the transcribed text.
    """
    if audio_data is None:
        return None

    try:
        buffer = io.BytesIO()
        buffer.name = 'audio.wav'
        sf.write(buffer, audio_data, samplerate, format='wav')
        buffer.seek(0)

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {openai.api_key}"}
        files = {
            "file": ("audio.wav", buffer, "audio/wav")
        }
        data = {
            "model": "whisper-1",
            "language": "en"  # Explicitly specify English
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()

        transcript = response.json()
        return transcript['text']

    except Exception as e:
        print("An error occurred during transcription:")
        traceback.print_exc()
        return None

import io
import traceback
import requests
import soundfile as sf
import openai

def callback(indata, q):
    """
    Callback for sounddevice; puts audio data into the queue.
    """
    q.put(indata.copy())

def process_with_whisper(audio_data, samplerate):
    """
    Sends the audio data to OpenAI's Whisper API for transcription.
    """
    try:
        buffer = io.BytesIO()
        buffer.name = 'audio.wav'
        sf.write(buffer, audio_data, samplerate, format='wav')
        buffer.seek(0)

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
        }
        files = {
            "file": ("audio.wav", buffer, "audio/wav"),
        }
        data = {
            "model": "whisper-1",
            "language": "en",
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()

        transcript = response.json()
        return transcript['text']

    except Exception as e:
        print("An error occurred during transcription:")
        traceback.print_exc()
        return None

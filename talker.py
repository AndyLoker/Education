import requests
from pydub import AudioSegment
from pydub.playback import play
import APIkey

CHUNK_SIZE = 1024

def talk(text):
    """
    Converts text to speech using the ElevenLabs TTS API 
    and plays the MP3 output using pydub.
    """
    # Your ElevenLabs Voice ID
    voice_id = "2YnMdqKVHlbWxi6e6hz9"  
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": APIkey.Elevenlabs
    }

    data = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "language_code": "en",  
        "voice_settings": {
            "stability": 1,
            "similarity_boost": 0.5
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers, stream=True)
        response.raise_for_status()

        audio_file = "output.mp3"
        with open(audio_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        sound = AudioSegment.from_mp3(audio_file)
        play(sound)

    except requests.RequestException as e:
        print(f"Error during ElevenLabs TTS request: {e}")

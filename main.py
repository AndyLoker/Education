import time
import queue
import numpy as np
import sounddevice as sd
from pynput import keyboard
import traceback

from recording import callback, process_with_whisper
from threads_handler import process_user_input

# Global variables
q = queue.Queue()
recording_stream = None
samplerate = 44100  # or 16000 if you want to reduce bandwidth

def on_press(key):
    global recording_stream
    if key == keyboard.Key.space and recording_stream is None:
        print('Space pressed, starting recording.')
        q.queue.clear()
        recording_stream = sd.InputStream(
            callback=lambda indata, frames, time_, status: callback(indata, q),
            samplerate=samplerate,
            channels=1
        )
        try:
            recording_stream.start()
        except Exception as e:
            print("An error occurred while starting the recording:")
            traceback.print_exc()
            recording_stream = None

def on_release(key):
    global recording_stream
    if key == keyboard.Key.space and recording_stream is not None:
        print('Space released, stopping recording.')
        try:
            recording_stream.stop()
            recording_stream.close()
            recording_stream = None

            frames = []
            while not q.empty():
                frames.append(q.get())

            if frames:
                audio_data = np.concatenate(frames, axis=0)
                print('Transcribing audio with Whisper...')
                user_input = process_with_whisper(audio_data, samplerate)
                if user_input:
                    print('Transcribed text:', user_input)
                    process_user_input(user_input)
                else:
                    print('No text transcribed.')
            else:
                print('No audio data recorded.')
        except Exception as e:
            print("Error during recording or processing:")
            traceback.print_exc()
            recording_stream = None

def main():
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except Exception as e:
        print("An error occurred in the main loop:")
        traceback.print_exc()
    finally:
        if recording_stream is not None:
            recording_stream.stop()
            recording_stream.close()

if __name__ == "__main__":
    main()

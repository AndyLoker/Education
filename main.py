# main.py
import threading
import RPi.GPIO as GPIO
import time
import openai

# Our existing modules
import recording
from threads_handler import process_user_input

BUTTON_PIN = 17  # BCM pin where the button is connected

running = True   # Global flag to let the button thread run

def init_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button_thread():
    """
    This thread waits for the button to be pressed. When pressed, record audio
    until released, then transcribe and process the input.
    """
    while running:
        # Poll if button is pressed
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            # Record voice until user releases button
            audio_data = recording.record_audio_while_button_held(BUTTON_PIN)
            user_input = recording.process_with_whisper(audio_data)
            if user_input:
                print(f"\n[VOICE INPUT] {user_input}")
                process_user_input(user_input)
        # Sleep a bit so we don't hammer the CPU
        time.sleep(0.1)

def main():
    global running
    init_gpio()

    # Start the button thread
    t = threading.Thread(target=button_thread, daemon=True)
    t.start()

    print("System ready! Press the button for voice input, or type a request below.")
    print("Type 'quit' to end the program.")

    try:
        while True:
            typed = input("Type request: ").strip()
            if typed.lower() == "quit":
                running = False
                break
            elif typed:
                # Send typed input to the AI
                process_user_input(typed)
            else:
                # If user just pressed Enter without typing,
                # do nothing (or you could do something else).
                pass

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt, exiting...")

    finally:
        running = False
        GPIO.cleanup()
        print("Goodbye.")

if __name__ == "__main__":
    main()

import lgpio
import time
import threading
import openai

import recording
from threads_handler import process_user_input

BUTTON_PIN = 17  # BCM pin
running = True

def init_lgpio():
    """
    Opens /dev/gpiochip0 and configures BUTTON_PIN as input with internal pull-up.
    Returns a handle to the gpiochip.
    """
    # Open the default gpiochip (gpiochip0)
    h = lgpio.gpiochip_open(0)
    # Claim the line as input
    lgpio.gpio_claim_input(h, BUTTON_PIN)
    # Enable pull-up on that line
    lgpio.gpio_set_pull_up_down(h, BUTTON_PIN, lgpio.LG_BB_UP)
    return h

def button_thread(gpio_handle):
    """
    Monitors BUTTON_PIN: when it goes LOW, start recording.
    When it goes HIGH again, stop recording.
    """
    global running
    is_recording = False
    stream = None
    audio_queue = None

    while running:
        val = lgpio.gpio_read(gpio_handle, BUTTON_PIN)
        
        if val == 0 and not is_recording:
            # Button just pressed => start recording
            print("Button pressed. Starting recording...")
            stream, audio_queue = recording.start_recording()
            is_recording = True

        elif val == 1 and is_recording:
            # Button released => stop recording
            print("Button released. Stopping recording...")
            audio_data = recording.stop_recording(stream, audio_queue)
            is_recording = False
            stream = None
            audio_queue = None

            # Transcribe with Whisper
            user_input = recording.process_with_whisper(audio_data)
            if user_input:
                print(f"[VOICE INPUT] {user_input}")
                # Send to AI
                process_user_input(user_input)

        time.sleep(0.05)  # short poll interval

def main():
    global running
    gpio_handle = init_lgpio()

    # Start the button thread
    t = threading.Thread(target=button_thread, args=(gpio_handle,), daemon=True)
    t.start()

    print("System ready! Press and hold the button for voice input.")
    print("Type a request for the AI below. Type 'quit' to exit.")

    try:
        while True:
            typed = input("Type request: ").strip()
            if typed.lower() == "quit":
                running = False
                break
            elif typed:
                process_user_input(typed)
            else:
                pass
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt, exiting.")
    finally:
        running = False
        lgpio.gpiochip_close(gpio_handle)
        print("Goodbye.")

if __name__ == "__main__":
    main()

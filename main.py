import lgpio
import time
import threading

import recording
from threads_handler import process_user_input

BUTTON_PIN = 17  # BCM pin for your pull-down circuit
running = True   # global flag to stop threads

def init_lgpio():
    """
    Opens /dev/gpiochip0 and claims BUTTON_PIN as input.
    No software pull is used, because we have a physical pull-down resistor.
    """
    h = lgpio.gpiochip_open(0)
    # Claim the line as input; no internal pull needed
    lgpio.gpio_claim_input(h, BUTTON_PIN)
    return h

def button_thread(gpio_handle):
    """
    Monitors BUTTON_PIN. When it reads HIGH (1), start recording.
    When it goes LOW (0) again, stop recording.
    """
    global running
    is_recording = False
    stream = None
    audio_queue = None

    while running:
        val = lgpio.gpio_read(gpio_handle, BUTTON_PIN)

        if val == 1 and not is_recording:
            # Button is pressed => start recording
            print("Button pressed -> start recording")
            stream, audio_queue = recording.start_recording()
            is_recording = True

        elif val == 0 and is_recording:
            # Button is released => stop recording
            print("Button released -> stop recording")
            audio_data = recording.stop_recording(stream, audio_queue)
            is_recording = False
            stream = None
            audio_queue = None

            # Transcribe with Whisper
            user_input = recording.process_with_whisper(audio_data)
            if user_input:
                print(f"[VOICE INPUT] {user_input}")
                process_user_input(user_input)

        time.sleep(0.05)  # Short polling interval

def main():
    global running
    gpio_handle = init_lgpio()

    # Start the button thread
    t = threading.Thread(target=button_thread, args=(gpio_handle,), daemon=True)
    t.start()

    print("System ready!")
    print("Press and hold the button (GPIO17) to record; release to stop.")
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
                # user pressed Enter without typing
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

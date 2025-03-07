import lgpio
import time
import threading

import recording
from threads_handler import process_user_input

# Our new Arduino code
import arduino_com

BUTTON_PIN = 17       # for voice recording
RESET_BUTTON_GPIO = 22
RESUME_BUTTON_GPIO = 27

running = True

def init_lgpio():
    """
    Claims pins for:
     - Voice recording: BUTTON_PIN
     - Reset button: RESET_BUTTON_GPIO
     - Resume button: RESUME_BUTTON_GPIO
    (We won't do fancy threads for them unless you want physical pressing for 'r' or 'c'.)
    """
    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_input(h, BUTTON_PIN)
    lgpio.gpio_claim_input(h, RESET_BUTTON_GPIO)
    lgpio.gpio_claim_input(h, RESUME_BUTTON_GPIO)
    return h

def button_thread(gpio_handle):
    """
    Voice button logic on GPIO17: pressed = record, released = stop.
    """
    global running
    is_recording = False
    stream = None
    audio_queue = None

    while running:
        val = lgpio.gpio_read(gpio_handle, BUTTON_PIN)
        if val == 1 and not is_recording:
            print("Voice Button pressed -> start recording")
            stream, audio_queue = recording.start_recording()
            is_recording = True
        elif val == 0 and is_recording:
            print("Voice Button released -> stop recording")
            audio_data = recording.stop_recording(stream, audio_queue)
            is_recording = False
            stream = None
            audio_queue = None

            # Transcribe
            user_input = recording.process_with_whisper(audio_data)
            if user_input:
                print(f"[VOICE INPUT] {user_input}")
                process_user_input(user_input)

        time.sleep(0.05)

def main():
    global running
    gpio_handle = init_lgpio()

    # Start voice-recording thread
    t_voice = threading.Thread(target=button_thread, args=(gpio_handle,), daemon=True)
    t_voice.start()

    print("System ready!")
    print("Press/hold voice button on GPIO17 to record. Type 'quit' to exit.")
    print("You can also type '#clean2', 'r' / 'c', or a normal AI request.")
    try:
        while True:
            typed = input("Type request / command: ").strip().lower()
            if typed == "quit":
                running = False
                break
            elif not typed:
                continue

            # If user typed r/c => call Arduino reset/resume
            if typed in ["r", "reset"]:
                print("Sending reset (r) to Arduino.")
                arduino_com.send_reset()
            elif typed in ["c", "resume"]:
                print("Sending resume (c) to Arduino.")
                arduino_com.send_resume()
            elif typed.startswith("#clean"):
                # e.g. "#clean2"
                pump_str = typed[6:].strip()
                if pump_str.isdigit():
                    arduino_com.send_clean(pump_str)
                else:
                    print("Invalid cleaning command. E.g. '#clean2'")
            else:
                # Otherwise treat typed as an AI request
                process_user_input(typed)

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt, exiting.")
    finally:
        running = False
        lgpio.gpiochip_close(gpio_handle)
        print("Goodbye.")

if __name__ == "__main__":
    main()

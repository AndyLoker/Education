import lgpio
import time
import threading

import recording
from threads_handler import process_user_input
import arduino_com  # For send_reset, send_resume, send_clean, etc.

# Pin assignments
VOICE_PIN = 17        # For voice recording
RESET_PIN = 22        # Physical reset button for Arduino
RESUME_PIN = 27       # Physical resume button for Arduino

running = True  # Global flag to stop the polling threads

def init_lgpio():
    """
    Opens gpiochip0 and claims the three input pins:
      - VOICE_PIN (recording)
      - RESET_PIN (arduino reset)
      - RESUME_PIN (arduino resume)
    No internal pulls by default (assuming external resistors).
    """
    h = lgpio.gpiochip_open(0)
    # Voice button
    lgpio.gpio_claim_input(h, VOICE_PIN)
    # Reset button
    lgpio.gpio_claim_input(h, RESET_PIN)
    # Resume button
    lgpio.gpio_claim_input(h, RESUME_PIN)
    return h

def voice_thread(gpio_handle):
    """
    Continuously polls the VOICE_PIN (GPIO17).
    Pressed (HIGH=1) => start recording, Released (LOW=0) => stop and transcribe.
    """
    global running
    is_recording = False
    stream = None
    audio_queue = None

    while running:
        val = lgpio.gpio_read(gpio_handle, VOICE_PIN)

        if val == 1 and not is_recording:
            print("Voice button pressed -> start recording")
            stream, audio_queue = recording.start_recording()
            is_recording = True

        elif val == 0 and is_recording:
            print("Voice button released -> stop recording")
            audio_data = recording.stop_recording(stream, audio_queue)
            is_recording = False
            stream = None
            audio_queue = None

            # Transcribe with Whisper
            user_input = recording.process_with_whisper(audio_data)
            if user_input:
                print(f"[VOICE INPUT] {user_input}")
                process_user_input(user_input)

        time.sleep(0.05)

def reset_resume_thread(gpio_handle):
    """
    Continuously polls RESET_PIN and RESUME_PIN.
    If RESET_PIN goes HIGH => call arduino_com.send_reset()
    If RESUME_PIN goes HIGH => call arduino_com.send_resume()
    """
    global running
    was_reset_pressed = False
    was_resume_pressed = False

    while running:
        val_reset = lgpio.gpio_read(gpio_handle, RESET_PIN)
        val_resume = lgpio.gpio_read(gpio_handle, RESUME_PIN)

        # Rising edge on reset pin
        if val_reset == 1 and not was_reset_pressed:
            print("Physical RESET pressed -> sending 'r' to Arduino")
            arduino_com.send_reset()
        was_reset_pressed = (val_reset == 1)

        # Rising edge on resume pin
        if val_resume == 1 and not was_resume_pressed:
            print("Physical RESUME pressed -> sending 'c' to Arduino")
            arduino_com.send_resume()
        was_resume_pressed = (val_resume == 1)

        time.sleep(0.05)

def main():
    global running
    gpio_handle = init_lgpio()

    # Start the voice-recording thread
    t_voice = threading.Thread(target=voice_thread, args=(gpio_handle,), daemon=True)
    t_voice.start()

    # Start the reset/resume thread
    t_rr = threading.Thread(target=reset_resume_thread, args=(gpio_handle,), daemon=True)
    t_rr.start()

    print("System ready!")
    print("Voice recording button: GPIO17.")
    print("Arduino reset button: GPIO22, resume button: GPIO27.")
    print("Type 'quit' to exit, #cleanN to clean a pump, r/c for manual reset/resume, or any other text for AI.")

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
                print("Manual reset command -> sending 'r'")
                arduino_com.send_reset()
            elif typed in ["c", "resume"]:
                print("Manual resume command -> sending 'c'")
                arduino_com.send_resume()
            elif typed.startswith("#clean"):
                # e.g. '#clean2'
                pump_str = typed[6:].strip()
                if pump_str.isdigit():
                    arduino_com.send_clean(pump_str)
                else:
                    print("Invalid cleaning command. Example: #clean2")
            else:
                # Otherwise treat typed as an AI request
                process_user_input(typed)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("KeyboardInterrupt -> exiting.")
    finally:
        running = False
        lgpio.gpiochip_close(gpio_handle)
        print("Goodbye.")

if __name__ == "__main__":
    main()

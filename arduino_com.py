import serial
import time

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
DEFAULT_TIMEOUT = 1

# One "unit" = 25 grams
GRAMS_PER_UNIT = 25

# Map each ingredient name to a pump number
INGREDIENT_TO_PUMP = {
    "Tequila": 1,
    "Whiskey": 2,
    "Lime Juice": 3,
    "Tonic Water": 4
}

def open_serial():
    """
    Opens the serial port, returns a serial object or None on failure.
    """
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=DEFAULT_TIMEOUT)
        time.sleep(2)  # let Arduino reset
        print(f"✅ Connected to Arduino on {SERIAL_PORT} at {BAUD_RATE} baud.")
        return ser
    except Exception as e:
        print("❌ Could not open serial port:", e)
        return None

def close_serial(ser):
    """Closes the serial connection."""
    if ser:
        ser.close()
        print("🔌 Serial connection closed.")

def send_command(cmd):
    """
    Opens serial, sends 'cmd', reads quick response, closes serial.
    Used for short commands like 'r', 'c', '#clean2'.
    """
    ser = open_serial()
    if not ser:
        print("⚠️ No serial connection. Skipping command.")
        return
    try:
        ser.write((cmd + "\n").encode('utf-8'))
        print(f"📤 Sent: {cmd}")
        time.sleep(0.5)
        # read immediate response
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                print("Arduino:", line)
    finally:
        close_serial(ser)

def send_clean(pump_number):
    """Send cleaning command, e.g. '#clean2'."""
    cmd = f"#clean{pump_number}"
    send_command(cmd)

def send_reset():
    """Sends 'reset' to reset an alarm."""
    send_command("reset")

def send_resume():
    """Sends 'resume' to resume after alarm."""
    send_command("resume")

def fill_drink_from_tags(tags_dict):
    """
    Takes a dictionary like {"Gin": 2, "Vodka": 1} each unit=25g.
    Sends each pump command sequentially, waiting for "DISPENSE_COMPLETE".
    If "EMERGENCY PRESSED" arrives from Arduino, aborts the entire dispensing process.
    """
    ser = open_serial()
    if not ser:
        print("⚠️ Cannot dispense: no serial connection.")
        return

    try:
        emergency_stop = False  # Flag to indicate we saw "EMERGENCY PRESSED"

        for ingredient, units in tags_dict.items():
            if emergency_stop:
                print("⚠️ Already in emergency stop, skipping remaining ingredients.")
                break

            pump_num = INGREDIENT_TO_PUMP.get(ingredient)
            if pump_num is None:
                print(f"⚠️ Unknown ingredient '{ingredient}'. Skipping.")
                continue

            grams = units * GRAMS_PER_UNIT
            command = f"{pump_num}w{grams}"
            print(f"Dispensing {grams}g of {ingredient} (units={units}) -> {command}")

            # Send the command
            ser.write((command + "\n").encode('utf-8'))
            time.sleep(0.2)  # Short delay so Arduino starts

            dispensing_done = False
            last_line_time = time.time()

            while not dispensing_done:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    print("Arduino:", line)
                    last_line_time = time.time()  # Reset no-data timer

                    # Check for normal completion
                    if "DISPENSE_COMPLETE" in line:
                        dispensing_done = True

                    # Check for emergency
                    if "EMERGENCY PRESSED" in line:
                        print("🚨 EMERGENCY STOP triggered! Aborting dispensing.")
                        emergency_stop = True
                        break
                else:
                    # No line; small sleep, then check if 10s have passed, for example
                    time.sleep(0.1)
                    if time.time() - last_line_time > 10:
                        print("⚠️ Timeout waiting for Arduino data (10s). Moving on.")
                        break  # Move on to next ingredient or end

            if emergency_stop:
                print("⚠️ Emergency stop: skipping remaining ingredients.")
                break

            if dispensing_done:
                print(f"✅ Finished dispensing {ingredient}.\n")
            else:
                print(f"⚠️ Did not get DISPENSE_COMPLETE for {ingredient}. Moving on.\n")

        if emergency_stop:
            print("🚨 Dispensing process ended prematurely due to EMERGENCY.")
        else:
            print("✅ All requested ingredients processed (no emergency triggered).")

    finally:
        close_serial(ser)

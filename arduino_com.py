import serial
import time

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
DEFAULT_TIMEOUT = 1

# One "unit" = 25 grams
GRAMS_PER_UNIT = 25

# Map each ingredient name to a pump number
INGREDIENT_TO_PUMP = {
    "Gin": 1,
    "Whiskey": 2,
    "Rum": 3,
    "Tequila": 4,
    "Vodka": 5,
    "Tonic Water": 6,
    "Club Soda": 7,
    "Ginger Beer": 8,
    "Cola": 9,
    "Lemon Juice": 10
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
    """Sends 'r' to reset an alarm."""
    send_command("r")

def send_resume():
    """Sends 'c' to resume after alarm."""
    send_command("c")

def fill_drink_from_tags(tags_dict):
    """
    Takes a dict like {'Gin': 2, 'Vodka': 1} meaning 2 units of Gin, 1 of Vodka.
    1 unit = 25 grams. So 'Gin': 2 => 50g on the pump mapped to Gin in INGREDIENT_TO_PUMP.
    Then sends commands "pumpX w grams" in sequence.
    """
    ser = open_serial()
    if not ser:
        print("⚠️ Cannot dispense: no serial connection.")
        return

    try:
        for ingredient, units in tags_dict.items():
            pump_num = INGREDIENT_TO_PUMP.get(ingredient)
            if pump_num is None:
                print(f"⚠️ Unknown ingredient '{ingredient}'. Skipping.")
                continue

            grams = units * GRAMS_PER_UNIT
            command = f"{pump_num}w{grams}"
            print(f"Dispensing {grams}g of {ingredient} (units={units}) -> {command}")
            ser.write((command + "\n").encode('utf-8'))
            time.sleep(0.5)
            # Optionally read immediate response lines
            while ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    print("Arduino:", line)

        print("✅ All requested ingredients dispensed.")
    finally:
        close_serial(ser)

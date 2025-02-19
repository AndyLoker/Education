# arduino_com.py

import serial
import time

# ===== Serial Port Configuration =====
SERIAL_PORT = "/dev/ttyACM0"   # Adjust if your Arduino enumerates differently
BAUD_RATE = 9600

# One "unit" is 50 grams
GRAMS_PER_UNIT = 50

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

def initialize_serial():
    """
    Initializes the serial connection with Arduino.
    Returns the serial object or None if it fails.
    """
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Give Arduino time to reset
        print("✅ Connected to Arduino successfully.")
        return ser
    except serial.SerialException as e:
        print(f"❌ Connection error: {e}")
        return None

def send_command(ser, command):
    """
    Sends a command to the Arduino and reads the response.
    """
    if ser:
        ser.write((command + "\n").encode())
        print(f"📤 Sent: {command}")
        time.sleep(0.5)
        return read_response(ser)
    else:
        print("⚠️ No active connection.")
        return None

def read_response(ser):
    """
    Reads responses from the Arduino and handles any alarms or completion messages.
    """
    responses = []
    while ser.in_waiting > 0:
        response = ser.readline().decode().strip()
        if response:
            print(f"📥 Received: {response}")
            responses.append(response)

            if "⚠️ ERROR" in response:
                print("🚨 ALARM! Check hardware or code on Arduino.")
            elif "✅ DISPENSE_COMPLETE" in response:
                print("✅ Dispensing completed.")

    return responses

def start_dispensing(ser, pump_number, grams):
    """
    Starts dispensing from the specified pump with the given weight (grams).
    """
    print("⚖️ Taring scale before dispensing...")
    send_command(ser, "cal")  # Tare the scale before each dispense
    time.sleep(2)

    print("⚖️ Scale after taring: 0 g")

    print(f"🚰 Starting dispense of {grams} g on pump {pump_number}...")
    command = f"{pump_number}w{grams}"
    send_command(ser, command)

    monitor_dispensing(ser)

def monitor_dispensing(ser):
    """
    Monitors dispensing in real-time, checking for weight changes and completion.
    Example serial messages from Arduino might include:
      "⚖️ Current Weight: <number> g"
      "✅ DISPENSE_COMPLETE"
    """
    start_time = time.time()
    last_weight = None

    while True:
        time.sleep(1)  # Check weight every 1 second
        responses = read_response(ser)
        for response in responses:
            if "⚖️ Current Weight:" in response:
                try:
                    # Example format: "⚖️ Current Weight: 25 g"
                    weight_value = int(response.split(":")[1].strip().split(" ")[0])
                    print(f"⚖️ Current weight: {weight_value} g")

                    # Check whether weight has changed (error detection)
                    if last_weight is not None and abs(weight_value - last_weight) < 2:
                        # If weight hasn't changed for >= 2 seconds, consider an error
                        if time.time() - start_time >= 2:
                            print("🚨 Error: No weight change! Check fluid level or pump.")
                            return
                    else:
                        # Reset the timer if weight is changing
                        start_time = time.time()

                    last_weight = weight_value

                except ValueError:
                    print("⚠️ Weight read error – invalid format!")

            if "✅ DISPENSE_COMPLETE" in response:
                print("✅ Dispensing process finished.")
                return

def fill_drink_from_tags(ser, tags_dict):
    """
    Takes a dictionary of { 'IngredientName': number_of_units, ... }
    and dispenses each ingredient in sequence, where each unit = 50 grams.
    
    Example usage:
        tags_dict = { 'Gin': 2, 'Vodka': 1 }
        This means 2 units of Gin -> 2*50=100g, 1 unit of Vodka -> 50g.
    """
    for ingredient, units in tags_dict.items():
        pump_number = INGREDIENT_TO_PUMP.get(ingredient)
        if pump_number is None:
            print(f"⚠️ No pump assigned for {ingredient}, skipping.")
            continue

        grams_to_dispense = units * GRAMS_PER_UNIT
        print(f"Filling {grams_to_dispense} g of {ingredient} (units: {units}) via pump {pump_number}...")
        start_dispensing(ser, pump_number, grams_to_dispense)

def main():
    """
    Example usage: Initialize serial, dispense a sample drink, then close.
    """
    ser = initialize_serial()
    if not ser:
        return

    # Example: If AI said "Gin: 2, Vodka: 1"
    sample_tags = {
        "Gin": 2,
        "Vodka": 1
    }

    fill_drink_from_tags(ser, sample_tags)

    ser.close()
    print("🔌 Connection closed.")

if __name__ == "__main__":
    main()

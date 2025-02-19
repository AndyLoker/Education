import serial
import time

# ===== Serial Port Configuration =====
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

def initialize_serial():
    """
    Initializes the serial connection with Arduino.
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
    Reads responses from the Arduino and handles any alarms.
    """
    responses = []
    while ser.in_waiting > 0:
        response = ser.readline().decode().strip()
        if response:
            print(f"📥 Received: {response}")
            responses.append(response)

            if "⚠️ ERROR" in response:
                print("🚨 ALARM! Type 'r' to reset or 'c' to continue dispensing.")
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

                    # Check whether the weight has changed (error detection)
                    if last_weight is not None and abs(weight_value - last_weight) < 2:
                        # If weight hasn't changed in 2 seconds, assume an error
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

def reset_alarm(ser):
    """
    Resets an alarm state on Arduino.
    """
    print("🔄 Resetting alarm...")
    send_command(ser, "r")

def continue_dispensing(ser):
    """
    Continues dispensing after an alarm.
    """
    print("▶️ Continuing dispensing...")
    send_command(ser, "c")

def start_weight_display(ser):
    """
    Starts continuous weight display from Arduino.
    """
    print("⚖️ Starting weight display...")
    send_command(ser, "cal")

def stop_weight_display(ser):
    """
    Stops continuous weight display.
    """
    print("⏹️ Stopping weight display...")
    send_command(ser, "f")

def fill_drink_from_tags(ser, tags_dict):
    """
    Takes a dictionary of { 'IngredientName': amount_in_grams, ... }
    and dispenses each ingredient in sequence.

    Example:
        tags_dict = { 'Gin': 20, 'Vodka': 25 }
    You will need a mapping from ingredient name -> pump number in this function.
    """

    # For example, define which pump each ingredient uses:
    ingredient_to_pump = {
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

    # Go through each ingredient
    for ingredient, grams in tags_dict.items():
        # Find the correct pump number
        pump_number = ingredient_to_pump.get(ingredient, None)
        if pump_number is None:
            print(f"⚠️ No pump assigned for {ingredient}, skipping.")
            continue

        print(f"Filling {grams} g of {ingredient} via pump {pump_number}...")
        start_dispensing(ser, pump_number, grams)

def main():
    """
    Main control loop. 
    You can type commands or try out the fill_drink_from_tags() function.
    """
    ser = initialize_serial()
    if not ser:
        return

    while True:
        command = input("Enter a command (nwX=start, r=reset, c=continue, cal=weight, f=stop, q=quit, tags=demo): ").strip()

        if command.lower() == "q":
            print("🔌 Closing connection...")
            break
        elif command.lower() == "r":
            reset_alarm(ser)
        elif command.lower() == "c":
            continue_dispensing(ser)
        elif command.lower() == "cal":
            start_weight_display(ser)
        elif command.lower() == "f":
            stop_weight_display(ser)
        elif "w" in command:
            # For example, "1w50" means pump #1, 50 grams
            try:
                pump_number, weight = command.split("w")
                start_dispensing(ser, pump_number, int(weight))
            except ValueError:
                print("⚠️ Invalid format! Use <pump_number>w<grams>")
        elif command.lower() == "tags":
            # DEMO: Suppose we have some tags dict from the AI
            sample_tags = {
                "Gin": 15,
                "Vodka": 20
            }
            print("Demo: filling drink from sample tags:")
            fill_drink_from_tags(ser, sample_tags)

    ser.close()
    print("🔌 Connection closed.")

if __name__ == "__main__":
    main()

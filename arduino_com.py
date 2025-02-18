import time
import tags

# Try to import the serial module
try:
    import serial
except ImportError:
    print("Error: The 'serial' module is not installed. Install it using: pip install pyserial")
    exit()

# Define the serial port and baud rate
port = '/dev/ttyACM0'  # Change to the correct port, e.g., 'COM3' on Windows
baudrate = 115200

# Attempt to connect to the serial port
try:
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(2)  # Wait for the connection to initialize
    print(f"✅ Connected to Arduino on port {port}")
except serial.SerialException as e:
    print(f"❌ Connection error: {e}")
    ser = None  # Prevent errors if the connection fails
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    ser = None

# Function to send a command to Arduino
def send_command(command):
    if ser and ser.is_open:  # Check if the connection is active
        ser.write((command + '\n').encode())
        print(f"📤 Command sent: {command}")
    else:
        print("⚠️ No connection to Arduino.")

# Display user instructions
print("\n=== Ready to send command ===")
print("1 - Position 1")
print("2 - Position 2")
print("3 - Position 3")
print("4 - Position 4")
print("1wX - Valve 1 (X = grams)")
print("2wX - Valve 2 (X = grams)")
print("3wX - Valve 3 (X = grams)")
print("4wX - Valve 4 (X = grams)")
print("k - Return to home position (Homing)")
print("wk - Weight calibration")
print("q - Exit the program")


# User interaction loop
"""
Can you modify this function so it only asks for commands if the ingredients_used is updated (when the user has requested a drink)
"""
try:
    while True:

        command = input("\nEnter a command: ").strip()

        if command == 'q':
            print("🔴 Closing the program... ")
            break

        elif command in ['1', '2', '3', '4', 'k', 'wk']:
            send_command(command)
        elif len(command) > 1 and command[1] == 'w' and command[0] in ['1', '2', '3', '4']:
            send_command(command)
        else:
            print("⚠️ Invalid command. Please select one of the available options.")

except KeyboardInterrupt:
    print("\n🔌 Connection interrupted by the user.")

# Close the serial connection
if ser and ser.is_open:
    ser.close()
    print("✅ Connection closed.")

import serial
import time

ser = None

def open_serial(port="/dev/ttyACM0", baudrate=115200):
    """
    Opens the UART/serial port to communicate with the Arduino Uno via USB.
    :param port: default "/dev/ttyACM0" for Arduino Uno on many Linux systems
    :param baudrate: e.g. 115200
    """
    global ser
    ser = serial.Serial(port, baudrate, timeout=1)
    # Some Arduinos auto-reset on connect, so give it a moment
    time.sleep(2)

def close_serial():
    """
    Closes the serial port.
    """
    global ser
    if ser is not None:
        ser.close()
        ser = None

def send_ingredient(ingredient_id, quantity):
    """
    Sends a command to the Arduino to dispense a certain ingredient in a certain quantity.
    Format: "ING:<id>:<quantity>\\n"
    """
    if ser is None:
        raise RuntimeError("Serial port is not open. Call open_serial() first.")

    command_str = f"ING:{ingredient_id}:{quantity}\n"
    ser.write(command_str.encode("utf-8"))

def send_multiple_ingredients(ingredients_dict):
    """
    Sends multiple ingredients in succession.
    :param ingredients_dict: {ingredient_id: quantity, ...}
    """
    for ing_id, qty in ingredients_dict.items():
        send_ingredient(ing_id, qty)
        time.sleep(0.1)  # short delay between commands

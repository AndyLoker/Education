import serial
import time
import lgpio

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

# ----- Robot Arm Pins (Raspberry Pi) -----
# We'll use BCM numbering as an example
ARM_START_OUT = 23    # Output 1: signals robot to grab glass & move to fill position
ARM_DELIVER_OUT = 25  # Output 2: signals robot to deliver drink & return
ARM_READY_IN = 24     # Input: robot signals it's in position

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

def open_arm_gpio():
    """
    Opens the GPIO chip for the robot arm signals:
      - ARM_START_OUT, ARM_DELIVER_OUT as outputs,
      - ARM_READY_IN as input.
    Returns a handle to be used in fill_drink_from_tags().
    """
    h = lgpio.gpiochip_open(0)
    # Claim outputs
    lgpio.gpio_claim_output(h, ARM_START_OUT)
    lgpio.gpio_claim_output(h, ARM_DELIVER_OUT)
    # Claim input
    lgpio.gpio_claim_input(h, ARM_READY_IN)
    return h

def close_arm_gpio(h):
    """Closes the gpiochip handle."""
    lgpio.gpiochip_close(h)
    print("GPIO handle closed for robot arm signals.")

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
    1) Activates ARM_START_OUT to signal the robot arm to grab glass & move to fill position.
    2) Waits for ARM_READY_IN (from the robot) to be HIGH (1) or times out after 60s.
    3) Sequentially sends pump commands to Arduino:
       - For each ingredient, wait for "DISPENSE_COMPLETE" or "EMERGENCY PRESSED"
       - If "EMERGENCY PRESSED", break out entirely.
       - If no data for 10s, skip that ingredient and move on.
    4) When done, sets ARM_DELIVER_OUT HIGH to tell the robot to deliver the drink & return home.
    """

    # ---------- Step 1: Robot Arm "start" signal ----------
    gpio_handle = open_arm_gpio()
    # Set ARM_START_OUT = 1 (HIGH)
    lgpio.gpio_write(gpio_handle, ARM_START_OUT, 1)
    print("🤖 Signaling robot arm to grab glass & move to fill position...")

    # Wait up to 60s for ARM_READY_IN = 1
    arm_ready = False
    start_time = time.time()
    while time.time() - start_time < 60:
        val = lgpio.gpio_read(gpio_handle, ARM_READY_IN)
        if val == 1:
            arm_ready = True
            break
        time.sleep(0.1)

    if not arm_ready:
        print("⚠️ Robot arm did not signal ready within 60s. Aborting dispensing.")
        # Optionally set ARM_START_OUT low again if needed
        lgpio.gpio_write(gpio_handle, ARM_START_OUT, 0)
        close_arm_gpio(gpio_handle)
        return

    print("✅ Robot arm is in position. Proceeding with dispensing...")

    # ---------- Step 2: open serial to Arduino & do normal fill ----------
    ser = open_serial()
    if not ser:
        # If we can't open serial, we won't fill
        # (but maybe leave ARM_START_OUT=1 so the robot stays in place?)
        close_arm_gpio(gpio_handle)
        return

    emergency_stop = False

    try:
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

            ser.write((command + "\n").encode('utf-8'))
            time.sleep(0.2)  # short delay for Arduino

            dispensing_done = False
            last_line_time = time.time()

            while not dispensing_done:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    print("Arduino:", line)
                    last_line_time = time.time()

                    if "DISPENSE_COMPLETE" in line:
                        dispensing_done = True

                    if "EMERGENCY PRESSED" in line:
                        print("🚨 EMERGENCY STOP triggered! Aborting dispensing.")
                        emergency_stop = True
                        break
                else:
                    time.sleep(0.1)
                    if time.time() - last_line_time > 60:
                        print("⚠️ Timeout waiting for Arduino data (60s). Moving on.")
                        break  # skip to the next ingredient

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

    # ---------- Step 3: Signal the robot arm to deliver the drink ----------
    print("🤖 Signaling robot arm to deliver the drink & return home...")
    lgpio.gpio_write(gpio_handle, ARM_DELIVER_OUT, 1)
    # Optionally sleep or wait until arm finishes returning
    time.sleep(5)

    # If you want to reset outputs to 0, do so now
    lgpio.gpio_write(gpio_handle, ARM_START_OUT, 0)
    lgpio.gpio_write(gpio_handle, ARM_DELIVER_OUT, 0)

    close_arm_gpio(gpio_handle)
    print("✅ Robot arm signals complete.")
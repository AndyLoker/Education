import re
import interface

# Map each tag to a numeric ID the Arduino understands
# For example, "@10" => 10, etc. Adjust these as needed.
TAG_TO_INGREDIENT_ID = {
    "@10": 10,
    "@11": 11,
    "@12": 12,
    "@13": 13,
    "@14": 14,
    "@15": 15,
    "@16": 16,
    "@17": 17,
    "@18": 18,
    "@19": 19
}

def process_tags(answer):
    """
    Finds ingredient tags in 'answer' (e.g. "@10" repeated 2 times means 2 units),
    prints them, and sends them to the Arduino over serial.
    """
    # We'll collect total counts for each tag
    tag_counts = {}

    for tag, ing_id in TAG_TO_INGREDIENT_ID.items():
        count = answer.count(tag)
        if count > 0:
            tag_counts[tag] = count

    if not tag_counts:
        return  # No recognized tags, do nothing

    # Print them to the console for debug
    for tag, count in tag_counts.items():
        print(f"{tag} x {count}")

    # Now send to Arduino
    try:
        interface.open_serial()  # open the serial port (defaults to /dev/ttyACM0, 115200)
        # Build a dict {ing_id: count}, pass it to the new 'interface'
        ingredients_dict = {}
        for tag, cnt in tag_counts.items():
            ing_id = TAG_TO_INGREDIENT_ID[tag]
            ingredients_dict[ing_id] = cnt

        # Send them all
        interface.send_multiple_ingredients(ingredients_dict)

    finally:
        # Always close the serial port
        interface.close_serial()

import re
import pico_interface

# Map each tag to a numeric ID the Pico understands
# (for example, 10 => 'Gin', 11 => 'Whiskey', etc.)
TAG_TO_PICO_ID = {
    "@10": 10,   # or maybe 1, if you prefer smaller IDs
    "@11": 11,
    "@12": 12,
    "@13": 13,
    "@14": 14,
    "@15": 15,
    "@16": 16,
    "@17": 17,
    "@18": 18,
    "@19": 19,
}

def process_tags(answer):
    """
    Finds tags in 'answer' (e.g. "@10" repeated 2 times means 2 units of that ingredient),
    prints them, and then sends instructions to the Pico over UART.
    """
    # We'll collect the total number of each tag
    tag_counts = {}

    for tag, pico_id in TAG_TO_PICO_ID.items():
        count = answer.count(tag)
        if count > 0:
            tag_counts[tag] = count

    if not tag_counts:
        return  # No recognized tags

    # Print them in the console
    for tag, count in tag_counts.items():
        # Example: @10 => "Gin x 2"
        print(f"{tag} x {count}")

    # If we want to actually send to the Pico:
    try:
        pico_interface.open_serial()  # open UART
        # Build a dict { pico_id: count } that we pass to send_multiple_ingredients()
        ingredients_dict = {}
        for tag, count in tag_counts.items():
            pico_id = TAG_TO_PICO_ID[tag]
            ingredients_dict[pico_id] = count

        pico_interface.send_multiple_ingredients(ingredients_dict)
    finally:
        pico_interface.close_serial()

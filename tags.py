TAG_MAP = {
    "@10": "Tequila",
    "@11": "Whiskey",
    "@12": "Lime Juice",
    "@13": "Tonic Water"
}

def process_tags(answer):
 
    ingredients_used = {}

    for tag, name in TAG_MAP.items():
        count = answer.count(tag)
        if count > 0:
            # If multiple tags reference the same ingredient, you could accumulate here
            # e.g., ingredients_used[name] = ingredients_used.get(name, 0) + count
            ingredients_used[name] = count

    return ingredients_used

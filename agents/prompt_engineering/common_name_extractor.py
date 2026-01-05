import re

# ------------------------------------------------
# Extract single entity name from a sentence
# ------------------------------------------------
def extract_entity_name(text: str, entity_word: str):
    """
    Supports:
    - show <name> <entity>
    - view <entity> <name>
    - link risk <name> with control <name>
    - map process <name> to risk <name>
    """

    if not text or not entity_word:
        return None

    text = text.lower().strip()
    entity_word = entity_word.lower()

    # Remove noise words (keep 'with' and 'to')
    noise_words = ["show", "view", "display", "details", "link", "map"]
    for word in noise_words:
        text = text.replace(word, "").strip()

    # -----------------------------
    # CASE 1: LINK SENTENCES
    # Example:
    # risk theft of stationery items with control stationery usage control
    # -----------------------------
    pattern = rf"{entity_word}\s+(.*?)(?:\s+with|\s+to|$)"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1).strip().title()

    # -----------------------------
    # CASE 2: "<name> entity"
    # -----------------------------
    if text.endswith(entity_word):
        name = text.replace(entity_word, "").strip()
        return name.title() if name else None

    # -----------------------------
    # CASE 3: "entity <name>"
    # -----------------------------
    if text.startswith(entity_word):
        name = text.replace(entity_word, "").strip()
        return name.title() if name else None

    return None


# ------------------------------------------------
# Extract all entity names from a prompt
# ------------------------------------------------
def extract_names(prompt: str):
    return {
        "process": extract_entity_name(prompt, "process"),
        "sub_process": extract_entity_name(prompt, "sub process"),
        "risk": extract_entity_name(prompt, "risk"),
        "control": extract_entity_name(prompt, "control")
    }

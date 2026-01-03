def extract_entity_name(text: str, entity_word: str):
    """
    Handles:
    - show <name> <entity>
    - show <entity> <name>
    - view <name> <entity>
    """

    text = text.lower().strip()

    noise_words = ["show", "view", "display", "details", "of"]
    for word in noise_words:
        text = text.replace(word, "").strip()

    entity_word = entity_word.lower()

    # "<name> entity"
    if text.endswith(entity_word):
        name = text.replace(entity_word, "").strip()
        return name.title() if name else None

    # "entity <name>"
    if text.startswith(entity_word):
        name = text.replace(entity_word, "").strip()
        return name.title() if name else None

    return None

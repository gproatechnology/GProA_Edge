def get_normalization_prompt(text: str) -> str:
    """
    Returns a prompt for normalizing entity names/identifiers.
    This is used to determine if different representations refer to the same entity.
    """
    prompt = f"""
    Return ONLY valid JSON.

    Schema:
    {{
      "same_entity": boolean,
      "confidence": float (0.0-1.0),
      "normalized_form": "string (the standardized representation)",
      "reason": "string (explanation of the decision)"
    }}

    Task: Determine if the following two entity references refer to the same real-world entity.
    Consider variations in formatting, spacing, punctuation, and case.

    Entity A: {text}
    """
    return prompt.strip()
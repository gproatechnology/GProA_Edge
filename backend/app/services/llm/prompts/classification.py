def get_classification_prompt(text: str) -> str:
    """
    Returns a prompt for classifying a technical document for EDGE certification.
    The prompt instructs the model to return a JSON object with the classification.
    """
    prompt = f"""
    Return ONLY valid JSON.

    Schema:
    {{
      "category_edge": "string (one of: ENERGY, WATER, MATERIALS, DESIGN)",
      "measure_edge": "string (e.g., EEM22, WEM01, etc.)",
      "doc_type": "string (e.g., ficha_tecnica, plano, etc.)",
      "confidence": 0.0-1.0
    }}

    Input text:
    {text}
    """
    return prompt.strip()
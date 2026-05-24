def get_summaries_prompt(text: str) -> str:
    """
    Returns a prompt for generating technical summaries of inconsistencies, validations, or EDGE compliance.
    """
    prompt = f"""
    Return ONLY valid JSON.

    Schema:
    {{
      "summary": "string (concise technical summary)",
      "key_points": ["string", "string", ...],
      "confidence": float (0.0-1.0)
    }}

    Task: Provide a clear, concise technical summary of the following text, focusing on inconsistencies, validation results, or EDGE compliance issues.

    Text to summarize:
    {text}
    """
    return prompt.strip()
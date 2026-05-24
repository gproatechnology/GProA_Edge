def get_validation_explanations_prompt(text: str) -> str:
    """
    Returns a prompt for explaining why a specific EDGE measure failed validation.
    """
    prompt = f"""
    Return ONLY valid JSON.

    Schema:
    {{
      "failed_measure": "string (e.g., EEM22)",
      "failure_reason": "string (detailed explanation)",
      "suggested_fix": "string (recommendation to pass validation)",
      "confidence": float (0.0-1.0)
    }}

    Task: Explain why the following technical document or data failed to comply with the specified EDGE measure.
    Provide a clear reason and a suggestion for how to fix it.

    Text/data to analyze:
    {text}
    """
    return prompt.strip()
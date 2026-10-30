import json
import re


def generate_quiz(text, client, num_questions=5):
    """
    Generate multiple-choice questions from study material.
    """

    if not text or not text.strip():
        raise ValueError("Study material is empty.")

    prompt = f"""
You are an educational quiz generator.

Create {num_questions} multiple-choice questions
using ONLY the study material provided below.

Requirements:
- Each question must have exactly 4 options.
- Exactly one option must be correct.
- Include the correct answer and a short explanation.
- Use clear, student-friendly English.
- Do not invent facts outside the material.

Return ONLY valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Short explanation based on the material"
    }}
  ]
}}

STUDY MATERIAL:
{text[:18000]}
"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )

    if not response.text:
        raise ValueError("The AI returned an empty response.")

    result_text = response.text.strip()

    # Remove Markdown code fences if the AI includes them.
    result_text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        result_text,
        flags=re.IGNORECASE
    ).strip()

    result = json.loads(result_text)
    questions = result.get("questions", [])

    if not questions:
        raise ValueError("No questions were generated.")

    for item in questions:
        if (
            not isinstance(item.get("question"), str)
            or not isinstance(item.get("options"), list)
            or len(item["options"]) != 4
            or item.get("correct_answer") not in item["options"]
            or not isinstance(item.get("explanation"), str)
        ):
            raise ValueError("The AI returned an invalid quiz format.")

    return questions
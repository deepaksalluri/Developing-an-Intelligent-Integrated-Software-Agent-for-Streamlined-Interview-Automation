import json
import re

import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_question(role):
    prompt = (
        "Ask exactly one clear technical interview question for a "
        f"{role} role. Return only the question text."
    )

    response = model.generate_content(prompt)

    return response.text.strip()


def _fallback_evaluation(answer):
    words = re.findall(r"\w+", answer.lower())
    technical_terms = {
        "because", "example", "design", "test", "database", "api", "security",
        "performance", "scalable", "algorithm", "complexity", "debug", "deploy",
        "architecture", "validation", "error", "handling",
    }
    term_hits = len(set(words) & technical_terms)
    length_score = min(len(words) // 12, 5)
    score = max(1, min(10, 2 + length_score + min(term_hits, 3)))

    return {
        "score": score,
        "strengths": "Answer submitted and contains relevant explanation.",
        "weaknesses": "The answer may need more specific technical detail and examples.",
        "suggestions": "Add concrete steps, mention trade-offs, and include a short real-world example.",
        "summary": "Automatic fallback evaluation was used because AI scoring was unavailable.",
    }


def _extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _normalise_evaluation(data, raw_text=""):
    score_match = re.search(r"(\d{1,2})\s*/\s*10", raw_text)
    score = data.get("score") if isinstance(data, dict) else None

    if score is None and score_match:
        score = score_match.group(1)

    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0

    return {
        "score": max(0, min(score, 10)),
        "strengths": str(data.get("strengths", "")).strip() if isinstance(data, dict) else "",
        "weaknesses": str(data.get("weaknesses", "")).strip() if isinstance(data, dict) else "",
        "suggestions": str(data.get("suggestions", "")).strip() if isinstance(data, dict) else "",
        "summary": str(data.get("summary", "")).strip() if isinstance(data, dict) else raw_text.strip(),
    }


def evaluate_answer(question, answer):
    try:
        prompt = f"""
        You are an AI interviewer.

        Question: {question}
        Candidate Answer: {answer}

        Evaluate the answer fairly for correctness, completeness, clarity,
        practical knowledge, and communication.

        Return only valid JSON with this exact structure:
        {{
          "score": 0,
          "strengths": "short paragraph",
          "weaknesses": "short paragraph",
          "suggestions": "short paragraph",
          "summary": "one-line hiring signal"
        }}

        The score must be an integer from 0 to 10.
        """

        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        parsed = _extract_json(raw_text)

        if parsed:
            return _normalise_evaluation(parsed, raw_text)

        return _normalise_evaluation({}, raw_text)

    except Exception as e:
        print("Evaluation Error:", e)
        return _fallback_evaluation(answer)


def format_evaluation_feedback(evaluation):
    return (
        f"Score: {evaluation['score']}/10\n"
        f"Strengths: {evaluation['strengths']}\n"
        f"Weaknesses: {evaluation['weaknesses']}\n"
        f"Suggestions: {evaluation['suggestions']}\n"
        f"Summary: {evaluation['summary']}"
    )

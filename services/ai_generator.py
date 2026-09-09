"""
Generates structured pitch-deck content from a raw startup idea using an LLM.
Swap the `_call_llm` internals for OpenAI / Gemini / any other provider if needed —
everything else in the app only depends on the JSON shape returned here.
"""
import os
import json
import re
from anthropic import Anthropic

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


SLIDE_TYPES = [
    "title",
    "problem",
    "solution",
    "key_features",
    "target_audience",
    "market_opportunity",
    "business_model",
    "competitors",
    "future_scope",
]

SYSTEM_PROMPT = """You are an expert startup pitch-deck writer.
Given a startup idea, generate concise, investor-ready content for a pitch deck.
Respond with ONLY valid JSON — no markdown fences, no commentary — matching exactly
this schema:

{
  "startup_name": "string",
  "tagline": "string",
  "slides": [
    {"slide_type": "problem", "title": "string", "content": {"bullets": ["...", "..."]}},
    {"slide_type": "solution", "title": "string", "content": {"bullets": ["...", "..."]}},
    {"slide_type": "key_features", "title": "string", "content": {"bullets": ["...", "..."]}},
    {"slide_type": "target_audience", "title": "string", "content": {"bullets": ["...", "..."]}},
    {"slide_type": "market_opportunity", "title": "string", "content": {"bullets": ["...", "..."], "stats": ["TAM: ...", "SAM: ...", "SOM: ..."]}},
    {"slide_type": "business_model", "title": "string", "content": {"bullets": ["...", "..."]}},
    {"slide_type": "competitors", "title": "string", "content": {"bullets": ["Competitor - key differentiator", "..."]}},
    {"slide_type": "future_scope", "title": "string", "content": {"bullets": ["...", "..."]}}
  ]
}

Rules:
- 3 to 5 bullets per slide, each bullet a short punchy sentence (max ~15 words).
- Be specific to the idea given; never output generic filler like "insert content here".
- Titles should be short slide headings (3-6 words), not full sentences.
"""


def _call_llm(idea_description, industry):
    client = _get_client()
    user_prompt = (
        f"Startup idea: {idea_description}\n"
        f"Industry: {industry or 'not specified'}\n\n"
        "Generate the pitch deck content JSON now."
    )
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw_text = "".join(block.text for block in response.content if block.type == "text")
    return raw_text


def _extract_json(raw_text):
    """Strip stray markdown fences if the model adds them despite instructions."""
    cleaned = re.sub(r"^```json|^```|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def generate_pitch_content(idea_description, industry=None):
    """
    Returns a dict: {startup_name, tagline, slides: [...]}
    Raises ValueError if the LLM output can't be parsed — caller should show a
    friendly "please retry" message rather than crash.
    """
    raw = _call_llm(idea_description, industry)
    try:
        data = _extract_json(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Could not parse AI response as JSON: {exc}") from exc

    if "slides" not in data or not isinstance(data["slides"], list):
        raise ValueError("AI response missing 'slides' array")

    return data

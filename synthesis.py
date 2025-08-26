import json
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from llm_client import LLMClient
from search_extract import SourceContent


@dataclass
class Slide:
    title: str
    bullets: List[str]


@dataclass
class Deck:
    topic: str
    slides: List[Slide]


SCHEMA_HINT = """
Return ONLY minified JSON with this shape:
{
  "topic": string,
  "slides": [
    { "title": string, "bullets": string[] }
  ]
}
""".strip()


def _build_prompt(topic: str, sources: List[SourceContent]) -> str:
    citations = []
    contents = []
    for idx, s in enumerate(sources, start=1):
        citations.append(f"[{idx}] {s.title} — {s.url}")
        contents.append(f"SOURCE [{idx}] {s.title}\nURL: {s.url}\nTEXT: {s.text}")
    joined_citations = "\n".join(citations)
    joined_contents = "\n\n".join(contents)
    user = f"""
Topic: {topic}

You are an expert analyst. Synthesize a concise, factual, and presentation-ready slide deck combining your knowledge with the SOURCES below. Prioritize recent and credible info. Avoid speculation. Where possible, generalize rather than quote.

Deck requirements:
- Slide 1: Title (the topic)
- Slide 2: Overview (2-4 bullets)
- Slides 3-6: Key points / trends / arguments (3-5 bullets each)
- Final slide: Conclusion / Takeaways (3-5 bullets)
- Bullets must be short, direct, and non-redundant
- No citations inline, no markdown, no numbering prefixes

Citations (do not include in slides):
{joined_citations}

SOURCES:
{joined_contents}

{SCHEMA_HINT}
Respond with JSON only.
""".strip()
    return user


def _extract_first_json(text: str) -> str:
    # Remove code fences
    text = re.sub(r"```(json)?", "", text).strip()
    # Try full parse first
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    # Fallback: find first {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    return text


def synthesize_deck(topic: str, sources: List[SourceContent], provider: str = "auto", model: Optional[str] = None) -> Deck:
    client = LLMClient(provider=provider, model=model)
    if not client.is_available():
        raise RuntimeError(
            "No available LLM provider. Configure OPENAI_API_KEY or run Ollama."
        )

    system = (
        "You generate accurate, well-structured slide outlines. "
        "Output must be strict JSON only."
    )
    user = _build_prompt(topic, sources)

    text = client.complete_json(system, user)
    json_text = _extract_first_json(text)
    try:
        data = json.loads(json_text)
    except Exception:
        # Second attempt with stricter instruction
        user2 = user + "\n\nRespond with strict minified JSON only. No prose."
        text2 = client.complete_json(system, user2)
        json_text = _extract_first_json(text2)
        data = json.loads(json_text)

    slides: List[Slide] = []
    for s in data.get("slides", []):
        title = str(s.get("title", "")).strip() or "Untitled"
        bullets = [str(b).strip() for b in (s.get("bullets") or []) if str(b).strip()]
        slides.append(Slide(title=title, bullets=bullets))

    topic_out = data.get("topic") or topic
    return Deck(topic=str(topic_out), slides=slides)
# Auto-Generate Slide Decks using LLM + Web Search

## Overview
Generate a structured PowerPoint presentation on any topic by combining an LLM with live web search. The script fetches recent sources, extracts content, asks an LLM to synthesize a slide outline in JSON, and builds a deck using python-pptx.

## Features
- Topic input via CLI
- DuckDuckGo web search with content extraction (readability + bs4)
- LLM synthesis with OpenAI (default) or Ollama fallback
- Structured slides: Title, Overview, 3–4 Key Sections, Conclusion
- Exports `.pptx`

## Requirements
- Python 3.9+
- Internet access for search and (if using OpenAI) the API

Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration
Provide at least one LLM provider:

- OpenAI (recommended):
  ```bash
  export OPENAI_API_KEY=sk-...
  # Optional overrides
  export OPENAI_MODEL=gpt-4o-mini
  ```

- Ollama (fallback):
  ```bash
  # Ensure Ollama is running locally
  export OLLAMA_HOST=http://localhost:11434
  export OLLAMA_MODEL=llama3.1
  ```

## Usage
```bash
python generate_deck.py "LLM Evaluation" -o llm-eval.pptx --max-sources 6 --provider auto
```

Arguments:
- `topic` (positional): Topic for the deck.
- `-o, --out`: Output path. Defaults to `deck-<topic>.pptx`.
- `--max-sources`: Number of web sources to include (default 6).
- `--provider`: `auto` (default), `openai`, or `ollama`.

## Output Structure
The generated deck contains:
- Slide 1: Title
- Slide 2: Overview
- Slides 3–6: Key sections (trends/arguments) with bullets
- Final slide: Conclusion / Takeaways

## Notes
- The script attempts to parse strict JSON from the LLM. If parsing fails, it retries with a stricter instruction.
- Web extraction uses readability; if it cannot extract the main content, it falls back to page text via BeautifulSoup.

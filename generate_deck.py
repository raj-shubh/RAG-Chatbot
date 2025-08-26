import argparse
import os
import sys
from datetime import datetime

from search_extract import gather_sources
from synthesis import synthesize_deck
from pptx_builder import build_presentation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a slide deck from topic using LLM + web search",
    )
    parser.add_argument("topic", type=str, help="Topic to generate the deck for")
    parser.add_argument("-o", "--out", type=str, default=None, help="Output .pptx path")
    parser.add_argument("--max-sources", type=int, default=6, help="Number of web sources to include")
    parser.add_argument("--provider", type=str, default="auto", choices=["auto", "openai", "ollama"], help="LLM provider")
    parser.add_argument("--model", type=str, default=None, help="Model name override")
    return parser.parse_args()


def main():
    args = parse_args()
    topic = args.topic.strip()
    if not topic:
        print("Topic cannot be empty", file=sys.stderr)
        sys.exit(1)

    out_path = args.out
    if not out_path:
        safe = "".join(c for c in topic if c.isalnum() or c in ("-", "_")).strip().strip("-")
        if not safe:
            safe = "deck"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_path = f"deck-{safe}-{timestamp}.pptx"

    print(f"Searching the web for: {topic} (max {args.max_sources} sources)...")
    sources = gather_sources(topic, max_results=args.max_sources)
    if not sources:
        print("No sources found or failed to extract content.", file=sys.stderr)
        sys.exit(2)

    print(f"Synthesizing slide outline using provider={args.provider}...")
    deck = synthesize_deck(topic, sources, provider=args.provider, model=args.model)

    print(f"Building PowerPoint -> {out_path}")
    build_presentation(deck, out_path)
    print(f"Done: {out_path}")


if __name__ == "__main__":
    main()
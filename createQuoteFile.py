#!/usr/bin/env python3
# =============================================================================
#  NAME:        createQuoteFile.py
#
#  DESCRIPTION: Convert a plaintext file of quotes (one quote per line) into
#               the JSON quote format used by stratopost.
#
#  VERSION:     v1.0d2
#
#  GITHUB:      https://github.com/r3v/stratopost
#
#  USAGE:
#               python3 createQuoteFile.py input.txt output.json
# =============================================================================
"""
createQuoteFile.py

Usage:
    python3 createQuoteFile.py input.txt output.json

Convert a plaintext file of quotes (one quote per line) into the JSON quote format used
by stratopost. Each non-empty line in the input file becomes a record:
    {
        "Quote_Text": "<line>",
        "Quote_Length": "<grapheme count as string>",
        "Post_Count": "0",
        "Last_Posted": "never"
    }

Quote_Length is measured in graphemes (ie. user-perceived characters), not raw
string length, so that combining marks, emoji, etc. are each counted once
rather than once per underlying code point. This is relevant because Bluesky's
limit is grapheme-based, not raw character-based.
"""

import argparse
import json
import sys

try:
    import regex  # regex needed for quote length  
except ImportError:
    sys.exit(
        "Missing dependency 'regex'. Install it with:\n"
        "    pip install regex"
    )

# \X matches one Unicode grapheme cluster
_GRAPHEME_PATTERN = regex.compile(r"\X")


def grapheme_length(text: str) -> int:
    """Count user-perceived characters (grapheme clusters) in text."""
    return len(_GRAPHEME_PATTERN.findall(text))


def build_quotes(lines: list[str]) -> list[dict]:
    quotes = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        quotes.append(
            {
                "Quote_Text": line,
                "Quote_Length": str(grapheme_length(line)),
                "Post_Count": "0",
                "Last_Posted": "never",
            }
        )
    return quotes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a plaintext quotes file into stratopost's JSON quote format."
    )
    parser.add_argument("input_file", help="Path to the plaintext quotes file (one quote per line).")
    parser.add_argument("output_file", help="Path to write the resulting JSON file.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    args = parser.parse_args()

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        sys.exit(f"Could not read input file '{args.input_file}': {e}")

    quotes = build_quotes(lines)
    if not quotes:
        sys.exit(f"No quotes found in '{args.input_file}' — nothing to write.")

    if not args.force:
        try:
            with open(args.output_file, "r", encoding="utf-8"):
                sys.exit(
                    f"Output file '{args.output_file}' already exists. "
                    "Use --force to overwrite it."
                )
        except FileNotFoundError:
            pass

    try:
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump({"quotes": quotes}, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as e:
        sys.exit(f"Could not write output file '{args.output_file}': {e}")

    print(f"Wrote {len(quotes)} quote(s) to '{args.output_file}'.")


if __name__ == "__main__":
    main()

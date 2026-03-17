"""
One-off preprocessor: inserts newlines before Art. section headings in BayBO.txt
so that draft_inventory.py can parse it.

In BayBO.txt the Art. headings appear inline after sentence ends, e.g.:
  "7. Einrichtungsgegenstände … Art. 2 Begriffe\n(1) 1Bauliche Anlagen …"

This script puts each "Art. N Title" on its own line.

Usage:
    python propra/data/preprocess_baybo_txt.py
"""

import re
from pathlib import Path

_IN = Path(__file__).parent / "txt" / "BayBO.txt"
_OUT = Path(__file__).parent / "txt" / "BayBO_clean.txt"

# Matches a genuine Art. heading: Art. N (with optional letter suffix) followed
# by a noun-phrase title (starts with capital letter, not Abs./Nr./Satz/etc.).
_HEADING_RE = re.compile(
    r"(?<!\n)"                            # not already at line start
    r"(?<=[.\s])"                         # preceded by period or whitespace
    r"(Art\.\s+\d+[a-zA-Z]?"             # "Art. 6" or "Art. 6a"
    r"(?:\s+(?!Abs\.|Nr\.|Satz\b|und\b|bis\b|oder\b|in\b|nach\b|vom\b|"
          r"der\b|die\b|des\b|dem\b|den\b|im\b|einer\b|einem\b|einen\b)"
          r"[A-ZÄÖÜ]\w*"
    r"(?:\s+[A-ZÄÖÜ,\-\w]+)*)?)"         # rest of title (may span multiple words)
    r"(?=\s*\n|\s*\()",                   # must be followed by newline or Absatz marker
)


def preprocess(text: str) -> str:
    """Insert a newline before each genuine Art. heading."""
    # Strategy: split every line, then re-join with newlines inserted at heading boundaries.
    # We scan for the pattern ". Art. N Title" or " Art. N Title" and add \n before Art.
    result = re.sub(
        r"(^|[.!?])\s+(Art\.\s+\d+[a-zA-Z]?\s+(?!Abs\.|Nr\.|Satz|und |bis |oder |in |nach |vom |der |die |des |dem |den |im |einer |einem |einen )[A-ZÄÖÜ])",
        r"\1\nArt.",
        text,
        flags=re.MULTILINE,
    )
    # Now also handle "Teil" section titles so they are on their own line
    result = re.sub(
        r"(?m)((?:Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebter|Achter|"
        r"Neunter|Zehnter) Teil\b[^\n]*)",
        r"\n\1\n",
        result,
    )
    return result


def main() -> None:
    raw = _IN.read_text(encoding="utf-8")
    cleaned = preprocess(raw)
    _OUT.write_text(cleaned, encoding="utf-8")

    # Quick sanity: count how many Art. N lines we now have at line start
    lines_with_art = [line for line in cleaned.splitlines() if re.match(r"^Art\.\s+\d+", line.strip())]
    print(f"Written: {_OUT}")
    print(f"Art. headings found at line starts: {len(lines_with_art)}")
    for line in lines_with_art[:20]:
        print(f"  {line.strip()[:80]}")


if __name__ == "__main__":
    main()

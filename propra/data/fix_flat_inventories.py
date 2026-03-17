"""Fix two classes of text quality issues in flat node inventories.

1. Page-noise prefix: rows where text starts with "Seite N von M ..."
   Fix: strip the noise prefix, keep the legal text that follows.

2. Title-only rows: rows where text is just "Section Title DD.MM.YYYY"
   Fix: look up the actual legal text from the corresponding .txt source file.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent  # /proplaw
INV_DIR = ROOT / "propra" / "data" / "node inventory"
TXT_DIR = ROOT / "propra" / "data" / "txt"

STATES = [
    "BauO_BE", "BauO_HE", "BauO_LSA", "BauO_MV",
    "LBO_SH", "LBauO_RLP", "SaechsBO", "ThuerBO",
]

# Pattern: text starts with optional dash/space then "Seite N von M"
# followed by optional section title/date, then the real legal text
NOISE_PREFIX = re.compile(
    r"^[-–]?\s*Seite\s+\d+\s+von\s+\d+\s+(?:[A-ZÄÖÜ§][^\n]{0,80}?\s+\d{2}\.\d{2}\.\d{4}\s+)?",
    re.IGNORECASE,
)

# SaechsBO-specific: noise APPENDED at end — "Fassung vom DD.MM.YYYY Seite N von M SächsBO ..."
NOISE_SUFFIX = re.compile(
    r"\s*Fassung\s+vom\s+\d{2}\.\d{2}\.\d{4}\s+Seite\s+\d+.*$",
    re.IGNORECASE,
)

# Pattern: entire text is just a section title + effective date (no legal content)
TITLE_ONLY = re.compile(r"^[A-ZÄÖÜ][^\d\n]{2,50}\s+\d{2}\.\d{2}\.\d{4}\s*$")


def extract_section_text(txt_path: Path, section_num: str) -> str:
    """Extract the first substantive paragraph text for a given section number
    from its .txt source file. Returns empty string if not found.

    The .txt files typically have three occurrences per section:
    1. TOC entry: "§ 13 - Title DD.MM.YYYY" (ends with date — skip)
    2. Short index: "§ 13 Title" (short line — skip)
    3. Body: "§ 13 Title Actual legal text starts here..." (long line — use this)
    """
    text = txt_path.read_text(encoding="utf-8", errors="replace")

    # Strip trailing letters from e.g. "64e" → "64"
    sec_int = re.sub(r"[a-zA-Z]+$", "", section_num.split(".")[0])

    pattern = re.compile(rf"§\s*{re.escape(sec_int)}\b([^\n]+)", re.MULTILINE)

    for m in pattern.finditer(text):
        line_rest = m.group(1).strip()

        # Skip TOC entries: end with a standalone date
        if re.search(r"\d{2}\.\d{2}\.\d{4}\s*$", line_rest):
            continue
        # Skip "Titel Gültig ab" table noise
        if re.match(r"Titel\s+Gültig|Gültig\s+ab", line_rest, re.IGNORECASE):
            continue
        # Skip very short lines (just the section title, no body)
        if len(line_rest) < 60:
            continue

        # This line has body text — extract up to 300 chars of substantive content
        cleaned = re.sub(r"Seite\s+\d+\s+von\s+\d+[^\n]*", "", line_rest).strip()
        return cleaned[:300]

    return ""


def fix_inventory(state: str, dry_run: bool = False) -> dict:
    inv_path = INV_DIR / f"{state}_node_inventory.md"
    txt_path = TXT_DIR / f"{state}.txt"

    if not inv_path.exists():
        print(f"  SKIP {state}: no flat inventory")
        return {}

    lines = inv_path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = []
    stats = {"noise_fixed": 0, "title_fixed": 0, "title_missing": 0}

    for line in lines:
        if not (line.startswith("| ") and re.match(r"^\| \d", line)):
            new_lines.append(line)
            continue

        parts = line.split("|")
        if len(parts) < 7:
            new_lines.append(line)
            continue

        text = parts[5].strip()
        row_id = parts[1].strip()  # e.g. "14.1"
        fixed_text = text

        if NOISE_PREFIX.match(text):
            # Strip noise prefix
            cleaned = NOISE_PREFIX.sub("", text).strip()
            # Also strip residual "Titel Gültig ab ..." table header after page marker
            cleaned = re.sub(r"^Titel\s+Gültig\s+ab\s+", "", cleaned).strip()
            if len(cleaned) > 15 and not TITLE_ONLY.match(cleaned):
                fixed_text = cleaned
                stats["noise_fixed"] += 1
                print(f"  [noise ] {state} {row_id}: '{text[:60]}' → '{cleaned[:60]}'")
            # If nothing substantive left after stripping, fall through to title lookup

        if fixed_text == text and NOISE_SUFFIX.search(text):
            # Strip tail noise (SaechsBO pattern: noise appended at end)
            cleaned = NOISE_SUFFIX.sub("", text).strip()
            if len(cleaned) > 15:
                fixed_text = cleaned
                stats["noise_fixed"] += 1
                print(f"  [tail  ] {state} {row_id}: '{text[:60]}' → '{cleaned[:60]}'")

        if fixed_text == text and (TITLE_ONLY.match(text) or NOISE_PREFIX.match(text)):
            # Title-only: look up from .txt file
            if txt_path.exists():
                real_text = extract_section_text(txt_path, row_id)
                if real_text and len(real_text) > 20:
                    fixed_text = real_text
                    stats["title_fixed"] += 1
                    print(f"  [title ] {state} {row_id}: '{text}' → '{real_text[:60]}'")
                else:
                    stats["title_missing"] += 1
                    print(f"  [MISS  ] {state} {row_id}: could not extract from .txt")
            else:
                stats["title_missing"] += 1
                print(f"  [MISS  ] {state} {row_id}: no .txt file")

        if fixed_text != text and not dry_run:
            # Reconstruct the pipe-delimited line with the fixed text
            parts[5] = f" {fixed_text} "
            line = "|".join(parts)

        new_lines.append(line)

    if not dry_run:
        inv_path.write_text("".join(new_lines), encoding="utf-8")

    return stats


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN — no files will be written ===\n")

    total = {"noise_fixed": 0, "title_fixed": 0, "title_missing": 0}
    for state in STATES:
        print(f"\n--- {state} ---")
        s = fix_inventory(state, dry_run=dry_run)
        for k in total:
            total[k] += s.get(k, 0)

    print("\n=== TOTALS ===")
    print(f"  Page-noise rows fixed : {total['noise_fixed']}")
    print(f"  Title-only rows fixed : {total['title_fixed']}")
    print(f"  Title-only not found  : {total['title_missing']}")


if __name__ == "__main__":
    main()

"""
Generate NBauO_node_inventory_v2.md from NBauO.txt.

NBauO uses standard § numbering with clear section headers in the format:
  '§ N NBauO - Title'  (on their own line in the text)

This script:
  1. Parses NBauO.txt into per-section blocks split at § N NBauO lines.
  2. Splits each block into Absätze (marked by '(N)' at line-start).
  3. Looks up the node type from the existing NBauO_node_inventory.md flat table.
  4. Outputs NBauO_node_inventory_v2.md in the ### § N — Title format
     expected by split_inventory_to_sentences.py and parse_inventory.py.

No API calls needed — types are taken from the existing flat inventory.

Usage:
    python propra/data/generate_nbauO_inventory.py
"""

from __future__ import annotations

import re
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
_DATA = Path(__file__).parent
_TXT_IN = _DATA / "txt" / "NBauO.txt"
_OLD_INVENTORY = _DATA / "node inventory" / "NBauO_node_inventory.md"
_V2_OUT = _DATA / "node inventory" / "NBauO_node_inventory_v2.md"

# ── regexes ────────────────────────────────────────────────────────────────────

# Matches lines like:  § 1 NBauO - Geltungsbereich
#                      § 3a NBauO - Elektronische Kommunikation
# The title group may bleed into body text for single-Absatz sections;
# callers should prefer the title from the flat inventory when available.
_SECTION_HEADER = re.compile(
    r"^§\s+(\d+[a-z]*)\s+NBauO\s*[-–]\s*(.+)$",
    re.IGNORECASE,
)

# Absatz marker: (1), (2), ... at line-start (possibly with leading whitespace)
_ABSATZ_RE = re.compile(r"^\s*\((\d+)\)\s*(.*)$")


def _load_flat_inventory(flat_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    Parse the existing flat-table NBauO_node_inventory.md to produce:
      - type_map:  section_number -> node_type
      - title_map: section_number -> official title (from the § column)

    Flat table format:
      | Row ID | § | Absatz | Node Type | Text (excerpt) |
      | 6.1    | §6 NBauO - Hinzurechnung benachbarter Grundstücke | Abs. 1 | abstandsflaeche | ... |
    """
    type_map: dict[str, str] = {}
    title_map: dict[str, str] = {}
    # Matches '§6 NBauO - Title' or '§3a NBauO - Title'
    _SEC_TITLE_RE = re.compile(r"§(\d+[a-z]*)\s+NBauO\s*[-–]\s*(.+)", re.IGNORECASE)
    for line in flat_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        row_id = cells[0]
        sec_col = cells[1] if len(cells) > 1 else ""
        node_type = cells[3] if len(cells) > 3 else ""
        # Skip header rows
        if row_id.lower() in {"row id", "nr", "nr.", "#"}:
            continue
        if not node_type or node_type.lower() in {
            "node type", "typ", "knotentyp", "type"
        }:
            continue
        # Extract section number from row ID (e.g. "6.1" -> "6", "3a.2" -> "3a")
        m = re.match(r"^(\d+[a-z]*)\.", row_id)
        if m:
            sec = m.group(1)
            if sec not in type_map:
                type_map[sec] = node_type.strip()
            if sec not in title_map:
                mt = _SEC_TITLE_RE.search(sec_col)
                if mt:
                    title_map[sec] = mt.group(2).strip()
    return type_map, title_map


def _parse_sections(
    txt: str, title_map: dict[str, str]
) -> list[tuple[str, str, str]]:
    """
    Split NBauO.txt into (section_number, title, body_text) triples.

    Uses title_map (from the flat inventory) for official titles so that
    single-Absatz sections whose header line contains the body text inline
    are handled correctly: the excess text after the official title is
    prepended to the body.

    Returns sections in document order.
    """
    lines = txt.splitlines()
    sections: list[tuple[str, str, str]] = []
    current_num: str = ""
    current_title: str = ""
    body_lines: list[str] = []

    for line in lines:
        m = _SECTION_HEADER.match(line.strip())
        if m:
            # Save previous section
            if current_num:
                sections.append((current_num, current_title, "\n".join(body_lines).strip()))
            current_num = m.group(1).strip()
            raw_rest = m.group(2).strip()  # everything after 'NBauO - '

            # Use official title from flat inventory when available
            official = title_map.get(current_num.lower(), "")
            if official:
                current_title = official
                # If raw_rest is longer than the official title, the remainder
                # is body text that was on the same line as the header.
                if len(raw_rest) > len(official) + 5:
                    body_lines = [raw_rest[len(official):].strip()]
                else:
                    body_lines = []
            else:
                current_title = raw_rest
                body_lines = []
        elif current_num:
            body_lines.append(line)

    # Flush last section
    if current_num:
        sections.append((current_num, current_title, "\n".join(body_lines).strip()))

    return sections


def _split_absaetze(body: str) -> list[tuple[str, str]]:
    """
    Split a section body into (absatz_number, text) pairs.

    Absätze are identified by '(N)' markers at line-start.
    If none are found, returns [('' , body)] so the whole text becomes one row.
    """
    lines = body.splitlines()
    absaetze: list[tuple[str, str]] = []
    current_n: str = ""
    current_lines: list[str] = []

    for line in lines:
        m = _ABSATZ_RE.match(line)
        if m:
            if current_n or current_lines:
                absaetze.append((current_n, " ".join(current_lines).strip()))
            current_n = m.group(1)
            first = m.group(2).strip()
            current_lines = [first] if first else []
        else:
            stripped = line.strip()
            if stripped:
                current_lines.append(stripped)

    if current_n or current_lines:
        absaetze.append((current_n, " ".join(current_lines).strip()))

    # Filter out empty entries
    absaetze = [(n, t) for n, t in absaetze if t.strip()]

    return absaetze or [("", body.strip())]


def _format_row_id(sec: str, abs_n: str, idx: int) -> str:
    """
    Build a row ID matching the convention used by parse_inventory.py.

    For numbered Absätze: '{sec_norm}.{abs_n}'  e.g. '6.1'
    For unnumbered:        '{sec_norm}.{idx+1}'  e.g. '85b.1'

    sec_norm: section number with letter suffix lowered, e.g. '85a', '3a'.
    """
    sec_norm = sec.lower()
    num = abs_n if abs_n else str(idx + 1)
    return f"{sec_norm}.{num}"


def generate(txt_path: Path, old_path: Path, out_path: Path) -> None:
    """Main generation function."""
    print(f"Reading {txt_path} …")
    txt = txt_path.read_text(encoding="utf-8", errors="replace")

    print(f"Loading type/title map from {old_path} …")
    type_map, title_map = _load_flat_inventory(old_path)
    print(f"  {len(type_map)} section types, {len(title_map)} titles loaded")

    sections = _parse_sections(txt, title_map)
    print(f"  {len(sections)} sections found")

    lines_out: list[str] = [
        "# NBauO — Node Inventory (Paragraph Level)",
        "",
        "_Generated by generate_nbauO_inventory.py from NBauO.txt._",
        "_Types sourced from existing flat NBauO_node_inventory.md._",
        "_Run split_inventory_to_sentences.py to produce the fine (sentence-level) version._",
        "",
    ]

    unknown_types: list[str] = []
    for sec_num, title, body in sections:
        node_type = type_map.get(sec_num.lower(), "")
        if not node_type:
            node_type = "allgemeine_anforderung"
            unknown_types.append(sec_num)

        lines_out.append(f"### § {sec_num} — {title}")
        lines_out.append(f"**type:** {node_type}")
        lines_out.append(f"**source_paragraph:** §{sec_num} NBauO")
        lines_out.append("")
        lines_out.append("| Nr. | Regeltext (NBauO-Wortlaut) |")
        lines_out.append("|---|---|")

        absaetze = _split_absaetze(body)
        for idx, (abs_n, text) in enumerate(absaetze):
            row_id = _format_row_id(sec_num, abs_n, idx)
            # Escape any pipe characters in the text
            text_clean = text.replace("|", "\\|")
            lines_out.append(f"| {row_id} | {text_clean} |")

        lines_out.append("")

    out_path.write_text("\n".join(lines_out), encoding="utf-8")
    print(f"Written to {out_path}")
    print(f"  Total sections: {len(sections)}")

    if unknown_types:
        print(
            f"  WARNING: {len(unknown_types)} sections had no type in flat inventory "
            f"(defaulted to allgemeine_anforderung): {unknown_types[:10]}"
        )


if __name__ == "__main__":
    generate(_TXT_IN, _OLD_INVENTORY, _V2_OUT)

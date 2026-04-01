"""
Synthetic user test runner for Propra.

Mirrors the PropLaw User Testing Protocol v2.0:
- 3 protocol tasks (fence/boundary, window/structural, garden shed Brandenburg)
- Each task is run against both RAG and GraphRAG
- Each response is individually evaluated (observation-sheet dimensions)
- After both modes, a RAG-vs-GraphRAG comparison evaluation is performed
- Outputs a timestamped CSV to propra/eval/results/

Usage:
    python -m propra.eval.synthetic_user_test
    python -m propra.eval.synthetic_user_test --personas 3 --delay 1.0
    python -m propra.eval.synthetic_user_test --personas 1 --timeout 120
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from dotenv import load_dotenv

from propra.schemas.synthetic_test import (
    ComparisonResult,
    EvaluationResult,
    Persona,
    SyntheticTestRow,
)

if TYPE_CHECKING:
    from openai import OpenAI

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only in envs without openai installed
    OpenAI = None

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent               # propra/eval/
_PROPRA_DIR = _THIS_DIR.parent                            # propra/
_PROJECT_ROOT = _PROPRA_DIR.parent                        # repo root
_PROMPTS_DIR = _PROPRA_DIR / "prompts"
_RESULTS_DIR = _THIS_DIR / "results"

load_dotenv(_PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Prompts (loaded from files per CLAUDE.md — never inlined)
# ---------------------------------------------------------------------------

_GENERATE_PROMPT = (_PROMPTS_DIR / "synthetic_generate_query.txt").read_text(encoding="utf-8")
_EVALUATE_PROMPT = (_PROMPTS_DIR / "synthetic_evaluate.txt").read_text(encoding="utf-8")
_COMPARE_PROMPT = (_PROMPTS_DIR / "synthetic_compare.txt").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Target endpoint
# ---------------------------------------------------------------------------

ASSESS_URL = "https://proplaw-graphrag.onrender.com/api/assess"

# ---------------------------------------------------------------------------
# Personas — 26 diverse archetypes
# ---------------------------------------------------------------------------

PERSONAS: list[Persona] = [
    Persona(role="Hauseigentümer", trait="ängstlicher Anfänger", description="Hat noch nie gebaut und fürchtet Bußgelder."),
    Persona(role="Hauseigentümer", trait="überzeugter Heimwerker", description="Glaubt, alles selbst machen zu können, fragt erst nachher."),
    Persona(role="Hauseigentümerin", trait="pensionierte Witwe", description="67 Jahre, wenig technisches Verständnis, vorsichtig."),
    Persona(role="Hauseigentümer", trait="junges Paar", description="Erstes Eigenheim, Budget-bewusst, ungeduldig."),
    Persona(role="Rechtsanwältin", trait="präzisionsorientiert", description="Will exakte Paragraphen und keine vagen Aussagen."),
    Persona(role="Architekt", trait="routiniert", description="Kennt die Bauordnung, testet Grenzbereiche."),
    Persona(role="Immobilienmakler", trait="geschäftsorientiert", description="Braucht schnelle Antworten für Kundenberatung."),
    Persona(role="Hauseigentümer", trait="technikaffin", description="Recherchiert gründlich online, fragt detailliert."),
    Persona(role="Hauseigentümerin", trait="sprachlich unsicher", description="Deutsch als Zweitsprache, formuliert einfach."),
    Persona(role="Hauseigentümer", trait="Nachbarschaftsstreit", description="Will wissen, ob der Nachbar gegen Vorschriften verstößt."),
    Persona(role="Hauseigentümerin", trait="umweltbewusst", description="Fokus auf nachhaltige Lösungen und Solartechnik."),
    Persona(role="Hauseigentümer", trait="kostenbewusster Rentner", description="Will nur das Nötigste machen, kein Geld verschwenden."),
    Persona(role="Hauseigentümer", trait="ungeduldig", description="Will sofort eine klare Ja/Nein-Antwort."),
    Persona(role="Hauseigentümerin", trait="perfektionistisch", description="Will alles korrekt machen, fragt mehrfach nach."),
    Persona(role="Hauseigentümer", trait="skeptisch", description="Vertraut Behörden nicht und will alles überprüfen."),
    Persona(role="Hauseigentümer", trait="Erbe", description="Hat ein Haus geerbt und kennt sich nicht aus."),
    Persona(role="Hauseigentümerin", trait="berufstätige Mutter", description="Wenig Zeit, braucht kurze und klare Antworten."),
    Persona(role="Hauseigentümer", trait="Handwerker von Beruf", description="Kennt Bautechnik, aber nicht Baurecht."),
    Persona(role="Hauseigentümer", trait="pensionierter Beamter", description="Sehr genau, will alles schriftlich belegt."),
    Persona(role="Hauseigentümerin", trait="kreative Gestalterin", description="Will ungewöhnliche Dinge bauen, denkt nicht an Vorschriften."),
    Persona(role="Hauseigentümer", trait="Investor", description="Mehrere Objekte, will Regeln effizient verstehen."),
    Persona(role="Hauseigentümer", trait="Zugezogener", description="Gerade erst nach Brandenburg gezogen, kennt lokale Regeln nicht."),
    Persona(role="Hauseigentümerin", trait="Seniorin mit Pflegebedarf", description="Braucht barrierefreie Umbauten, versteht Bürokratie nicht."),
    Persona(role="Hauseigentümer", trait="Baugruppen-Mitglied", description="Plant gemeinschaftliches Bauprojekt, denkt mehrstöckig."),
    Persona(role="Hauseigentümer", trait="Minimalist", description="Will wissen, was ohne Genehmigung geht."),
    Persona(role="Hauseigentümerin", trait="Gartenliebhaberin", description="Fokus auf Garten- und Außenbereich, wenig Bauerfahrung."),
]

# ---------------------------------------------------------------------------
# Tasks — from PropLaw User Testing Protocol v2.0
# ---------------------------------------------------------------------------

TASKS = [
    "Zaun um das Grundstück bauen — welche Regeln gelten in Brandenburg?",
    "Fenster einbauen oder verändern — brauche ich eine Genehmigung in Brandenburg?",
    "Kleines Gartenhaus nahe der Grundstücksgrenze in Brandenburg bauen — was ist erlaubt?",
]

# ---------------------------------------------------------------------------
# Retrieval modes — protocol requires both per task
# ---------------------------------------------------------------------------

RETRIEVAL_MODES = ["rag", "graphrag"]

# ---------------------------------------------------------------------------
# CSV columns
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "persona_role", "persona_trait", "task", "generated_query", "retrieval_mode",
    # Response
    "verdict", "confidence", "explanation", "cited_sources", "next_action",
    "kg_status", "response_time_ms",
    # Per-mode evaluation (observation sheet)
    "task_success", "user_confidence", "trustworthiness", "clarity",
    "usability", "traceability", "key_issue",
    # RAG vs GraphRAG comparison (filled on graphrag row only)
    "cmp_trustworthiness_rag", "cmp_trustworthiness_graphrag",
    "cmp_clarity_rag", "cmp_clarity_graphrag",
    "cmp_usability_rag", "cmp_usability_graphrag",
    "cmp_preferred_version", "cmp_preference_reason",
    "error",
]

# ---------------------------------------------------------------------------
# OpenAI model
# ---------------------------------------------------------------------------

OPENAI_MODEL = "gpt-4o"


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _make_openai_client() -> "OpenAI":
    """Create the OpenAI client with a clearer runtime error when dependency is missing."""
    if OpenAI is None:
        raise RuntimeError(
            "The 'openai' package is not installed in this Python environment."
        )
    return OpenAI()


def generate_query(client: "OpenAI", persona: Persona, task: str, jurisdiction: str) -> str:
    """Generate a realistic German homeowner question using GPT-4o."""
    prompt = _GENERATE_PROMPT.format(
        persona_role=persona.role,
        persona_trait=persona.trait,
        task_topic=task,
        jurisdiction=jurisdiction,
    )
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip()


def call_assess(query: str, retrieval_mode: str, timeout: float = 60.0) -> tuple[dict, int]:
    """POST to /api/assess. Returns (response_json, response_time_ms)."""
    payload = {
        "jurisdiction": "Brandenburg",
        "property_type": "Einfamilienhaus",
        "project_description": query,
        "has_bplan": False,
        "retrieval_mode": retrieval_mode,
    }
    start = time.monotonic()
    resp = httpx.post(ASSESS_URL, json=payload, timeout=timeout)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    resp.raise_for_status()
    return resp.json(), elapsed_ms


def _parse_llm_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON from an LLM response."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return json.loads(text)


def evaluate_response(
    client: "OpenAI",
    query: str,
    response: dict,
    persona: Persona,
    retrieval_mode: str,
) -> EvaluationResult:
    """Evaluate a single /assess response using GPT-4o."""
    cited_str = json.dumps(response.get("cited_sources", []), ensure_ascii=False, indent=2)
    prompt = _EVALUATE_PROMPT.format(
        persona_role=persona.role,
        persona_trait=persona.trait,
        query=query,
        retrieval_mode=retrieval_mode,
        verdict=response.get("verdict", "N/A"),
        explanation=response.get("explanation", "N/A"),
        cited_sources=cited_str,
        next_action=response.get("next_action", "N/A"),
        confidence=response.get("confidence", "N/A"),
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.0,
    )
    parsed = _parse_llm_json(resp.choices[0].message.content)
    return EvaluationResult(**parsed)


def compare_responses(
    client: "OpenAI",
    query: str,
    rag_response: dict,
    graphrag_response: dict,
    persona: Persona,
) -> ComparisonResult:
    """Compare RAG vs GraphRAG for the same query — mirrors observation sheet section 2."""
    def _sources_str(resp: dict) -> str:
        return json.dumps(resp.get("cited_sources", []), ensure_ascii=False, indent=2)

    prompt = _COMPARE_PROMPT.format(
        persona_role=persona.role,
        persona_trait=persona.trait,
        query=query,
        rag_verdict=rag_response.get("verdict", "N/A"),
        rag_explanation=rag_response.get("explanation", "N/A"),
        rag_cited_sources=_sources_str(rag_response),
        rag_next_action=rag_response.get("next_action", "N/A"),
        rag_confidence=rag_response.get("confidence", "N/A"),
        graphrag_verdict=graphrag_response.get("verdict", "N/A"),
        graphrag_explanation=graphrag_response.get("explanation", "N/A"),
        graphrag_cited_sources=_sources_str(graphrag_response),
        graphrag_next_action=graphrag_response.get("next_action", "N/A"),
        graphrag_confidence=graphrag_response.get("confidence", "N/A"),
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.0,
    )
    parsed = _parse_llm_json(resp.choices[0].message.content)
    return ComparisonResult(**parsed)


def _make_row(
    persona: Persona, task: str, query: str, mode: str,
) -> SyntheticTestRow:
    """Create a blank row with identity fields populated."""
    return SyntheticTestRow(
        persona_role=persona.role,
        persona_trait=persona.trait,
        task=task,
        generated_query=query,
        retrieval_mode=mode,
    )


def _fill_response(row: SyntheticTestRow, response: dict, elapsed_ms: int) -> None:
    """Populate response fields on a row."""
    row.verdict = response.get("verdict")
    row.confidence = response.get("confidence")
    row.explanation = response.get("explanation")
    row.cited_sources = json.dumps(response.get("cited_sources", []), ensure_ascii=False)
    row.next_action = response.get("next_action")
    row.kg_status = response.get("kg_status")
    row.response_time_ms = elapsed_ms


def _fill_eval(row: SyntheticTestRow, evaluation: EvaluationResult) -> None:
    """Populate evaluation fields on a row."""
    row.task_success = evaluation.task_success
    row.user_confidence = evaluation.user_confidence
    row.trustworthiness = evaluation.trustworthiness
    row.clarity = evaluation.clarity
    row.usability = evaluation.usability
    row.traceability = evaluation.traceability
    row.key_issue = evaluation.key_issue


def _fill_comparison(row: SyntheticTestRow, comparison: ComparisonResult) -> None:
    """Populate comparison fields on a row (graphrag row only)."""
    row.cmp_trustworthiness_rag = comparison.trustworthiness_rag
    row.cmp_trustworthiness_graphrag = comparison.trustworthiness_graphrag
    row.cmp_clarity_rag = comparison.clarity_rag
    row.cmp_clarity_graphrag = comparison.clarity_graphrag
    row.cmp_usability_rag = comparison.usability_rag
    row.cmp_usability_graphrag = comparison.usability_graphrag
    row.cmp_preferred_version = comparison.preferred_version
    row.cmp_preference_reason = comparison.preference_reason


def _init_csv(output_path: Path) -> None:
    """Create or reset the output CSV with a header row."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()


def _append_rows(output_path: Path, rows: list[SyntheticTestRow]) -> None:
    """Append completed rows so long runs leave visible progress on disk."""
    if not rows:
        return

    if not output_path.exists():
        _init_csv(output_path)

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        for row in rows:
            writer.writerow(row.model_dump(include=set(CSV_COLUMNS)))


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run(
    personas: list[Persona],
    tasks: list[str],
    delay: float = 0.5,
    jurisdiction: str = "Brandenburg",
    timeout: float = 60.0,
    output_path: Path | None = None,
) -> list[SyntheticTestRow]:
    """Run the full protocol: for each persona × task, call RAG + GraphRAG, evaluate, compare."""
    client = _make_openai_client()
    results: list[SyntheticTestRow] = []
    total = len(personas) * len(tasks)
    idx = 0

    for persona in personas:
        for task in tasks:
            idx += 1
            print(f"\n[{idx}/{total}] {persona.role} ({persona.trait}) — {task}")

            # --- Step 1: generate ONE query (shared by both modes) ---
            try:
                query = generate_query(client, persona, task, jurisdiction)
                print(f"  Query: {query[:90]}...")
            except Exception as exc:
                print(f"  ERROR generating query: {exc}")
                error_rows: list[SyntheticTestRow] = []
                for mode in RETRIEVAL_MODES:
                    row = _make_row(persona, task, "", mode)
                    row.error = f"query_generation: {exc}"
                    error_rows.append(row)
                results.extend(error_rows)
                if output_path is not None:
                    _append_rows(output_path, error_rows)
                continue

            # --- Step 2 & 3: call /assess + evaluate for each mode ---
            mode_rows: dict[str, SyntheticTestRow] = {}
            mode_responses: dict[str, dict] = {}

            for mode in RETRIEVAL_MODES:
                row = _make_row(persona, task, query, mode)
                mode_rows[mode] = row

                try:
                    response, elapsed_ms = call_assess(query, mode, timeout=timeout)
                    _fill_response(row, response, elapsed_ms)
                    mode_responses[mode] = response
                    print(f"  [{mode.upper():>8}] {row.verdict} | {row.confidence} | {elapsed_ms}ms")

                    evaluation = evaluate_response(client, query, response, persona, mode)
                    _fill_eval(row, evaluation)
                    print(f"           Eval: {evaluation.task_success} | Conf:{evaluation.user_confidence}/5 | Clarity:{evaluation.clarity}/5 | Trace:{evaluation.traceability}/5")

                except Exception as exc:
                    row.error = str(exc)
                    print(f"  [{mode.upper():>8}] ERROR: {exc}")

                if delay > 0:
                    time.sleep(delay)

            # --- Step 4: compare RAG vs GraphRAG ---
            if "rag" in mode_responses and "graphrag" in mode_responses:
                try:
                    comparison = compare_responses(
                        client, query, mode_responses["rag"], mode_responses["graphrag"], persona,
                    )
                    _fill_comparison(mode_rows["graphrag"], comparison)
                    print(f"  Comparison: preferred={comparison.preferred_version} — {comparison.preference_reason}")
                except Exception as exc:
                    print(f"  Comparison ERROR: {exc}")

            completed_rows = list(mode_rows.values())
            results.extend(completed_rows)
            if output_path is not None:
                _append_rows(output_path, completed_rows)

    return results


def write_csv(results: list[SyntheticTestRow], output_path: Path) -> None:
    """Write results to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in results:
            writer.writerow(row.model_dump(include=set(CSV_COLUMNS)))


def print_summary(results: list[SyntheticTestRow]) -> None:
    """Print a summary aligned with the protocol observation sheet."""
    total = len(results)
    errors = sum(1 for r in results if r.error)

    for mode in RETRIEVAL_MODES:
        rows = [r for r in results if r.retrieval_mode == mode and r.error is None]
        scored = [r for r in rows if r.clarity is not None]
        if not scored:
            continue

        successes = sum(1 for r in scored if r.task_success == "Yes")
        partials = sum(1 for r in scored if r.task_success == "Partial")
        failures = sum(1 for r in scored if r.task_success == "No")
        n = len(scored)

        avg_conf = sum(r.user_confidence for r in scored) / n
        avg_trust = sum(r.trustworthiness for r in scored) / n
        avg_clarity = sum(r.clarity for r in scored) / n
        avg_usability = sum(r.usability for r in scored) / n
        avg_trace = sum(r.traceability for r in scored) / n
        avg_time = sum(r.response_time_ms for r in scored if r.response_time_ms) / n

        print(f"\n{'─' * 50}")
        print(f"  {mode.upper()} ({n} scored)")
        print(f"{'─' * 50}")
        print(f"  Task success:     {successes} Yes / {partials} Partial / {failures} No")
        print(f"  Avg user conf:    {avg_conf:.1f}/5")
        print(f"  Avg trust:        {avg_trust:.1f}/5")
        print(f"  Avg clarity:      {avg_clarity:.1f}/5")
        print(f"  Avg usability:    {avg_usability:.1f}/5")
        print(f"  Avg traceability: {avg_trace:.1f}/5")
        print(f"  Avg response:     {avg_time:.0f}ms")

    # Comparison summary
    compared = [r for r in results if r.cmp_preferred_version is not None]
    if compared:
        rag_pref = sum(1 for r in compared if r.cmp_preferred_version == "rag")
        graphrag_pref = sum(1 for r in compared if r.cmp_preferred_version == "graphrag")
        print(f"\n{'─' * 50}")
        print(f"  RAG vs GraphRAG PREFERENCE ({len(compared)} comparisons)")
        print(f"{'─' * 50}")
        print(f"  Preferred RAG:      {rag_pref}")
        print(f"  Preferred GraphRAG: {graphrag_pref}")

    print(f"\n  Total rows: {total} | Errors: {errors}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Propra synthetic user test runner (protocol v2.0)")
    parser.add_argument(
        "--personas", type=int, default=None,
        help="Limit number of personas (default: all 26)",
    )
    parser.add_argument(
        "--tasks", type=str, nargs="*", default=None,
        help="Filter to specific tasks (substring match)",
    )
    parser.add_argument(
        "--delay", type=float, default=0.5,
        help="Delay in seconds between API calls (default: 0.5)",
    )
    parser.add_argument(
        "--timeout", type=float, default=120.0,
        help="HTTP timeout for /assess calls in seconds (default: 120)",
    )
    args = parser.parse_args()

    # Select personas
    personas = PERSONAS[: args.personas] if args.personas else PERSONAS

    # Filter tasks
    tasks = TASKS
    if args.tasks:
        tasks = [t for t in TASKS if any(f.lower() in t.lower() for f in args.tasks)]
        if not tasks:
            print(f"No tasks matched filters: {args.tasks}")
            sys.exit(1)

    test_cases = len(personas) * len(tasks)
    output_path = _RESULTS_DIR / f"synthetic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    _init_csv(output_path)

    print(f"Running {len(personas)} personas × {len(tasks)} tasks × 2 modes = {test_cases * 2} rows")
    print(f"Delay: {args.delay}s")
    print(f"Assess timeout: {args.timeout}s")
    print(f"Streaming results to: {output_path}\n")

    results = run(
        personas=personas,
        tasks=tasks,
        delay=args.delay,
        timeout=args.timeout,
        output_path=output_path,
    )

    # Rewrite once at the end so the final file is guaranteed to be consistent.
    write_csv(results, output_path)
    print(f"\nResults written to: {output_path}")

    print_summary(results)


if __name__ == "__main__":
    main()

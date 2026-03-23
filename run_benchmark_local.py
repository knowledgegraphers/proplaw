"""
Benchmark runner — Phase 1 (local FAISS retrieval only).

Runs all 20 queries from benchmark_methodology_v2.md directly against the
FAISS retriever, bypassing FastAPI and the Anthropic API entirely.

For each query the top-5 retrieved chunks are logged and written to:
  benchmark_results_raw.json   — full chunk data per query
  benchmark_results_table.csv  — one row per query (Sources 1-5, latency, …)

Usage (from proplaw/ root, .venv active):
    python run_benchmark_local.py
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from propra.retrieval import rag  # noqa: E402  (must follow sys.stdout.reconfigure)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

JURISDICTION = "DE-BW"
K = 5
OUTPUT_DIR = Path(__file__).parent

_STATE_TO_ABBR: dict[str, str] = {
    "Baden-Württemberg":      "BW",
    "Bayern":                 "BY",
    "Berlin":                 "BE",
    "Brandenburg":            "BB",
    "Bremen":                 "HB",
    "Hamburg":                "HH",
    "Hessen":                 "HE",
    "Mecklenburg-Vorpommern": "MV",
    "Niedersachsen":          "NI",
    "Nordrhein-Westfalen":    "NW",
    "Rheinland-Pfalz":        "RP",
    "Saarland":               "SL",
    "Sachsen":                "SN",
    "Sachsen-Anhalt":         "ST",
    "Schleswig-Holstein":     "SH",
    "Thüringen":              "TH",
}


_STATE_TO_CODE: dict[str, str] = {
    "Baden-Württemberg":      "DE-BW",
    "Bayern":                 "DE-BY",
    "Berlin":                 "DE-BE",
    "Brandenburg":            "DE-BB",
    "Bremen":                 "DE-HB",
    "Hamburg":                "DE-HH",
    "Hessen":                 "DE-HE",
    "Mecklenburg-Vorpommern": "DE-MV",
    "Niedersachsen":          "DE-NI",
    "Nordrhein-Westfalen":    "DE-NW",
    "Rheinland-Pfalz":        "DE-RP",
    "Saarland":               "DE-SL",
    "Sachsen":                "DE-SN",
    "Sachsen-Anhalt":         "DE-ST",
    "Schleswig-Holstein":     "DE-SH",
    "Thüringen":              "DE-TH",
}


def _output_paths(state: str) -> tuple[Path, Path]:
    """Return timestamped (raw_json, csv) output paths for the given state."""
    date_str = datetime.date.today().strftime("%d-%m-%Y")
    abbr = _STATE_TO_ABBR.get(state, state.replace(" ", "_"))
    stem = f"benchmark_results_{date_str}_{abbr}"
    return OUTPUT_DIR / f"{stem}_raw.json", OUTPUT_DIR / f"{stem}_table.csv"

# ---------------------------------------------------------------------------
# 20 benchmark queries (from benchmark_methodology_v2.md)
# ---------------------------------------------------------------------------

QUERIES: list[dict] = [
    {"id": "Q01", "query": "Was sind bauliche Anlagen?",                                                                             "type": "Direct",              "difficulty": 1},
    {"id": "Q02", "query": "Was gilt als Aufenthaltsraum?",                                                                          "type": "Direct",              "difficulty": 1},
    {"id": "Q03", "query": "Was sind Stellplätze?",                                                                                  "type": "Structured",          "difficulty": 2},
    {"id": "Q04", "query": "Wann ist ein Bauvorhaben genehmigungspflichtig?",                                                        "type": "Structured",          "difficulty": 2},
    {"id": "Q05", "query": "Welche Anforderungen gelten für Abstandsflächen?",                                                       "type": "Structured",          "difficulty": 2},
    {"id": "Q06", "query": "Welche allgemeinen Anforderungen müssen bauliche Anlagen erfüllen?",                                     "type": "Structured",          "difficulty": 2},
    {"id": "Q07", "query": "Welche Anforderungen bestehen an Aufenthaltsräume?",                                                     "type": "Multi-step",          "difficulty": 3},
    {"id": "Q08", "query": "Welche Anforderungen gelten für den Brandschutz?",                                                       "type": "Multi-step",          "difficulty": 3},
    {"id": "Q09", "query": "Welche Anforderungen bestehen an Rettungswege in Gebäuden?",                                             "type": "Multi-step",          "difficulty": 3},
    {"id": "Q10", "query": "Welche Voraussetzungen müssen Grundstücke für eine Bebauung erfüllen?",                                  "type": "Multi-step",          "difficulty": 2},
    {"id": "Q11", "query": "Welche Zusammenhänge bestehen zwischen Brandschutzanforderungen und der Gebäudeklasse?",                 "type": "Cross-concept",       "difficulty": 3},
    {"id": "Q12", "query": "Welche Regelungen gelten für Stellplätze im Zusammenhang mit Gebäuden?",                                 "type": "Structured",          "difficulty": 2},
    {"id": "Q13", "query": "Wann ist ein Bauvorhaben verfahrensfrei?",                                                               "type": "Exception/Procedure", "difficulty": 3},
    {"id": "Q14", "query": "Welche Folgen kann Bauen ohne Genehmigung haben?",                                                       "type": "Multi-step",          "difficulty": 3},
    {"id": "Q15", "query": "Unter welchen Bedingungen kann die Nutzung einer baulichen Anlage untersagt werden?",                    "type": "Exception/Procedure", "difficulty": 3},
    {"id": "Q16", "query": "Unter welchen Voraussetzungen sind Abweichungen von bauordnungsrechtlichen Anforderungen möglich?",      "type": "Exception/Procedure", "difficulty": 3},
    {"id": "Q17", "query": "Wie hängen Abstandsflächen und Grundstücksbebauung zusammen?",                                          "type": "Cross-concept",       "difficulty": 3},
    {"id": "Q18", "query": "Welche Rolle spielen Rettungswege im Brandschutz?",                                                     "type": "Cross-concept",       "difficulty": 3},
    {"id": "Q19", "query": "Welche Voraussetzungen müssen erfüllt sein, bevor eine Nutzung aufgenommen werden darf?",               "type": "Multi-step",          "difficulty": 3},
    {"id": "Q20", "query": "Welche Pflichten hat der Bauherr im Bauprozess?",                                                       "type": "Structured",          "difficulty": 2},
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_benchmark(retriever: rag.Retriever, state: str, iso_code: str | None) -> list[dict]:
    """Run all 20 queries against the local FAISS index and return raw results."""
    results = []

    print(f"Running local FAISS benchmark  |  State: {state}  |  ISO code: {iso_code or 'None (all states)'}  |  k={K}")
    print(f"Queries: {len(QUERIES)}\n")

    for q in QUERIES:
        print(f"  [{q['id']}] {q['query'][:70]}")

        t_start = time.perf_counter()
        chunks = retriever.retrieve(query=q["query"], k=K, jurisdiction=iso_code)
        latency_ms = round((time.perf_counter() - t_start) * 1000)

        chunk_summaries = []
        for rank, c in enumerate(chunks, 1):
            summary = {
                "rank": rank,
                "jurisdiction_label": c.get("jurisdiction_label", ""),
                "jurisdiction": c.get("jurisdiction", ""),
                "source_paragraph": c.get("source_paragraph", ""),
                "score": round(float(c.get("score", 0.0)), 4),
                "text_preview": c.get("text", "")[:300],
                "text_full": c.get("text", ""),
            }
            chunk_summaries.append(summary)
            print(
                f"    [{rank}] {summary['jurisdiction_label']} · "
                f"{summary['source_paragraph']} · score={summary['score']:.4f}\n"
                f"        {summary['text_preview'][:120]}…"
            )

        top_score = chunk_summaries[0]["score"] if chunk_summaries else 0.0
        print(f"        latency={latency_ms}ms  top_score={top_score:.4f}\n")

        results.append({
            **q,
            "jurisdiction": iso_code,
            "latency_ms": latency_ms,
            "chunks": chunk_summaries,
            "top_score": top_score,
        })

    return results


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_raw(results: list[dict], path: Path, iso_code: str | None = None) -> None:
    """Write full chunk data per query as JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"system": "RAG-local", "jurisdiction": iso_code, "results": results},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Raw results written to:   {path}")


def write_csv(results: list[dict], path: Path) -> None:
    """Write one-row-per-query scoring table CSV."""
    fieldnames = [
        "Query ID", "Query", "Type", "Difficulty", "Latency (ms)",
        "Source 1", "Source 2", "Source 3", "Source 4", "Source 5",
        "Top Score", "Notes",
    ]

    def fmt_source(chunk: dict) -> str:
        return (
            f"{chunk['jurisdiction_label']} · "
            f"{chunk['source_paragraph']} · "
            f"{chunk['score']:.4f}"
        )

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            chunks = r.get("chunks", [])
            sources = {f"Source {i+1}": fmt_source(chunks[i]) if i < len(chunks) else "" for i in range(5)}
            writer.writerow({
                "Query ID": r["id"],
                "Query": r["query"],
                "Type": r["type"],
                "Difficulty": "★" * r["difficulty"],
                "Latency (ms)": r["latency_ms"],
                **sources,
                "Top Score": f"{r['top_score']:.4f}",
                "Notes": "",
            })

    print(f"Scoring table written to: {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Propra local FAISS benchmark runner")
    parser.add_argument(
        "--state",
        default="Baden-Württemberg",
        help="German federal state label (default: Baden-Württemberg)",
    )
    args = parser.parse_args()

    raw_output, csv_output = _output_paths(args.state)

    iso_code = _STATE_TO_CODE.get(args.state)
    if iso_code is None:
        print(f"WARNING: '{args.state}' not in STATE_TO_CODE lookup — searching all states (jurisdiction=None).")

    retriever = rag.Retriever()
    results = run_benchmark(retriever, state=args.state, iso_code=iso_code)

    print(f"\n{len(results)}/{len(QUERIES)} queries completed.\n")

    write_raw(results, raw_output, iso_code=iso_code)
    write_csv(results, csv_output)

    print(f"\nOutput files:")
    print(f"  {raw_output.name}")
    print(f"  {csv_output.name}")
    print("\nBenchmark complete.")

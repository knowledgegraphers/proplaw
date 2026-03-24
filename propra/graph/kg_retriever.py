"""
KG retriever for Propra.

Loads the NetworkX knowledge graph from propra/data/graph.pkl and exposes
get_related_chunks(), which takes a list of FAISS chunk dicts and returns
KG-derived context dicts by BFS-traversing the graph from each chunk's
source_paragraph.
"""

import logging
import sys
from collections import deque
from pathlib import Path
from typing import Any

import joblib

# Ensure UTF-8 output on Windows (cp1252 consoles would otherwise mangle
# German legal text in log messages).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graph — loaded once at module level
# ---------------------------------------------------------------------------

_GRAPH_PATH = Path(__file__).parent.parent / "data" / "graph.pkl"

_graph = None
_graph_load_attempted = False


def _load_graph():
    """Load the graph from disk exactly once; return None on failure."""
    global _graph, _graph_load_attempted
    if _graph_load_attempted:
        return _graph
    _graph_load_attempted = True

    if not _GRAPH_PATH.exists():
        logger.warning(
            "KG graph file not found at %s — KG enrichment disabled.", _GRAPH_PATH
        )
        return None

    try:
        _graph = joblib.load(_GRAPH_PATH)
        logger.info(
            "KG graph loaded: %d nodes, %d edges",
            _graph.number_of_nodes(),
            _graph.number_of_edges(),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load KG graph from %s: %s", _GRAPH_PATH, exc)
        _graph = None

    return _graph


# Trigger load at import time so the first real query pays no extra cost.
_load_graph()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_related_chunks(
    faiss_chunks: list[dict[str, Any]],
    hops: int = 2,
    max_per_seed: int = 5,
) -> list[dict[str, Any]]:
    """
    Traverse the KG from seed nodes matched to FAISS chunks and return
    KG-derived context dicts.

    Args:
        faiss_chunks:   List of FAISS result dicts, each with at least a
                        ``source_paragraph`` key.
        hops:           BFS depth (default 2).
        max_per_seed:   Maximum neighbour nodes collected per seed (default 5).

    Returns:
        List of dicts with keys: text, source_paragraph, jurisdiction,
        jurisdiction_label, kg_source, kg_node_id.
        Returns [] when the graph is unavailable or no seeds match.
    """
    g = _load_graph()
    if g is None:
        return []

    if not faiss_chunks:
        return []

    # Build a lookup: source_paragraph -> node_id for all graph nodes.
    # We use substring matching (chunk value IN node value) so a shorter
    # chunk reference like "§6 BbgBO" still matches "§6 Abs. 1 BbgBO".
    results: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()

    for chunk in faiss_chunks:
        chunk_sp = (chunk.get("source_paragraph") or "").strip()
        if not chunk_sp:
            continue

        # Find all seed nodes whose source_paragraph contains chunk_sp.
        seed_ids: list[str] = []
        for node_id, data in g.nodes(data=True):
            node_sp = (data.get("source_paragraph") or "").strip()
            if chunk_sp in node_sp:
                seed_ids.append(node_id)

        if not seed_ids:
            continue

        # BFS from each seed over both successors and predecessors.
        for seed in seed_ids:
            neighbours = _bfs_neighbours(g, seed, hops=hops, max_nodes=max_per_seed)
            for node_id in neighbours:
                if node_id in seen_node_ids:
                    continue
                seen_node_ids.add(node_id)
                node_data = g.nodes[node_id]
                results.append(_make_context_dict(node_id, node_data))

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bfs_neighbours(g, start: str, hops: int, max_nodes: int) -> list[str]:
    """
    Collect up to max_nodes unique node IDs reachable from start within hops
    steps, traversing both successors and predecessors.

    The start node itself is excluded from the result.
    """
    visited: set[str] = {start}
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    collected: list[str] = []

    while queue and len(collected) < max_nodes:
        current, depth = queue.popleft()
        if depth >= hops:
            continue
        neighbours = list(g.successors(current)) + list(g.predecessors(current))
        for nb in neighbours:
            if nb in visited:
                continue
            visited.add(nb)
            collected.append(nb)
            if len(collected) >= max_nodes:
                break
            queue.append((nb, depth + 1))

    return collected


def _make_context_dict(node_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Build the standardised context dict from a graph node."""
    jurisdiction = data.get("jurisdiction") or ""
    jurisdiction_label = data.get("jurisdiction_label") or jurisdiction
    return {
        "text": data.get("text") or "",
        "source_paragraph": data.get("source_paragraph") or "",
        "jurisdiction": jurisdiction,
        "jurisdiction_label": jurisdiction_label,
        "kg_source": True,
        "kg_node_id": node_id,
    }

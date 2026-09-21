"""Check that FAISS ``source_file`` stems and KG node prefixes agree per state.

GraphRAG bridges the FAISS index and the knowledge graph by deriving a node ID
from chunk metadata: ``f"{source_file}_§{section}"`` (see
``propra.graph.kg_retriever._chunk_to_node_id``). ``source_file`` is the stem
of the ``propra/data/txt/*.txt`` file (``JURISDICTION_MAP`` in
``propra.retrieval.rag``), while the KG nodes are created with the ``prefix``
of the matching ``_STATE_REGISTRY`` entry in ``propra.graph.build_graph``.

If the two differ for a state, every KG lookup for that state silently misses
and GraphRAG degrades to plain vector retrieval. This test pins that contract
for all 16 Bundesländer, joined via their ISO 3166-2 jurisdiction code.
"""

import pytest

from propra.graph.build_graph import _STATE_REGISTRY
from propra.graph.kg_retriever import _chunk_to_node_id
from propra.retrieval.rag import JURISDICTION_MAP

# jurisdiction code -> (FAISS stem, human label), built from the FAISS side
_STEM_BY_CODE = {
    meta["code"]: (stem, meta["label"]) for stem, meta in JURISDICTION_MAP.items()
}

_STATES = [
    pytest.param(cfg, id=_STEM_BY_CODE.get(cfg["jurisdiction"], ("?", cfg["name"]))[1])
    for cfg in _STATE_REGISTRY
]


def test_registry_covers_all_16_states():
    """Sanity check: the KG registry holds exactly the 16 Bundesländer (no MBO)."""
    codes = sorted(cfg["jurisdiction"] for cfg in _STATE_REGISTRY)
    assert len(codes) == 16, codes
    assert len(set(codes)) == 16, "duplicate jurisdiction in _STATE_REGISTRY"
    assert "DE-MBO" not in codes


@pytest.mark.parametrize("cfg", _STATES)
def test_faiss_stem_and_kg_prefix_yield_same_node_id(cfg: dict):
    """FAISS source_file stem and KG prefix must produce the same node ID for § 1."""
    code = cfg["jurisdiction"]
    assert code in _STEM_BY_CODE, f"no txt/JURISDICTION_MAP entry for {code}"
    stem, label = _STEM_BY_CODE[code]

    # What GraphRAG derives at query time from a FAISS chunk of this state
    derived = _chunk_to_node_id({"source_file": stem, "source_paragraph": "§ 1 Anwendungsbereich"})

    # What build_graph actually names the node
    expected = f"{cfg['prefix']}§1"

    assert derived == expected, (
        f"{label} ({code}): FAISS source_file stem '{stem}' derives node ID "
        f"'{derived}', but the KG uses prefix '{cfg['prefix']}' -> '{expected}'. "
        f"GraphRAG will never find KG nodes for this state."
    )

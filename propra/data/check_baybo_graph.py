"""Quick sanity-check: print BayBO node stats and key section content from graph.pkl."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pickle  # noqa: E402
from collections import Counter  # noqa: E402
from pathlib import Path  # noqa: E402

G = pickle.loads(Path("propra/data/graph.pkl").read_bytes())
out = []
out.append(f"Total nodes: {G.number_of_nodes()}  edges: {G.number_of_edges()}")

# Check content nodes (sentence-level) for key sections
for prefix, label in [
    ("BayBO_§6_",   "Abstandsflächen – fence/boundary distances"),
    ("BayBO_§57_",  "Verfahrensfreie – permit-free builds"),
    ("BayBO_§44a_", "Solaranlagen – solar panels"),
    ("BayBO_§82c_", "Bau-Turbo – fast-track planning"),
]:
    nodes = sorted(n for n in G.nodes if n.startswith(prefix))
    out.append(f"\n{prefix[:-1]} [{label}] — {len(nodes)} sentence nodes")
    for n in nodes[:2]:
        text = G.nodes[n].get("text", "")[:110]
        src  = G.nodes[n].get("source_paragraph", "")
        out.append(f"  {n}  src={src!r}")
        out.append(f"    {text!r}")

# Type distribution
out.append("\nBayBO node type distribution:")
types = Counter(d.get("type") for n, d in G.nodes(data=True) if n.startswith("BayBO_§"))
for t, c in types.most_common(10):
    out.append(f"  {t:<40} {c}")

Path("propra/data/baybo_check_result.txt").write_text("\n".join(out), encoding="utf-8")
print("Done — see propra/data/baybo_check_result.txt")

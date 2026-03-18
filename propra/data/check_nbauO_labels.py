"""Check that every NBauO section anchor type in the graph matches the fine inventory."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from propra.graph.builder import load_graph

G = load_graph("propra/data/graph.pkl")

inv_types: dict[str, str] = {}
current_sec = None
for line in open("propra/data/node inventory/NBauO_node_inventory_fine.md", encoding="utf-8"):
    m = re.match(r"^### §\s*(\w+)", line)
    if m:
        current_sec = m.group(1).lower()
    m2 = re.match(r"^\*\*type:\*\*\s*(\S+)", line)
    if m2 and current_sec:
        inv_types[current_sec] = m2.group(1)
        current_sec = None

mismatches = []
for nid, data in G.nodes(data=True):
    if not nid.startswith("NBauO_§"):
        continue
    suffix = nid.split("_§")[1]
    if "." in suffix or "_" in suffix:
        continue
    sec_num = suffix.lower()
    graph_type = data.get("type")
    inv_type = inv_types.get(sec_num)
    if inv_type and graph_type != inv_type:
        mismatches.append((nid, graph_type, inv_type))

if mismatches:
    print(f"MISMATCHES ({len(mismatches)}):")
    for nid, gt, it in mismatches:
        print(f"  {nid}: graph={gt}  inventory={it}")
    sys.exit(1)
else:
    print(f"ALL MATCH — {len(inv_types)} sections checked, 0 mismatches")

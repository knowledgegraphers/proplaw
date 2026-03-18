"""Check what parse_inventory produces for BayBO fine inventory."""
from propra.graph.parse_inventory import parse_inventory
from pathlib import Path

nodes = parse_inventory(
    path=Path("propra/data/node inventory/BayBO_node_inventory_fine.md"),
    source_suffix="BayBO",
    node_prefix="BayBO_",
)

out = []
out.append(f"Total nodes loaded: {len(nodes)}")

matched = [n for n in nodes if "44a" in n.id or "82c" in n.id
           or "44a" in n.source_paragraph or "82c" in n.source_paragraph]
out.append(f"Nodes with 44a or 82c: {len(matched)}")
for n in matched[:5]:
    out.append(f"  {n.id}  src={n.source_paragraph!r}  text={n.text[:80]!r}")

out.append("\nFirst 3 nodes:")
for n in nodes[:3]:
    out.append(f"  {n.id}  src={n.source_paragraph}")

Path("propra/data/parse_check.txt").write_text("\n".join(out), encoding="utf-8")
print("done")

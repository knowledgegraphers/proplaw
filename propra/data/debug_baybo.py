"""Debug BayBO.txt structure to understand Art. heading patterns."""
import re
from pathlib import Path

data = Path("propra/data/txt/BayBO.txt").read_text(encoding="utf-8")
lines = data.splitlines()

print(f"Total lines: {len(lines)}")
print(f"Total chars: {len(data)}\n")

# Find all 'Art. N' occurrences
art_re = re.compile(r"Art\.\s+(\d+[a-zA-Z]?)\s*(\S*)")
for i, line in enumerate(lines):
    for m in art_re.finditer(line):
        num = m.group(1)
        after = m.group(2)[:30]
        pos_in_line = m.start()
        ctx_before = line[max(0, pos_in_line-20):pos_in_line]
        print(f"L{i+1:4d} pos={pos_in_line:4d} Art.{num:5s} after={after!r:30s} ctx={ctx_before!r}")

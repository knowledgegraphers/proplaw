# Start here

You don't have to review everything at once.

**What to do:** Open [INDEX.md](INDEX.md). The list is ordered **smallest first** (fewest edges per file). Open the first file, check that each "From" → "To" link makes sense, then move to the next. Leave the big files (references, supplements) for when you're ready.

**Only the small stuff?** To generate section files only for relation types with ≤10 edges (quick audit):
```bash
python -m propra.graph.audit_relations --sections-dir propra/data/audit_sections --max-edges-per-relation 10
```

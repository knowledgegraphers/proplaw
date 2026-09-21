# CLAUDE.md — Agent Conventions for PropLaw

This file defines the rules and conventions the Claude Code agent must follow throughout this project. Read it before making any change to this codebase.

---

## Product Context

- PropLaw is a **consumer product for German homeowners**. It is not a developer tool and not a B2B product.
- The end user is someone like **Renate** (67, retired, low technical confidence) or **Tobias** (41, wants to be informed before talking to an architect).
- Every output the product generates must be:
  - Written in **plain German**
  - Include a **cited source** (paragraph, regulation name, jurisdiction)
  - End with a **concrete next action** for the user
- Never generate UI copy that sounds like a legal disclaimer. It should sound like a **knowledgeable friend explaining the rules**.

---

## Code Conventions

### Python

- All Python files must include a **module-level docstring** explaining what the file does.
- All functions over 20 lines must include a **docstring**.
- No hardcoded API keys — use environment variables loaded from `.env`. The `.env` file must never be committed.
- All API endpoints must include **input validation** (Pydantic) and return structured error messages:
  - **English** for developers (in the `detail` field)
  - **German** for end users (in the `user_message` field)
- Never push directly to main, always open a PR.

### JavaScript / React

- Components go in `propra/frontend/src/components/`.
- Frontend design rules (mobile-first, Tailwind, colours, typography) live in `propra/frontend/CLAUDE.md` and load automatically when working on frontend files.

---

## AI / Data Conventions

### Prompts

- Every LLM prompt must be stored as a `.txt` or `.md` file in `propra/prompts/`. **Never inline prompts in code.**
- Every prompt file must begin with a comment block containing:
  ```
  # WHAT: What this prompt does
  # INPUTS: What variables it expects
  # OUTPUT FORMAT: What structure it returns
  ```

### LLM Outputs

- All LLM outputs must be **validated against a Pydantic schema** before being passed to the frontend.
- **Confidence must never be set to `HIGH`** when B-Plan data is absent from the corpus.

### Knowledge Graph

- Every **node** must include: `type`, `jurisdiction`, `source_paragraph`, `text`
- Every **edge** must include: `relation`, `sourced_from`

---

## Testing Conventions

- Every API endpoint must have at least **one happy-path test** and **one error-path test** in `propra/tests/`.
- Every prompt must be tested against at least **5 sample inputs** before being used in the pipeline.
- KG queries must be tested against the **10 benchmark questions** defined in `propra/eval/benchmark.py`.

---

## Commands & Fallstricke

- Start: `uvicorn propra.main:app --reload` — **nicht** `api.main` wie in der README.
- Tests: `PYTHONPATH=. pytest propra/tests/`, einzeln mit `-k`.
- Vollcheck: `bash kontrolle.sh`.
- Paket heißt `propra`, Produkt heißt PropLaw — Absicht, nicht umbenennen.
- `propra/graph/*_section_edges.py` sind generiert — niemals von Hand editieren.
- FAISS `source_file` und KG-Präfix müssen identisch sein, sonst greift GraphRAG nicht.

---

## Findings & Tagesplanung

`propra/benchmark/results/FINDINGS.md` ist die einzige Liste offener Befunde.
Jedes OPEN-Finding traegt ein Feld `**Reviewed:**` — das Datum, an dem es
zuletzt angeschaut *und entschieden* wurde. Alter = heute minus Reviewed.

- Die Tagesplanung zieht aus dieser Datei: mindestens ein Block pro Arbeitstag
  kommt aus der OPEN-Liste, und zwar das aelteste Finding, das in die Zeit passt.
- Ein OPEN-Finding ueber 21 Tage ohne Sichtung muss eingeplant oder nach
  `DEFERRED` verschoben werden — mit Begruendung und `Deferred until:` Datum.
- Bei der **Neuanlage** eines Findings setzt der anlegende Lauf `Reviewed:` auf
  das Anlagedatum. Das startet die Alterung, statt sie zu verbergen.
- Jede **spaetere** Aenderung von `Reviewed:` macht ausschliesslich der Skill
  `/tagesplan`, wenn Sebastian die Planung durchgeht. Nie von Hand, nie durch
  einen unbeaufsichtigten Lauf: ein nachtraeglich gesetztes Datum verbirgt genau
  die Alterung, die sichtbar bleiben soll.
- Ein montaeglicher geplanter Task meldet ueberfaellige Findings, ohne die Datei
  anzufassen.

Hintergrund: Blocker B-01 stand ab dem 06.09. ganz oben im Audit und wurde erst
dreizehn Tage spaeter behoben. Sechs weitere Findings lagen fuenf Monate.
Aufschreiben allein bewirkt nichts.

## What This Agent Must Never Do

- Never generate **legal advice** — always regulatory information with cited sources.
- Never return a **`HIGH` confidence verdict** when corpus coverage is incomplete.
- Never add **features outside the current epic scope** without flagging it first with a comment and asking.
- Never skip **mobile optimisation** on any UI component.
- Never **inline secrets or API keys** in code, prompts, or config files.
- Never commit the `.env` file.

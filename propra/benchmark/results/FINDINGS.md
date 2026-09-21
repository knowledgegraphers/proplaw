# PropLaw — Benchmark Findings Log

**Project:** neuefische AIPM Bootcamp Capstone 2025/2026
**Corpus:** BbgBO (DE-BB) — Phase 1 Baseline
**Methodology:** benchmark\_methodology\_v2.md

\---

## How to use this file

* One entry per finding. Assign sequential ID (F001, F002, ...).
* Status: OPEN / IN REVIEW / DEFERRED / CLOSED
* Reviewed: date an OPEN finding was last looked at. A stale Reviewed
  date is the signal, not noise.
* On creation, the run that adds a finding sets Reviewed to the date it
  was added. That starts the ageing clock instead of hiding it.
* Every later change to Reviewed is made by the /tagesplan skill during
  day planning — never by hand, and never by an unattended job.
* An OPEN finding unreviewed for more than 21 days must be scheduled
  into a day plan or moved to DEFERRED with a reason and a review date.
* Update status and add resolution when closed.
* Reference finding IDs in CSV notes column for traceability.
* Commit this file with every benchmark run.

\---

## Open Findings

### F004 — Q13 Verfahrensfreiheit — retrieval misses § 61 BbgBO (corpus complete)

**Date:** 2026-03-26
**Status:** OPEN — corpus extraction issue
**Reviewed:** 2026-09-20
**Query:** Q13 — Wann ist ein Bauvorhaben verfahrensfrei?
**Finding:** Both RAG and GraphRAG scored Retrieval=0 for this query.
The BbgBO corpus does not contain sufficient content from the
verfahrensfreie Vorhaben list (§ 61 BbgBO equivalent). Top FAISS
score was 0.70 — retrieval fired but returned wrong context.
This is a corpus extraction gap, not a pipeline failure.
**Action:** Re-extract BbgBO §61 section. Verify chunk content
covers the full list of verfahrensfreie Vorhaben.
**Impact:** Q13 scores (2/6 both systems) understate system quality.
Will improve after corpus fix.
**Owner:** Sebastian

\---

### F005 — Q1 cold-start latency outlier

**Date:** 2026-03-26
**Status:** OPEN — known, document only
**Reviewed:** 2026-09-20
**Finding:** Q1 RAG retrieval\_ms = 37,877ms (vs 20-70ms for all
subsequent queries). This is the sentence-transformer model loading
on first FAISS call. Skews RAG mean retrieval\_ms significantly.
**Action:** Document in benchmark report. Exclude Q1 from latency
aggregates or note as cold-start outlier. Consider warming the model
before benchmark runs in future.
**Impact:** Mean RAG retrieval\_ms is inflated. Real retrieval latency
is 20-70ms after warm-up.
**Messung 2026-09-21:** Der in der Produktion gemessene Cold Start
betraegt 82,9 s, nicht die rund 40 s aus dem Benchmark. Die
Benchmark-Zahl erfasst nur das Laden des Embedding-Modells, nicht das
Hochfahren der schlafenden Render-Instanz. Siehe F012.
**Owner:** Sebastian (documentation only)

\---

### F006 — Q11 GraphRAG +3 over RAG — classification layer effect

**Date:** 2026-03-26
**Status:** DEFERRED — bis Pitch-Vorbereitung
**Deferred until:** 2026-11-02
**Reviewed:** 2026-09-20
**Reason:** Die urspruengliche Hypothese (Delta ohne KG-Chunks =
Classifier-Effekt) ist auf der aktuellen Pipeline nicht mehr
untersuchbar — Q11 GraphRAG 4/6 vs RAG 2/6 mit 31 KG-Chunks in
Stage 3. Die Frage dahinter bleibt offen und ist die wichtigere:
traegt GraphRAG messbar bei? Audit v7.0 misst +0,03 bis +0,07 auf
5er-Skala bei +2 s Latenz, 49:22 in 71 Paarvergleichen — Richtung,
kein Beweis. Zur Pitch-Vorbereitung mit den Stage-3-Daten als
KG-Evidenz neu formulieren. Wenn zu diesem Datum kein Pitch
terminiert ist, erneut entscheiden statt weiter verschieben.
**Query:** Q11 — Welche Zusammenhänge bestehen zwischen
Brandschutzanforderungen und der Gebäudeklasse?
**Finding:** GraphRAG scored 6/6 vs RAG 3/6 on this cross-concept
query despite KG chunks = 0. The delta must come from the goal
classification step (kg\_query.query\_by\_category) influencing FAISS
retrieval context or the synthesis prompt. This is the strongest
single piece of evidence for KG architectural value in this run.
**Action:** Investigate what the classifier returned for Q11 and
how it affected retrieval. Document as pitch evidence.
**Impact:** Positive. Strengthens dual-retrieval hypothesis even
before KG enrichment is fully active.
**Owner:** Sebastian + Sumit

\---

### F010 — State-to-corpus-filename mapping hardcoded in six places

**Date:** 2026-09-19
**Status:** OPEN — refactor required
**Reviewed:** 2026-09-19
**Finding:** The mapping Bundesland -> corpus file stem is maintained
independently in six places: JURISDICTION\_MAP in retrieval/rag.py,
\_STATE\_REGISTRY in graph/build\_graph.py, \_CORPUS\_MAP in
benchmark/judge\_runner.py (both the ISO-code and the plain-label
variant), jurisdiction\_from\_filename in data/bulk\_inventory.py, and
data/audit\_extraction\_artifacts.py together with its test. Any rename
must be applied to all six by hand; F009 is what happens when one of
them drifts. This is the same class of defect as F003 (FAISS metadata
and KG attributes agreeing only by convention, with no single source of
truth). test\_prefix\_alignment.py covers only the first two.
**Action:** Introduce one canonical registry (stem, ISO code, label,
KG prefix) and derive the other five from it, or extend
test\_prefix\_alignment.py to assert all six agree.
**Impact:** Root cause of F009. Until fixed, every future corpus
rename or new state carries the same silent-mismatch risk.
**Owner:** Sebastian

\---

### F011 — 89 open ruff findings in production code

**Date:** 2026-09-19
**Status:** OPEN — known, deferred
**Reviewed:** 2026-09-19
**Finding:** ruff 0.16.x widened its default rule set (UP, I, SIM, B,
FLY, BLE, ...). Against the current code it reports 89 findings in
real modules (plus \~3,000 in the generated \*\_section\_edges.py files,
which are now excluded via pyproject.toml). ruff is deliberately
pinned to 0.15.7 in ci.yml, .pre-commit-config.yaml and locally, so
CI stays green and the 89 stay invisible until the pin is bumped.
**Action:** Bump the pin to 0.16.x in a dedicated PR and resolve the
89 findings there. Most are auto-fixable (UP006, I001, UP045, RUF100).
**Impact:** No runtime impact. Lint debt only; a version bump without
the cleanup would turn CI red.
**Owner:** Sebastian

\---

### F012 — Anthropic-Key arbeitet in einem fremden Deployment

**Date:** 2026-09-21
**Status:** OPEN — Zugriffs- und Kostenrisiko
**Reviewed:** 2026-09-21
**Finding:** Der Render-Service proplaw-graphrag wurde in der
Capstone-Phase von einer ehemaligen Teamkollegin deployt. Sebastian hat
keinen Zugriff auf diesen Service, kann dort weder Konfiguration noch
Logs einsehen und ihn nicht abschalten. Der dort hinterlegte API-Key
gehoert zu seinem Anthropic-Account — fremde Last laeuft also auf seine
Rechnung, ohne dass er sie sehen oder begrenzen kann. Der Service ist
nachweislich erreichbar: ein POST auf /api/assess antwortet am
2026-09-21 mit 422 nach 82,9 s, der Endpoint nimmt Anfragen also
weiterhin entgegen (Cold Start, siehe F005). Der Key war nie im Repo:
git log --all -S"sk-ant-" liefert keinen Treffer, .env steht in
.gitignore.
**Korrektur zu Audit v7.0:** Audit v7.0 beschreibt den Endpoint unter
Blocker B-02 als Eigentum des Projekts. Das ist nachweislich falsch —
das Deployment gehoert der ehemaligen Kollegin, nicht diesem Projekt.
Die Audit-Datei selbst bleibt unveraendert; diese Zeile ist die
Korrektur.
**Action:** Key im Anthropic-Account widerrufen, neuen Key anlegen und
ausschliesslich lokal in .env halten. Vorher die Kollegin informieren,
damit ihr Service nicht unangekuendigt ausfaellt.
**Impact:** Bis zum Widerruf laeuft ein Schluessel unter fremder
Kontrolle, dessen Nutzung Sebastian weder einsehen noch stoppen kann.
**Owner:** Sebastian

\---

### F013 — Backend-URL hartkodiert im Frontend

**Date:** 2026-09-21
**Status:** OPEN — Konfigurationsfehler
**Reviewed:** 2026-09-21
**Finding:** propra/frontend/src/pages/AdvisorPage.tsx ruft die
Render-URL hart kodiert auf (Zeile 423,
https://proplaw-graphrag.onrender.com/api/assess). Die Adresse gehoert
in VITE\_API\_URL, damit lokale, Staging- und Produktionsumgebung ohne
Codeaenderung auseinandergehalten werden koennen. Solange sie im Code
steht, zeigt das Frontend zwangslaeufig auf das fremde Deployment aus
F012.
**Action:** Aufruf auf VITE\_API\_URL umstellen, Variable in .env und in
der Deployment-Konfiguration setzen. In Audit v7.0 als Erstaufgabe des
ux-engineer gefuehrt.
**Impact:** Kein Umschalten der Umgebung ohne Rebuild; koppelt das
Frontend an F012.
**Owner:** Sebastian (ux-engineer)

\---

## Closed Findings

### F001 — Q18 GraphRAG 0/6 suspicious score

**Date:** 2026-03-26
**Status:** CLOSED — superseded 2026-09-20
**Query:** Q18 — Welche Rolle spielen Rettungswege im Brandschutz?
**Finding:** GraphRAG scored 0/6 (Retrieval=0, Reasoning=0, Grounding=0).
Answer content is identical to RAG answer (KG chunks = 0 for this run,
meaning both systems received the same context and prompt). A 0/6 score
is inconsistent with identical content scoring 6/6 for RAG. Likely a
judge API error or empty response during the GPT-4o judge run.
**Action:** Re-run judge\_runner.py on Q18 GraphRAG row specifically.
Expert review required before including this score in aggregates.
**Impact:** Q18 GraphRAG excluded from current mean totals.
**Resolution:** Superseded. The 0/6 was a judge artefact of the 2026-03-26 run.
In Stage 3 (judged\_baseline\_20260330\_2254.csv, commit ae0f4db) Q18
scores 4/6 for both RAG and GraphRAG; the 2026-03-26 run is no longer
the basis of any aggregate. No expert review needed. Closed during
day planning 2026-09-20.
**Owner:** Matteo (expert validation)

\---

### F002 — 3 missing judge scores (API timeout)

**Date:** 2026-03-26
**Status:** CLOSED — superseded 2026-09-20
**Affected rows:** Q5 GraphRAG, Q14 RAG, Q14 GraphRAG, Q16 GraphRAG
**Finding:** Judge runner failed to score these rows during the
2026-03-26 run. Likely Anthropic/OpenAI API timeout or rate limit.
The runner's resume support means re-running will skip already-scored
rows and only fill the missing ones.
**Action:** Re-run: python -m benchmark.judge\_runner benchmark/results/judged\_baseline\_20260326\_1357.csv
**Impact:** Missing rows excluded from aggregates. RAG mean based on
19/20 rows, GraphRAG mean based on 16/20 rows.
**Resolution:** Superseded by later runs. Source: judged\_baseline\_20260330\_2254.csv
(Stage 3), 40/40 rows judged (total\_draft populated, no gaps). The
2026-03-26 CSV was not backfilled and is not used in aggregates.
Closed during day planning 2026-09-20.
**Owner:** Sebastian

\---

### F003 — KG enrichment inactive (0 chunks for all queries)

**Date:** 2026-03-26
**Status:** CLOSED — resolved in Stage 2/3, closed 2026-09-20
**Finding:** get\_related\_chunks() returned 0 KG-derived chunks for
every query in the DE-BB run. Root cause: source\_paragraph string
matching between FAISS chunk metadata and graph node attributes is
not connecting. FAISS chunks use formats like "§ 6 BbgBO" while graph
nodes may use slightly different formats. As a result, RAG and
GraphRAG answers are identical for this entire run — the GraphRAG
vs RAG delta cannot be meaningfully measured yet.
**Action:** Sumit to investigate source\_paragraph format alignment
between rag.py chunk metadata and kg\_retriever.py node matching logic.
**Impact:** RAG vs GraphRAG comparison is invalid for this run.
GraphRAG scores reflect pure FAISS retrieval, not KG enrichment.
**Resolution:** Resolved in Stage 2/3 (commits b0caa2e, ae0f4db). Source:
judged\_baseline\_20260330\_2254.csv, column kg\_chunks\_added —
GraphRAG receives 5–35 KG chunks per query there, vs 0 in this run.
Lineage: F003 (KG enrichment silent for all of DE-BB,
source\_paragraph format mismatch) → F009 (same symptom, limited to
DE-BW/DE-HB, FAISS stem vs KG prefix; fixed 2026-09-19, guarded by
test\_prefix\_alignment.py) → F010 (root cause class: state-to-corpus
mapping kept in six places without a single source of truth; OPEN).
The residual risk of F003 lives on in F010. Closed during day
planning 2026-09-20.
**Owner:** Sumit

\---

### F007 — GraphRAG latency incorrectly measured (fixed)

**Date:** 2026-03-26
**Status:** CLOSED — fixed 2026-03-26
**Finding:** benchmark\_runner.py was measuring retrieval latency only,
not full pipeline latency. Two compounding bugs: (1) timer stopped
before LLM synthesis call, (2) GraphRAG FAISS call was cache-warm
after prior RAG call, causing \~44ms mean vs RAG \~769ms.
**Resolution:** Split into retrieval\_ms (retrieval only) and total\_ms
(full pipeline). Timer now wraps full retrieval + synthesis block.
Committed to feature/benchmark-runner-v2.
**Owner:** Sebastian

\---

### F008 — assess.py k=5 (updated to k=8)

**Date:** 2026-03-26
**Status:** CLOSED — fixed 2026-03-26
**Finding:** Production assess.py used k=5 for FAISS retrieval.
Annex-heavy and exception-heavy queries (e.g. Q13 Verfahrensfreiheit)
need more chunks to cover list-item content spread across multiple
chunks. k=8 increases coverage at negligible cost.
**Resolution:** k updated to 8 in assess.py and benchmark\_runner.py.
Committed to feature/benchmark-runner-v2.
**Owner:** Sebastian

\---

### F009 — FAISS/KG prefix misalignment for BW and HB (fixed)

**Date:** 2026-09-19
**Status:** CLOSED — fixed 2026-09-19
**Finding:** For Baden-Württemberg and Bremen the FAISS source\_file
stem (BauO\_BW, LBO\_HB) did not match the KG node prefix (BW\_LBO\_,
BremLBO\_). kg\_retriever.\_chunk\_to\_node\_id() derives the node ID as
f"{source\_file}\_§{section}", so every KG lookup for these two states
missed and GraphRAG silently degraded to plain FAISS retrieval —
the same symptom as F003, limited to DE-BW and DE-HB. The other 14
states were aligned.
**Resolution:** FAISS side aligned to the KG side (BW\_LBO and
BremLBO are the official abbreviations): txt files renamed via git mv,
JURISDICTION\_MAP in rag.py, \_CORPUS\_MAP in judge\_runner.py,
bulk\_inventory.py and audit\_extraction\_artifacts.py updated, FAISS
index rebuilt (6564 vectors). Regression test
propra/tests/test\_prefix\_alignment.py checks all 16 states by joining
JURISDICTION\_MAP and \_STATE\_REGISTRY on the ISO code and running
\_chunk\_to\_node\_id() against the registry prefix. On
chore/claude-setup.
**Owner:** Sebastian

\---

*Last updated: 2026-09-20 — day planning: F001, F002, F003 closed (superseded by Stage 3), F006 deferred until 2026-11-02, F004 and F005 scheduled*

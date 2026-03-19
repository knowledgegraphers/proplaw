# Benchmark Methodology — RAG vs GraphRAG
**Version:** 2.0  
**Last updated:** 2026-03-18  
**Status:** Ready — ground truth finalised, review by teammate pending

---

## Purpose

This benchmark is designed to evaluate and compare the performance of:

- RAG (Retrieval-Augmented Generation)
- GraphRAG

The comparison is based on how each system answers a fixed set of 20 legal queries using German Landesbauordnung (LBO).

The goal is to measure how well each system:

- retrieves relevant legal information
- reasons over that information
- avoids unsupported or fabricated content

> **Scope note:** This benchmark measures quality of legal retrieval and reasoning under controlled conditions. Latency and token cost are tracked separately as secondary efficiency metrics (see [Output Format](#output-format)).

---

## Query Set (20)

Each query is labeled with a **Type** and **Difficulty**.

- Type: Direct, Structured, Multi-step, Exception/Procedure, Cross-concept
- Difficulty: ★ (low), ★★ (medium), ★★★ (high)

| # | Query | Type | Difficulty |
|---|-------|------|------------|
| 1 | Was sind bauliche Anlagen? | Direct | ★ |
| 2 | Was gilt als Aufenthaltsraum? | Direct | ★ |
| 3 | Was sind Stellplätze? | Structured | ★★ |
| 4 | Wann ist ein Bauvorhaben genehmigungspflichtig? | Structured | ★★ |
| 5 | Welche Anforderungen gelten für Abstandsflächen? | Structured | ★★ |
| 6 | Welche allgemeinen Anforderungen müssen bauliche Anlagen erfüllen? | Structured | ★★ |
| 7 | Welche Anforderungen bestehen an Aufenthaltsräume? | Multi-step | ★★★ |
| 8 | Welche Anforderungen gelten für den Brandschutz? | Multi-step | ★★★ |
| 9 | Welche Anforderungen bestehen an Rettungswege in Gebäuden? | Multi-step | ★★★ |
| 10 | Welche Voraussetzungen müssen Grundstücke für eine Bebauung erfüllen? | Multi-step | ★★ |
| 11 | Welche Zusammenhänge bestehen zwischen Brandschutzanforderungen und der Gebäudeklasse? | Cross-concept | ★★★ |
| 12 | Welche Regelungen gelten für Stellplätze im Zusammenhang mit Gebäuden? | Structured | ★★ |
| 13 | Wann ist ein Bauvorhaben verfahrensfrei? | Exception/Procedure | ★★★ |
| 14 | Welche Folgen kann Bauen ohne Genehmigung haben? | Multi-step | ★★★ |
| 15 | Unter welchen Bedingungen kann die Nutzung einer baulichen Anlage untersagt werden? | Exception/Procedure | ★★★ |
| 16 | Unter welchen Voraussetzungen sind Abweichungen von bauordnungsrechtlichen Anforderungen möglich? | Exception/Procedure | ★★★ |
| 17 | Wie hängen Abstandsflächen und Grundstücksbebauung zusammen? | Cross-concept | ★★★ |
| 18 | Welche Rolle spielen Rettungswege im Brandschutz? | Cross-concept | ★★★ |
| 19 | Welche Voraussetzungen müssen erfüllt sein, bevor eine Nutzung aufgenommen werden darf? | Multi-step | ★★★ |
| 20 | Welche Pflichten hat der Bauherr im Bauprozess? | Structured | ★★ |

**Distribution note:** The query set is intentionally weighted toward higher complexity (11 of 20 queries are ★★★, of which 8 are Multi-step or Cross-concept). This design choice favours tasks where graph traversal is hypothesised to have a structural advantage. Direct and Structured queries (★–★★) serve as a baseline and are expected to be competitive between systems. Interpreting results should account for this weighting — a raw score advantage for GraphRAG does not imply superiority at simpler retrieval tasks.

---

## Design Rationale for Query Set

The 20 benchmark queries are intentionally **normalized and structured** rather than written in natural, user-style language.

This choice is based on the following constraints:

- **Comparability**: All systems must be evaluated on identical inputs. Normalized queries reduce variance caused by wording.
- **Isolation of reasoning**: Each query targets a specific legal concept or relationship (e.g. Abstandsflächen, Rettungswege, Abweichungen).
- **Controlled difficulty**: Queries are categorized (Direct → Cross-concept) to ensure coverage of different reasoning types.
- **Cross-state applicability**: Queries avoid state-specific phrasing so they remain valid across all LBO texts.

As a result, the benchmark measures system performance on **legal retrieval and reasoning under controlled conditions**, not on handling real-world user phrasing.

---

## Additional User-Style Queries (Not Scored)

The following queries reflect how users typically phrase questions in practice. They are written in English to simulate a non-German speaker interacting with the system. They are included for qualitative inspection only and are not part of the scored benchmark.

1. Can I build directly on the property boundary?
2. Do I need a permit to convert my attic into a room?
3. How far does my house need to be from my neighbor's property?
4. What happens if I already built something without approval?
5. Can the authorities stop me from using my building?

---

## Ground Truth

Each query is associated with:

- A **section family** (e.g. definitions, Abstandsflächen, Rettungswege) pointing to the relevant part of the LBO corpus
- A set of **minimum answer elements** — exactly 3 concrete facts or legal conditions that must be present in a correct answer, derived directly from the TXT corpus

> **Ground truth status: FINAL.** Elements were extracted from the raw LBO TXT corpus by a separate model (GPT-4o) with no access to the RAG or GraphRAG systems or their outputs. This ensures independence from the evaluated systems.

### Ground Truth Table (Final)

| # | Query | Section Family | Minimum Answer Elements |
|---|-------|----------------|------------------------|
| 1 | Was sind bauliche Anlagen? | Definitionen | mit dem Boden verbunden; aus Bauprodukten hergestellt; bauliche Anlagen und Einrichtungen |
| 2 | Was gilt als Aufenthaltsraum? | Definitionen | nicht nur vorübergehender Aufenthalt; geeignet für Menschen (Wohnen/Arbeiten); Abgrenzung zu Nebenräumen |
| 3 | Was sind Stellplätze? | Stellplätze | Flächen zum Abstellen von Fahrzeugen; außerhalb öffentlicher Verkehrsflächen; Abgrenzung zu Garagen |
| 4 | Wann ist ein Bauvorhaben genehmigungspflichtig? | Genehmigungsverfahren | Grundsatz der Genehmigungspflicht; gesetzliche Ausnahmen definiert; Erfordernis einer Baugenehmigung vor Durchführung des Vorhabens |
| 5 | Welche Anforderungen gelten für Abstandsflächen? | Abstandsflächen | Abstand zu Grundstücksgrenzen; Einfluss auf Gebäudeanordnung; Sicherung von Belichtung und Belüftung |
| 6 | Welche allgemeinen Anforderungen müssen bauliche Anlagen erfüllen? | Allgemeine Anforderungen | Sicherheit und Ordnung; Schutz von Leben und Gesundheit; Gebrauchstauglichkeit der Anlage |
| 7 | Welche Anforderungen bestehen an Aufenthaltsräume? | Aufenthaltsräume | ausreichende Belichtung; ausreichende Lüftung; Mindesthöhe oder Raumgröße |
| 8 | Welche Anforderungen gelten für den Brandschutz? | Brandschutz | Entstehung von Bränden verhindern; Ausbreitung von Feuer begrenzen; Rettung von Menschen ermöglichen |
| 9 | Welche Anforderungen bestehen an Rettungswege in Gebäuden? | Rettungswege | erster Rettungsweg erforderlich; zweiter Rettungsweg erforderlich; sichere Nutzung im Gefahrenfall |
| 10 | Welche Voraussetzungen müssen Grundstücke für eine Bebauung erfüllen? | Grundstücke / Erschließung | bauliche Eignung des Grundstücks; gesicherte Erschließung; Zugang für Rettungskräfte |
| 11 | Welche Zusammenhänge bestehen zwischen Brandschutzanforderungen und der Gebäudeklasse? | Brandschutz / Gebäudeklassen | Gebäudeklasse bestimmt Brandschutzanforderungen; höhere Gebäudeklassen führen zu strengeren Anforderungen; Einfluss auf Rettungswege und bauliche Ausführung |
| 12 | Welche Regelungen gelten für Stellplätze im Zusammenhang mit Gebäuden? | Stellplätze | Stellplatzpflicht abhängig von Nutzung; Bereitstellung erforderlicher Stellplätze; funktionaler Zusammenhang mit Gebäude |
| 13 | Wann ist ein Bauvorhaben verfahrensfrei? | Verfahrensfreiheit | gesetzlich definierte Vorhaben; keine Genehmigung erforderlich; Einhaltung materieller Anforderungen bleibt bestehen |
| 14 | Welche Folgen kann Bauen ohne Genehmigung haben? | Bauaufsichtliche Maßnahmen | Baustopp möglich; Beseitigungsanordnung möglich; Nutzungsuntersagung möglich |
| 15 | Unter welchen Bedingungen kann die Nutzung einer baulichen Anlage untersagt werden? | Bauaufsichtliche Maßnahmen | Verstoß gegen öffentliches Recht; Gefährdung von Sicherheit oder Ordnung; behördliche Untersagung |
| 16 | Unter welchen Voraussetzungen sind Abweichungen von bauordnungsrechtlichen Anforderungen möglich? | Abweichungen | behördliche Zulassung erforderlich; begründeter Antrag notwendig; keine Gefährdung öffentlicher Belange |
| 17 | Wie hängen Abstandsflächen und Grundstücksbebauung zusammen? | Abstandsflächen / Grundstücke | Abstandsflächen begrenzen Bebauung; bestimmen Lage des Gebäudes; Schutz von Nachbargrundstücken |
| 18 | Welche Rolle spielen Rettungswege im Brandschutz? | Rettungswege / Brandschutz | ermöglichen Flucht von Personen; Bestandteil des Brandschutzkonzepts; Grundlage für Rettungskräfte |
| 19 | Welche Voraussetzungen müssen erfüllt sein, bevor eine Nutzung aufgenommen werden darf? | Genehmigungsverfahren | Genehmigung oder Abnahme erforderlich; Einhaltung aller Anforderungen; Fertigstellung des Bauwerks |
| 20 | Welche Pflichten hat der Bauherr im Bauprozess? | Beteiligte am Bau (Bauherr) | Verantwortung für Einhaltung der Vorschriften; Organisation und Koordination; Sicherstellung notwendiger Genehmigungen |

---

## Evaluation Structure

Each answer is scored on three dimensions:

### 1. Retrieval (0–2)

Did the system retrieve legal content from the correct section family? Scored by comparing the **logged retrieved chunks** (RAG) or **traversed subgraph nodes** (GraphRAG) against the expected section family defined in the ground truth table — not inferred from the answer.

- **0** = Retrieved content is from the wrong section family, irrelevant to the query, or nothing was retrieved
- **1** = Retrieved content is partially from the correct section family but incomplete, or mixed with irrelevant sections
- **2** = Retrieved content is clearly from the expected section family and includes the key passages needed to answer the query

### 2. Reasoning (0–2)

Did the answer correctly interpret the retrieved legal content against the minimum answer elements?

- **0** = Answer is factually wrong, contradicts the corpus, or does not address the query
- **1** = Answer addresses the query partially — at least one minimum element is present, but one or more are missing or misinterpreted
- **2** = Answer is correct and complete — all minimum answer elements are addressed without contradiction

### 3. Grounding (0–2)

Is every factual claim in the answer traceable to the reference corpus? Assessed by LLM-as-judge with the full corpus in the prompt.

- **0** = at least one claim directly contradicts the corpus, or introduces external legal content with no basis in the TXT
- **1** = at least one claim is a reasonable inference or generalisation not directly stated in the corpus, but nothing is contradicted
- **2** = every factual claim can be found verbatim or clearly paraphrased in the corpus

### Total Score

Each query is scored from **0 to 6** (sum of the three dimensions).

---

## Evaluator

Scoring uses a **two-stage process**: the LLM-as-judge produces a first-pass draft score for all answers, which is then fully validated by the team's legal expert. The judge acts as a draft scorer to save time; the legal expert's score is the one of record.

> **Estimated reviewer time:** ~3–3.5 hours total (40 answers × ~5 min average). Can be split across two sessions.

**Independence constraint:** The evaluator must not be the same model used to build or power the RAG or GraphRAG systems. Since RAG generation uses Claude Sonnet, the judge must be a different model — GPT-4o or equivalent — to avoid shared model bias, where a model may systematically favour its own output patterns and phrasing when scoring.

> ⚠️ **Pending:** Confirm which model powers GraphRAG generation. If also Claude Sonnet, no change needed. If a different model, update this constraint and the Known Limitations entry accordingly.

**Anti-circularity statement:** Ground truth and evaluation are separated from system generation. While LLMs were used in the benchmark design phase, evaluation is performed by an independent model to minimise circularity and shared bias.

### Stage 1 — LLM-as-judge (draft scores)

All three dimensions are scored by `gpt-4o` or equivalent non-Claude model. The queries are state-agnostic but each answer is tied to a specific state corpus.

> The queries are state-agnostic but each answer is tied to a specific state corpus. In the product, state selection is a mandatory input: the user must explicitly select a German federal state before submitting any query. No query is processed without a state being declared, ensuring every answer is unambiguously grounded in the correct LBO.

**Implementation note:** Log the source state alongside the answer at query time, then load the corresponding TXT file when building the judge prompt:

```python
# Extract from ground truth table
section_family = ground_truth[query]["section_family"]
ground_truth_elements = ground_truth[query]["minimum_answer_elements"]

# RAG — log top-k retrieved chunks + source state
results[query] = {
    "answer": answer,
    "retrieved_chunks": chunks,        # list of retrieved text chunks from the index
    "source_state": source_state,      # e.g. "Baden-Württemberg" — which state was retrieved from
    "latency_ms": latency,
    "tokens": token_count
}

# GraphRAG — log traversed subgraph nodes as text + source state
results[query] = {
    "answer": answer,
    "retrieved_chunks": subgraph_summary,   # nodes/relationships traversed, serialised as text
    "source_state": source_state,
    "latency_ms": latency,
    "tokens": token_count
}

# Load only the relevant state corpus for the judge
corpus_text = open(f"lbo_{results[query]['source_state']}.txt").read()
```

> **Note on GraphRAG retrieved content:** GraphRAG does not return text chunks — it returns a subgraph. Serialise the traversed nodes and relationships as plain text before passing to the judge. A simple format like `"Node: Abstandsflächen → requires: Grenzabstand → defined_in: §6 LBO"` is sufficient for the judge to assess section family relevance.

> **Context window:** A single state LBO TXT is typically 25,000–50,000 tokens. Combined with the query, ground truth elements, retrieved chunks, and answer, total prompt size is estimated at 60,000–70,000 tokens per call — within GPT-4o's 128k token context window, though with limited headroom at the upper end. Monitor token usage during the run and truncate retrieved chunks if necessary.

#### Judge Prompt

```
You are evaluating a legal question-answering system against a reference corpus (German LBO).

Reference corpus:
{corpus_text}

Query: {query}
Expected section family: {section_family}
Minimum answer elements: {ground_truth_elements}
Retrieved content: {retrieved_chunks}
System answer: {answer}

Score the answer on the following three dimensions. Return only a JSON object.

Retrieval (0–2): Do the retrieved chunks come from the expected section family: {section_family}?
  Use only the retrieved content field above — do not infer retrieval quality from the answer.
  0 = retrieved content is from the wrong section family or absent
  1 = retrieved content is partially from the correct section but incomplete or mixed with irrelevant sections
  2 = retrieved content is clearly from {section_family} and covers the key passages needed

Reasoning (0–2): Does the answer correctly address all minimum answer elements?
  0 = incorrect, 1 = partial (some elements present), 2 = all elements correct

Grounding (0–2): Is every factual claim in the answer traceable to the reference corpus?
  0 = at least one claim contradicts the corpus or has no basis in it
  1 = at least one claim is a reasonable inference not directly stated in the corpus, but nothing is contradicted
  2 = every factual claim can be found verbatim or clearly paraphrased in the corpus

Do not introduce external legal knowledge. Do not assume uniform wording across German states.
Only evaluate based on the provided reference corpus.

Return: {"retrieval": <0|1|2>, "reasoning": <0|1|2>, "grounding": <0|1|2>}
```

### Stage 2 — Legal expert validation (final scores)

The team's legal expert reviews all 40 draft-scored answers with the relevant state's LBO TXT corpus open (matching the `source_state` logged per answer). For each answer they either confirm the judge's scores or override one or more dimensions.

**Review workflow per answer:**
1. Open the ground truth table — note the expected section family and minimum answer elements for the query
2. Read the system answer
3. Check each judge score against the rubric — for Retrieval, compare retrieved chunks against the expected section family; for Reasoning, check answer content against the minimum elements; for Grounding, verify claims against the state corpus
4. Confirm or override — log any changes using the format below

**Override log format** (one row per changed dimension):

| Query | System | Dimension | Judge Score | Expert Score | Reason |
|-------|--------|-----------|-------------|--------------|--------|
| Q8 | GraphRAG | Grounding | 2 | 1 | Answer states specific fire resistance class not found in corpus |
| Q13 | RAG | Reasoning | 1 | 0 | Answer conflates verfahrensfrei with genehmigungsfrei — legally distinct |

> The override log is part of the benchmark record. It documents where and why human judgment diverged from the judge, and provides qualitative insight into systematic judge failure modes. The expert score always takes precedence over the judge score in final results.

---

## Evaluation Process

### Stage 1 — Run systems and collect draft scores

For each query:

1. Run RAG → collect answer + **log retrieved chunks + source state** + record latency (ms) + token count
2. Run GraphRAG → collect answer + **log traversed subgraph nodes (serialised as text) + source state** + record latency (ms) + token count
3. Apply LLM judge prompt to each answer (state-specific corpus + retrieved chunks + section family + ground truth elements included)
4. Record draft scores for all three dimensions in the output table

### Stage 2 — Legal expert validation

Once all 40 draft scores are collected:

5. Legal expert reviews all answers against the rubric with the relevant state's LBO TXT corpus open (matching the `source_state` logged per answer)
6. Confirms or overrides each score — logs any change in the override log
7. Final scores (expert-validated) replace draft scores in the output table
8. Override log is appended to the benchmark record as a supplementary document

> **Final scores are always the expert-validated scores.** Draft scores are retained for transparency but not used in aggregation or reporting.

---

## Output Format

The output table records both draft (judge) and final (expert-validated) scores for full transparency, including the source state for each answer.

| Query | System | State | Retrieval (draft) | Retrieval (final) | Reasoning (draft) | Reasoning (final) | Grounding (draft) | Grounding (final) | Total (final) | Latency (ms) | Tokens |
|-------|--------|-------|-------------------|-------------------|-------------------|-------------------|-------------------|-------------------|---------------|--------------|--------|

### Example

| Query | System | State | Retrieval (draft) | Retrieval (final) | Reasoning (draft) | Reasoning (final) | Grounding (draft) | Grounding (final) | Total (final) | Latency (ms) | Tokens |
|-------|--------|-------|-------------------|-------------------|-------------------|-------------------|-------------------|-------------------|---------------|--------------|--------|
| Q7 – Welche Anforderungen bestehen an Aufenthaltsräume? | RAG | Baden-Württemberg | 1 | 1 | 1 | 1 | 2 | 2 | 4 | 1240 | 312 |
| Q7 – Welche Anforderungen bestehen an Aufenthaltsräume? | GraphRAG | Baden-Württemberg | 2 | 2 | 2 | 2 | 2 | 2 | 6 | 2870 | 428 |

---

## Score Aggregation

### Primary metric: mean score per system

Scores are aggregated as a simple mean across all 20 queries, treating each query equally regardless of difficulty.

**Formula:**

```
Mean Score = Σ score_i / 20
```

Compute separately per system, then compare. Maximum possible score is 6.0.

> **Why flat mean:** Each query targets a distinct legal concept and is independently valid.

### Secondary breakdowns (for reporting)

- Mean score per query **type** (Direct, Structured, Multi-step, Exception/Procedure, Cross-concept)
- Mean score per query **difficulty tier**
- Mean score per **dimension** (Retrieval / Reasoning / Grounding independently)
- Mean score per **source state** — if queries were run against multiple states, this reveals whether system performance is consistent across LBO variants or state-dependent
- Mean **latency** and **token count** per system

These breakdowns allow you to identify not just which system scores higher overall, but *where* and *why*.

---

## Rules

- **Paragraph numbers** may be used in answers for traceability (e.g. to cite a source), but the scoring of Retrieval and Reasoning is based on whether the answer content matches the minimum elements — not on whether the correct paragraph number was cited. Do not award or deduct points based on citation format alone.
- Do not introduce external legal knowledge beyond the provided TXT corpus
- Do not assume uniform wording or structure across German state LBO texts
- Only evaluate based on the provided TXT corpus

---

## Known Limitations

- **Query distribution is complexity-heavy**: 11/20 queries are ★★★ — this is intentional but means overall scores will naturally favour the system better suited to multi-hop reasoning. Results should be interpreted by tier, not only in aggregate.
- **LLM-as-judge is a first-pass draft only**: All judge scores are fully validated by the team's legal expert before use in analysis. The override log documents every case where judge and expert diverged, providing transparency into systematic judge failure modes.
- **Judge model is intentionally independent**: RAG generation uses Claude Sonnet; the judge uses GPT-4o. This separation is required to prevent shared model bias. If the judge model is changed, the independence constraint must be re-evaluated.
- **GraphRAG retrieved content is serialised, not native**: Subgraph nodes and relationships are converted to plain text before passing to the judge. The serialisation format may not capture the full relational structure — the legal expert should pay particular attention to Retrieval scores for GraphRAG answers during validation.
- **Q14 and Q15 share a section family**: Both map to `Bauaufsichtliche Maßnahmen`. Their answer elements are fully distinct — Q14 covers consequences of building without a permit, Q15 covers conditions for usage prohibition — so there is no scoring overlap. The shared section family reflects the LBO's own structure and is intentional.
- **Latency is environment-dependent**: Latency figures reflect the specific hardware and API conditions of the test run and should not be generalised.

---

*This document defines the benchmark setup and evaluation method.*

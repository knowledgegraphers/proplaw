---
name: tagesplan
description: Baut die Tagesplanung fuer PropLaw aus den offenen Findings. Liest propra/benchmark/results/FINDINGS.md, sortiert die OPEN-Findings nach Alter, schlaegt Bloecke fuer den Arbeitstag vor und aktualisiert die Reviewed-Daten. Nutze diesen Skill am Anfang eines Arbeitstages oder wenn gefragt wird, was heute ansteht.
---

# Tagesplanung aus den Findings

Dieser Skill existiert wegen eines konkreten Vorfalls: Blocker B-01 stand am
6. September ganz oben im Audit und wurde erst dreizehn Tage spaeter behoben —
nicht weil jemand die Liste abarbeitete, sondern zufaellig. Sechs weitere
Findings lagen fuenf Monate unbearbeitet. Aufschreiben allein bewirkt nichts.
Der Weg von der Liste in einen Arbeitstag ist der Zweck dieses Skills.

## Ablauf

### 1. Findings lesen

Lies `propra/benchmark/results/FINDINGS.md` vollstaendig. Sammle alle Eintraege
mit Status `OPEN` oder `IN REVIEW`. Fuer jeden brauchst du: ID, Titel, `Date`,
`Reviewed`, `Owner` und die Action-Zeile.

Ermittle das heutige Datum mit `date +%F` — rate es nicht.

Alter = heute minus `Reviewed`. Fehlt `Reviewed`, nimm `Date` und weise darauf
hin, dass das Feld fehlt.

### 2. Lage zeigen, bevor du planst

Gib eine Tabelle aus: ID, Titel gekuerzt, Alter in Tagen, Status, Owner.
Absteigend nach Alter. Markiere alles ueber 21 Tagen deutlich.

Danach genau einen Satz zur Lage — keine Bewertung der Person, nur der Zustand.
Beispiel: "Vier Findings sind ueber 21 Tage ohne Sichtung, das aelteste 177 Tage."

### 3. Verfuegbare Zeit erfragen

Wenn der Nutzer beim Aufruf keine Zeitangabe gemacht hat (etwa `/tagesplan 2h`),
frag nach — eine Frage, keine Liste. Ohne Zeitbudget ist jeder Plan Fiktion.

### 4. Bloecke vorschlagen

Drei Bloecke, zusammen hoechstens das genannte Zeitbudget. Regeln:

- **Mindestens ein Block kommt aus der OPEN-Liste**, und zwar das aelteste
  Finding, das in die verfuegbare Zeit passt. Nicht das bequemste.
- Ein Block dauert 15 bis 45 Minuten. Laenger heisst: falsch geschnitten.
- Jeder Block nennt ein konkretes Ergebnis, nicht eine Taetigkeit.
  "FINDINGS.md ergaenzt" ist ein Ergebnis, "an Findings arbeiten" nicht.
- Reihenfolge: Absicherung vor Eingriff. Ein Test, der den Defekt zeigt,
  steht vor dem Fix. Andersherum weiss niemand, ob das Richtige repariert wurde.

Fuer jeden Block, dessen Ende sich aus dem Verlauf belegen laesst, formuliere
eine `/goal`-Bedingung nach diesem Muster:

> **messbarer Endzustand · benannter Beweis · ausdrueckliche Auslassung · Turn-Deckel**

Beispiel:

```
/goal Der Test propra/tests/test_prefix_alignment.py laeuft fuer alle 16
Bundeslaender durch und propra/tests/ bleibt vollstaendig gruen.
Beweis: beide pytest-Ausgaben, gelaufen ueber .venv/Scripts/python.exe.
Aendere nichts ausserhalb von propra/retrieval/ und propra/data/txt/.
Stopp nach 12 Turns.
```

Fuer Schreibaufgaben — Dokumentation, Findings eintragen, PR-Beschreibung —
**kein `/goal`**. Es gibt dort keine pruefbare Endbedingung, der Evaluator
erzeugt nur Reibung. Gib stattdessen den Prompt direkt.

### 5. Entscheidung bei ueberfaelligen Findings erzwingen

Jedes OPEN-Finding ueber 21 Tage, das heute nicht eingeplant wird, braucht eine
ausdrueckliche Entscheidung. Leg sie dem Nutzer vor, einzeln:

- **einplanen** — dann gehoert es in einen der drei Bloecke
- **DEFERRED** — Status aendern, mit Begruendung und `Deferred until:` Datum
- **schliessen** — wenn es sich erledigt hat, mit Resolution-Zeile

Nicht entscheiden ist keine Option, die du anbietest. Genau daran ist B-01
gescheitert.

### 6. Reviewed-Daten aktualisieren

Setze `**Reviewed:**` auf das heutige Datum — **nur** bei den Findings, die in
Schritt 2 tatsaechlich aufgelistet und in Schritt 5 entschieden wurden. Das Feld
bedeutet "angeschaut und entschieden", nicht "existiert noch".

Eine Ausnahme, und nur diese: Bei der **Neuanlage** eines Findings traegt der
anlegende Lauf `Reviewed:` selbst ein, naemlich das Anlagedatum. Dort startet das
Feld die Alterung, statt sie zu verbergen. Jede **spaetere** Aenderung von
`Reviewed:` gehoert ausschliesslich diesem Skill — nicht der Hand, nicht einem
unbeaufsichtigten Lauf.

Aktualisiere die `Last updated`-Zeile am Dateiende.

Aendere sonst nichts an bestehenden Findings — keine Umformulierung, keine
Neusortierung, keine Statusaenderung ohne ausdrueckliche Zustimmung.

### 7. Ausgabe

Gib den Plan in der Form aus, die in die Tagesprotokolle passt:

```
A · <Ergebnis> — <Minuten>
<ein bis zwei Saetze, warum dieser Block jetzt>
<Prompt oder /goal-Bedingung>

B · ...
C · ...
```

Am Ende eine Zeile: welche Findings heute angefasst wurden, welche auf DEFERRED
gingen, und welches das naechste ueberfaellige ist.

## Grenzen

- Dieser Skill aendert ausschliesslich `FINDINGS.md`. Kein Code, keine Tests,
  keine Commits.
- Er erfindet keine Findings. Was nicht in der Datei steht, kommt nicht in den
  Plan — es sei denn, der Nutzer nennt es selbst.
- Er faerbt nichts schoen. Ein 177 Tage altes Finding wird als 177 Tage altes
  Finding gemeldet.

## Verhaeltnis zu den anderen Teilen

- Das **Tagesbriefing** um 08:00 kommt aufs Handy und nennt genau eine Aufgabe
  ueber alle Projekte hinweg. Es liest, es schreibt nichts.
- **Dieser Skill** plant den Block, an dem du gerade sitzt — in dem Repo, in dem
  du arbeitest. Nicht mechanisch in jedem Projekt. Wechselst du spaeter bewusst
  das Projekt, rufst du ihn dort erneut auf.
- **`/feierabend`** schliesst die Sitzung ab und schreibt den Stand fort.

Wenn die Aufgabe aus dem Morgenbriefing noch offen ist, gehoert sie in Block A —
unabhaengig davon, was die Findings sagen. Was Geld kostet, solange es offen ist,
schlaegt jedes Finding.

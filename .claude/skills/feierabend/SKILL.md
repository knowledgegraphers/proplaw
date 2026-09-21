---
name: feierabend
description: Schliesst eine Arbeitssitzung ab. Sammelt belegbar, was in diesem Projekt passiert ist, aktualisiert den Spur-Abschnitt in KOMMANDOZENTRALE.md, haengt eine Logbuchzeile an und schreibt den eigenen Abschnitt in STATUS.md in Google Drive. Nutze diesen Skill am Ende jeder Arbeitssitzung in einem Projekt.
---

# Feierabend

Der Schreiber im System. Ohne ihn altert jeder Status still vor sich hin — genau
das Muster, an dem Blocker B-01 dreizehn Tage und die Findings F001 bis F006
178 Tage gelegen haben.

Dieser Skill laeuft **pro Projekt**, am Ende der Arbeit dort. Zwei Projekte an
einem Tag heisst zwei Aufrufe.

## Feste Pfade

- Kommandozentrale: `$HOME/AIPM/KOMMANDOZENTRALE.md`
- Status in Drive: `/g/Meine Ablage/Kommandozentrale/STATUS.md`

Beide existieren. Wenn einer fehlt, brich ab und sag es — leg nichts neu an.

## Ablauf

### 1. Projekt bestimmen

Lies den Repo-Namen: `basename "$(git rev-parse --show-toplevel)"`.

| Repo | Abschnitt |
|---|---|
| `proplaw` | `## Spur 2 — PropLaw` |
| `aipm-studio-ops` | `## Spur 3 — AIPM Praxis-Guide` |

Steht das Repo nicht in der Tabelle, frag nach, welcher Spur es zugehoert.
Rate nicht.

Ermittle das Datum mit `date +%F`.

### 2. Belege sammeln

Nur was nachweisbar ist, nichts Erinnertes:

- `git --no-pager log --oneline --since="24 hours ago"` — was committet wurde
- `git --no-pager status --short` — was offen im Working Tree liegt
- `git rev-parse --short HEAD` und der aktuelle Branch
- bei PropLaw zusaetzlich: Anzahl `**Status:** OPEN` in
  `propra/benchmark/results/FINDINGS.md` und das aelteste `Reviewed`-Datum

Wenn nichts committet wurde, ist das das Ergebnis. Schreib es so hin, ohne
Beschoenigung und ohne Motivationssatz.

### 3. Eine Frage stellen

Frag genau eine Sache, die du nicht messen kannst:

> Wie viele Bewerbungen hast du heute abgeschickt?

Antwortet er mit einer Zahl, rechne sie auf den Wochenstand in `STATUS.md`
drauf. Antwortet er nicht oder weicht aus, lass Spur 1 unveraendert und aendere
auch das `Aktualisiert`-Datum dort nicht. Ein unveraendertes Datum ist die
ehrliche Anzeige.

### 4. Kommandozentrale aktualisieren

Im Abschnitt des Projekts: Zeilen, die nicht mehr stimmen, **ersetzen** — nicht
ergaenzen. Erledigte Punkte aus der Offen-Liste streichen, neue aufnehmen.
Andere Abschnitte nicht anfassen.

Dann ans Logbuch am Dateiende **eine** Zeile anhaengen:

```
- TT.MM.JJJJ: <was belegbar fertig wurde oder dass nichts passierte>, offen: <der naechste Schritt>
```

Nie die Datei ueberschreiben, immer anhaengen.

### 5. STATUS.md in Drive schreiben

**Nur den eigenen Abschnitt.** Die anderen bleiben Zeichen fuer Zeichen
unveraendert — ein anderes Projekt hat sie geschrieben, und wer sie ueberbuegelt,
loescht fremden Stand.

Setze im eigenen Abschnitt `Aktualisiert:` auf heute. Halte dich an das Format:
kurze Zeilen, Zustaende und Zahlen.

**Was nicht hineingehoert:** Firmennamen, Gehaelter, Namen von Personen,
Bewerbungsdetails. Die Datei liegt in der Cloud. Sie traegt Zaehlstaende, keine
Geschichten.

Schreib die Datei mit einem Read-Modify-Write in Python oder mit `sed -i` —
niemals, indem du den Inhalt aus einer frueheren Ausgabe neu abtippst.

### 6. Melden

Drei Saetze, nicht mehr: was heute belegbar fertig wurde, was offen bleibt,
und was die Kommandozentrale jetzt als naechstes fuehrt.

## Grenzen

- Keine Commits, kein Push, keine Aenderung am Code.
- Keine Bewertung der Person. Der Skill haelt Zustaende fest, er beurteilt nicht.
- Kein Eintrag ohne Beleg. „Vermutlich fertig" ist kein Zustand.

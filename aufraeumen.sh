#!/usr/bin/env bash
# PropLaw Repo-Aufräumen — ein Block pro Aufruf.
#
#   ./aufraeumen.sh 1     # nur Block 1
#   ./aufraeumen.sh 1 2   # Block 1 und 2
#   ./aufraeumen.sh alle  # alles
#
# Jeder Block ist ein eigener Commit. Nichts ist endgültig weg —
# git hat jede gelöschte Datei in der Historie.

set -euo pipefail
cd "$(dirname "$0")"

# Windows/Git-Bash: CRLF im Script bricht bash mit "\r: command not found".
if grep -q $'\r' "$0" 2>/dev/null; then
  echo "Dieses Script hat Windows-Zeilenenden (CRLF)."
  echo "Einmal reparieren, dann erneut starten:"
  echo "    sed -i 's/\\r\$//' $(basename "$0")"
  exit 1
fi

# Sanity: sind wir wirklich im PropLaw-Repo?
if [ ! -d propra ] || [ ! -d .git ]; then
  echo "Das hier sieht nicht nach dem PropLaw-Repo aus (kein propra/ oder .git/)."
  echo "Aktuelles Verzeichnis: $(pwd)"
  echo "Lege aufraeumen.sh ins Repo-Root und starte es von dort."
  exit 1
fi

run() { [[ " ${BLOCKS[*]} " == *" $1 "* || " ${BLOCKS[*]} " == *" alle "* ]]; }
del() { for f in "$@"; do
          if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then git rm -r -q --ignore-unmatch "$f"
          elif [ -e "$f" ]; then rm -rf "$f"; fi
        done; }
done_msg() { echo "  ✓ Block $1 fertig — $2"; echo; }
commit() { git diff --cached --quiet && { echo "  (nichts zu tun)"; echo; return; }
           git commit -q -m "$1"; }

BLOCKS=("$@")
[ ${#BLOCKS[@]} -eq 0 ] && { sed -n '2,12p' "$0"; exit 1; }

BEFORE=$(du -sm . | cut -f1)
echo

# ─────────────────────────────────────────────────────────────────────
if run 1; then
echo "▸ BLOCK 1 — Ballast im Repo-Root (4 Einträge, ~2,8 MB)"
del check_structure.py data lib package-lock.json
commit "chore: remove stray root artefacts

- check_structure.py: leere Datei (0 Byte)
- data/: verirrter Ordner mit BayBO-Zwischenformaten, von nichts gelesen
- lib/: vendored vis-network + tom-select aus einem pyvis-HTML-Export
- package-lock.json: leerer Stub ohne Pakete"
done_msg 1 "Root ist aufgeräumt"
fi

# ─────────────────────────────────────────────────────────────────────
if run 2; then
echo "▸ BLOCK 2 — Frontend: Duplikate und Mock-Code"
del propra/frontend/bun.lockb propra/frontend/src/lib/api.ts
commit "chore(frontend): drop second lockfile and mocked api client

- bun.lockb: zweites Lockfile neben package-lock.json
- src/lib/api.ts: vollständig gemockter Client, von keiner Komponente
  importiert; definierte einen dritten, abweichenden API-Vertrag"
done_msg 2 "ein Lockfile, kein Mock-Client"
fi

# ─────────────────────────────────────────────────────────────────────
if run 3; then
echo "▸ BLOCK 3 — Debug- und Check-Skripte aus der Capstone-Phase"
del propra/data/check_baybo_graph.py \
    propra/data/check_nbauO_labels.py \
    propra/data/debug_baybo.py \
    propra/data/parse_check_script.py \
    propra/data/parse_check.txt \
    propra/data/baybo_check_result.txt \
    propra/benchmark/debug_f003.py
commit "chore: remove one-off debug scripts from capstone phase

Einmalige Diagnose-Skripte ohne Aufrufer. Verifiziert: kein Modul
importiert sie, keine CI-Stufe ruft sie auf."
done_msg 3 "7 Wegwerf-Skripte weg"
fi

# ─────────────────────────────────────────────────────────────────────
if run 4; then
echo "▸ BLOCK 4 — Leere Module und unerreichbarer Code"
del propra/analytics propra/retrieval/kg_query.py
commit "chore: remove empty analytics package and unreachable kg_query

- analytics/events.py: nur ein Docstring, keine Implementierung
- retrieval/kg_query.py: aus keinem Laufzeitpfad erreichbar, 0 % Coverage,
  enthielt einen sys.path-Hack

Analytics kommt in Phase 2 zurück — dann mit echten Funnel-Events."
done_msg 4 "keine leeren Versprechen mehr"
fi

# ─────────────────────────────────────────────────────────────────────
if run 5; then
echo "▸ BLOCK 5 — Ungenutzte Prompts und doppelter Generator"
del propra/prompts/propose_edges.txt \
    propra/prompts/rag_answer.txt \
    propra/graph/generate_bbgbo_section_edges.py \
    propra/data/txt/BayBO_clean.txt
commit "chore: remove unused prompts, duplicate generator, orphan corpus file

- prompts/propose_edges.txt, rag_answer.txt: von keinem Modul geladen
- graph/generate_bbgbo_section_edges.py: Vorgänger des generischen
  generate_state_section_edges.py
- data/txt/BayBO_clean.txt: kein Eintrag in JURISDICTION_MAP, wird beim
  Index-Build mit einer Warnung übersprungen"
done_msg 5 "keine toten Prompts, ein Generator"
fi

# ─────────────────────────────────────────────────────────────────────
if run 6; then
echo "▸ BLOCK 6 — Verwaiste Node-Inventare (26 Dateien, ~3,5 MB)"
INV="propra/data/node inventory"
for s in BauO_HE BauO_LSA BauO_MV BauO_NRW BremLBO HBauO LBO_HB LBO_SH \
         LBO_SL LBauO_RLP SaechsBO ThuerBO; do
  del "$INV/${s}_node_inventory.md"
done
for s in BW_LBO BauO_BE BauO_HE BauO_LSA BauO_MV BauO_NRW BremLBO HBauO \
         LBO_SH LBO_SL LBauO_RLP SaechsBO ThuerBO; do
  del "$INV/${s}_node_inventory_v2.md"
done
del "$INV/cleanup_bearbeitungsstand.py" \
    "$INV/fix_dangling_markers.py" \
    "$INV/merge_reference_splits.py" \
    "$INV/split_list_markers.py"
commit "chore(data): remove superseded node inventory generations

Es gab bis zu drei Generationen pro Bundesland (plain, _v2, _fine).
Gelesen wird ausschließlich _fine. Entfernt sind nur die Dateien, auf
die kein einziges Modul verweist — BayBO/BbgBO/NBauO _v2 bleiben, weil
Generator bzw. Test sie noch referenzieren.

Ausserdem: vier Fix-Skripte im Inventarordner ohne Aufrufer."
done_msg 6 "eine Inventar-Generation statt drei"
fi

# ─────────────────────────────────────────────────────────────────────
if run 7; then
echo "▸ BLOCK 7 — .gitignore reparieren, damit der Müll nicht zurückkommt"
if grep -q ".pytest_cache" .gitignore 2>/dev/null; then
  echo "  .gitignore war schon aktuell"
else
  cat >> .gitignore <<'IGN'

# Test- und Build-Artefakte
.coverage
coverage.xml
htmlcov/
.pytest_cache/
.ruff_cache/
*.egg-info/

# Retrieval-Artefakte (werden gebaut, nicht committet)
propra/retrieval/faiss.index
propra/retrieval/chunks.pkl
IGN
  echo "  .gitignore ergänzt"
fi
git add .gitignore
commit "chore: extend .gitignore for test artefacts and retrieval index

.coverage und .pytest_cache landeten bisher als untracked files im Tree.
faiss.index ist ausserdem ohne die zugehoerige chunks.pkl wertlos —
beide gehoeren nicht in Git, sondern werden gebaut (Blocker B-01)."
done_msg 7 ".gitignore hält jetzt dicht"
fi

# ─────────────────────────────────────────────────────────────────────
AFTER=$(du -sm . | cut -f1)
echo "───────────────────────────────────────────────"
echo "  Vorher: ${BEFORE} MB   →   Jetzt: ${AFTER} MB"
echo "  Gelöschte Dateien liegen weiter in der git-Historie."
echo
echo "  Kontrolle:  PYTHONPATH=. pytest propra/tests/ -q"
echo "───────────────────────────────────────────────"

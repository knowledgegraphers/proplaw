#!/usr/bin/env bash
# PropLaw — Kontrolle nach dem Aufräumen.
#
#   bash kontrolle.sh
#
# Sucht ein venv, aktiviert es, prüft die Test-Abhängigkeiten und läuft
# dann drei Checks: Tests, Linter, App-Import. Installiert nichts ohne
# Ansage und fasst nie das globale Python an.

set -uo pipefail
cd "$(dirname "$0")"

if grep -q $'\r' "$0" 2>/dev/null; then
  echo "Dieses Script hat Windows-Zeilenenden (CRLF)."
  echo "Einmal reparieren, dann erneut starten:"
  echo "    sed -i 's/\\r\$//' $(basename "$0")"
  exit 1
fi

if [ ! -d propra ] || [ ! -d .git ]; then
  echo "Das hier sieht nicht nach dem PropLaw-Repo aus."
  echo "Aktuelles Verzeichnis: $(pwd)"
  exit 1
fi

echo
echo "▸ Schritt 1 — Python finden"

PY=""
for c in python python3 py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)" 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "  Kein Python 3.11+ gefunden."
  echo "  Installieren: https://www.python.org/downloads/  (beim Setup 'Add to PATH' anhaken)"
  exit 1
fi
echo "  $PY — $($PY --version 2>&1)"

# ─────────────────────────────────────────────────────────────────────
echo
echo "▸ Schritt 2 — virtuelle Umgebung"

VENV=""
for d in .venv venv env; do
  if   [ -f "$d/Scripts/activate" ]; then VENV="$d/Scripts/activate"; break
  elif [ -f "$d/bin/activate"     ]; then VENV="$d/bin/activate";     break
  fi
done

if [ -n "${VIRTUAL_ENV:-}" ]; then
  echo "  Schon aktiv: $VIRTUAL_ENV"
elif [ -n "$VENV" ]; then
  # shellcheck disable=SC1090
  source "$VENV"
  echo "  Aktiviert: $VENV"
else
  echo "  Kein venv gefunden. Lege .venv an (einmalig, dauert ~20 s)..."
  "$PY" -m venv .venv || { echo "  venv anlegen fehlgeschlagen."; exit 1; }
  if   [ -f .venv/Scripts/activate ]; then source .venv/Scripts/activate
  else source .venv/bin/activate; fi
  echo "  Aktiviert: .venv"
fi

PY=python   # im venv heißt es immer python

# ─────────────────────────────────────────────────────────────────────
echo
echo "▸ Schritt 3 — Abhängigkeiten für die Kontrolle"

# Nur was die 98 Tests wirklich brauchen. faiss-cpu und
# sentence-transformers (zieht torch, ~800 MB) sind hierfür NICHT nötig —
# die Tests mocken das Retrieval. Für einen echten Index-Build brauchst du
# später das volle requirements.txt.
NEED="pytest ruff fastapi pydantic httpx networkx joblib anthropic python-dotenv pytest-asyncio"
MISSING=""
for mod in pytest ruff fastapi pydantic httpx networkx joblib anthropic dotenv; do
  $PY -c "import $mod" >/dev/null 2>&1 || MISSING="$MISSING $mod"
done

if [ -n "$MISSING" ]; then
  echo "  Fehlt:$MISSING"
  echo "  Installiere ins venv (nicht global)..."
  $PY -m pip install --quiet --upgrade pip
  # shellcheck disable=SC2086
  $PY -m pip install --quiet $NEED || { echo "  pip install fehlgeschlagen."; exit 1; }
  echo "  Fertig."
else
  echo "  Alles da."
fi

# ─────────────────────────────────────────────────────────────────────
echo
echo "▸ Schritt 4 — die Checks"
echo

FAIL=0

# ── [1/3] Tests — harte Schranke ─────────────────────────────────────
echo "  [1/3] Tests"
TESTOUT=$(PYTHONPATH=. $PY -m pytest propra/tests/ -q 2>&1)
echo "$TESTOUT" | tail -2 | sed 's/^/        /'
if echo "$TESTOUT" | grep -qE "^[0-9]+ passed"; then
  echo "        ✓ grün"
else
  echo "        ✗ rot — hier ist wirklich etwas kaputt"
  FAIL=1
fi
echo

# ── [2/3] App-Import — harte Schranke ────────────────────────────────
echo "  [2/3] App-Import"
if PYTHONPATH=. $PY -c "import propra.main" >/dev/null 2>&1; then
  echo "        ✓ propra.main importierbar"
else
  PYTHONPATH=. $PY -c "import propra.main" 2>&1 | tail -3 | sed 's/^/        /'
  echo "        ✗ Import bricht"
  FAIL=1
fi
echo

# ── [3/3] Linter — Vergleich, keine Schranke ─────────────────────────
# `ruff check .` als Ja/Nein-Gate taugt hier nicht: das Ergebnis hängt
# an der ruff-Version, und ~2.980 Befunde stammen aus den generierten
# *_section_edges.py — also aus Daten, nicht aus Code (TD-01). Was
# wirklich zählt: hat das Aufräumen NEUE Befunde erzeugt?
echo "  [3/3] Linter — Vergleich gegen main"
EXC='propra/graph/*_section_edges.py'
count(){ $PY -m ruff check . --exclude "$EXC" --output-format=concise 2>/dev/null | grep -c ':' ; }

NOW=$(count)
BASE="?"
if git rev-parse --verify -q main >/dev/null && git diff --quiet && git diff --cached --quiet; then
  HERE=$(git rev-parse --abbrev-ref HEAD)
  git stash list >/dev/null 2>&1
  if git checkout main -q 2>/dev/null; then
    BASE=$(count)
    git checkout "$HERE" -q
  fi
fi

echo "        ruff $($PY -m ruff --version | awk '{print $2}'), generierte Kanten ausgeschlossen"
if [ "$BASE" = "?" ]; then
  echo "        jetzt: $NOW Befunde (Vergleich mit main nicht möglich —"
  echo "        uncommittete Änderungen im Tree)"
else
  echo "        main: $BASE  →  jetzt: $NOW"
  if [ "$NOW" -le "$BASE" ]; then
    echo "        ✓ keine neuen Befunde durch das Aufräumen"
  else
    echo "        ! $((NOW-BASE)) neue Befunde — schau dir die an:"
    echo "          python -m ruff check . --exclude '$EXC'"
  fi
fi

# ─────────────────────────────────────────────────────────────────────
echo
echo "───────────────────────────────────────────────"
if [ "$FAIL" -eq 0 ]; then
  echo "  Alles grün. Das Aufräumen hat nichts kaputt gemacht."
  echo "  Weiter mit Schritt 10: Pull Request öffnen."
else
  echo "  Mindestens ein Check ist rot — Ausgabe oben."
  echo "  Zum Zurücknehmen:  git checkout main"
fi
echo "───────────────────────────────────────────────"
echo
exit "$FAIL"

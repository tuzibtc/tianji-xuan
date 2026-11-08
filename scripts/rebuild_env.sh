#!/usr/bin/env bash
# Create or repair the Python environment for xuan.
#   scripts/rebuild_env.sh           rebuild if missing or broken
#   scripts/rebuild_env.sh --check   only check (exit 0 = healthy)
#   scripts/rebuild_env.sh --force   delete and rebuild
# The env lives in "xuan-venv" (override with XUAN_VENV). The name deliberately
# avoids .venv / venv / node_modules / build / dist / out / target / .cache,
# which some hosting platforms skip when they save and restore a workspace.
set -euo pipefail
ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
VENV="${XUAN_VENV:-$ROOT/xuan-venv}"
LOCK="$ROOT/requirements-lock.txt"
BASE_PY="${XUAN_BASE_PYTHON:-python3}"
MODE="${1:-}"

check() {
  [[ -x "$VENV/bin/python" ]] || return 1
  "$VENV/bin/python" - "$LOCK" <<'PY' || return 1
import sys, importlib.metadata as md
want = {}
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.split("#", 1)[0].strip()
    if "==" in line:
        n, v = line.split("==", 1); want[n.strip()] = v.strip()
bad = []
for n, v in want.items():
    try:
        got = md.version(n)
    except md.PackageNotFoundError:
        bad.append(f"{n} missing"); continue
    if got != v: bad.append(f"{n} {got} != {v}")
import zstandard, numpy  # import test
if bad:
    print("; ".join(bad), file=sys.stderr); sys.exit(1)
PY
}

if [[ "$MODE" == "--check" ]]; then check; exit $?; fi
if [[ "$MODE" != "--force" ]] && check 2>/dev/null; then echo "xuan env OK: $VENV"; exit 0; fi

echo "[$(date '+%F %T')] rebuilding xuan env at $VENV"
rm -rf "$VENV"
"$BASE_PY" -m venv "$VENV"
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet -r "$LOCK"
check
echo "[$(date '+%F %T')] xuan env rebuilt OK"

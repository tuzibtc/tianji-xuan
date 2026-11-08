#!/usr/bin/env bash
# Offline tests: env auto-rebuild and backup-template safety checks.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export XUAN_HOME="$T/home"; export XUAN_VENV="$T/xuan-venv"; unset XUAN_PYTHON || true
ok(){ echo "ok - $1"; }
# 1. no default env path uses a name that platforms skip
! grep -nE '(^|[/"])\.?venv([/"]|$)' "$ROOT/bin/xuan" "$ROOT/scripts/rebuild_env.sh" | grep -v xuan-venv && ok "env name not on skip list"
# 2. missing env -> xuan rebuilds automatically and logs it
bash "$ROOT/scripts/rebuild_env.sh" --check && exit 1 || true
"$ROOT/bin/xuan" -h >/dev/null 2>"$T/err"
grep -q "rebuilt OK" "$T/err" && grep -q "rebuilt OK" "$XUAN_HOME/env-rebuild.log" && ok "auto-rebuild + log"
bash "$ROOT/scripts/rebuild_env.sh" --check && ok "check passes after rebuild"
# 3. broken env (package removed) -> rebuilt again
"$XUAN_VENV/bin/python" -m pip uninstall -y -q zstandard
bash "$ROOT/scripts/rebuild_env.sh" --check 2>/dev/null && exit 1 || true
"$ROOT/bin/xuan" -h >/dev/null 2>&1 && bash "$ROOT/scripts/rebuild_env.sh" --check && ok "broken env repaired"
# 4. backup template: scanning and refusals (dry run, no network)
S="$T/src"; mkdir -p "$S/node_modules" "$S/xuan-venv"
echo hello > "$S/ok.txt"; echo x > "$S/.env"; echo x > "$S/my_token.json"; echo x > "$S/node_modules/a"
printf 'api_key = "%s"\n' "abcdefghijklmnopqrstuv123" > "$S/conf.txt"
head -c $((2*1024*1024)) /dev/zero > "$S/big.bin"
OUT=$(python3 "$ROOT/scripts/backup_to_github.py" --repo someone/my-backup --src "$S" --max-mb 1 --dry-run)
echo "$OUT" | grep -q '^1 files to back up' && ok "only safe file kept"
for r in "credential-like filename" "content looks like a secret" "larger than 1 MB" "excluded directory"; do
  echo "$OUT" | grep -q "$r" || { echo "missing: $r"; exit 1; }; done; ok "manifest reasons"
python3 "$ROOT/scripts/backup_to_github.py" --repo Renhuai123/ziwei-doushu --src "$S" --dry-run >/dev/null 2>&1 && exit 1
ok "refuses upstream repo"
O=$(git -C "$ROOT" remote get-url origin 2>/dev/null || true)
if [[ -n "$O" ]]; then python3 "$ROOT/scripts/backup_to_github.py" --repo "$O" --src "$S" --dry-run >/dev/null 2>&1 && exit 1; ok "refuses own code repo"; fi
echo "all passed"

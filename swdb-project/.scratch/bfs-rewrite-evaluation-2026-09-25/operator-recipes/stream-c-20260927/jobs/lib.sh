# Shared step helper for Stream C jobs. Created 2026-09-27 ET.
# Sourced by jobs/*.sh with: CODE DISPATCH RAW set. One bounded public call per step;
# a failing step stops the job (no retry). Each step records argv, times, exit and hashes.
set -u
PY=/usr/bin/python3
cd "$CODE"
step() {
  local name=$1 seconds=$2; shift 2
  local started finished rc
  started=$(date --iso-8601=ns)
  printf '%q ' "$@" > "$DISPATCH/$name.argv"
  timeout --signal=TERM --kill-after=15s "$seconds" "$@" > "$DISPATCH/$name.stdout" 2> "$DISPATCH/$name.stderr"
  rc=$?
  finished=$(date --iso-8601=ns)
  printf '{"step":"%s","limit_seconds":%s,"started":"%s","finished":"%s","exit":%s,"stdout_sha256":"%s","stderr_sha256":"%s"}\n' \
    "$name" "$seconds" "$started" "$finished" "$rc" \
    "$(sha256sum "$DISPATCH/$name.stdout" | cut -d' ' -f1)" "$(sha256sum "$DISPATCH/$name.stderr" | cut -d' ' -f1)" \
    >> "$DISPATCH/steps.jsonl"
  return $rc
}
swdb() { local name=$1 seconds=$2; shift 2; step "$name" "$seconds" "$PY" -m swdb "$@"; }
lane() { [[ "$JOB_NODE" == 0 || "$JOB_NODE" == 1 ]] || { echo "job requires a socket lane" >&2; exit 64; }; echo "$JOB_NODE"; }

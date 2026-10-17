#!/usr/bin/env bash
# SOURCE ONLY / NOT RUN. Explicit future parent-reviewed argv and native pins.
# Parent must first verify real mbit10/account, all native utilities, exact M2
# source/raw routes and directory ownership/canonicality against original M2.
# This bootstrap does not infer or replace those original observations.
# Positional fields1..20 are documented in the accompanying handoff; remaining
# args are the COMPLETE unchanged private-outer-capture eighteen-flag vector.
set +e
umask 077
exec 3>&1
refuse() { printf '%s\n' '{"state":"bootstrap_refused","error_class":"PrivateCaptureGuardRefusal","raw_diagnostics_returned":false}' >&3; exit 3; }
[[ $# -eq 56 && $UID -eq 114316761 && $EUID -eq 114316761 ]] || refuse
BOOT=$1; SECONDS_CAP=$2; PYTHON=$3; GNU_TIMEOUT=$4; SHA256SUM=$5; WC=$6; MKDIR=$7
OUTER_SOURCE=$8; SOURCE_ROOT=$9; RAW_ROOT=${10}; WRITER_OUT=${11}; INNER_LOGS=${12}; OUTER_LOGS=${13}
M2=${14}; M2_SHA=${15}; OUTER_SHA=${16}; SHA_UTILITY_SHA=${17}; WC_UTILITY_SHA=${18}; MKDIR_UTILITY_SHA=${19}; BOOTSTRAP_SHA=${20}
shift 20
FORWARDED=("$@")
[[ $SECONDS_CAP =~ ^[1-9][0-9]{1,3}$ ]] && (( 10#$SECONDS_CAP >= 60 && 10#$SECONDS_CAP <= 3600 )) || refuse
[[ $OUTER_SHA == 59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544 ]] || refuse
for hash in "$M2_SHA" "$OUTER_SHA" "$SHA_UTILITY_SHA" "$WC_UTILITY_SHA" "$MKDIR_UTILITY_SHA" "$BOOTSTRAP_SHA"; do
  [[ $hash =~ ^[0-9a-f]{64}$ ]] || refuse
done
canonical_path() {
  local p=$1 q
  [[ ${#p} -le 1024 && $p =~ ^/[A-Za-z0-9_./-]+$ && $p != *'//'* && $p != *'/./'* && $p != *'/../'* && $p != */. && $p != */.. && $p != */ ]] || return 1
  [[ $p != */.codex/* && $p != */.ssh/* && $p != */.aws/* && $p != */auth.json && $p != */provider.json && $p != */prompt.txt && $p != */feedback.txt ]] || return 1
  q=$p
  while [[ $q != / ]]; do
    [[ ! -L $q ]] || return 1
    q=${q%/*}; [[ -n $q ]] || q=/
  done
}
for path in "$BOOT" "$PYTHON" "$GNU_TIMEOUT" "$SHA256SUM" "$WC" "$MKDIR" "$OUTER_SOURCE" "$SOURCE_ROOT" "$RAW_ROOT" "$WRITER_OUT" "$INNER_LOGS" "$OUTER_LOGS" "$M2" "${BASH_SOURCE[0]}"; do canonical_path "$path" || refuse; done
[[ $BOOT == /data/yanruj/* || $BOOT == /data1/yanruj/* ]] || refuse
[[ -d $SOURCE_ROOT && -O $SOURCE_ROOT && -d $RAW_ROOT && -O $RAW_ROOT && $M2 == "$RAW_ROOT/manifest.json" ]] || refuse
[[ -f $M2 && -O $M2 && -f $OUTER_SOURCE && -O $OUTER_SOURCE && -f ${BASH_SOURCE[0]} && -O ${BASH_SOURCE[0]} ]] || refuse
ROOTS=("$SOURCE_ROOT" "$RAW_ROOT" "$WRITER_OUT" "$INNER_LOGS" "$OUTER_LOGS")
for suffix in 1 2 3 4; do ROOTS+=("$RAW_ROOT/campaign-runs/extensa/extensa-gem5-bfs-20261006-p$suffix"); done
for root in "${ROOTS[@]}"; do
  [[ $BOOT != "$root" && $BOOT != "$root/"* && $root != "$BOOT/"* ]] || refuse
done
[[ ! -e $BOOT && ! -L $BOOT && -d ${BOOT%/*} && -O ${BOOT%/*} ]] || refuse
for exe in "$PYTHON" "$GNU_TIMEOUT" "$SHA256SUM" "$WC" "$MKDIR"; do [[ -f $exe && -x $exe ]] || refuse; done
# Native tools/real route bindings MUST already have been pinned by parent.
# Suppress even mkdir/redirection failures before private capture is established.
"$GNU_TIMEOUT" --signal=TERM --kill-after=60s 30s "$MKDIR" -m 700 -- "$BOOT" 3>&- >/dev/null 2>/dev/null || refuse
[[ -d $BOOT && -O $BOOT && ! -L $BOOT ]] || refuse
set -o noclobber
{ exec >"$BOOT/stdout" 2>"$BOOT/stderr"; } 2>/dev/null || refuse
# No raw command/argv/source/environment/parser diagnostic can now reach fd3.
# Close fd3 in EVERY external command. Hard file ceiling is administrative only.
ulimit -f 16384 || refuse
file_pin() {
  local p=$1 cap=$2 size whole
  canonical_path "$p" && [[ -f $p && ! -L $p ]] || return 1
  size=$("$GNU_TIMEOUT" --signal=TERM --kill-after=60s 30s "$WC" -c 3>&- <"$p") || return 1
  size=${size//[[:space:]]/}
  [[ $size =~ ^[0-9]{1,9}$ ]] && (( 10#$size <= cap )) || return 1
  whole=$("$GNU_TIMEOUT" --signal=TERM --kill-after=60s 30s "$SHA256SUM" 3>&- <"$p") || return 1
  [[ $whole =~ ^([0-9a-f]{64})[[:space:]]+-$ ]] || return 1
  PIN_BYTES=$size; PIN_SHA=${BASH_REMATCH[1]}
}
check_originals() {
  file_pin "$SHA256SUM" 134217728 && [[ $PIN_SHA == "$SHA_UTILITY_SHA" ]] || return 1
  file_pin "$WC" 134217728 && [[ $PIN_SHA == "$WC_UTILITY_SHA" ]] || return 1
  file_pin "$MKDIR" 134217728 && [[ $PIN_SHA == "$MKDIR_UTILITY_SHA" ]] || return 1
  file_pin "$OUTER_SOURCE" 8388608 && [[ $PIN_SHA == "$OUTER_SHA" ]] || return 1
  file_pin "${BASH_SOURCE[0]}" 8388608 && [[ $PIN_SHA == "$BOOTSTRAP_SHA" ]] || return 1
  file_pin "$M2" 8388608 && [[ $PIN_SHA == "$M2_SHA" ]] || return 1
}
check_originals || refuse
# The eighteen flags include the exact real native Python/GNU hashes, request
# SHA, original review, source1ee hash and all three underlying output paths.
# Parent reviews the WHOLE56-argument bootstrap vector and all M2 route fields;
# unchanged59c independently binds those fields and original inner science.
printf '{"format":"swdb.lanl17-private-bootstrap.start.v1","original_sealed":false,"outer_source_sha256":"%s","M2_sha256":"%s","writer_deadline_seconds":%s,"GNU_timeout_seconds":%s,"GNU_kill_after_seconds":60}\n' "$OUTER_SHA" "$M2_SHA" "$SECONDS_CAP" "$((10#$SECONDS_CAP+720))" >"$BOOT/start.json" || refuse
"$GNU_TIMEOUT" --signal=TERM --kill-after=60s "$((10#$SECONDS_CAP+720))s" "$PYTHON" -B "$OUTER_SOURCE" "${FORWARDED[@]}" 3>&-
CONTROL_EXIT=$?
check_originals || refuse
RESULT_FIELDS=''
for name in start.json stdout stderr; do
  file_pin "$BOOT/$name" 16777216 || refuse
  (( 10#$PIN_BYTES < 16777216 )) || refuse
  [[ -z $RESULT_FIELDS ]] || RESULT_FIELDS+=,
  RESULT_FIELDS+="\"$name\":{\"path\":\"$BOOT/$name\",\"bytes\":$PIN_BYTES,\"sha256\":\"$PIN_SHA\",\"original_sealed\":false}"
done
printf '{"format":"swdb.lanl17-private-bootstrap-result.v1","bootstrap_exit":%s,"outer_source_sha256":"%s","bootstrap_source_sha256":"%s","M2_sha256":"%s","capture_pins":{%s},"original_sealed":false,"raw_diagnostics_returned":false,"independent_validation_or_campaign_admission":false}\n' "$CONTROL_EXIT" "$OUTER_SHA" "$BOOTSTRAP_SHA" "$M2_SHA" "$RESULT_FIELDS" >"$BOOT/bootstrap-result.json" || refuse
file_pin "$BOOT/bootstrap-result.json" 16384 || refuse
RESULT_SHA=$PIN_SHA; RESULT_BYTES=$PIN_BYTES
check_originals || refuse
# This is the ONLY returned stream: bounded status plus an unsealed remote pin.
printf '{"format":"swdb.lanl17-private-bootstrap-return.v1","control_exit":%s,"result_pin":{"path":"%s/bootstrap-result.json","bytes":%s,"sha256":"%s"},"original_sealed":false,"raw_diagnostics_returned":false}\n' "$CONTROL_EXIT" "$BOOT" "$RESULT_BYTES" "$RESULT_SHA" >&3
exit "$CONTROL_EXIT"

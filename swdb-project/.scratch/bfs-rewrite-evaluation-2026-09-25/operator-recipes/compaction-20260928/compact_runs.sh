#!/usr/bin/env bash
# Lossless compaction of /data/yanruj/EvolveSWDB_runs on mbit10.
# Created 2026-09-28 ET at the owner's request. Run by the owner (agent deletion is refused).
#  1) zstd -19 every uncompressed *.log over 100 MB (the 10.9 GB T15 a1 simulation log is the
#     main target). Original path, size and sha256 go to manifest.tsv; zstd verifies before --rm.
#  2) Hardlink byte-identical files >= 10 MB (for example duplicate graph.swdb copies),
#     verified by sha256 and cmp. Content is unchanged, so recorded hashes still verify.
# Run directories modified in the last 120 minutes (active runs) are skipped.
set -u
R=/data/yanruj/EvolveSWDB_runs; M=$R/compaction-20260928
mkdir -p "$M"; cd "$R"
echo "start $(date --iso-8601=s) free=$(df -B1 /data | tail -1 | awk '{print $4}')" >> "$M/log.txt"
find . -mindepth 1 -maxdepth 1 -type d -mmin -120 -printf '%f\n' | sort > "$M/skipped-active.txt"
skip() { local p=${1#./}; p=${p%%/*}; grep -qxF "$p" "$M/skipped-active.txt"; }

find . -type f -name '*.log' -size +100M | while read -r f; do
  skip "$f" && continue
  s=$(sha256sum "$f" | cut -d' ' -f1); z=$(stat -c %s "$f")
  if nice -n 19 zstd -q -19 -T4 --rm "$f" -o "$f.zst"; then
    printf 'zstd\t%s\t%s\t%s\n' "$f" "$z" "$s" >> "$M/manifest.tsv"
  fi
done

find . -type f -size +10M ! -name '*.zst' -printf '%s %p\n' | sort -n > "$M/candidates.txt"
awk '{print $1}' "$M/candidates.txt" | uniq -d | while read -r sz; do
  awk -v s="$sz" '$1==s {sub(/^[0-9]+ /,""); print}' "$M/candidates.txt" | while read -r f; do
    skip "$f" && continue; echo "$(sha256sum "$f" | cut -d' ' -f1) $f"; done | sort > "$M/h.tmp"
  prev=""; keep=""
  while read -r h f; do
    if [ "$h" = "$prev" ]; then
      if [ "$(stat -c %i "$f")" != "$(stat -c %i "$keep")" ] && cmp -s "$keep" "$f"; then
        ln -f "$keep" "$f" && printf 'hardlink\t%s\t%s\t%s\t%s\n' "$f" "$sz" "$h" "$keep" >> "$M/manifest.tsv"
      fi
    else prev=$h; keep=$f; fi
  done < "$M/h.tmp"
done
rm -f "$M/h.tmp"
echo "end $(date --iso-8601=s) free=$(df -B1 /data | tail -1 | awk '{print $4}')" >> "$M/log.txt"

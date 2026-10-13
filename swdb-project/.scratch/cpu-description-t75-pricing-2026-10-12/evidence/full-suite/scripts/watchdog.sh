#!/usr/bin/env bash
# Stops both cpud suite sides if /data free < 25 GB or /data1 free < 12 GB; records why. Runs until both result.txt exist.
R=/data/yanruj/EvolveSWDB_runs/cpud-fullsuite-20261013; SIDES="$*"
while true; do
  done_all=1; for s in $SIDES; do [ -f $R/$s/result.txt ] || done_all=0; done
  [ $done_all = 1 ] && { echo "$(date -Is) all done" >> $R/watchdog.log; exit 0; }
  d=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9); d1=$(df -BG --output=avail /data1 | tail -1 | tr -dc 0-9)
  echo "$(date -Is) data=${d}G data1=${d1}G $(for s in $SIDES; do echo -n "$s=$(du -s -BG $R/$s 2>/dev/null | cut -f1) "; done)" >> $R/watchdog-du.log
  if [ "$d" -lt 25 ] || [ "$d1" -lt 12 ]; then
    echo "$(date -Is) STOP: /data ${d}G free, /data1 ${d1}G free" | tee -a $R/watchdog.log
    for s in $SIDES; do p=$(cat $R/$s/timeout.pid 2>/dev/null) && kill -INT $p 2>/dev/null && echo "$(date -Is) INT -> $s timeout pid $p" >> $R/watchdog.log; done
    sleep 600
    for s in $SIDES; do p=$(cat $R/$s/timeout.pid 2>/dev/null) && kill -0 $p 2>/dev/null && pkill -KILL -g $(ps -o pgid= $p | tr -d ' ') && echo "$(date -Is) KILL group of $s" >> $R/watchdog.log; done
    touch $R/WATCHDOG_STOPPED; exit 1
  fi
  sleep 60
done

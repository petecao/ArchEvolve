#!/usr/bin/env python3
"""Ticket 06 continuation (CBMC box), 2026-10-14 ET. Throwaway.

Runs bounded jobs ONE AT A TIME (called inside one verifier_run.py job, which holds the machine-wide
lock and the 8 GB watchdog over the whole tree). Per job: its own wall-time budget (default 900 s,
map 19 item 8), its own log, and <log>.json with exit code, wall seconds, exact peak RSS of the job
(getrusage in a fresh per-job process), timed_out, host and the log's sha256.

Usage: cbmc_job.py [--budget 900] [--host mac] JOBFILE
JOBFILE lines: <log path> <TAB> <working dir> <TAB> <shell command>
"""
import argparse, hashlib, json, os, resource, signal, socket, subprocess, sys, time


def single(log, cwd, cmd, budget, host):
    t0 = time.time()
    with open(log, "w") as out:
        out.write(f"# cmd: {cmd}\n# cwd: {cwd}\n# host: {host} ({socket.gethostname()})\n"
                  f"# start: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        out.flush()
        p = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        try:
            rc = p.wait(timeout=budget)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(p.pid, signal.SIGKILL)
            rc = p.wait()
        wall = time.time() - t0
        out.write(f"\n# end: wall {wall:.1f} s, exit {rc}, timed_out {timed_out}\n")
    ru = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss   # bytes on macOS, KiB on Linux
    peak_mb = ru / 2**20 if sys.platform == "darwin" else ru / 2**10
    sha = hashlib.sha256(open(log, "rb").read()).hexdigest()
    summary = dict(log=log, cmd=cmd, exit_code=rc, wall_seconds=round(wall, 2), timed_out=timed_out,
                   peak_rss_mb=round(peak_mb, 1), budget_seconds=budget, host=host,
                   log_sha256=sha, finished=time.strftime('%Y-%m-%d %H:%M:%S %Z'))
    json.dump(summary, open(log + ".json", "w"), indent=1)
    print(f"JOB {os.path.basename(log)} exit={rc} wall={wall:.1f}s peak={peak_mb:.0f}MB timed_out={timed_out}", flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        _, _, log, cwd, cmd, budget, host = sys.argv
        single(log, cwd, cmd, float(budget), host)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=900)
    ap.add_argument("--host", default="mac")
    ap.add_argument("jobfile")
    a = ap.parse_args()
    for line in open(a.jobfile):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        log, cwd, cmd = line.split("\t", 2)
        subprocess.run([sys.executable, os.path.abspath(__file__), "--single", log, cwd, cmd, str(a.budget), a.host])


if __name__ == "__main__":
    main()

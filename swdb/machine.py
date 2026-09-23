"""`swdb capture-machine`: a machine record captured from the host itself.

The capture is read-only: it runs `lscpu`, `uname -r`, reads /proc and /etc/os-release,
`numactl --hardware`, `perf_event_paranoid`, and `id -nG`, starts no job, and writes
nothing on the host. It runs locally, over ssh (`--ssh HOST`, the script goes on stdin),
or parses a saved capture (`--from-file`).
"""

import re
import subprocess

SCRIPT = r"""echo "### hostname"; hostname
echo "### lscpu"; LC_ALL=C lscpu
echo "### lscpu-caches"; LC_ALL=C lscpu -C -B
echo "### uname"; uname -r
echo "### os-release"; cat /etc/os-release
echo "### meminfo"; head -3 /proc/meminfo
echo "### numa"; LC_ALL=C numactl --hardware
echo "### perf_event_paranoid"; cat /proc/sys/kernel/perf_event_paranoid
echo "### groups"; id -nG
echo "### date"; date -u +%Y-%m-%dT%H:%M:%SZ
"""


class CaptureError(ValueError):
    pass


def run_capture(ssh_host=None):
    """Run the capture script; returns (raw text, the command that ran it)."""
    if ssh_host:
        argv, shown = ["ssh", ssh_host, "sh", "-s"], f"ssh {ssh_host} sh -s < (swdb capture-machine script)"
    else:
        argv, shown = ["sh", "-s"], "sh -s < (swdb capture-machine script)"
    done = subprocess.run(argv, input=SCRIPT, capture_output=True, text=True, timeout=120)
    if done.returncode != 0 and "### lscpu" not in done.stdout:
        raise CaptureError(f"capture failed (exit {done.returncode}): {done.stderr.strip()}")
    return done.stdout, shown


def sections(raw):
    found, name = {}, None
    for line in raw.splitlines():
        if line.startswith("### "):
            name = line[4:].strip()
            found[name] = []
        elif name is not None:
            found[name].append(line)
    return {key: "\n".join(value).strip() for key, value in found.items()}


def _kv(text):
    pairs = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            pairs[key.strip()] = value.strip()
    return pairs


def _need(pairs, key, where):
    if key not in pairs:
        raise CaptureError(f"{where}: no {key!r} line")
    return pairs[key]


def parse(raw, machine_id, command, date):
    part = sections(raw)
    for name in ("hostname", "lscpu", "lscpu-caches", "uname", "meminfo", "numa", "perf_event_paranoid"):
        if not part.get(name):
            raise CaptureError(f"capture has no {name} section")
    cpu = _kv(part["lscpu"])
    sockets = int(_need(cpu, "Socket(s)", "lscpu"))
    cores = int(_need(cpu, "Core(s) per socket", "lscpu"))
    threads = int(_need(cpu, "Thread(s) per core", "lscpu"))
    max_mhz = cpu.get("CPU max MHz")
    caches = _caches(part["lscpu-caches"], sockets, cores)
    mem_kb = int(re.search(r"MemTotal:\s+(\d+)\s+kB", part["meminfo"]).group(1))
    numa = _numa(part["numa"])
    osrel = dict(line.split("=", 1) for line in part.get("os-release", "").splitlines() if "=" in line)
    paranoid = int(part["perf_event_paranoid"].split()[0])
    groups = part.get("groups", "").split()
    counters_ok = paranoid <= 2 or "vtune" in groups
    note = (f"perf_event_paranoid is {paranoid}"
            + (" (above 2, so unprivileged perf events are blocked)" if paranoid > 2 else "")
            + ("; the user is in the vtune group" if "vtune" in groups else "; the user is not in the vtune group")
            + ". Rule: counters are available if paranoid <= 2 or the user is in the vtune group.")
    return {
        "kind": "machine", "schema_version": "0.2", "id": machine_id, "status": "draft", "deprecated_by": None,
        "created": date[:10], "updated": date[:10],
        "provenance": [{"id": "capture", "kind": "measurement",
                        "description": f"Read-only capture by swdb capture-machine at {date} (UTC).", "uri": None}],
        "hostname": part["hostname"].split()[0],
        "cpu": {"model": _need(cpu, "Model name", "lscpu"), "architecture": _need(cpu, "Architecture", "lscpu"),
                "sockets": sockets, "cores_per_socket": cores, "threads_per_core": threads,
                "logical_cpus": int(_need(cpu, "CPU(s)", "lscpu")),
                "max_mhz": float(max_mhz) if max_mhz else None},
        "caches": caches,
        "memory_bytes": mem_kb * 1024,
        "numa_nodes": numa,
        "os": {"kernel": part["uname"].split()[0], "distribution": osrel.get("PRETTY_NAME", "").strip('"') or None},
        "counters": {"perf_event_paranoid": paranoid,
                     "hardware_counters_available": {"value": counters_ok, "basis": "inferred",
                                                     "evidence_refs": ["capture"], "note": note}},
        "capture": {"command": command, "date": date},
        "lane_required": len(numa) > 1,
        "notes": (["lane_required is host policy, not captured: true on every multi-socket host "
                   "(multi-threaded profiles run only inside a verified socket lane)."] if len(numa) > 1 else []),
        "extensions": {},
    }


def _caches(text, sockets, cores):
    lines = [line.split() for line in text.splitlines() if line.strip()]
    if not lines or lines[0][0] != "NAME":
        raise CaptureError("lscpu -C -B output has no NAME header")
    head = lines[0]
    kinds = {"Data": "data", "Instruction": "instruction", "Unified": "unified"}
    found = []
    for row in lines[1:]:
        cell = dict(zip(head, row))
        one, total = int(cell["ONE-SIZE"]), int(cell["ALL-SIZE"])
        instances = total // one
        if instances == sockets:
            shared = "socket"
        elif instances == sockets * cores:
            shared = "core"
        else:
            raise CaptureError(f"cache {cell['NAME']}: {instances} instances is neither per core nor per socket")
        found.append({"level": int(cell["LEVEL"]), "type": kinds[cell["TYPE"]], "size_bytes": one,
                      "instances": instances, "shared_by": shared})
    return found


def _numa(text):
    nodes = {}
    for line in text.splitlines():
        match = re.match(r"node (\d+) cpus:\s*(.*)$", line)
        if match:
            nodes.setdefault(int(match.group(1)), {})["cpus"] = ",".join(match.group(2).split())
        match = re.match(r"node (\d+) size:\s*(\d+) MB", line)
        if match:
            nodes.setdefault(int(match.group(1)), {})["memory_bytes"] = int(match.group(2)) * 2**20
    if not nodes:
        raise CaptureError("numactl --hardware output lists no nodes")
    return [{"node": n, "cpus": v.get("cpus", ""), "memory_bytes": v.get("memory_bytes")} for n, v in sorted(nodes.items())]


def llc_bytes(machine):
    """Size of one last-level cache instance (the highest level, data or unified)."""
    caches = [c for c in machine["caches"] if c["type"] != "instruction"]
    top = max(c["level"] for c in caches)
    return max(c["size_bytes"] for c in caches if c["level"] == top)

"""Linux Landlock boundary and external resource observation. Updated: 2026-09-29 ET.

The standalone entry point imports only the standard library. It fails closed if
ABI 4 is unavailable; the evaluator stays outside the confined process tree.
"""
import ctypes
import json
import os
import platform
import re
import resource
import shlex
import shutil
import socket
import sys
import time
from pathlib import Path


class GuardError(RuntimeError):
    pass


class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64), ("handled_access_net", ctypes.c_uint64)]


class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


class PortRule(ctypes.Structure):
    _fields_ = [("allowed_access", ctypes.c_uint64), ("port", ctypes.c_uint64)]


def abi():
    if sys.platform != "linux" or platform.machine() not in {"x86_64", "aarch64"}:
        return 0
    return ctypes.CDLL(None, use_errno=True).syscall(444, 0, 0, 1)


def restrict(policy, inner=False):
    if abi() < 4:
        raise GuardError("SWDB provider guard requires Linux Landlock ABI >= 4")
    libc = ctypes.CDLL(None, use_errno=True)
    # ABI 4 includes REFER (13) and TRUNCATE (14). Every supported file
    # operation is handled, so an omitted path receives no access.
    fs_all = (1 << 15) - 1
    read = (1 << 0) | (1 << 2) | (1 << 3)
    rules = Ruleset(fs_all, 3)
    fd = libc.syscall(444, ctypes.byref(rules), ctypes.sizeof(rules), 0)
    if fd < 0:
        raise GuardError("Landlock create_ruleset failed: " + os.strerror(ctypes.get_errno()))
    try:
        for name, access in [(p, read) for p in policy["read_roots"]] + [(p, fs_all) for p in policy["write_roots"]]:
            root = Path(name)
            if not root.exists():
                continue
            pfd = os.open(root, os.O_PATH | os.O_CLOEXEC)
            try:
                rights = access if root.is_dir() else access & ~((1 << 3) | sum(1 << i for i in range(4, 14)))
                entry = PathRule(rights, pfd)
                if libc.syscall(445, fd, 1, ctypes.byref(entry), 0) < 0:
                    raise GuardError("Landlock path rule failed: " + os.strerror(ctypes.get_errno()))
            finally:
                os.close(pfd)
        for port in ([] if inner else policy["tcp_connect_ports"]):
            entry = PortRule(2, port)
            if libc.syscall(445, fd, 2, ctypes.byref(entry), 0) < 0:
                raise GuardError("Landlock port rule failed: " + os.strerror(ctypes.get_errno()))
        if libc.prctl(38, 1, 0, 0, 0) < 0 or libc.syscall(446, fd, 0) < 0:
            raise GuardError("Landlock restrict_self failed: " + os.strerror(ctypes.get_errno()))
    finally:
        os.close(fd)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    memory = policy["limits"]["memory_bytes"]
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_FSIZE, (policy["limits"]["workspace_bytes"],) * 2)
    if inner:
        resource.setrlimit(resource.RLIMIT_CPU, (120, 120))


def _lane():
    if socket.gethostname().split(".")[0] != "mbit10":
        raise GuardError("real rewrite providers require a verified socket lane on mbit10")
    # Reuse the evaluator's kernel-backed verification: exact socket affinity,
    # memory binding, ancestor launcher, lease descriptor and generation.
    from swdb.profile import _verified_lane
    machine = {"id": "mbit10", "hostname": "mbit10", "lane_required": True,
               "numa_nodes": [{"node": node,
                   "cpus": Path(f"/sys/devices/system/node/node{node}/cpulist").read_text().strip()}
                   for node in (0, 1)]}
    return _verified_lane(machine, None)


def _api_addresses(kind):
    hosts = {"codex": ["chatgpt.com", "api.openai.com", "auth.openai.com"],
             "claude": ["api.anthropic.com", "claude.ai"]}.get(kind, [])
    addresses = set()
    for host in hosts:
        try:
            addresses.update(row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM))
        except OSError:
            pass
    if hosts and not addresses:
        raise GuardError("could not resolve provider model API endpoints for network auditing")
    return {"hosts": hosts, "addresses": sorted(addresses)}


def context(config, workspace, home, folder, *, login_path=None, fixture=False):
    """Return the provider-call context; configuration and policy stay evaluator-owned."""
    from swdb.cli import Failure
    workspace, home, folder = (Path(p).resolve() for p in (workspace, home, folder))
    kind = config.get("resolved_kind", config.get("kind"))
    if sys.platform != "linux" and fixture:
        return {"cwd": workspace, "env": _environment(home, workspace, kind),
                "guard": {"enforced": False, "reason": "non-Linux fixture"}}
    try:
        if abi() < 4:
            raise GuardError("SWDB provider guard requires Linux Landlock ABI >= 4; refusing unguarded session")
        lane = _lane() if not fixture or socket.gethostname().split(".")[0] == "mbit10" else None
        tracer = shutil.which("strace")
        if not tracer:
            raise GuardError("SWDB provider guard requires strace for outbound connection auditing")
        command = config["command"][0]
        executable = Path(shutil.which(command) or command).resolve()
        install = executable.parent
        for parent in executable.parents:
            if parent.name == "node_modules":
                install = parent
                break
        roots = ["/usr", "/bin", "/lib", "/lib64", "/etc/ld.so.cache", "/etc/ssl/certs",
                 "/etc/resolv.conf", "/etc/hosts", "/etc/nsswitch.conf", "/etc/passwd", "/etc/localtime",
                 "/dev/null", "/dev/urandom", "/dev/random", "/dev/zero", str(install)]
        guard_folder = folder / "guard"
        guard_folder.mkdir(exist_ok=True)
        launcher = guard_folder / "launch.py"
        shutil.copyfile(__file__, launcher)
        roots.append(str(guard_folder))
        if fixture:
            # Fixtures are operator-owned programs, not model-selected executables.
            roots += [str(Path(p).resolve()) for p in config["command"][1:] if Path(p).is_file()]
        policy = {"enforced": True, "landlock_abi": abi(), "lane": lane,
                  "read_roots": sorted(set(str(Path(p).resolve()) for p in roots if Path(p).exists())),
                  "write_roots": [str(workspace), str(home)], "tcp_connect_ports": [443],
                  "inner_tcp_connect_ports": [], "tcp_bind_ports": [],
                  "model_api": _api_addresses(kind) if not fixture else {"hosts": [], "addresses": []},
                  "login_path": str(login_path) if login_path else None,
                  "limits": {"threads": 16, "memory_bytes": 32 * 1024**3,
                             "command_seconds": 120, "workspace_bytes": 5 * 1024**3},
                  "residual_risks": ["Landlock ABI 4 does not restrict UDP", "login copy readable during session"],
                  "command_network_wrapper": kind == "claude"}
        path = guard_folder / "policy.json"
        path.write_text(json.dumps(policy, indent=2))
        trace = folder / "network.trace"
        env = _environment(home, workspace, kind)
        env["CLAUDE_CODE_SHELL_PREFIX"] = shlex.join([sys.executable, str(launcher), str(path), "--inner", "--"])
        started = {}
        reasons = []

        def wrap_command(argv):
            return [tracer, "-f", "-qq", "-yy", "-e", "trace=connect", "-o", str(trace),
                    sys.executable, str(launcher), str(path), "--", *argv]

        def monitor(child):
            """Observe aggregate descendants externally; never trust provider reports."""
            table = {}
            for entry in Path("/proc").iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    status = (entry / "status").read_text()
                    fields = dict(re.findall(r"^(PPid|Threads|VmRSS):\s*(\d+)", status, re.M))
                    table[int(entry.name)] = fields
                except (OSError, ValueError):
                    continue
            children = {child.pid}
            while True:
                grown = children | {pid for pid, row in table.items() if int(row.get("PPid", 0)) in children}
                if grown == children:
                    break
                children = grown
            threads = sum(int(table[p].get("Threads", 0)) for p in children if p in table)
            rss = sum(int(table[p].get("VmRSS", 0)) * 1024 for p in children if p in table)
            # The observer and standalone launcher count toward the aggregate.
            if threads > 16 or rss > policy["limits"]["memory_bytes"]:
                reasons.append(f"provider resource limit exceeded: threads={threads}, resident_bytes={rss}")
                raise Failure(reasons[-1])
            # Codex has no shell-prefix setting in the verified CLI. Its tool
            # commands inherit the outer TCP policy; observe their wall time
            # from outside that tree and stop the entire attempt on overrun.
            for pid in children:
                try:
                    comm = Path(f"/proc/{pid}/comm").read_text().strip()
                except OSError:
                    continue
                parent = int(table.get(pid, {}).get("PPid", 0))
                # The tracer's direct child is the provider launcher. Native
                # Codex also has a Node installation wrapper; everything else
                # is a provider-created command, including Python/Node helpers.
                provider_root = pid == child.pid or parent == child.pid
                if comm == "codex" and parent in children:
                    try:
                        provider_root = Path(f"/proc/{pid}/exe").resolve().is_relative_to(install)
                    except OSError:
                        pass
                if not provider_root:
                    started.setdefault(pid, time.monotonic())
                    if time.monotonic() - started[pid] > 120:
                        reasons.append("provider tool command exceeds the 120 s wall-time limit")
                        raise Failure(reasons[-1])
            size = 0
            for path in workspace.rglob("*"):
                # Build commands legitimately remove temporary files while the
                # external observer walks the workspace. A disappeared file
                # contributes no live bytes; other errors still fail closed.
                try:
                    if path.is_file() and not path.is_symlink():
                        size += path.stat().st_size
                except FileNotFoundError:
                    continue
            if size > policy["limits"]["workspace_bytes"]:
                reasons.append("provider workspace exceeds the 5 GB limit")
                raise Failure(reasons[-1])

        def finish():
            failures = list(reasons)
            if not fixture:
                if not trace.exists():
                    failures.append("provider outbound connection trace is missing")
                else:
                    for line in trace.read_text(errors="replace").splitlines():
                        if "AF_INET" not in line:
                            continue
                        if "<UDP:" in line:
                            # ABI 4 leaves UDP unrestricted; DNS connections
                            # are not TCP model-API connection violations.
                            continue
                        port = re.search(r"(?:sin_port|sin6_port)=htons\((\d+)\)", line)
                        address = re.search(r'inet_addr\("([^\"]+)"\)|inet_pton\(AF_INET6, "([^\"]+)"', line)
                        if not port or not address:
                            failures.append("unresolved outbound connection in provider network trace")
                        elif int(port[1]) != 443 or (address[1] or address[2]) not in policy["model_api"]["addresses"]:
                            failures.append("provider outbound connection is outside the model API")
            result = {"passed": not failures, "reasons": sorted(set(failures)), "trace": str(trace)}
            (folder / "guard-audit.json").write_text(json.dumps(result, indent=2))
            return result

        return {"cwd": workspace, "env": env, "guard": policy, "guard_policy": policy, "network_trace": str(trace),
                "wrap_command": wrap_command, "monitor": monitor, "finish": finish}
    except (GuardError, OSError, ValueError) as exc:
        raise Failure(str(exc)) from None


def _environment(home, workspace, kind):
    # Never inherit credentials, proxy settings, project variables, or user homes.
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(workspace / "build"),
           "LANG": "C.UTF-8", "OMP_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4",
           "MAKEFLAGS": "-j4", "UV_THREADPOOL_SIZE": "2", "TOKIO_WORKER_THREADS": "2",
           "RAYON_NUM_THREADS": "2", "NODE_OPTIONS": "--max-old-space-size=4096",
           "DISABLE_TELEMETRY": "1", "DISABLE_ERROR_REPORTING": "1",
           "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
           "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1", "DISABLE_AUTOUPDATER": "1",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    env["CODEX_HOME" if kind == "codex" else "CLAUDE_CONFIG_DIR"] = str(home)
    (workspace / "build").mkdir(exist_ok=True)
    return env


def prompt_context(config, folder):
    """Keep opt-in prompt-only real sessions confined as required by story 37."""
    from swdb.cli import Failure
    folder = Path(folder).resolve()
    workspace, home = folder / "workspace", folder / "provider-home"
    workspace.mkdir(exist_ok=True)
    home.mkdir(mode=0o700, exist_ok=True)
    kind = config.get("resolved_kind", config.get("kind"))
    original = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json" if kind == "codex" else Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))) / ".credentials.json"
    login = home / original.name
    try:
        if not original.is_file():
            raise Failure("provider login file is unavailable")
        shutil.copyfile(original, login)
        login.chmod(0o600)
        result = context(config, workspace, home, folder, login_path=login)
    except BaseException:
        login.unlink(missing_ok=True)
        raise
    result["cleanup"] = lambda: login.unlink(missing_ok=True)
    return result


def main():
    args = sys.argv[1:]
    if len(args) < 3 or "--" not in args:
        raise GuardError("usage: launch.py policy.json [--inner] -- command [args]")
    policy = json.loads(Path(args[0]).read_text())
    split = args.index("--")
    command = args[split + 1:]
    inner = "--inner" in args[:split]
    restrict(policy, inner)
    if inner:
        command = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=5", "120", *command]
    os.execvpe(command[0], command, os.environ)


if __name__ == "__main__":
    try:
        main()
    except (GuardError, OSError, ValueError) as exc:
        print("provider guard refused: " + str(exc), file=sys.stderr)
        sys.exit(78)

"""Linux Landlock boundary and external resource observation. Updated: 2026-09-29 ET.

The standalone entry point imports only the standard library. It fails closed if
ABI 4 is unavailable; the evaluator stays outside the confined process tree.
An outside-Landlock subreaper execs strace in place and adopts detached helpers.
A native seccomp filter protects supervisor signal targets while preserving
ordinary helper signals; this is not general hostile-process isolation.
"""
import ctypes
import errno
import json
import os
import platform
import pwd
import re
import resource
import shutil
import signal
import socket
import sys
import time
from pathlib import Path


class GuardError(RuntimeError):
    pass


def _process_identity(pid):
    # comm can contain spaces and parentheses. The fields following its final
    # ')' begin with state (field 3); starttime is field 22, in boot clock ticks.
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "start_time_ticks": int(fields[19]),
            "parent": int(fields[1]), "state": fields[0]}


def _kernel_key(row):
    return row["pid"], row["start_time_ticks"]


def _supervisor_identity(pid):
    identity = _process_identity(pid)
    return {"pid": pid, "start_time_ticks": identity["start_time_ticks"],
            "tids": sorted(int(entry.name) for entry in Path(f"/proc/{pid}/task").iterdir()),
            "process_group": os.getpgid(pid), "session": os.getsid(pid)}


SIGNAL_SYSCALLS = {
    "x86_64": {"arch": 0xc000003e, "seccomp": 317, "kill": 62, "tkill": 200,
               "tgkill": 234, "rt_sigqueueinfo": 129, "rt_tgsigqueueinfo": 297, "pidfd_open": 434},
    "aarch64": {"arch": 0xc00000b7, "seccomp": 277, "kill": 129, "tkill": 130,
                "tgkill": 131, "rt_sigqueueinfo": 138, "rt_tgsigqueueinfo": 240, "pidfd_open": 434}}


class _SockFilter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
               ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]


class _SockFProg(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(_SockFilter))]


def _protect_supervisors(protection):
    """Narrow signal continuity protection; not general hostile-process isolation."""
    machine = platform.machine()
    if machine not in SIGNAL_SYSCALLS or sys.byteorder != "little":
        raise GuardError("provider supervisor signal filter requires a supported native little-endian ABI")
    calls = SIGNAL_SYSCALLS[machine]
    supervisors = protection["supervisors"]
    ids = sorted({value for row in supervisors for value in [row["pid"], *row["tids"]]})
    groups = sorted({row["process_group"] for row in supervisors})
    if not ids or any(value <= 0 for value in ids + groups):
        raise GuardError("provider supervisor signal identities are invalid")
    # Provider-root enters its own session before filtering. Descendants cannot
    # join a supervisor's group across sessions, so kill(0) remains available for
    # legitimate cleanup without reaching the tracer or evaluator.
    if os.getsid(0) != os.getpid() or any(os.getsid(0) == row["session"] for row in supervisors):
        raise GuardError("provider session is not separate from its protected supervisors")
    allow, deny, kill = 0x7fff0000, 0x00050000 | errno.EPERM, 0x80000000
    load, equal, jump, bits, ret = 0x20, 0x15, 0x05, 0x45, 0x06
    # seccomp_data: nr at 0, arch at 4, uint64 args at 16. Native PID arguments
    # are signed 32-bit values; compare their low word even if an attacker puts
    # unrelated bits in the high word. Reject compat/x32 before syscall dispatch.
    program = [(load, 0, 0, 4), (equal, 1, 0, calls["arch"]), (ret, 0, 0, kill),
               (load, 0, 0, 0), (bits, 0, 1, 0x40000000), (ret, 0, 0, kill)]
    checks = {"kill": [(0, [*ids, -1, *(-value for value in groups)])],
              "tkill": [(0, ids)], "tgkill": [(0, ids), (1, ids)],
              "rt_sigqueueinfo": [(0, ids)],
              "rt_tgsigqueueinfo": [(0, ids), (1, ids)], "pidfd_open": [(0, ids)]}
    for name, arguments in checks.items():
        block = []
        for argument, forbidden in arguments:
            block.append((load, 0, 0, 16 + 8 * argument))
            for value in forbidden:
                block.extend([(equal, 0, 1, value & 0xffffffff), (ret, 0, 0, deny)])
        block.append((ret, 0, 0, allow))
        program.extend([(load, 0, 0, 0), (equal, 1, 0, calls[name]),
                        (jump, 0, 0, len(block)), *block])
    program.append((ret, 0, 0, allow))
    if len(program) > 4096:
        raise GuardError("provider supervisor signal filter exceeds the kernel instruction limit")
    instructions = (_SockFilter * len(program))(*(_SockFilter(*entry) for entry in program))
    descriptor = _SockFProg(len(program), instructions)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(39, 0, 0, 0, 0) != 1:
        raise GuardError("provider supervisor signal filter requires no_new_privs")
    # TSYNC is required, never silently retried with fewer flags. This trusted
    # launcher has one thread; all later CLI threads and children inherit it.
    installed = libc.syscall(calls["seccomp"], 1, 1, ctypes.byref(descriptor))
    if installed != 0:
        reason = os.strerror(ctypes.get_errno()) if installed < 0 else f"thread synchronization failed for TID {installed}"
        raise GuardError("provider supervisor signal filter installation failed: " + reason)
    if libc.prctl(21, 0, 0, 0, 0) != 2:
        raise GuardError("provider supervisor signal filter was not enabled")


class _OwnedTree:
    """Observer-owned identities survive reparenting, setsid and PID reuse."""

    def __init__(self, policy):
        self.policy = policy
        self.tracer = None
        self.provider = None
        self.records = {}
        self.cleanup_result = None
        self.first_observed = None
        self.supervisor_protection = None

    def handshakes(self, child, *, required=False):
        ownership = self.policy["process_ownership"]
        records = []
        for key in ("subreaper_record", "provider_record"):
            path = Path(ownership[key])
            if not path.exists():
                if required:
                    raise GuardError("provider process ownership handshake is missing")
                return
            value = json.loads(path.read_text())
            if value.get("nonce") != ownership["nonce"]:
                raise GuardError("provider process ownership handshake does not match this attempt")
            records.append(value)
        owner, provider = records
        tracer = _kernel_key(owner["identity"])
        if tracer[0] != child.pid or not owner.get("subreaper"):
            raise GuardError("provider tracer is not the declared subreaper")
        if self.tracer is not None and self.tracer != tracer:
            raise GuardError("provider tracer kernel identity changed")
        if _kernel_key(provider["parent_identity"]) != tracer:
            raise GuardError("provider root was not launched by its declared tracer")
        original = _kernel_key(provider["identity"])
        if self.provider is not None and self.provider != original:
            raise GuardError("provider root kernel identity changed")
        protection = provider.get("supervisor_protection")
        if (not protection or protection.get("provider_session") != original[0]
                or protection.get("architecture") != platform.machine()
                or [_kernel_key(row) for row in protection.get("supervisors", [])]
                    != [_kernel_key(self.policy["supervisor_protection"]["observer"]), tracer]):
            raise GuardError("provider supervisor signal identities do not match this attempt")
        marker = Path(ownership["filter_marker"])
        if not marker.exists() or marker.read_bytes() != b"1":
            if required:
                raise GuardError("provider supervisor signal filter was not installed")
            return
        self.supervisor_protection = {**protection, "enforced": True}
        self.tracer, self.provider = tracer, original

    def snapshot(self, child):
        """Pin every observed member before using its PID for accounting/signals."""
        if self.first_observed is None:
            self.first_observed = time.monotonic()
        table = {}
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                fields = dict(re.findall(r"^(Threads|VmRSS):\s*(\d+)",
                                         (entry / "status").read_text(), re.M))
                row = _process_identity(int(entry.name))
                row.update(threads=int(fields.get("Threads", 0)),
                           resident_bytes=int(fields.get("VmRSS", 0)) * 1024)
                table[row["pid"]] = row
            except (OSError, ValueError, IndexError):
                continue
        # Popen retains ownership until wait/poll reaps the leader. Capture the
        # initial Python bootstrap identity before it execs strace in place.
        if self.tracer is None and child.returncode is None and child.pid in table:
            self.tracer = _kernel_key(table[child.pid])
        live_keys = {_kernel_key(row) for row in table.values()}
        # Sessions can execute many short commands. Retain their identities for
        # the cleanup receipt without retaining a pidfd after the process exits.
        for key, fd in self.records.items():
            if fd is not None and key not in live_keys:
                os.close(fd)
                self.records[key] = None
        members = {pid for pid, row in table.items() if _kernel_key(row) in self.records
                   or _kernel_key(row) == self.tracer}
        while True:
            grown = members | {pid for pid, row in table.items() if row["parent"] in members}
            if grown == members:
                break
            members = grown
        for pid in members:
            row, fd = table[pid], None
            key = _kernel_key(row)
            if key in self.records:
                continue
            try:
                ancestor = row
                seen = set()
                while _kernel_key(ancestor) not in self.records and _kernel_key(ancestor) != self.tracer:
                    parent = table.get(ancestor["parent"])
                    if (parent is None or parent["pid"] in seen
                            or _kernel_key(_process_identity(parent["pid"])) != _kernel_key(parent)):
                        break
                    seen.add(parent["pid"])
                    ancestor = parent
                else:
                    ancestor = None
                if ancestor is not None:
                    # A numeric PPid alone must not attach a newly reused PID
                    # (and an unrelated process tree) to this attempt.
                    continue
                if (hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal")
                        and sum(value is not None for value in self.records.values()) < 64):
                    fd = os.pidfd_open(pid)
                current = _process_identity(pid)
                if _kernel_key(current) != key or current["parent"] != row["parent"]:
                    if fd is not None:
                        os.close(fd)
                    continue
            except (ProcessLookupError, FileNotFoundError):
                if fd is not None:
                    os.close(fd)
                continue
            except BaseException:
                if fd is not None:
                    os.close(fd)
                raise
            self.records[key] = fd
        return {pid: table[pid] for pid in members if _kernel_key(table[pid]) in self.records}

    def _signal(self, row, sig):
        key = _kernel_key(row)
        fd = self.records[key]
        try:
            if fd is not None:
                signal.pidfd_send_signal(fd, sig)
            elif _kernel_key(_process_identity(row["pid"])) == key:
                os.kill(row["pid"], sig)
        except (ProcessLookupError, FileNotFoundError):
            pass

    def stop(self, child):
        if self.cleanup_result is not None or child is None:
            return self.cleanup_result
        # Keep the tracer alive while it adopts/reaps detached descendants.
        # Repeated scans include descendants forked during TERM handling; every
        # signal targets a pinned identity, never an unchecked reused PID.
        started = time.monotonic()
        survivors = []
        errors = set()
        while True:
            table = self.snapshot(child)
            survivors = [row for row in table.values()
                         if _kernel_key(row) != self.tracer and row["state"] not in {"Z", "X"}]
            if not survivors:
                break
            elapsed = time.monotonic() - started
            for row in survivors:
                try:
                    self._signal(row, signal.SIGTERM if elapsed < .25 else signal.SIGKILL)
                except OSError as exc:
                    errors.add(str(exc))
            if elapsed >= 2:
                break
            time.sleep(.025)
        self.cleanup_result = {"passed": not survivors and not errors, "tracer_pid": child.pid,
            "processes_observed": [{"pid": key[0], "start_time_ticks": key[1], "pidfd": fd is not None}
                                   for key, fd in sorted(self.records.items())],
            "survivors": [{"pid": row["pid"], "start_time_ticks": row["start_time_ticks"]}
                          for row in survivors], "errors": sorted(errors), "wall_s": time.monotonic() - started}
        return self.cleanup_result

    def close(self):
        for fd in self.records.values():
            if fd is not None:
                os.close(fd)
        self.records.clear()


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
        # Bun's runtime inspects its own mapping/cgroup entries at startup.
        # Resolve these inside this standalone process, never to the observer's
        # /proc entries, and never grant access to other processes or environ.
        self_roots = [f"/proc/{os.getpid()}/{name}" for name in policy.get("runtime_self_reads", [])]
        sinks = [(p, read | (1 << 1) | (1 << 14)) for p in policy.get("device_write_roots", [])]
        for name, access in [(p, read) for p in policy["read_roots"] + self_roots] + [(p, fs_all) for p in policy["write_roots"]] + sinks:
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
    # The observer verifies the full socket before launching. The provider uses
    # one CPU within that socket; the full process tree still has a separate
    # 16-thread cap, including idle runtime workers and the external tracer.
    if policy.get("execution_cpus"):
        os.sched_setaffinity(0, policy["execution_cpus"])
    # V8 and JavaScriptCore reserve large, mostly uncommitted address ranges.
    # The 32 GiB limit is aggregate resident memory, observed by the parent;
    # an address-space rlimit would abort these CLIs before they use that RAM.
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
        from swdb import provider_adapters
        command = provider_adapters.get(config).launch_command(config)[0]
        command_path = Path(shutil.which(command) or command).absolute()
        executable = command_path.resolve()
        # Only the selected real native CLI can own a persistent Code Mode
        # service. Fixtures and installation wrappers receive no exemption.
        native_codex = executable if (not fixture and config.get("kind") == "codex"
                                       and executable.name == "codex") else None
        code_mode_host = native_codex.with_name("codex-code-mode-host") if native_codex else None
        install = executable.parent
        if not fixture and config.get("kind") in {"codex", "claude"}:
            for parent in executable.parents:
                manifest = parent / "package.json"
                if manifest.is_file():
                    # The selected package can read its own dependencies. Do
                    # not grant unrelated packages in global node_modules, or
                    # an arbitrary ancestor project of a custom executable.
                    metadata = json.loads(manifest.read_text())
                    name = metadata.get("name", "") if isinstance(metadata, dict) else ""
                    expected = (r"@openai/codex(?:-linux-[a-z0-9-]+)?" if config["kind"] == "codex"
                                else r"@anthropic-ai/claude-code(?:-[a-z0-9-]+)?")
                    if isinstance(name, str) and re.fullmatch(expected, name):
                        install = parent
                    break
        roots = ["/usr", "/bin", "/lib", "/lib64", "/etc/ld.so.cache", "/etc/ssl/certs",
                 "/etc/ssl/openssl.cnf", "/etc/resolv.conf", "/etc/hosts", "/etc/nsswitch.conf", "/etc/passwd", "/etc/localtime",
                 "/proc/sys/vm/mmap_min_addr", "/dev/null", "/dev/urandom", "/dev/random", "/dev/zero", str(install)]
        # A venv's executable symlink resolves into /usr, but Python still reads
        # its adjacent configuration and libraries during interpreter startup.
        # This is the selected toolchain, not an application/evaluator root.
        environment_root = command_path.parent.parent
        if (environment_root / "pyvenv.cfg").is_file():
            roots.append(str(environment_root))
        guard_folder = folder / "guard"
        guard_folder.mkdir(exist_ok=True)
        if kind == "codex":
            # The CLI initializes global SQLite even for an ephemeral turn.
            # Its verified nonfatal fallback avoids persistent state and the
            # five database pools when this empty location cannot be written.
            (guard_folder / "ephemeral-state").mkdir(exist_ok=True)
        launcher = guard_folder / "launch.py"
        shutil.copyfile(__file__, launcher)
        roots.append(str(guard_folder))
        if fixture:
            # Fixtures are operator-owned programs, not model-selected executables.
            roots += [str(Path(p).resolve()) for p in config["command"][1:] if Path(p).is_file()]
        policy = {"enforced": True, "landlock_abi": abi(), "lane": lane,
                  "selected_install_root": str(install),
                  "read_roots": sorted(set(str(Path(p).resolve()) for p in roots if Path(p).exists())),
                  "runtime_self_reads": ["maps", "cgroup", "stat", "statm", "status"],
                  "device_write_roots": ["/dev/null"],
                  "execution_cpus": sorted(os.sched_getaffinity(0))[:1],
                  "resource_scope": "provider process tree including its external strace launcher",
                  "write_roots": [str(workspace), str(home)], "tcp_connect_ports": [443],
                  "inner_tcp_connect_ports": [], "tcp_bind_ports": [],
                  "model_api": _api_addresses(kind) if not fixture else {"hosts": [], "addresses": []},
                  "login_path": str(login_path) if login_path else None,
                  "limits": {"threads": 16, "memory_bytes": 32 * 1024**3,
                             "command_seconds": 120, "workspace_bytes": 5 * 1024**3},
                  "residual_risks": ["Landlock ABI 4 does not restrict UDP", "login copy readable during session",
                                     "supervisor filter covers listed native signal APIs, not general hostile-process isolation"],
                  "command_network_wrapper": kind == "claude"}
        policy["process_ownership"] = {
            "subreaper": True, "bootstrap": "outside Landlock; execs strace in the same PID",
            "original_cli_identity": "observer-owned read-only PID and kernel start-time handshake",
            "cleanup": "pidfd or checked kernel start time; detached descendants before tracer",
            "subreaper_record": str(guard_folder / "subreaper.json"),
            "provider_record": str(guard_folder / "provider-process.json"),
            "filter_marker": str(guard_folder / "supervisor-filter.ready"),
            "nonce": os.urandom(16).hex()}
        policy["supervisor_protection"] = {
            "required": True, "observer": _supervisor_identity(os.getpid()),
            "architecture": platform.machine(), "compat_abi_allowed": False,
            "scope": "listed native signal APIs and direct pidfd_open; not general hostile-process isolation",
            "provider_session": "separate from both supervisor sessions; preserves ordinary kill(0)",
            "pidfd_signals": "ordinary child pidfds allowed; supervisor pidfds not inherited or openable"}
        if kind == "codex":
            policy["session_state"] = {"sqlite_home": str(guard_folder / "ephemeral-state"),
                                       "writable": False, "ephemeral": True}
            policy["persistent_services"] = ([{"executable": str(code_mode_host),
                "parent_executable": str(native_codex), "direct_parent_required": True,
                "resource_accounting": "included"}] if native_codex else [])
        path = guard_folder / "policy.json"
        path.write_text(json.dumps(policy, indent=2))
        trace = folder / "network.trace"
        env = _environment(home, workspace, kind)
        if kind == "claude":
            # Claude passes this value as one executable, followed by -- and
            # one shell command string. It is not a shell-joined argv prefix.
            shell = pwd.getpwuid(os.getuid()).pw_shell
            shell = shutil.which(shell) or "/usr/bin/bash"
            policy["command_shell"] = shell
            path.write_text(json.dumps(policy, indent=2))
            prefix = guard_folder / "shell-prefix"
            prefix.write_text(f"#!{sys.executable}\nimport os, sys\n"
                "args = sys.argv[1:]\n"
                "if args[:1] == ['--']: args = args[1:]\n"
                "if len(args) != 1: raise SystemExit('SWDB shell prefix expects one command')\n"
                f"os.execv({sys.executable!r}, [{sys.executable!r}, {str(launcher)!r}, {str(path)!r}, "
                f"'--inner', '--', {shell!r}, '-c', args[0]])\n")
            prefix.chmod(0o700)
            env["CLAUDE_CODE_SHELL_PREFIX"] = str(prefix)
        reasons = []
        owned = _OwnedTree(policy)

        def wrap_command(argv):
            # PR_SET_CHILD_SUBREAPER survives exec. This adds no live process
            # to the charged tree: the bootstrap becomes the external tracer.
            return [sys.executable, str(launcher), str(path), "--subreaper", "--",
                    tracer, "-f", "-qq", "-yy", "-e", "trace=connect", "-o", str(trace),
                    sys.executable, str(launcher), str(path), "--provider-root", "--", *argv]

        def monitor(child):
            """Observe aggregate descendants externally; never trust provider reports."""
            try:
                table = owned.snapshot(child)
                owned.handshakes(child, required=time.monotonic() - owned.first_observed > 5)
            except (GuardError, OSError, ValueError, KeyError, TypeError) as exc:
                reasons.append("provider process ownership observation failed: " + str(exc))
                raise Failure(reasons[-1]) from None
            threads = sum(row["threads"] for row in table.values())
            rss = sum(row["resident_bytes"] for row in table.values())
            # Charge the external tracer as well as every provider descendant.
            if threads > 16 or rss > policy["limits"]["memory_bytes"]:
                details = []
                for p in sorted(table):
                    names = []
                    try:
                        for task in Path(f"/proc/{p}/task").iterdir():
                            try:
                                names.append((task / "comm").read_text().strip())
                            except OSError:
                                pass
                    except OSError:
                        pass
                    details.append({"pid": p, "parent": table[p]["parent"],
                                    "start_time_ticks": table[p]["start_time_ticks"],
                                    "threads": table[p]["threads"],
                                    "resident_bytes": table[p]["resident_bytes"], "tasks": names})
                (folder / "resource-overrun.json").write_text(json.dumps(details, indent=2))
                reasons.append(f"provider resource limit exceeded: threads={threads}, resident_bytes={rss}")
                raise Failure(reasons[-1])
            # Codex has no shell-prefix setting in the verified CLI. Its tool
            # commands inherit the outer TCP policy; observe their wall time
            # from outside that tree and stop the entire attempt on overrun.
            executables = {}

            def process_executable(pid):
                if pid not in executables:
                    try:
                        executables[pid] = Path(f"/proc/{pid}/exe").resolve(strict=True)
                    except OSError:
                        executables[pid] = None
                return executables[pid]

            native_roots = {pid for pid, row in table.items() if native_codex is not None
                and _kernel_key(row) == owned.provider and process_executable(pid) == native_codex}
            for pid, row in table.items():
                parent = row["parent"]
                # The exact original child is the provider launcher. Native
                # Codex's exact sibling service may outlive a tool invocation,
                # but only as a direct child of that selected native CLI. It
                # remains in the aggregate thread/RSS counts above. Model shells
                # and helpers, including same-named binaries, keep the watchdog.
                provider_root = _kernel_key(row) in {owned.tracer, owned.provider}
                persistent_service = (parent in native_roots
                    and process_executable(pid) == code_mode_host)
                if not provider_root and not persistent_service and row["state"] not in {"Z", "X"}:
                    lifetime = time.clock_gettime(time.CLOCK_BOOTTIME) - row["start_time_ticks"] / os.sysconf("SC_CLK_TCK")
                    if lifetime > policy["limits"]["command_seconds"]:
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

        def stop_owned(child):
            if child is None:
                return
            try:
                owned.handshakes(child, required=True)
            except (GuardError, OSError, ValueError, KeyError, TypeError) as exc:
                reasons.append("provider process ownership observation failed: " + str(exc))
            previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
            try:
                try:
                    cleanup = owned.stop(child)
                    (folder / "process-cleanup.json").write_text(json.dumps(cleanup, indent=2))
                    if cleanup and not cleanup["passed"]:
                        reasons.append("provider owned-process cleanup failed or left surviving descendants")
                except OSError as exc:
                    reasons.append("provider owned-process cleanup failed: " + str(exc))
            finally:
                # A repeated interruption may unwind the adapter, but it cannot
                # kill the tracer first while detached owned helpers are alive.
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)

        def finish():
            failures = list(reasons)
            if not fixture:
                if not trace.exists():
                    failures.append("provider outbound connection trace is missing")
                else:
                    for line in trace.read_text(errors="replace").splitlines():
                        if "AF_INET" not in line or not re.search(r"^(?:\d+\s+)?connect\(", line):
                            continue
                        if re.search(r"<UDP(?:v6)?:", line):
                            # ABI 4 leaves UDP unrestricted; DNS connections
                            # are not TCP model-API connection violations.
                            continue
                        port = re.search(r"(?:sin_port|sin6_port)=htons\((\d+)\)", line)
                        address = re.search(r'inet_addr\("([^\"]+)"\)|inet_pton\(AF_INET6, "([^\"]+)"', line)
                        if not port or not address:
                            failures.append("unresolved outbound connection in provider network trace")
                        elif int(port[1]) != 443 or (address[1] or address[2]) not in policy["model_api"]["addresses"]:
                            failures.append("provider outbound connection is outside the model API")
            result = {"passed": not failures, "reasons": sorted(set(failures)), "trace": str(trace),
                      "process_cleanup": owned.cleanup_result,
                      "supervisor_protection": owned.supervisor_protection,
                      "original_provider": ({"pid": owned.provider[0], "start_time_ticks": owned.provider[1]}
                                            if owned.provider else None)}
            try:
                (folder / "guard-audit.json").write_text(json.dumps(result, indent=2))
                return result
            finally:
                owned.close()

        return {"cwd": workspace, "env": env, "guard": policy, "guard_policy": policy, "network_trace": str(trace),
                "wrap_command": wrap_command, "monitor": monitor, "stop_owned": stop_owned, "finish": finish}
    except (GuardError, OSError, ValueError) as exc:
        raise Failure(str(exc)) from None


def _environment(home, workspace, kind):
    # Never inherit credentials, proxy settings, project variables, or user homes.
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(workspace / "build"),
           "LANG": "C.UTF-8", "OMP_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4",
           "MAKEFLAGS": "-j4", "UV_THREADPOOL_SIZE": "1", "TOKIO_WORKER_THREADS": "1",
           "RAYON_NUM_THREADS": "1", "NODE_OPTIONS": "--max-old-space-size=4096 --v8-pool-size=1",
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
        raise GuardError("usage: launch.py policy.json [--inner|--subreaper|--provider-root] -- command [args]")
    policy = json.loads(Path(args[0]).read_text())
    split = args.index("--")
    command = args[split + 1:]
    options = args[1:split]
    if not command or options not in ([], ["--inner"], ["--subreaper"], ["--provider-root"]):
        raise GuardError("invalid provider guard launch mode")
    filter_fd, protection = None, None
    if options in (["--subreaper"], ["--provider-root"]):
        ownership = policy["process_ownership"]
        identity = _process_identity(os.getpid())
        record = {"nonce": ownership["nonce"],
                  "identity": {key: identity[key] for key in ("pid", "start_time_ticks")}}
        if options == ["--subreaper"]:
            libc = ctypes.CDLL(None, use_errno=True)
            enabled = ctypes.c_int()
            if (libc.prctl(36, 1, 0, 0, 0) < 0
                    or libc.prctl(37, ctypes.byref(enabled), 0, 0, 0) < 0 or enabled.value != 1):
                raise GuardError("provider tracer subreaper could not be enabled")
            record["subreaper"] = True
            record["supervisor"] = _supervisor_identity(os.getpid())
            target = Path(ownership["subreaper_record"])
        else:
            parent = _process_identity(os.getppid())
            record["parent_identity"] = {key: parent[key] for key in ("pid", "start_time_ticks")}
            owner = json.loads(Path(ownership["subreaper_record"]).read_text())
            observer = _supervisor_identity(policy["supervisor_protection"]["observer"]["pid"])
            tracer = _supervisor_identity(parent["pid"])
            if (owner.get("nonce") != ownership["nonce"] or not owner.get("subreaper")
                    or _kernel_key(owner["identity"]) != _kernel_key(tracer)
                    or _kernel_key(observer) != _kernel_key(policy["supervisor_protection"]["observer"])):
                raise GuardError("provider supervisors do not match the trusted launch records")
            # A separate session prevents kill(0) or setpgid from reaching a
            # supervisor group while preserving ordinary helper group signals.
            os.setsid()
            protection = {"architecture": platform.machine(), "supervisors": [observer, tracer],
                          "provider_session": os.getsid(0),
                          "filtered_syscalls": ["kill", "tkill", "tgkill", "rt_sigqueueinfo",
                                                "rt_tgsigqueueinfo", "pidfd_open"],
                          "compat_abi_allowed": False, "kill_all_allowed": False}
            record["supervisor_protection"] = protection
            # Open a one-byte acknowledgement before Landlock, then write it
            # only after successful seccomp installation. No model code runs
            # before this descriptor is closed, and it is never inherited.
            filter_fd = os.open(ownership["filter_marker"], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600)
            target = Path(ownership["provider_record"])
        # Publish atomically outside Landlock. The final file is evaluator-owned
        # read-only context for every confined child, so model code cannot forge
        # the original CLI identity. Exclusive creation also rejects stale runs.
        temporary = target.with_suffix(".pending")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as handle:
            json.dump(record, handle)
        os.link(temporary, target)
        temporary.unlink()
        if options == ["--subreaper"]:
            # The flag survives execve, while children do not inherit it. The
            # evaluator itself is never a subreaper; no observer process is added.
            os.execvpe(command[0], command, os.environ)
    inner = options == ["--inner"]
    try:
        restrict(policy, inner)
        if protection is not None:
            _protect_supervisors(protection)
            if os.write(filter_fd, b"1") != 1:
                raise GuardError("provider supervisor signal filter acknowledgement failed")
    finally:
        if filter_fd is not None:
            os.close(filter_fd)
    if inner:
        command = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=5", "120", *command]
    os.execvpe(command[0], command, os.environ)


if __name__ == "__main__":
    try:
        main()
    except (GuardError, OSError, ValueError) as exc:
        print("provider guard refused: " + str(exc), file=sys.stderr)
        sys.exit(78)

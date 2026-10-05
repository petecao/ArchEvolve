# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/targets/base.py (unchanged logic)
# 2026-10-05 ET (code review): docstring references to MemAcc's CUDA target, its spec and a MemAcc
# document, none of which were ported (D1), removed.
"""WS-C synthesis — per-target harness protocol (build / sanitize / run seams)."""
from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple


@dataclass(frozen=True)
class BuildResult:
    ok: bool
    binary: Optional[Path]
    log: str


class TargetHarness:
    name: str = "base"

    def preflight(self, workdir: Path) -> Tuple[bool, str]:
        """Check target/tool availability before spending a Claude invocation."""
        return True, "no target-specific preflight required"

    def build(self, sources: Sequence[Path], out_bin: Path, *,
              sanitize: bool = False) -> BuildResult:
        raise NotImplementedError

    def run(self, binary: Path, args: Sequence[str], cwd: Optional[Path] = None,
            timeout_s: int = 600) -> Tuple[int, str]:
        """Run `binary`. Contract unchanged: returns (returncode, combined
        stdout+stderr); a timeout returns (124, "timeout after {timeout_s}s")
        rather than raising.

        Process-group hygiene (final-review hardening — naive-daemon
        reaping). The child is launched in its OWN session
        (`start_new_session=True`, POSIX `setsid()`), so it heads a fresh
        process group, and that whole group is best-effort SIGKILLed in
        `finally` -- after EVERY run, not only on timeout -- so a background
        process the target forked WITHOUT itself calling `setsid()` is
        reaped together with it. This closes a known residual: a process
        trick such as forking a detached background process that outlives its
        own measured invocation and races a *later* case's `ref_dir`. A
        candidate that calls `setsid()` itself detaches into a session this
        harness has no handle on and escapes this net entirely -- that
        residual still needs real OS-level process sandboxing (a restricted
        filesystem view / chroot / container / `sandbox-exec`), tracked
        separately; this closes the NAIVE-fork case only. It should not be
        read as closing the race in general, and this docstring makes no
        broader claim than that. This is also just correct subprocess
        hygiene independent of the security angle: a legitimate backend
        writes its output and exits on its own, so by the time `finally`
        runs there is nothing left alive in the group -- `killpg` raises
        `ProcessLookupError`, swallowed below -- making this a no-op for the
        common case.

        Deliberately captures `pgid = proc.pid` at spawn time rather than
        calling `os.getpgid(proc.pid)` inside `finally` (the more obvious
        phrasing). `start_new_session=True` makes the child its own
        process-group leader, so its pid IS the group id for the group's
        entire lifetime, independent of whether that leader process is
        later reaped -- but `communicate()`'s non-timeout path internally
        calls `wait()` once the child's pipes reach EOF, which DOES reap
        that specific pid, and `os.getpgid()` on an already-reaped pid
        raises `ProcessLookupError` even when the group still has a live
        member. Verified empirically: a child that backgrounds a
        stdio-detached grandchild and exits immediately leaves the
        grandchild alive and in the same group, but `os.getpgid(proc.pid)`
        called after `communicate()` has already returned fails to find it
        (ESRCH) -- silently skipping the kill in exactly the case this
        hardening exists for, which is also precisely the common shape of a
        "naive" background process (a plain `fork()` with the child's own
        stdio closed/redirected, not inherited). Capturing `proc.pid` once,
        up front, and using it directly as the pgid sidesteps that gap.
        """
        with subprocess.Popen([str(binary), *map(str, args)], cwd=cwd,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, start_new_session=True) as proc:
            pgid = proc.pid
            try:
                stdout, stderr = proc.communicate(timeout=timeout_s)
                return proc.returncode, (stdout or "") + (stderr or "")
            except subprocess.TimeoutExpired:
                return 124, f"timeout after {timeout_s}s"
            finally:
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass

    def build_ref(self, sources: Sequence[Path], out_bin: Path, *,
                  sanitize: bool = False) -> BuildResult:
        """Build the TRUSTED REFERENCE binary. Defaults to build() so CPU
        targets (neon/avx512) are unaffected. A target whose candidate needs
        another toolchain overrides this, keeping the trusted side independent
        of the candidate's toolchain."""
        return self.build(sources, out_bin, sanitize=sanitize)

    def sanitized_run(self, binary: Path, args: Sequence[str],
                      cwd: Optional[Path] = None,
                      timeout_s: int = 600) -> Tuple[int, str]:
        """Run the CANDIDATE binary under its sanitizer. Defaults to run() so
        CPU targets keep the ASan/UBSan-in-the-binary discipline (a plain run
        whose exit code catches an ASan abort). Contract: (returncode, combined
        output); nonzero => the certify loop rejects the candidate."""
        return self.run(binary, args, cwd=cwd, timeout_s=timeout_s)

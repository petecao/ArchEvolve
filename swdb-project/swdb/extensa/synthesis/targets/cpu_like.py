# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/targets/cpu_like.py (imports rewritten onto swdb.extensa)
"""Shared CPU-compile target harness: build with the spec's cc/flags; the
sanitize layer is ASan/UBSan. NEON (local Apple-Silicon) and AVX-512 (mbit10
Ice Lake) differ only in name and in what the spec's flags say — the harness
is identical, so it lives once here. run() is inherited from TargetHarness
(process-group hygiene) unchanged."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence

from swdb.extensa.synthesis.spec import TargetSpec
from swdb.extensa.synthesis.targets.base import BuildResult, TargetHarness

_SANITIZE_FLAGS = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]


class CpuCompileTarget(TargetHarness):
    name = "cpu"

    def __init__(self, spec: TargetSpec):
        self.spec = spec

    def build(self, sources: Sequence[Path], out_bin: Path, *,
              sanitize: bool = False) -> BuildResult:
        cmd = [self.spec.cc, *self.spec.flags]
        if sanitize:
            cmd += _SANITIZE_FLAGS
        cmd += [*map(str, sources), "-o", str(out_bin)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        log = (p.stdout or "") + (p.stderr or "")
        if p.returncode != 0:
            return BuildResult(False, None, log)
        return BuildResult(True, Path(out_bin), log)

# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/testgen_backend.py (prompt, cleanroom
#         compile, pass-on-real and fail-on-mutant mutation gate)
"""Independent test generation and the mutation gate.

The test author sees the contract only, never the synthesized backend or the
certification cases. Its test is accepted only if it passes on the real backend AND
fails on a mutant chosen at gate time with an rng it never sees.

SWDB changes (2026-10-03 ET): the call goes through SWDB's provider launcher role
`independent_test_generation` (structured output `{tests, unresolved}`); one attempt
per call (each call is charged by the campaign ledger, decision D7); the cleanroom
compile is unchanged.
"""
from __future__ import annotations

import dataclasses
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from swdb.extensa.synthesis.families import canonical_contract_json, contract_sha256
from swdb.extensa.synthesis.mutants import write_mutant
from swdb.extensa.synthesis.shape_classes import SHAPE_CLASSES
from swdb.extensa.synthesis.families import FAMILIES
from swdb.extensa.synthesis.targets.base import TargetHarness

_TESTGEN_BASE = """\
You are a test author. Write ONE standalone C++11 test file named test_{family}.cpp.

Contract under test (implement checks from the CONTRACT ONLY):
{intent}

The complete contract is in `CONTRACT.json` (SHA-256 `{contract_sha256}`).

The backend is `struct SynthBackend` from `#include "synth_backend.hh"`. Its hook is a
FUNCTION TEMPLATE:
  {hook}

Test EXACTLY ONE instantiation (ValueT = double, IndexT = int) with EXPLICIT template
arguments.
{hint}

Requirements: deterministic inputs; include boundary indices (first/last element, a
duplicate); compute the expected result independently with a plain loop; assert the
backend output equals the expected result elementwise (bitwise); return nonzero if any
assertion fails; print SYNTH_TEST_OK and return 0 on success. Return the file in the
`tests` array of your JSON answer.
"""


def build_prompt(family_name: str, contract: dict, feedback: str = "") -> str:
    sc = SHAPE_CLASSES[FAMILIES[family_name].shape_class]
    p = _TESTGEN_BASE.format(family=family_name, intent=contract.get("intent", ""), hook=sc.hook,
                             contract_sha256=contract_sha256(contract), hint=sc.test_hint)
    if feedback:
        p += "\n\n## Previous attempt failed\n```\n" + feedback[-2000:] + "\n```\n"
    return p


@dataclass(frozen=True)
class TestgenResult:
    __test__ = False
    accepted: bool
    test_path: Optional[Path]
    reason: str
    infrastructure_error: bool = False


def _compile_and_run(test_src: Path, backend_header: Path, incdir_name: str, target: TargetHarness,
                     workdir: Path, extra_include: Path):
    inc = workdir / incdir_name
    inc.mkdir(parents=True, exist_ok=True)
    shutil.copy(backend_header, inc / "synth_backend.hh")
    cleanroom_test = inc / test_src.name
    shutil.copy(test_src, cleanroom_test)
    spec = dataclasses.replace(target.spec, flags=(*target.spec.flags, f"-I{inc}", f"-I{extra_include}"))
    harness = type(target)(spec)
    build = harness.build([cleanroom_test], workdir / f"test_{incdir_name}", sanitize=True)
    if not build.ok:
        return None, f"test build failed: {build.log[-1200:]}"
    return harness.run(build.binary, [])


def run_testgen_gate(family_name: str, contract: dict, backend_header: Path, target: TargetHarness,
                     workdir: Path, *, invoker: Callable[..., dict], extra_include: Path,
                     mutant_rng: Optional[random.Random] = None, feedback: str = "") -> TestgenResult:
    """One charged attempt. `invoker(files=..., prompt=...)` returns the role's output."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        response = invoker(files={"CONTRACT.json": canonical_contract_json(contract)},
                           prompt=build_prompt(family_name, contract, feedback))
    except Exception as exc:                          # noqa: BLE001 - recorded as infrastructure
        return TestgenResult(False, None, f"test generation call failed: {exc}", infrastructure_error=True)
    tests = [t for t in (response or {}).get("tests", []) if t.get("path") == f"test_{family_name}.cpp"]
    if not tests:
        return TestgenResult(False, None, f"no test_{family_name}.cpp in the test-generation output")
    test_src = workdir / "generated" / f"test_{family_name}.cpp"
    test_src.parent.mkdir(parents=True, exist_ok=True)
    test_src.write_text(tests[0]["content"])
    code_real, out_real = _compile_and_run(test_src, backend_header, "real", target, workdir, extra_include)
    if code_real is None:
        return TestgenResult(False, None, f"test failed to COMPILE against the backend: {str(out_real)[-400:]}")
    if code_real != 0:
        return TestgenResult(False, None, f"test asserts false on the backend (exit {code_real}): {out_real[-400:]}")
    mutant = write_mutant(family_name, workdir / "mutant" / "mutant.hh", rng=mutant_rng)
    code_mut, _ = _compile_and_run(test_src, mutant, "mut", target, workdir, extra_include)
    if code_mut is None:
        return TestgenResult(False, None, "mutant build failed (gate infrastructure error)", infrastructure_error=True)
    if code_mut == 0:
        return TestgenResult(False, None, "TOOTHLESS: the test passes on the injected mutant")
    return TestgenResult(True, test_src, "passes on real, kills mutant")

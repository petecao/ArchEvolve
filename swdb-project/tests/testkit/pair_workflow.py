"""2026-10-16 ET. Shared pair public-lowering and isolated fixture builders.

Extracted unchanged from test_pair_workflow; actual execution still requires
an explicitly admitted profile. Importing this module performs no tool probes.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb

SOURCE = FIXTURES / "proof/lowering/pair_only.cc"
CONTRACT = "contract.fixture_pair_values"


def _lower(source, function, out, *, ok=True):
    done = run_swdb("lower", "--source", source, "--function", function,
                    "--out", out, "--format", "json")
    assert (done.returncode == 0) is ok, done.stdout + done.stderr
    return json.loads(done.stdout) if ok else done


def _seed(root, *, actual=False, source=SOURCE):
    """Small library/empty store: no catalog, candidate or unrelated vector fixture."""
    from swdb import c_lowering, std_models
    records = make_records(root)
    records.path.mkdir(exist_ok=True)
    library = root / "library"
    methods = library / "methods"
    methods.mkdir(parents=True)
    method = yaml.safe_load((FIXTURES / "proof/methods/contract-fixture-1.yaml").read_text())
    method.update(id="method.pair-workflow-fixture", sequence=2,
                  description="2026-10-15 ET: pair-only original body and caller contract fixture.")
    method["lineup"] = yaml.safe_load((REPO / "library/methods/probata-draft-1.yaml").read_text())["lineup"]
    next(row for row in method["lineup"] if row["tool"] == "frama-c-wp")["flags"] += [
        "-rte-initialized", "@all", "-wp-no-filter-init"]
    method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    method["models"].update(std_vector=std_models.identity(), std_pair=std_models.identity())
    (methods / "pair-workflow-fixture.yaml").write_text(yaml.safe_dump(method, sort_keys=False))
    units = library / "proof_units"
    units.mkdir()
    shutil.copy(source, units / "pair_only.cc")
    clauses = [("pre", "legality", r"requires -1000 <= x <= 1000 && -1000 <= y <= 1000;"),
               ("post", "postcondition", r"assigns \nothing; ensures \result == 3*x+y;")]
    entry = {
        "kind": "rewrite_contract", "id": CONTRACT, "formal_frame": 1, "version": "1.0",
        "provenance": {"origin": {"intrinsic_specification": "pair-only-fixture-20261015"}},
        "proof_unit": {"function": "swdb_pair_values", "source": {"root": "library",
            "path": "proof_units/pair_only.cc", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}},
        "concurrency_frame": [],
        "clauses": [{"id": name, "role": role, "statement": "Pair fixture " + name,
            "discharge_mode": "runtime_guard", "negative_control": {"id": name + "-control", "check": name},
            "acsl": {"text": text, "uses": []}, "proof_placement": {"once": "self"}}
            for name, role, text in clauses],
        "pattern_key": [{"roles": ["index", "target"], "address_shapes": ["stream", "single_valued_indirect"],
                         "update_kind": "read"}],
        "strategies": [], "uses_intrinsics": [], "uses_library_operations": [], "runtime_guards": [],
        "knobs": [], "preservation_obligations": [], "correctness_check": {"kernel": "fixture", "check": "fixture"},
        "execution_witness": {"check": "fixture"},
        "negative_controls": [{"id": kind, "kind": kind, "check": "fixture"}
            for kind in ("overlapping_pointer", "double_claim", "dropped_operand")], "requirement_map": []}
    contracts = library / "rewrite_contracts"
    contracts.mkdir()
    (contracts / "fixture_pair_values.yaml").write_text(yaml.safe_dump(entry, sort_keys=False))
    wrong = json.loads(json.dumps(entry))
    wrong["id"] = "contract.fixture_pair_wrong_field"
    wrong["proof_unit"]["function"] = "swdb_pair_wrong_field"
    (contracts / "fixture_pair_wrong_field.yaml").write_text(yaml.safe_dump(wrong, sort_keys=False))
    marker = root / "standin-parser-launched"
    env = {}
    if not actual:
        frama = root / "frama-standin.py"
        frama.write_text('import sys\nfrom pathlib import Path\n'
            'if "-version" in sys.argv: print("33.0");sys.exit(0)\n'
            'if "-wp" in sys.argv:\n'
            f' Path({str(marker)!r}).write_text("parser-error stand-in; no solver")\n'
            ' print("[kernel] wp_input.c:3: User Error: scripted fault\\nFrama-C aborted: invalid user input.");sys.exit(1)\n')
        names = {"alt-ergo": "Alt-Ergo", "z3": "Z3", "cvc5": "CVC5"}
        config = root / "why3-standin.conf"
        config.write_text("".join(f'[prover]\nname = "{names[row["tool"]]}"\nversion = "{row["version"]}"\n'
            'command = "/usr/bin/false"\n' for row in method["lineup"] if row["tool"] in names))
        env = {"SWDB_FRAMA_C": f"{sys.executable} {frama}", "WHY3CONFIG": str(config),
               "SWDB_VERIFIER_LOCK": str(root / "standin-only.lock")}

    def prove(*args, ok=True, extra_env=None, runtime=None):
        timeout = 600
        if actual:
            deadline = float(os.environ["SWDB_PAIR_DEADLINE_MONOTONIC"])
            remaining = deadline - time.monotonic()
            assert remaining > 15, "actual pair profile exhausted its prospective wall budget"
            # Leave setup/record-writing headroom; the actual adapter's own
            # process-tree watchdog enforces the remaining per-job allocation.
            args = (*args, "--budget-minutes", str((remaining - 15) / 60))
            timeout = remaining
        command = ("prove", "--records", records.path, "--adapter", "wp",
                   "--method-version", method["id"], "--runs-dir", root / "runs", "--format", "json", *args)
        selected_env = {**env, **(extra_env or {})}
        if runtime:
            done = subprocess.run([sys.executable, "-m", "swdb", *map(str, command)], cwd=runtime,
                                  env={**os.environ, **selected_env}, capture_output=True, text=True, timeout=timeout)
        else:
            done = run_swdb(*command, env=selected_env, timeout=timeout)
        if not ok:
            return done
        assert done.returncode == 0, done.stdout + done.stderr
        return yaml.safe_load((records.path / json.loads(done.stdout)["path"]).read_text())
    return prove, marker

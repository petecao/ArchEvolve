"""BC gem5 v2 completion witness. Created: 2026-10-03 ET (ticket 44).

gem5 exits at the ROI seal before the program's own BCVerifier would run, so a
BC gem5 evaluation, like BFS's, resumes the same guest after the seal, checks the
exact returned scores with the trusted original-graph oracle and requires a
bounded syscall-trace witness that the guest called ``exit_group(0)``.

``swdb/dx100_witness.py`` is frozen (protocols pin its sha256) and names only
BFS. This module applies the same v2 rules to BC identities instead of copying
them: it checks the BC-specific parts itself (checker, protected score result,
original-adjacency treatment, exact output bytes) and runs the BFS validator on
a translated copy of the evaluation for every kernel-agnostic rule (execution
binding, ROI seal, runtime helpers, continuation, trace witness and artifacts).
The syscall-trace parser and ROI-seal serializer are kernel-agnostic and shared.
"""

import copy
import hashlib
import math
import os
import re
import stat
from pathlib import Path

from swdb import dx100_witness as w

CHECKER = "dx100.bc.verifier.v2"
ROI = "bc.complete_call.v1"
RESULT = re.compile(r"SWDB_BC_RESULT source=(\d+) vertices=(\d+) score_count=(\d+) score_fnv1a64=([a-f0-9]{16})\s*")
FINGERPRINT = "noncryptographic FNV-1a over little-endian IEEE single score bits"


def graph_verification_contract(application):
    """Stable BC treatment identity shared by compilation, dispatch and evidence."""
    w._need(application in {"gapbs", "dx100-gapbs"}, "unsupported original graph application")
    return {"contract": "swdb.bc.original-adjacency.v1",
            "input_format": "gapbs.sg64" if application == "gapbs" else "gapbs.sg32",
            "byte_order": "little",
            "adjacency": "outgoing CSR from exact registered serialized input",
            "maximum_extra_bytes": 2147483648,
            "preload": "before checkpoint and ROI",
            "verification": "after ROI on exact returned score buffer; serial Brandes in the source's float types",
            "count_type": "double" if application == "gapbs" else "float",
            "allocation": "oracle adjacency before ROI; Brandes work arrays in the post-ROI continuation"}


def parse_result(line, number, after_seal):
    found = RESULT.fullmatch(line)
    if not found:
        return None
    return {"source": int(found[1]), "vertices": int(found[2]), "score_count": int(found[3]),
            "score_fnv1a64": found[4], "line": number, "after_seal": after_seal, "fingerprint_kind": FINGERPRINT}


def _output_evidence(path):
    """Recompute BC completion rows and hash from the same bounded output bytes."""
    path = Path(path)
    w._need(path.is_absolute() and not path.is_symlink(), "output requires an absolute regular file")
    verdicts, results, times, markers, digest, consumed = [], [], [], 0, hashlib.sha256(), 0
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            w._need(stat.S_ISREG(before.st_mode) and before.st_size <= w.MAX_OUTPUT_BYTES,
                    "output exceeds regular-file bound")
            number = 0
            for raw in iter(lambda: stream.readline(1024 * 1024 + 1), b""):
                number += 1
                consumed += len(raw)
                w._need(len(raw) <= 1024 * 1024 and consumed <= w.MAX_OUTPUT_BYTES, "output exceeds line or byte bound")
                digest.update(raw)
                line = raw.decode("utf-8", errors="replace")
                if line.strip() == "SWDB_DX100_ROI_SEALED":
                    markers += 1
                found = re.fullmatch(r"\s*Verification\s*:\s*(PASS|FAIL)\s*", line)
                if found:
                    verdicts.append({"verdict": found[1], "line": number, "after_seal": markers == 1})
                row = parse_result(line, number, markers == 1)
                if row:
                    results.append(row)
                found = re.fullmatch(r"\s*(Verification Time|Average Time):\s*([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?\d+)?)\s*", line)
                if found:
                    value = float(found[2])
                    times.append({"kind": found[1], "seconds": value, "line": number,
                                  "after_seal": markers == 1, "finite": math.isfinite(value)})
            after = os.fstat(stream.fileno())
            w._need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and consumed == before.st_size,
                    "output changed while reading")
    except OSError as exc:
        raise w.WitnessError(f"protected output unavailable: {exc}") from None
    w._need(markers == 1, "protected output needs exactly one ROI seal marker")
    return digest.hexdigest(), verdicts, results, times


def _bc_rules(evaluation):
    """BC-specific identities the BFS rules cannot see; returns the protected score row."""
    request, context, build = evaluation["request"], evaluation["context"], evaluation["build"]
    check = evaluation["correctness"]["checks"][0]
    continuation = check["continuation"]
    w._need(request["verification"]["checker"] == context["verifier"] == check["checker"]
            == continuation["checker"] == context["sealed_roi"]["verification"]["checker"] == CHECKER,
            "BC v2 request/context/checker identity differs")
    w._need(context.get("candidate_build") is True and context.get("roi") == ROI,
            "BC v2 applies to protected complete-call BC candidates only")
    contract = graph_verification_contract(context.get("application"))
    w._need(build.get("adapter") == "dx100.complete_call.v2"
            and w._same(context.get("graph_verification"), contract)
            and w._same(context["instrumentation"].get("graph_verification"), contract),
            "complete-call BC candidate lacks the original-adjacency oracle treatment")
    w._need(w._same(w._reference(context["verifier_source"], "original graph oracle"),
                    w._reference(context["candidate_driver"], "candidate wrapper")),
            "original graph oracle is not the protected compiled wrapper")
    w._need("parent_results" not in check, "BC evaluations carry score results, not parent results")
    rows = check["score_results"]
    w._need(isinstance(rows, list) and len(rows) == 1, "protected score result is missing or ambiguous")
    row = rows[0]
    w._need(isinstance(row, dict) and set(row) == {"source", "vertices", "score_count", "score_fnv1a64", "line",
                                                   "after_seal", "fingerprint_kind"}
            and row["fingerprint_kind"] == FINGERPRINT, "invalid protected score result fields")
    return row


def _translated(evaluation, row):
    """The evaluation under BFS v2 names, so the frozen BFS rules apply unchanged."""
    data = copy.deepcopy(evaluation)
    data["request"]["verification"]["checker"] = w.CHECKER
    data["context"]["verifier"] = w.CHECKER
    check = data["correctness"]["checks"][0]
    check["checker"] = w.CHECKER
    check["continuation"]["checker"] = w.CHECKER
    data["context"]["sealed_roi"]["verification"]["checker"] = w.CHECKER
    check["parent_results"] = [{"source": row["source"], "vertices": row["vertices"],
                                "parent_count": row["score_count"], "parent_fnv1a64": row["score_fnv1a64"],
                                "line": row["line"], "after_seal": row["after_seal"]}]
    del check["score_results"]
    return data


def _verify_output(evaluation, reference):
    check = evaluation["correctness"]["checks"][0]
    digest, verdicts, results, times = _output_evidence(reference["path"])
    w._need(digest == reference["sha256"] and w._same(verdicts, check["observed_verdicts"])
            and w._same(results, check["score_results"]) and w._same(times, check["completion_sequence"]["times"]),
            "retained protected output observations differ from actual bytes")


def _verify_artifacts(evaluation, available_only=False):
    rows = []
    for kind, reference in w._witness_artifacts(evaluation):
        path = Path(reference["path"])
        if available_only and not path.exists():
            rows.append((kind, reference, False))
            continue
        if kind == "output":
            _verify_output(evaluation, reference)
        else:
            # Seal, trace, parser and helper checks read the actual BC identities.
            w._verify_artifact(evaluation, kind, reference)
        rows.append((kind, reference, True))
    return rows


def validate_completed_witness(evaluation, *, verify_artifacts=True, require_complete_evaluation=True):
    """Validate one BC v2 execution's completion witness (BFS v2 rules, BC identities)."""
    from swdb.cli import Failure
    try:
        row = _bc_rules(evaluation)
        _integer = w._integer
        w._need(row["after_seal"] is True and _integer(row["vertices"], "score vertices", 1)
                == _integer(row["score_count"], "score count", 1), "protected score result is incomplete")
    except (w.WitnessError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise Failure(f"invalid completed BC v2 witness: {exc}") from None
    # Every kernel-agnostic rule: the frozen BFS validator on the translated copy.
    witness = w.validate_completed_witness(_translated(evaluation, row), verify_artifacts=False,
                                           require_complete_evaluation=require_complete_evaluation)
    if verify_artifacts:
        try:
            _verify_artifacts(evaluation)
        except (w.WitnessError, KeyError, TypeError, ValueError, OverflowError) as exc:
            raise Failure(f"invalid completed BC v2 witness: {exc}") from None
    return witness


def validate_record_witness(evaluation, store=None):
    """Qualify retained BC v2 metadata; present artifacts are rechecked, as for BFS."""
    from swdb.cli import Failure
    from swdb.retention import retained
    import socket
    witness = validate_completed_witness(evaluation, verify_artifacts=False)
    try:
        context = evaluation["context"]
        hosts = [host for host in (context.get("host"), context.get("execution_environment", {}).get("host"),
                                   evaluation.get("build", {}).get("execution_environment", {}).get("host"))
                 if host is not None]
        w._need(all(isinstance(host, str) and host and host == host.strip() for host in hosts), "invalid execution host identity")
        w._need(len({host.split(".")[0] for host in hosts}) <= 1, "inconsistent execution host identities")
        host = hosts[0].split(".")[0] if hosts else None
        remote = host is not None and host != socket.gethostname().split(".")[0]
        rows = []
        for kind, reference, checked in _verify_artifacts(evaluation, available_only=True):
            w._need(not Path(reference["path"]).is_symlink(), f"{kind} artifact is a symlink")
            if checked:
                state = "verified"
            else:
                receipt = retained(store, reference, evaluation["id"])
                if receipt:
                    state = receipt["state"]
                else:
                    w._need(remote and str(reference["path"]).startswith(("/data/", "/data1/")),
                            f"{kind} raw artifact is unavailable locally")
                    state = "remote_unverified"
            rows.append({"kind": kind, **reference, "state": state})
        state = ("remote_unverified" if any(r["state"] == "remote_unverified" for r in rows) else
                 "pruned, sha256 retained" if any(r["state"] == "pruned, sha256 retained" for r in rows) else "verified")
        return {"witness": witness, "availability": {"state": state, "host": host, "artifacts": rows}}
    except (w.WitnessError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise Failure(f"invalid retained BC v2 witness: {exc}") from None


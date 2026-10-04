#!/usr/bin/env python3
"""Ticket 58: the "is the specification enough?" experiment driver.

Created: 2026-10-04 ET. Extensa mode (decisions D7, D10 of
`.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`).

Three inputs (arms), each given to the rewrite role through the provider launcher
(`swdb.provider_roles.run`, shared pins, guard and audit) on an mbit10 socket lane:

  A `spec`               Peter's v1.1 intrinsic specification only;
  B `spec_draft`         A plus Josh's hardware-candidate draft;
  C `spec_draft_contract` B plus our rewrite contract `contract.bfs_read_offload`.

Every arm also gets the same base source (the scalar-only snapshot), the canonical
lowering header the certifier requires, and HARNESS.md (the evaluator's interface:
which file may change, build macros, the protected logging line and the execution
witness hooks). The working rewrite (ticket 20's patch) and the authors' accelerated
code are never inputs; the role's input check and a driver check refuse them.

Each sample is scored by the unchanged `swdb certify` (contract.bfs_read_offload,
scalar-only snapshot, full matrix) with records created under the Extensa tags. If
certification aborts (for example a negative control has no mutation site in the
candidate), the sample is not certified and a labeled diagnostic (functional matrix
without controls, control-site presence) is kept; the diagnostic is never a
certification.

Stages: `provider` (all samples, sequential, at most the budgeted counted calls),
`score` (scores samples as their responses appear), `reference` (scores ticket 20's
patch through the same harness as a positive control; no provider call) and
`summary`. Raw output stays under <runs root>/extensa/<campaign>/.
"""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parent
sys.path.insert(0, str(PROJECT))

from swdb import artifacts, certification, provider_adapters, provider_login, provider_roles, workflow  # noqa: E402
from swdb.cli import Failure, UsageError, _require_valid  # noqa: E402

CAMPAIGN_PATTERN = "extensa-gem5-bfs-{date}-s1"
SNAPSHOT = "bfs-dx100-scalar-only-20260929-a1.source"
SNAPSHOT_SHA256 = "2bf9b1b85bf3be392e2986d1879aeabea5a23479fd7e8060a31d76e5b3a5c6af"
CONTRACT = "contract.bfs_read_offload"
SPEC = {"commit": "0b56895", "path": "docs/bfs-intrinsics-spec-yanru.md",
        "sha256": "3e54374ae43c841bad3f71d9210cb110742dfdb1bf688cde1953de9df64aabf9"}
DRAFT = {"path": "runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/intrinsic-draft.yaml",
         "sha256": "01f05bdc517922a082a10c9e28d8f1501c92892ba06a1e5298a60e7cc5d0bf30"}
DRAFT_REDACTION = ("inspected TDStepMAA sequence", "inspected accelerated-TDStep sequence")
CONTRACT_FILE = "swdb-project/library/rewrite_contracts/bfs_read_offload.yaml"
LOWERING = PROJECT / "library/dx100/dxc_lowering.hpp"
REFERENCE_PATCH = PROJECT / "library/dx100/peter-section5.patch"
LOGIN = re.compile(r"login|not logged in|unauthori[sz]ed|authentication|credentials|token_invalidated|"
                   r"refresh_token_reused", re.I)
ARMS = ("spec", "spec_draft", "spec_draft_contract")
SAMPLES = 3
COUNTED_CALL_BUDGET = len(ARMS) * SAMPLES        # D7-style cap for this experiment: 9
LANE_SECONDS = 3 * 3600                           # ticket 58: about 3 lane-hours
#: Distinctive text of the working rewrite (ticket 20's patch); never an input.
WORKING_REWRITE_MARKERS = ("swdb_contexts[omp_get_thread_num()]", "if(claimed){parent[v]=u;lqueue.push_back(v);}",
                           "Peter section 5 read offload, fixes E1-E5")

ROLE = provider_roles.Role("extensa_rewriting_spec_experiment", {
    "type": "object", "additionalProperties": False, "required": ["patch", "unresolved"],
    "properties": {"patch": {"type": "string"},
                   "unresolved": {"type": "array", "items": {"type": "string"}}}})

PROMPT = """\
Extensa-mode rewrite, campaign {campaign}, input {arm}, sample {sample}.
Rewrite the scalar top-down step `TDStep` in `source/benchmarks/gapbs/src/bfs.cc` so that
its reads are offloaded to the DX100 accelerator through the `__dxc_*` intrinsics, as
described by the documents under `spec/`. Read HARNESS.md first: it states the build,
the only file you may change and the execution-witness hooks. The lowering header under
`lowering/` is the executable intrinsic interface; the harness adds it to the tree.
Return ONE unified diff against `source/` in `patch` (paths `a/benchmarks/gapbs/src/bfs.cc`
and `b/benchmarks/gapbs/src/bfs.cc`), and list in `unresolved` every point the documents
left open that you had to decide. Do not state performance outcomes.
"""

HARNESS = """\
# Harness interface (identical for every input)

- Only `benchmarks/gapbs/src/bfs.cc` may change. The harness adds
  `benchmarks/gapbs/src/swdb_dxc_lowering.hpp`, byte-identical to `lowering/swdb_dxc_lowering.hpp`;
  include it as `#include "swdb_dxc_lowering.hpp"`. Do not add or edit it in your patch.
- Build: `g++ -std=c++11 -fopenmp -DFUNC -DGEM5 -DTILE_SIZE=<t> -DNUM_CORES=<n>` with the
  DX100 functional model and a strict functional layer that checks intrinsic usage at run
  time (ownership, waits, bounds, capacity). `TILE_SIZE` and `NUM_CORES` vary between builds;
  OpenMP runs with `NUM_CORES` threads.
- Keep this statement in `TDStep` unchanged and executed once per top-down step:
  `std::cout << "Starting TDStep: " << queue.size() << " elements" << std::endl;`
  Keep `BFSVerifier` unchanged.
- Execution witness: call `__dxc_accelerated_chunk()` once for every chunk the accelerator
  processes, and `__dxc_report()` once per BFS call before it returns. The evaluator expects
  the accelerated path to run whenever a frontier holds at least 64 vertices.
- You cannot compile or run anything here; reason from the files.
"""


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(text):
    return hashlib.sha256(text.encode() if isinstance(text, str) else text).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def checked_input(text, pin, name):
    if sha(text) != pin:
        raise Failure(f"{name} differs from its sha256 pin")
    return text


def spec_text():
    text = subprocess.run(["git", "show", f"{SPEC['commit']}:{SPEC['path']}"], cwd=REPOSITORY,
                          capture_output=True, text=True, check=True).stdout
    return checked_input(text, SPEC["sha256"], "specification")


def base_source(scratch):
    """The scalar-only snapshot, reconstructed and checked against its registered identity."""
    store = _require_valid(PROJECT / "records")
    tree, snapshot = certification.materialize_snapshot(store, SNAPSHOT, scratch)
    if snapshot["artifact"]["sha256"] != SNAPSHOT_SHA256:
        raise Failure("scalar-only snapshot identity changed")
    files = {}
    for path in sorted(p for p in tree.rglob("*") if p.is_file()):
        files["source/" + path.relative_to(tree).as_posix()] = path.read_text()
    return files


def arm_files(arm, base):
    files = dict(base)
    files["HARNESS.md"] = HARNESS
    files["lowering/swdb_dxc_lowering.hpp"] = LOWERING.read_text()
    files["spec/bfs-intrinsics-spec.md"] = spec_text()
    pins = {"spec/bfs-intrinsics-spec.md": SPEC["sha256"]}
    if arm in ("spec_draft", "spec_draft_contract"):
        draft = checked_input((REPOSITORY / DRAFT["path"]).read_text(), DRAFT["sha256"], "draft")
        # The pinned draft names the authors' accelerated function once, in a note (line 198).
        # The role's input check refuses that identifier, so the workspace copy replaces only
        # that one name; the redacted copy's sha256 is recorded next to the pin.
        if draft.count(DRAFT_REDACTION[0]) != 1:
            raise Failure("draft redaction site changed")
        files["spec/intrinsic-draft.yaml"] = draft.replace(*DRAFT_REDACTION)
        pins["spec/intrinsic-draft.yaml"] = {"pinned": DRAFT["sha256"],
                                             "workspace_copy": sha(files["spec/intrinsic-draft.yaml"]),
                                             "redaction": list(DRAFT_REDACTION)}
    if arm == "spec_draft_contract":
        files["spec/bfs_read_offload.contract.yaml"] = (REPOSITORY / CONTRACT_FILE).read_text()
        pins["spec/bfs_read_offload.contract.yaml"] = sha(files["spec/bfs_read_offload.contract.yaml"])
    for name, text in files.items():
        hit = [m for m in WORKING_REWRITE_MARKERS if m in text]
        if hit:
            raise Failure(f"input {name} exposes the working rewrite ({hit[0]})")
    return files, pins


def folders(args):
    """Attempt a1 (2026-10-04) used runs/ and provider-ledger.json; later attempts get their own."""
    root = artifacts.external_directory(args.runs_root) / "extensa" / args.campaign
    runs = root / "runs" if args.attempt == "a1" else root / f"runs-{args.attempt}"
    return root, root / "records", runs


def ledger_file(args, root):
    return root / ("provider-ledger.json" if args.attempt == "a1" else f"provider-ledger-{args.attempt}.json")


def sample_ids():
    return [(arm, n) for n in range(1, SAMPLES + 1) for arm in ARMS]   # interleaved in time


def login_preflight(ledger, ledger_path, kind="codex"):
    """D7 login preflight (2026-10-04): pause, uncounted, before any session is spent.

    Offline only: a missing or malformed login file, or the same login file (by hash)
    that a recorded session already saw refused, pauses the run. Never records values.
    Returns the login file's short hash for the session row.
    """
    check = provider_login.preflight(kind)
    refused = {c.get("login_source_sha256") for c in ledger["calls"] if c.get("outcome") == "login"} - {None}
    if check["state"] == "ok" and check["source_sha256"] in refused:
        check.update(state="login", reason="this login was already refused by the provider; run `codex login`")
    if check["state"] != "ok":
        ledger.setdefault("preflights", []).append({"at": now(), "outcome": "login", "counted": False, **check})
        save(ledger_path, ledger)
        raise Failure(f"provider paused (login); uncounted; preflight: {check['reason']}")
    return check["source_sha256"]


def provider_stage(args):
    root, _records, runs = folders(args)
    runs.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_file(args, root)
    ledger = json.loads(ledger_path.read_text()) if ledger_path.is_file() else {"calls": []}
    pins = provider_adapters.PINS["codex"]
    if pins != {"model": "gpt-5.6-sol", "effort": "xhigh"}:
        raise Failure("the authorized Codex model/effort pin changed")
    config_path = root / "codex-provider.request.json"
    if args.provider_config:          # contract-fixture smoke tests only
        config_path = args.provider_config
    else:
        save(config_path, {"kind": "codex", "command": [args.codex_command], "workspace": True,
                           "timeout_s": 1200, "total_seconds": 1200, "max_repairs": 0})
    from swdb import rewrite
    config = rewrite.configuration(config_path)
    if (root / "base-source").exists():
        shutil.rmtree(root / "base-source")     # the driver's own reconstruction scratch
    base = base_source(root / "base-source")
    started = time.monotonic()
    for arm, n in sample_ids():
        folder = runs / f"{arm}-s{n}"
        if (folder / "failure.json").is_file() and \
                json.loads((folder / "failure.json").read_text())["outcome"] in ("login", "usage_limit"):
            k = 1
            while folder.with_name(f"{folder.name}.paused{k}").exists():
                k += 1
            folder.rename(folder.with_name(f"{folder.name}.paused{k}"))     # kept; retried after resume
        if (folder / "response.json").is_file() or (folder / "failure.json").is_file():
            continue
        counted = sum(1 for c in ledger["calls"] if c["counted"])
        if counted >= COUNTED_CALL_BUDGET:
            raise Failure("the experiment's counted provider calls are spent")
        if time.monotonic() - started + 1200 > args.lane_seconds:
            raise Failure("the next provider call could exceed the lane-hour budget")
        files, input_pins = arm_files(arm, base)
        provider_roles._inputs(files)       # refused inputs never open (or count) a call
        login_sha = None if args.provider_config else login_preflight(ledger, ledger_path)
        folder.mkdir(parents=True, exist_ok=True)
        row = {"arm": arm, "sample": n, "invocation": f"{args.campaign}.{arm}-s{n}", "started": now(),
               "input_pins": input_pins, "visible_files": sorted(files), "login_source_sha256": login_sha}
        try:
            response, meta = provider_roles.run(ROLE, files, PROMPT.format(campaign=args.campaign, arm=arm, sample=n),
                                                config, folder / "provider")
            row.update(outcome="completed", counted=True)
            save(folder / "response.json", response)
        except provider_adapters.ProviderUnavailable as exc:
            row.update(outcome="usage_limit", counted=False, error=str(exc))
        except Failure as exc:
            # D7: a login failure is uncounted and pauses the run. Codex reports it only on
            # stderr (attempt a1, 2026-10-04: 401 token_invalidated / refresh_token_reused).
            text = str(exc)
            stderr = folder / "provider" / "stderr.txt"
            detail = text + (stderr.read_text(errors="replace") if stderr.is_file() else "")
            login = bool(LOGIN.search(detail))
            row.update(outcome="login" if login else "failed", counted=not login, error=text)
        receipt = folder / "provider" / "provider.json"
        meta = json.loads(receipt.read_text()) if receipt.is_file() else {}
        audit = meta.get("audit") or {}
        row.update(ended=now(), model=meta.get("model"), effort=meta.get("effort"),
                   classification=meta.get("classification"), cli_version=meta.get("cli_version"),
                   audit_passed=audit.get("passed"), guard_passed=(meta.get("guard_result") or {}).get("passed"),
                   login_copy_deleted=(meta.get("workspace_manifest") or {}).get("login_copy_deleted"),
                   login_writeback={k: v for k, v in ((meta.get("workspace_manifest") or {})
                                    .get("login_writeback") or {}).items() if k in ("changed", "written_back", "reason")},
                   lane=meta.get("lane"))
        ledger["calls"].append(row)
        save(ledger_path, ledger)
        if row["outcome"] != "completed":
            save(folder / "failure.json", row)
        if row["outcome"] in ("usage_limit", "login"):
            raise Failure(f"provider paused ({row['outcome']}); uncounted; resume later")
    return {"calls": len(ledger["calls"]), "counted": sum(1 for c in ledger["calls"] if c["counted"])}


def scoring_patch(response_patch):
    """The provider's bfs.cc diff plus the canonical lowering header addition (harness rule)."""
    patch = response_patch if response_patch.endswith("\n") else response_patch + "\n"
    header = LOWERING.read_text()
    lines = header.splitlines()
    addition = ("--- /dev/null\n+++ b/benchmarks/gapbs/src/swdb_dxc_lowering.hpp\n"
                f"@@ -0,0 +1,{len(lines)} @@\n" + "".join("+" + line + "\n" for line in lines))
    return patch + addition


def control_sites(source):
    sites = {}
    for name in certification._CONTROL_EXPECTED:
        try:
            certification._rewrite_control(certification.instrument_source(source), name)
            sites[name] = True
        except Failure:
            sites[name] = False
    return sites


class _SiteControls:
    """Diagnostic only: the BFS plug-in restricted to the controls whose mutation site exists
    in this candidate. Never a certification and never a record."""

    def __init__(self, plugin, names):
        self._plugin = plugin
        self.certification_controls = {k: v for k, v in plugin.certification_controls.items() if k in names}

    def __getattr__(self, name):
        return getattr(self._plugin, name)


def diagnostic(patch_path, folder, library):
    from swdb import kernels
    store = _require_valid(PROJECT / "records")
    folder.mkdir(parents=True, exist_ok=True)
    tree, _snapshot = certification.materialize_snapshot(store, SNAPSHOT, folder)
    certification.apply_patch(tree, patch_path)
    source = (tree / certification.BFS).read_text()
    try:
        sites = control_sites(source)
    except Failure as exc:
        sites = {"error": str(exc)}
    present = {k for k, v in sites.items() if v is True}
    matrix, controls = certification.certify_bfs(tree, library, folder, (16384, 1024), 4, (0,),
                                                 plugin=_SiteControls(kernels.BFS, present))
    return {"label": "diagnostic, not certification", "control_sites": sites,
            "matrix": [{k: c.get(k) for k in ("graph", "tile_size", "source", "status", "reason")} for c in matrix],
            "matrix_passed": sum(1 for c in matrix if c["status"] == "passed"), "matrix_cells": len(matrix),
            "site_controls": {f"{c['id']}@{c['tile_size']}": c["status"] for c in controls},
            "site_controls_rejected": sum(1 for c in controls if c["status"] == "rejected")}


def score_one(args, name, response_patch, folder):
    root, records, _runs = folders(args)
    store_dir = root / "scoring-store" / "records"
    if not store_dir.is_dir():
        shutil.copytree(PROJECT / "records", store_dir)
    folder.mkdir(parents=True, exist_ok=True)
    patch_path = folder / "scoring.patch"
    patch_path.write_text(scoring_patch(response_patch))
    result = {"sample": name, "patch_sha256": artifacts.file_hash(patch_path), "started": now()}
    touched = sorted({line[6:].strip() for line in response_patch.splitlines() if line.startswith("+++ b/")})
    result["provider_patch_files"] = touched
    from swdb.store import Store
    previous = dict(workflow.CREATION_TAGS)
    workflow.CREATION_TAGS.clear()
    workflow.CREATION_TAGS.update(mode="extensa", campaign=args.campaign)
    try:
        record = certification.certify(Store(store_dir), CONTRACT, runs_dir=folder / "certify", snapshot=SNAPSHOT,
                                       patch=patch_path, tile_sizes=(16384, 1024), threads=4, sources=(0,))
        controls = record["negative_controls"]
        result.update(certification=record["id"], verdict=record["verdict"],
                      matrix_passed=sum(1 for c in record["matrix"] if c["status"] == "passed"),
                      matrix_cells=len(record["matrix"]),
                      controls_rejected=sum(1 for c in controls if c["status"] == "rejected"),
                      controls_total=len(controls),
                      controls={f"{c['id']}@{c['tile_size']}": c["status"] for c in controls})
        records.mkdir(parents=True, exist_ok=True)
        (records / "certifications").mkdir(exist_ok=True)
        for path in (store_dir / "certifications").glob(record["id"] + ".*"):
            shutil.copy2(path, records / "certifications" / path.name)
    except (Failure, UsageError) as exc:
        result.update(verdict="aborted", certification=None, abort_reason=str(exc),
                      controls_rejected=0, controls_total=16)
    finally:
        workflow.CREATION_TAGS.clear()
        workflow.CREATION_TAGS.update(previous)
    if result["verdict"] == "aborted" and "cannot be applied" not in result["abort_reason"] \
            and "changed files" not in result["abort_reason"]:
        try:
            result["diagnostic"] = diagnostic(patch_path, folder / "diagnostic", (PROJECT / "library").resolve())
        except (Failure, UsageError) as exc:
            result["diagnostic"] = {"label": "diagnostic, not certification", "error": str(exc)}
    result["ended"] = now()
    save(folder / "score.json", result)
    return result


def score_stage(args):
    _root, _records, runs = folders(args)
    pending = {f"{arm}-s{n}" for arm, n in sample_ids()}
    deadline = time.monotonic() + args.lane_seconds
    while pending and time.monotonic() < deadline:
        progressed = False
        for name in sorted(pending):
            folder = runs / name
            if (folder / "score" / "score.json").is_file():
                pending.discard(name); progressed = True
            elif (folder / "failure.json").is_file():
                pending.discard(name); progressed = True
            elif (folder / "response.json").is_file():
                patch = json.loads((folder / "response.json").read_text())["patch"]
                score_one(args, name, patch, folder / "score")
                pending.discard(name); progressed = True
        if pending and not progressed:
            if (args.provider_done.is_file() if args.provider_done else False):
                break
            time.sleep(30)
    return {"unscored": sorted(pending)}


def reference_stage(args):
    """Positive control of the harness: ticket 20's bfs.cc diff through the same scoring path."""
    _root, _records, runs = folders(args)
    text = REFERENCE_PATCH.read_text()
    bfs_only = text[:text.index("--- /dev/null\n+++ b/benchmarks/gapbs/src/swdb_dxc_lowering.hpp")]
    return score_one(args, "reference-ticket20", bfs_only, runs / "reference-ticket20" / "score")


def summary_stage(args):
    root, _records, runs = folders(args)
    ledger_path = ledger_file(args, root)
    ledger = json.loads(ledger_path.read_text()) if ledger_path.is_file() else {"calls": []}
    rows = []
    for arm, n in sample_ids():
        name = f"{arm}-s{n}"
        call = next((c for c in ledger["calls"] if c["arm"] == arm and c["sample"] == n), None)
        score_path = runs / name / "score" / "score.json"
        score = json.loads(score_path.read_text()) if score_path.is_file() else None
        response_path = runs / name / "response.json"
        response = json.loads(response_path.read_text()) if response_path.is_file() else None
        rows.append({"arm": arm, "sample": n,
                     "provider": None if call is None else {k: call.get(k) for k in (
                         "outcome", "counted", "started", "ended", "model", "effort", "audit_passed",
                         "guard_passed", "login_copy_deleted")},
                     "unresolved": None if response is None else response.get("unresolved"),
                     "score": None if score is None else {k: score.get(k) for k in (
                         "verdict", "certification", "matrix_passed", "matrix_cells", "controls_rejected",
                         "controls_total", "controls", "abort_reason", "diagnostic", "patch_sha256",
                         "provider_patch_files")}})
    reference = runs / "reference-ticket20" / "score" / "score.json"
    result = {"format": "swdb.spec-enough-experiment-summary.v1", "campaign": args.campaign, "mode": "extensa",
              "attempt": args.attempt,
              "ticket": 58, "created": now(), "swdb_commit": subprocess.run(
                  ["git", "rev-parse", "HEAD"], cwd=REPOSITORY, capture_output=True, text=True).stdout.strip(),
              "inputs": {"spec": SPEC, "draft": DRAFT, "contract": {"path": CONTRACT_FILE,
                         "sha256": artifacts.file_hash(REPOSITORY / CONTRACT_FILE)},
                         "snapshot": {"id": SNAPSHOT, "sha256": SNAPSHOT_SHA256},
                         "lowering": {"path": "swdb-project/library/dx100/dxc_lowering.hpp",
                                      "sha256": artifacts.file_hash(LOWERING)},
                         "harness_sha256": sha(HARNESS), "prompt_sha256": sha(PROMPT)},
              "budget": {"counted_calls_limit": COUNTED_CALL_BUDGET, "lane_seconds": args.lane_seconds,
                         "counted_calls_used": sum(1 for c in ledger["calls"] if c["counted"]),
                         "uncounted_calls": sum(1 for c in ledger["calls"] if not c["counted"])},
              "reference_positive_control": json.loads(reference.read_text()) if reference.is_file() else None,
              "samples": rows, "gain_claim": False, "evidence_basis": "simulated"}
    target = root / ("summary.json" if args.attempt == "a1" else f"summary-{args.attempt}.json")
    save(target, result)
    return {"summary": str(target), "sha256": artifacts.file_hash(target)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=["provider", "score", "reference", "summary"], required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--provider-config", type=Path, help="external_fixture provider (smoke tests only)")
    parser.add_argument("--lane-seconds", type=int, default=LANE_SECONDS)
    parser.add_argument("--attempt", default="a1", help="attempt label; each attempt keeps its own runs and ledger")
    parser.add_argument("--provider-done", type=Path, help="file whose presence ends the score stage's wait")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"a[0-9]+", args.attempt):
        raise SystemExit("attempt must look like a2")
    if not re.fullmatch(r"extensa-gem5-bfs-[0-9]{8}-s[0-9]+", args.campaign):
        raise SystemExit("campaign ID must look like " + CAMPAIGN_PATTERN)
    stage = {"provider": provider_stage, "score": score_stage, "reference": reference_stage,
             "summary": summary_stage}[args.stage]
    try:
        print(json.dumps(stage(args), indent=2))
    except (Failure, UsageError) as exc:
        print(json.dumps({"stage": args.stage, "error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

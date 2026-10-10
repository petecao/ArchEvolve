#!/usr/bin/env python3
"""Ticket 58: the "is the intrinsic specification enough?" experiment driver.

Created: 2026-10-04 ET. Updated: 2026-10-05 ET (code review: P1 call outcomes, P6 named
budgets, J5 public names, glossary). Extensa mode (decisions D7, D10 of
`.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`).

Three inputs (arms), each given to the rewrite role through the provider launcher
(`swdb.provider_roles.run`, shared pins, guard and audit) on an mbit10 socket lane:

  A `spec`               Peter's v1.1 intrinsic specification only;
  B `spec_draft`         A plus Josh's hardware-candidate draft;
  C `spec_draft_contract` B plus our rewrite contract `contract.bfs_read_offload`.

The arm IDs are recorded labels (legacy: "spec" there means the intrinsic specification).
Every arm also gets the same base source (the scalar-only snapshot), the canonical
lowering header the certifier requires, and the evaluator interface file (`HARNESS.md`,
its recorded legacy name: which file may change, build macros, the protected logging
line and the execution witness hooks). The working rewrite (ticket 20's patch) and the
authors' accelerated code are never inputs; the role's input check and a driver check
refuse them. The provider-visible texts (PROMPT, EVALUATOR_INTERFACE) are pinned inputs
whose hashes the summaries record, so their wording is never edited.

Each sample's candidate artifact is scored by `swdb certify` (contract.bfs_read_offload,
scalar-only snapshot, full matrix) with records created under the Extensa tags. Since ticket
62 (2026-10-04 ET) the negative controls are library-side faults, so a sample's spelling no
longer decides whether a control exists. If certification aborts for another reason, the
sample is not certified and a labeled diagnostic is kept; the diagnostic is never a
certification.

Attempt a3 (2026-10-04 ET): the prompt names the only commands the strict audit can
follow (plain reads) and forbids heredocs, awk, git apply, patch and file writes; a
`STOP-<attempt>` file in the Extensa campaign folder stops the provider stage before its
next session; and the stage stops itself (writing that file) when the attempt's first
`--stop-after-failures` sessions all fail.

Call outcomes (code review P1, 2026-10-05 ET): every provider call is classified by
`swdb.provider_adapters.classify`, the classifier the Extensa campaign uses. A usage limit,
provider capacity, guard runtime limit or login stop is recorded uncounted under its own
outcome and pauses the stage; a resume retries the sample. Before, a capacity stop was
recorded as `usage_limit` and a guard runtime-limit stop was counted as a failed rewrite.

Stages: `provider` (all samples, sequential, at most the budgeted counted calls),
`score` (scores samples as their responses appear), `reference` (scores ticket 20's
patch through the same evaluator interface as a positive control; no provider call) and
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

from swdb import (artifacts, certification, certification_legality, kernels, provider_adapters,  # noqa: E402
                  provider_login, provider_roles, workflow)
from swdb.cli import Failure, UsageError, _require_valid  # noqa: E402
from swdb.extensa import search  # noqa: E402

CAMPAIGN_PATTERN = "extensa-gem5-bfs-{date}-s1"
SNAPSHOT = "bfs-dx100-scalar-only-20260929-a1.source"
SNAPSHOT_SHA256 = "2bf9b1b85bf3be392e2986d1879aeabea5a23479fd7e8060a31d76e5b3a5c6af"
CONTRACT = "contract.bfs_read_offload"
#: The intrinsic specification (Peter's v1.1); `SPEC` and the `spec*` arm IDs are recorded names.
SPEC = {"commit": "0b56895", "path": "docs/bfs-intrinsics-spec-yanru.md",
        "sha256": "3e54374ae43c841bad3f71d9210cb110742dfdb1bf688cde1953de9df64aabf9"}
DRAFT = {"path": "runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/intrinsic-draft.yaml",
         "sha256": "01f05bdc517922a082a10c9e28d8f1501c92892ba06a1e5298a60e7cc5d0bf30"}
DRAFT_REDACTION = ("inspected TDStepMAA sequence", "inspected accelerated-TDStep sequence")
CONTRACT_FILE = "swdb-project/library/rewrite_contracts/bfs_read_offload.yaml"
LOWERING = PROJECT / "library/dx100/dxc_lowering.hpp"
REFERENCE_PATCH = PROJECT / "library/dx100/peter-section5.patch"
ARMS = ("spec", "spec_draft", "spec_draft_contract")
SAMPLES = 3
COUNTED_CALL_BUDGET = len(ARMS) * SAMPLES        # D7-style cap for this experiment: 9
LANE_SECONDS = 3 * 3600                           # ticket 58: about 3 lane-hours
#: P6 (2026-10-05 ET): the per-call provider budget; also the lane time a next call may need.
CALL_SECONDS = 1200
STOP_AFTER_FAILURES = 2                           # a3: stop when the first N counted sessions all fail
SCORE_POLL_SECONDS = 30                           # the score stage's wait for the next response
#: Certification matrix of every sample (tile sizes, OpenMP threads, BFS sources).
TILE_SIZES = (16384, 1024)
CERTIFY_THREADS = 4
CERTIFY_SOURCES = (0,)
#: The file name of the evaluator interface in every arm's workspace (recorded inputs keep it).
EVALUATOR_INTERFACE_FILE = "HARNESS.md"
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

Tool rules (a strict audit checks every command; one violation discards the sample):
- Inspect files only with plain reads: `cat FILE`, `sed -n 'A,Bp' FILE`, `grep`/`rg` with a
  literal pattern, `ls`, `wc`, `head`, `tail`. Use workspace-relative paths.
- Do not use shell heredocs, `awk`, `perl`, `python`, `git` (including `git apply` or
  `git diff`), `patch`, `diff`, redirections, pipes into editors, or any command that
  writes, copies or transforms a file. Do not create files. You cannot build or run code.
- Write the unified diff yourself, by hand, from what you read, and return it only in
  `patch`. Hunk headers must count lines exactly.
"""

#: The evaluator interface every arm reads (provider-visible text; its hash is recorded as `harness_sha256`).
EVALUATOR_INTERFACE = """\
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
    files[EVALUATOR_INTERFACE_FILE] = EVALUATOR_INTERFACE
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


#: Ledger rows name the login file's short hash (16 hex digits) `login_source_short_hash` since
#: 2026-10-05 ET (J6); rows of attempts a1-a3 call the same value `login_source_sha256`.
LOGIN_HASH_KEYS = ("login_source_short_hash", "login_source_sha256")


def uncounted(row):
    """True for a recorded call that D7 leaves uncounted (any attempt's row format)."""
    return row.get("counted") is False or row.get("outcome") in {o.value for o in search.UNCOUNTED_CALL_OUTCOMES}


def login_preflight(ledger, ledger_path, kind="codex"):
    """D7 login preflight (2026-10-04): pause, uncounted, before any session is spent.

    Offline only: a missing or malformed login file, a provider home a lab host forbids, or the
    same login file (by short hash) that a recorded session already saw refused, pauses the run.
    Never records values. Returns the login file's short hash for the session row.
    """
    check = provider_login.preflight(kind)
    refused = {c.get(key) for c in ledger["calls"] if c.get("outcome") == "login" for key in LOGIN_HASH_KEYS} - {None}
    if check["state"] == "ok" and check["source_short_hash"] in refused:
        check.update(state="login", reason="this login was already refused by the provider; run `codex login`")
    if check["state"] != "ok":
        ledger.setdefault("preflights", []).append({"at": now(), "outcome": "login", "counted": False, **check})
        save(ledger_path, ledger)
        raise Failure(f"provider paused (login); uncounted; preflight: {check['reason']}")
    return check["source_short_hash"]


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
                           "timeout_s": CALL_SECONDS, "total_seconds": CALL_SECONDS, "max_repairs": 0})
    from swdb import rewrite
    config = rewrite.configuration(config_path)
    if (root / "base-source").exists():
        shutil.rmtree(root / "base-source")     # the driver's own reconstruction scratch
    base = base_source(root / "base-source")
    started = time.monotonic()
    stop = root / f"STOP-{args.attempt}"
    for arm, n in sample_ids():
        if stop.exists():
            raise Failure(f"provider stage stopped by {stop.name}: {stop.read_text().strip()[:300]}")
        folder = runs / f"{arm}-s{n}"
        if (folder / "failure.json").is_file() and uncounted(json.loads((folder / "failure.json").read_text())):
            k = 1
            while folder.with_name(f"{folder.name}.paused{k}").exists():
                k += 1
            folder.rename(folder.with_name(f"{folder.name}.paused{k}"))     # kept; retried after resume
        if (folder / "response.json").is_file() or (folder / "failure.json").is_file():
            continue
        counted = sum(1 for c in ledger["calls"] if c["counted"])
        if counted >= COUNTED_CALL_BUDGET:
            raise Failure("the experiment's counted provider calls are spent")
        if time.monotonic() - started + CALL_SECONDS > args.lane_seconds:
            raise Failure("the next provider call could exceed the lane-hour budget")
        files, input_pins = arm_files(arm, base)
        provider_roles.checked_inputs(files)       # refused inputs never open (or count) a call
        login_hash = None if args.provider_config else login_preflight(ledger, ledger_path)
        folder.mkdir(parents=True, exist_ok=True)
        row = {"arm": arm, "sample": n, "invocation": f"{args.campaign}.{arm}-s{n}", "started": now(),
               "input_pins": input_pins, "visible_files": sorted(files), "login_source_short_hash": login_hash}
        try:
            response, meta = provider_roles.run(ROLE, files, PROMPT.format(campaign=args.campaign, arm=arm, sample=n),
                                                config, folder / "provider")
            row.update(outcome="completed", counted=True)
            save(folder / "response.json", response)
        except Failure as exc:
            # D7 / P1 (2026-10-05 ET): the shared classifier. Usage limit, capacity, guard runtime limit
            # and login (Codex reports a login failure only on stderr: attempt a1, 401 token_invalidated
            # / refresh_token_reused) are uncounted; everything else is a counted failure.
            outcome = provider_adapters.classify(exc, folder / "provider")
            row.update(outcome=outcome.value, counted=outcome not in search.UNCOUNTED_CALL_OUTCOMES, error=str(exc))
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
        if not row["counted"]:
            raise Failure(f"provider paused ({row['outcome']}); uncounted; resume later")
        counted_rows = [c for c in ledger["calls"] if c["counted"]]
        limit = args.stop_after_failures
        if limit and len(counted_rows) == limit and all(c["outcome"] != "completed" for c in counted_rows):
            reasons = "; ".join(str(c.get("error"))[:200] for c in counted_rows)
            stop.write_text(f"{now()} systematic failure: the first {limit} sessions failed; diagnose before "
                            f"continuing. {reasons}\n")
            raise Failure(f"provider stage stopped: the first {limit} sessions failed (see {stop.name})")
    return {"calls": len(ledger["calls"]), "counted": sum(1 for c in ledger["calls"] if c["counted"])}


HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$")


def recount(patch):
    """Rewrite every hunk header's line counts from the hunk body (2026-10-04 ET, a3).

    Equivalent to `git apply --recount`, which the campaign adapters already use: a provider
    that cannot run tools writes the diff by hand and miscounts. Only the two counts change;
    start lines, context and edits stay exactly as written. A line with no prefix inside a
    hunk is a context line that lost its leading space.
    """
    lines = patch.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    out, header, body = [], None, []

    def close():
        if header is None:
            return
        old = sum(1 for line in body if line[:1] in (" ", "-"))
        new = sum(1 for line in body if line[:1] in (" ", "+"))
        out.append(f"@@ -{header[0]},{old} +{header[1]},{new} @@{header[2]}")
        out.extend(body)

    for line in lines:
        match = HUNK.match(line)
        if match:
            close()
            header, body = (match[1], match[2], match[3]), []
        elif header is not None and (line.startswith("--- ") or line.startswith("diff ")):
            close()
            header, body = None, []
            out.append(line)
        elif header is not None:
            body.append(line if line[:1] in (" ", "-", "+", "\\") else " " + line)
        else:
            out.append(line)
    close()
    return "\n".join(out) + "\n"


def scoring_patch(response_patch):
    """The provider's bfs.cc diff (hunk counts recounted) plus the canonical lowering header."""
    patch = recount(response_patch)
    header = LOWERING.read_text()
    lines = header.splitlines()
    addition = ("--- /dev/null\n+++ b/benchmarks/gapbs/src/swdb_dxc_lowering.hpp\n"
                f"@@ -0,0 +1,{len(lines)} @@\n" + "".join("+" + line + "\n" for line in lines))
    return patch + addition


def control_sites(source):
    """Which of the BFS plug-in's negative controls can be built on this source (diagnostic only).

    J5 (2026-10-05 ET): through the kernel plug-in's public interface, not certification internals."""
    plugin, sites = kernels.BFS, {}
    for name in plugin.certification_controls:
        try:
            plugin.certification_control(plugin.certification_instrument(source), name)
            sites[name] = True
        except Failure:
            sites[name] = False
    return sites


def planned_controls():
    """How many negative controls certification runs for one sample (P6, 2026-10-05 ET).

    Derived from the BFS plug-in's controls, plus the legality controls when the contract has
    knob or schedule clauses (ticket 68), once per tile size. An aborted certification reports
    this total; the driver once hard-coded 16 (certify 1.0-1.1, before the legality controls)."""
    import yaml
    contract = yaml.safe_load((REPOSITORY / CONTRACT_FILE).read_text())
    names = len(kernels.BFS.certification_controls)
    if certification_legality.applies(contract):
        names += len(certification_legality.CONTROLS)
    return names * len(TILE_SIZES)


class _SiteControls:
    """Diagnostic only: the BFS plug-in restricted to the controls whose mutation site exists
    in this candidate. Never a certification and never a record."""

    def __init__(self, plugin, names):
        self._plugin = plugin
        self.certification_controls = {k: v for k, v in plugin.certification_controls.items() if k in names}

    def __getattr__(self, name):
        return getattr(self._plugin, name)


def diagnostic(patch_path, folder, library):
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
    matrix, controls = certification.certify_bfs(tree, library, folder, TILE_SIZES, CERTIFY_THREADS,
                                                 CERTIFY_SOURCES, plugin=_SiteControls(kernels.BFS, present))
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
    result = {"sample": name, "patch_sha256": artifacts.file_hash(patch_path), "response_patch_sha256": sha(response_patch),
              "patch_normalization": "hunk counts recounted (git apply --recount equivalent)", "started": now()}
    touched = sorted({line[6:].strip() for line in response_patch.splitlines() if line.startswith("+++ b/")})
    result["provider_patch_files"] = touched
    from swdb.store import Store
    previous = dict(workflow.CREATION_TAGS)
    workflow.CREATION_TAGS.clear()
    workflow.CREATION_TAGS.update(mode="extensa", campaign=args.campaign)
    try:
        record = certification.certify(Store(store_dir), CONTRACT, runs_dir=folder / "certify", snapshot=SNAPSHOT,
                                       patch=patch_path, tile_sizes=TILE_SIZES, threads=CERTIFY_THREADS,
                                       sources=CERTIFY_SOURCES)
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
                      controls_rejected=0, controls_total=planned_controls())
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
            time.sleep(SCORE_POLL_SECONDS)
    return {"unscored": sorted(pending)}


def reference_stage(args):
    """Positive control of the evaluator interface: ticket 20's bfs.cc diff through the same scoring path."""
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
                         "harness_sha256": sha(EVALUATOR_INTERFACE), "prompt_sha256": sha(PROMPT)},
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
    parser.add_argument("--stop-after-failures", type=int, default=STOP_AFTER_FAILURES,
                        help="stop when the attempt's first N counted sessions all fail (0 disables)")
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

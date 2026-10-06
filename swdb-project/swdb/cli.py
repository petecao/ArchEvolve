"""Command line: `swdb <command>`. Exit 0 = success, 1 = the check or command failed,
2 = usage error. Errors go to stderr; results (YAML or JSON) go to stdout.

Updated: 2026-10-06 ET (ticket 03): validate accepts a standalone slide-based crosswalk.
2026-10-05 ET (code review): the `campaign` and library-operation commands register here
directly; `promote` states who performed a review and `correct-review` corrects an earlier
attribution (spec review C1)."""

import argparse
import json
import sys
from pathlib import Path

from swdb import paths, yamlio


class Failure(Exception):
    """A command failed for a reason the user can fix; printed to stderr, exit 1."""


class UsageError(Exception):
    """Bad arguments or a missing folder; printed to stderr, exit 2."""


def main(argv=None):
    parser = argparse.ArgumentParser(prog="swdb", description="ArchEvolve Software Database tool.")
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, help_text, records=True, db=False, fmt=False):
        sub = commands.add_parser(name, help=help_text, description=help_text)
        if records:
            sub.add_argument("--records", type=Path, default=paths.RECORDS,
                             help="records folder (default: the repo's records/)")
        if db:
            sub.add_argument("--db", type=Path, default=None,
                             help="SQLite file (default: build/swdb.sqlite beside a folder named records, "
                                  "else build/swdb-<folder name>.sqlite beside the folder)")
        if fmt:
            sub.add_argument("--format", choices=["yaml", "json"], default="yaml", help="output format (default yaml)")
        return sub

    sub = command("validate", "check records and typed library shapes, pins and clauses")
    sub.add_argument("--library", type=Path)
    sub.add_argument("--crosswalk", type=Path, help="also validate a slide-based main-database crosswalk")

    sub = command("promote", "record a review of one certified library entry or Extensa candidate artifact",
                  db=True, fmt=True)
    sub.add_argument("id")
    sub.add_argument("--reviewer", default="Yan-Ru Jhou")
    sub.add_argument("--library", type=Path)
    sub.add_argument("--protocol", help="Extensa candidate: the current team protocol to derive the re-evaluation from")
    sub.add_argument("--workload-class", help="Extensa candidate: the artifact's workload class (workload family)")
    sub.add_argument("--output", type=Path, help="Extensa candidate: folder for the re-evaluation requests")
    _attribution_options(sub)

    sub = command("correct-review", "record who actually performed an earlier review (the review stays unchanged)",
                  fmt=True)
    sub.add_argument("id", help="the review record to correct")
    sub.add_argument("--recorded-by", required=True, help="who records this correction")
    sub.add_argument("--recorder-kind", choices=["agent_run", "human_report"], default="agent_run",
                     help="provenance of the correction itself (default agent_run)")
    sub.add_argument("--reason", required=True, help="why the earlier attribution was wrong")
    _attribution_options(sub)

    command("build", "regenerate the SQLite database from the records, from scratch", db=True)

    sub = command("sql", "run one SQL query against the built database", db=True, fmt=True)
    sub.add_argument("query")

    sub = command("find", "find access patterns by address shape, update kind, and semantic values", db=True, fmt=True)
    sub.add_argument("--shape", action="append", default=[], help="an address shape some step must have (repeatable)")
    sub.add_argument("--update", help="the pattern's update kind")
    sub.add_argument("--semantic", action="append", default=[], metavar="FIELD=VALUE",
                     help="a semantic value the pattern must have, e.g. loop_carried_dependencies=false (repeatable)")
    sub.add_argument("--kernel", help="only this kernel's implementations")
    sub.add_argument("--strategy", help="an access-pattern strategy: report where it is legal or undetermined "
                                        "(illegal patterns are left out)")

    sub = command("strategies", "list optimization strategies with their legality for one target", db=True, fmt=True)
    which = sub.add_mutually_exclusive_group(required=True)
    which.add_argument("--pattern", metavar="IMPL/PATTERN", help="access-pattern strategies for one access pattern")
    which.add_argument("--loop", metavar="IMPL/LOOP",
                       help="loop strategies for one loop (every access pattern in it and its child loops must pass)")
    which.add_argument("--input", metavar="IMPL", help="input strategies for one implementation's input")

    sub = command("implementations", "list a kernel's implementations whose semantics meet the requirements",
                  db=True, fmt=True)
    sub.add_argument("kernel")
    sub.add_argument("--require", action="append", default=[], metavar="FIELD=VALUE",
                     help="every access pattern must have this known semantic value (repeatable)")
    sub.add_argument("--applies", metavar="STRATEGY",
                     help="only implementations that apply this strategy, with their baseline's profiles")

    sub = command("compare", "compare an explicit baseline and exact compatible profile pair", db=True, fmt=True)
    sub.add_argument("implementation")
    sub.add_argument("--baseline", help="explicit comparison baseline (or the implementation's recorded selection)")
    sub.add_argument("--profile", required=True)
    sub.add_argument("--baseline-profile", required=True)
    sub.add_argument("--protocol", required=True)

    sub = command("view", "print the workload view (HW Ensemble format) of one implementation on one input and machine",
                  fmt=True)
    sub.add_argument("implementation")
    sub.add_argument("input")
    sub.add_argument("machine")
    sub.add_argument("--profile", help="profile ID to use (default: the newest complete one for the triple)")

    sub = command("add", "validate a new record, write it to its canonical place, and rebuild the database", db=True)
    sub.add_argument("file", type=Path)
    sub.add_argument("--agent", action="store_true",
                     help="the record comes from an agent: mark it draft with an agent_run provenance entry")
    sub.add_argument("--agent-name", default="agent", help="who the agent is (goes into the provenance entry)")

    sub = command("capture-machine", "print a machine record captured read-only from a host", records=False)
    sub.add_argument("--id", required=True, help="the machine record ID")
    where = sub.add_mutually_exclusive_group()
    where.add_argument("--ssh", metavar="HOST", help="capture over ssh instead of locally")
    where.add_argument("--from-file", type=Path, help="parse a saved capture instead of running one")

    sub = command("profile", "build and profile an implementation on an input and machine; write a profile record",
                  db=True)
    sub.add_argument("implementation")
    sub.add_argument("input")
    sub.add_argument("machine")
    sub.add_argument("--runs-dir", type=Path, required=True,
                     help="folder outside git for raw output; a new run folder is made inside it")
    sub.add_argument("--threads", default="1,2,4,8,16", help="thread counts for the timing sweep (default 1,2,4,8,16)")
    sub.add_argument("--trials", type=int, default=5, help="trials per thread count (default 5)")
    sub.add_argument("--timeout", type=float, default=1800, help="timeout in seconds for each timing process")
    sub.add_argument("--correctness-timeout", type=float, default=None,
                     help="timeout for the correctness check (default: --timeout)")
    sub.add_argument("--allow-unverified", action="store_true",
                     help="if the correctness check times out (without printing FAIL), record an incomplete "
                          "profile instead of stopping")
    sub.add_argument("--cachegrind", choices=["auto", "yes", "no"], default="auto",
                     help="run cachegrind single-threaded (auto: only if valgrind is installed)")
    sub.add_argument("--cachegrind-timeout", type=float, default=3600, help="cachegrind timeout in seconds")
    sub.add_argument("--features", choices=["auto", "yes", "no"], default="auto",
                     help="run the index-stream feature extractor (auto: if the implementation names an index stream)")
    sub.add_argument("--features-timeout", type=float, default=1800)
    sub.add_argument("--cxx", default=None, help="C++ compiler (default: the implementation's build.compiler)")
    sub.add_argument("--binding", default=None,
                     help="how threads are bound, as recorded (default: detected from numactl --show)")
    sub.add_argument("--lane", default=None, help="socket lane lease the run is inside (e.g. mbit10-evaluation-node1); on a machine "
                          "that requires lanes it must match the verified lane")
    sub.add_argument("--update-input", choices=["yes", "no"], default="yes",
                     help="write measured edge counts back into the input record (default yes)")
    sub.add_argument("--runs-note", default=None, help="why this runs folder was chosen (recorded in the profile)")
    sub.add_argument("--agent", action="store_true", help="the run is made by an agent (provenance agent_run)")

    sub = command("recompute-cachegrind", "re-read profiles' raw cachegrind output with the current parser "
                  "(on the host that holds it) and update their simulated metrics", db=True)
    sub.add_argument("profile", nargs="+")
    sub.add_argument("--reason", required=True, help="why the profiles are re-read (goes into their provenance)")

    sub = command("source-snapshot", "retain an exact buildable source snapshot and evaluator protections", db=True, fmt=True)
    sub.add_argument("implementation")
    sub.add_argument("--runs-dir", type=Path, required=True)
    sub.add_argument("--id")

    sub = command("fixture-package", "create a labeled contract fixture package without execution evidence", db=True, fmt=True)
    sub.add_argument("snapshot")
    sub.add_argument("--id", required=True)

    sub = command("baseline-candidate", "materialize unchanged starting source for baseline evaluation", db=True, fmt=True)
    sub.add_argument("snapshot")
    sub.add_argument("--id", required=True)
    sub.add_argument("--runs-dir", type=Path, required=True)

    sub = command("submit", "retain a rewrite proposal and produce a candidate or explicit rejection", db=True, fmt=True)
    sub.add_argument("file", type=Path)
    sub.add_argument("--runs-dir", type=Path, required=True)
    sub.add_argument("--provider-config", type=Path)

    sub = command("repair", "repair a build/correctness failure or retry an unavailable initial provider", db=True, fmt=True)
    sub.add_argument("evaluation")
    sub.add_argument("--runs-dir", type=Path, required=True)
    sub.add_argument("--provider-config", type=Path, required=True)

    for name in ("dx100-build", "dx100-execute", "dx100-compile"):
        sub = command(name, "run a bounded DX100 backend stage with durable evidence", db=True, fmt=True)
        sub.add_argument("file", type=Path)
        sub.add_argument("--runs-dir", type=Path, required=True)
        sub.add_argument("--lane", type=int, required=True)

    sub = command("dx100-profile", "collect sealed simulated BFS region and memory observations", db=True, fmt=True)
    sub.add_argument("file", type=Path)
    sub.add_argument("--runs-dir", type=Path, required=True)

    sub = command("capabilities", "query source-backed operations and executable readiness of a target", db=True, fmt=True)
    sub.add_argument("target")

    sub = command("evaluate", "build and evaluate an identified native BFS candidate", db=True, fmt=True)
    sub.add_argument("file", type=Path)
    sub.add_argument("--runs-dir", type=Path, required=True)
    sub.add_argument("--lane")

    sub = command("evaluate-pair", "collect a prospective interleaved native A/A or A/B pair", db=True, fmt=True)
    sub.add_argument("file", type=Path)
    sub.add_argument("--runs-dir", type=Path, required=True)
    sub.add_argument("--lane")

    sub = command("bfs-profile", "collect automatic native BFS region and memory observations", db=True, fmt=True)
    sub.add_argument("file", type=Path)
    sub.add_argument("--runs-dir", type=Path, required=True)
    sub.add_argument("--lane")

    sub = command("bfs-hotspots", "retrieve attributable BFS function or loop observations", db=True, fmt=True)
    sub.add_argument("id")
    sub.add_argument("--kind", choices=["function", "loop"], required=True)
    sub.add_argument("--evaluation")

    sub = command("profile-package", "assemble an exact-context BFS profile package", db=True, fmt=True)
    sub.add_argument("file", type=Path)

    sub = command("profile-strategies", "query strategy relevance and legality for a profile package", db=True, fmt=True)
    sub.add_argument("package")
    sub.add_argument("--region")

    sub = command("strategy-regions", "query profiled regions relevant to a strategy", db=True, fmt=True)
    sub.add_argument("strategy")
    sub.add_argument("--package")

    sub = command("bfs-coverage", "reconstruct the fixed BFS acceptance matrix and retained history", db=True, fmt=True)
    sub.add_argument("file", type=Path)

    sub = command("handoff-message", "render a versioned D06 handoff message (profile package, rewrite proposal, "
                  "or evaluation result) from an existing record", db=True, fmt=True)
    sub.add_argument("message", choices=["profile_package", "rewrite_proposal", "evaluation_result"])
    sub.add_argument("id")

    for name, help_text in (
        ("register-workload", "register graph representations after checking canonical adjacency identity"),
        ("freeze-protocol", "freeze an immutable workload and comparison protocol"),
        ("compare-evaluations", "compare explicit evaluation evidence under a frozen protocol"),
        ("aggregate-evaluations", "combine completed simulator trials with exact protocol coverage"),
    ):
        sub = command(name, help_text, db=True, fmt=True)
        sub.add_argument("file", type=Path)

    sub = command("get", "retrieve an authoritative record through the generated query index", db=True, fmt=True)
    sub.add_argument("id")
    sub.add_argument("--chain", action="store_true", help="include linked proposal, candidate, source, and package records")

    from swdb import annotation, campaign, certification, extensa_boundary, library_operations, retention
    extensa_boundary.register_cli(commands, paths)
    library_operations.register_cli(commands, paths)
    campaign.register_cli(commands, paths)
    annotation.register_cli(commands)
    certification.register_cli(commands)
    retention.register_cli(commands)

    from swdb import analytic
    analytic.register_cli(commands)
    from swdb import cpu_calibration
    cpu_calibration.register_cli(commands)
    from swdb import cpu_service_calibration
    cpu_service_calibration.register_cli(commands)
    from swdb import cpu_error_band
    cpu_error_band.register_cli(commands)
    from swdb import cpu_native_validation
    cpu_native_validation.register_cli(commands)

    from swdb import archevolve
    archevolve.register_cli(commands)
    args = parser.parse_args(argv)
    try:
        with archevolve.command_mode(args):
            archevolve.guard_cli(args)
            return _dispatch(args)
    except UsageError as exc:
        print(f"swdb: {exc}", file=sys.stderr)
        return 2
    except Failure as exc:
        print(f"swdb {args.command}: {exc}", file=sys.stderr)
        return 1


def _attribution_options(sub):
    """Who performed a review (spec review C1, 2026-10-05 ET); without them, a human review."""
    sub.add_argument("--performed-by", choices=["human", "agent"], default=None,
                     help="who did the reviewing (default human)")
    sub.add_argument("--delegated-by", help="an agent review: the maintainer who delegated it")
    sub.add_argument("--delegation", help="an agent review: what was delegated and when")
    sub.add_argument("--review-document", help="repository path of the written review")


def _dispatch(args):
    records = getattr(args, "records", None)
    if records is not None and not records.is_dir():
        raise UsageError(f"records folder not found: {records}")
    if hasattr(args, "analytic_handler"):
        _emit(args.analytic_handler(args), args.format)
        return 0
    if hasattr(args, "cpu_calibration_handler"):
        _emit(args.cpu_calibration_handler(args), args.format)
        return 0
    if hasattr(args, "cpu_error_band_handler"):
        _emit(args.cpu_error_band_handler(args), args.format)
        return 0
    if hasattr(args, "cpu_native_validation_handler"):
        _emit(args.cpu_native_validation_handler(args), args.format)
        return 0
    if hasattr(args, "cpu_service_calibration_handler"):
        _emit(args.cpu_service_calibration_handler(args), args.format)
        return 0
    if hasattr(args, "_annotation_handler"):
        _emit(args._annotation_handler(args), args.format)
        return 0
    if hasattr(args, "retention_handler"):
        _emit(args.retention_handler(args), args.format)
        return 0
    if hasattr(args, "extensa_handler"):
        _emit(args.extensa_handler(args), args.format)
        return 0
    if args.command == "certify":
        from swdb.certification import run_cli
        return run_cli(args)
    if args.command == "validate":
        return _validate(records, args.library, args.crosswalk)
    if args.command == "promote":
        from swdb.library import promote
        from swdb.store import Store
        if args.protocol or args.workload_class or args.output or Store(records).get(args.id, "candidate"):
            from swdb.extensa_boundary import promote_candidate
            _emit(promote_candidate(args), args.format)
            return 0
        _emit(promote(args), args.format)
        return 0
    if args.command == "correct-review":
        from swdb.library import correct_review
        _emit(correct_review(args), args.format)
        return 0
    if args.command == "capture-machine":
        return _capture(args)

    if args.command == "capabilities":
        from swdb import capabilities

        return _emit(capabilities.query(args), args.format)

    if args.command in {"dx100-build", "dx100-execute", "dx100-compile"}:
        from swdb import dx100

        method = "compile_candidate" if args.command == "dx100-compile" else args.command.removeprefix("dx100-")
        result = getattr(dx100, method)(args)
        _emit(result, args.format)
        return 0 if result.get("outcome", {}).get("state") == "complete" else 1

    if args.command == "dx100-profile":
        from swdb import dx100_profile

        result = dx100_profile.collect(args)
        _emit(result, args.format)
        return 1 if result.get("outcome", {}).get("state") in {"failed", "rejected", "unresolved"} else 0

    if args.command == "evaluate":
        from swdb import bfs_native

        result = bfs_native.run(args)
        _emit(result, args.format)
        return 0 if result.get("outcome", {}).get("state") == "complete" else 1

    if args.command == "evaluate-pair":
        from swdb import bfs_native_pair

        result = bfs_native_pair.run(args)
        _emit(result, args.format)
        return 0 if result.get("outcome", {}).get("state") == "complete" else 1

    if args.command in {"register-workload", "freeze-protocol", "compare-evaluations", "aggregate-evaluations"}:
        from swdb import bfs_protocol

        result = getattr(bfs_protocol, args.command.replace("-", "_"))(args)
        _emit(result, args.format)
        if args.command == "aggregate-evaluations":
            return 0 if result.get("outcome", {}).get("state") == "complete" else 1
        return 1 if result.get("decision", {}).get("state") == "rejected" else 0

    if args.command in {"bfs-profile", "bfs-hotspots"}:
        from swdb import bfs_profiling

        result = bfs_profiling.run(args) if args.command == "bfs-profile" else bfs_profiling.query(args)
        _emit(result, args.format)
        return 0 if args.command == "bfs-hotspots" or result.get("outcome", {}).get("state") in {"complete", "partial"} else 1

    if args.command in {"profile-package", "profile-strategies", "strategy-regions"}:
        from swdb import profile_package

        method = {"profile-package": "assemble", "profile-strategies": "strategies", "strategy-regions": "regions"}[args.command]
        result = getattr(profile_package, method)(args)
        _emit(result, args.format)
        return 1 if result.get("outcome", {}).get("state") in {"failed", "rejected", "unresolved"} else 0

    if args.command == "bfs-coverage":
        from swdb import bfs_coverage

        _emit(bfs_coverage.report(args), args.format)
        return 0

    if args.command == "handoff-message":
        from swdb import handoff

        _emit(handoff.message(args), args.format)
        return 0

    workflow_commands = {"source-snapshot": "snapshot", "fixture-package": "fixture_package",
                         "baseline-candidate": "baseline_candidate",
                         "submit": "submit", "repair": "repair", "get": "get_record"}
    if args.command in workflow_commands:
        from swdb import workflow

        result = getattr(workflow, workflow_commands[args.command])(args)
        _emit(result, args.format)
        return 1 if args.command in {"submit", "repair"} and result.get("outcome", {}).get("state") in {"rejected", "unresolved", "failed", "provider_unavailable"} else 0

    from swdb import db

    db_path = args.db if getattr(args, "db", None) else db.default_path(records)
    if args.command == "build":
        _require_valid(records)
        info = db.build(records, db_path)
        print(f"OK: built {db_path} from {info['records']} record(s) in {info['seconds']:.2f} s")
        return 0
    if args.command == "sql":
        _ensure_db(records, db_path)
        return _emit(db.sql(db_path, args.query), args.format)
    if args.command == "find":
        _ensure_db(records, db_path)
        found = db.find(db_path, shapes=args.shape, update=args.update,
                        semantics=[_pair(text) for text in args.semantic], kernel=args.kernel,
                        strategy=args.strategy)
        return _emit(found, args.format)
    if args.command == "strategies":
        _ensure_db(records, db_path)
        if args.pattern:
            found = db.strategies_for_pattern(db_path, args.pattern)
        elif args.loop:
            found = db.strategies_for_loop(db_path, args.loop)
        else:
            found = db.strategies_for_input(db_path, args.input)
        return _emit(found, args.format)
    if args.command == "implementations":
        _ensure_db(records, db_path)
        requirements = [_pair(text) for text in args.require]
        if args.applies:
            found = db.applying(db_path, args.kernel, args.applies, requirements)
        else:
            found = db.implementations(db_path, args.kernel, requirements)
        if found is None:
            raise Failure(f"kernel {args.kernel!r} does not exist")
        return _emit(found, args.format)
    if args.command == "compare":
        _ensure_db(records, db_path)
        return _emit(db.compare(db_path, args.implementation, args.baseline, args.profile,
                                args.baseline_profile, args.protocol), args.format)
    if args.command == "view":
        from swdb import view

        _require_valid(records)
        return _emit(view.workload_view(records, args.implementation, args.input, args.machine, args.profile),
                     args.format)
    if args.command == "add":
        from swdb import writer, workflow

        written = writer.add(records, args.file, agent=args.agent, agent_name=args.agent_name,
                             creation_tags=workflow.CREATION_TAGS)
        info = db.build(records, db_path)
        print(f"OK: wrote {written}; rebuilt {db_path} ({info['records']} records)")
        return 0
    if args.command == "profile":
        from swdb import profile

        written = profile.run(args, records)
        info = db.build(records, db_path)
        print(f"OK: wrote {written}; rebuilt {db_path} ({info['records']} records)")
        return 0
    if args.command == "recompute-cachegrind":
        from swdb import profile

        for profile_id in args.profile:
            print(profile.recompute_cachegrind(records, profile_id, args.reason))
        db.build(records, db_path)
        return 0
    raise UsageError(f"unknown command {args.command}")


def _validate(records_dir, library_root=None, crosswalk=None):
    from swdb.validate import validate_records

    result = validate_records(records_dir, library_root=library_root)
    if crosswalk is not None:
        from swdb.crosswalk import validate_crosswalk
        result.problems.extend(validate_crosswalk(crosswalk))
    for problem in result.problems:
        print(problem, file=sys.stderr)
    if result.problems:
        files = len({problem.file for problem in result.problems})
        print(
            f"FAILED: {len(result.problems)} error(s) in {files} file(s); {result.count} record(s) checked",
            file=sys.stderr,
        )
        return 1
    suffix = "; crosswalk valid" if crosswalk is not None else ""
    print(f"OK: {result.count} record(s) valid{suffix}")
    return 0


def _require_valid(records_dir):
    from swdb.validate import validate_records

    result = validate_records(records_dir)
    if result.problems:
        for problem in result.problems:
            print(problem, file=sys.stderr)
        raise Failure(f"{len(result.problems)} validation error(s); run swdb validate")
    return result.store


def _ensure_db(records_dir, db_path):
    from swdb import db

    if db.is_stale(records_dir, db_path):
        _require_valid(records_dir)
        db.build(records_dir, db_path)
        print(f"swdb: rebuilt {db_path} (it was missing, older than the records, or built by another swdb version)",
              file=sys.stderr)


def _capture(args):
    from swdb import machine

    try:
        if args.from_file:
            raw, command = args.from_file.read_text(), f"swdb capture-machine --from-file {args.from_file.name}"
        else:
            raw, command = machine.run_capture(args.ssh)
        date = machine.sections(raw).get("date", "").strip()
        if not date:
            raise machine.CaptureError("capture has no date section")
        record = machine.parse(raw, args.id, command, date)
    except (machine.CaptureError, OSError) as exc:
        raise Failure(str(exc)) from None
    sys.stdout.write(yamlio.dumps(record))
    return 0


def _pair(text):
    if "=" not in text:
        raise UsageError(f"expected FIELD=VALUE, got {text!r}")
    name, raw = text.split("=", 1)
    return name.strip(), parse_value(raw.strip())


def parse_value(raw):
    lowered = raw.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "none", "unknown"}:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _emit(data, fmt):
    if fmt == "json":
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        sys.stdout.write(yamlio.dumps(data))
    return 0

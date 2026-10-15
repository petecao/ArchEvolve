"""The logic library: versioned, hash-pinned ACSL files, their lemma proofs and their `\\false` check.

Created: 2026-10-14 ET (Probata proof of concept ticket 26). Design: formal-verification map 16 items
2, 9 and 12; 24 item 4; 27 item 3; spec "Modules" (logic library), "Records and levels", "Proven once vs
per candidate" (the "with the method" row). Format: docs/reference/format-v0.4-logic-library.md.

- Files: shared files `library/logic/<name>.acsl` (ID `logic.<name>`) and at most one file per library
  entry, `<entry file>.acsl` beside the entry's YAML (ID `logic.<entry ID>`; only that entry's formal
  halves may use it). The first line of every file is `// version: <dotted numbers>`. `swdb validate`
  checks the version line and the allowed-ACSL rules (`swdb.acsl_subset`, `swdb.formal_frame`).
- Pins: a proof record whose formal halves use logic files pins each one as `{id, version, sha256}` in
  `pins.logic`. The level rule (`swdb.level_rule`) stops counting the record when a file's hash changes,
  and makes it depend on a counting proof of the file's lemmas.
- `swdb prove-logic` runs Frama-C/WP (`-wp-model +real`, fresh session, the method version's lineup)
  under the machine-wide verifier lock and the RSS watchdog, and writes one proof record:
  - `--lemmas <id>`: every lemma of the file, with its saved proof hints and replayed scripts
    (`proofs/<name>/` for a shared file, `<entry file>.proofs/` for an entry's own file). Subject: method
    part `logic_lemmas` (shared) or contract-proof part `contract_logic_lemmas` (an entry's own file).
  - `--false-check <id>`: WP must not prove `\\false` from the file alone. One generated lemma mentions
    every definition (wrapped in uninterpreted functions, so each definitional axiom enters the context)
    after every lemma of the file. Proven `\\false`: the record is refuted (a failed part that voids the
    version, `voids: logic`) and the version is refused (exit 1). Not proven: the check passes; this is
    evidence, not a consistency proof (map 16 item 9).
  - `--program <C file> --uses <id>...`: a fixture or calibration program (subject `calibration_program`)
    proven against its own ACSL contract with the logic files placed before it. Library lemmas are
    excluded (`-wp-prop=-@lemma`): they are proven once, with the method.
"""

import os
import re
import shlex
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from swdb import acsl_subset, artifacts, paths
from swdb.cli import Failure

SHARED = "logic"
PROOFS = "proofs"
VERSION_LINE = re.compile(r"// version: (\d+(?:\.\d+)*)[ \t]*(?:\n|\Z)")
LEMMA_PARTS = {"shared": "logic_lemmas", "own": "contract_logic_lemmas"}
FALSE_PARTS = {"shared": "logic_false_check", "own": "contract_logic_false_check"}
FALSE_GOAL = "SWDB_FALSE_CHECK"
FALSE_SECONDS = 10             # per solver: Z3 ignores -wp-memlimit on macOS (ticket 08), so the check stays short
PROVERS = ("alt-ergo", "z3", "cvc5")
BOUNDS = {"threads": "unbounded"}   # a logic fact holds for every input; it never caps a level


@dataclass(frozen=True)
class LogicFile:
    id: str
    path: Path
    owner: str = None          # the library entry that owns the file (None: a shared file)
    home: Path = None          # --file: where the file lives in the library (its proofs folder is there)

    @property
    def text(self):
        return self.path.read_text()

    @property
    def sha256(self):
        return artifacts.file_hash(self.path)

    @property
    def version(self):
        return version_of(self.text)

    @property
    def proofs(self):
        """The folder of the file's proof hints (hints.acsl) and saved WP scripts (script/)."""
        place = self.home or self.path
        if self.owner is None:
            return place.parent / PROOFS / place.stem
        return place.with_name(f"{place.stem}.proofs")

    @property
    def scope(self):
        return "shared" if self.owner is None else "own"

    def pin(self):
        return {"id": self.id, "version": self.version, "sha256": self.sha256}


def version_of(text):
    """The file's version (its first line, `// version: 1.0`), or None."""
    match = VERSION_LINE.match(text)
    return match.group(1) if match else None


def files(root, library=None):
    """{ID: LogicFile}: the shared files of <root>/logic/ and, given the Library, each entry's own file."""
    found = {f"logic.{path.stem}": LogicFile(f"logic.{path.stem}", path)
             for path in sorted((Path(root) / SHARED).glob("*.acsl"))}
    if library is not None:
        for entry_id, path in sorted(library.files.items()):
            own = Path(path).with_suffix(".acsl")
            if own.is_file():
                found[f"logic.{entry_id}"] = LogicFile(f"logic.{entry_id}", own, owner=entry_id)
    return found


def used(entry, placement="per_candidate"):
    """The logic-file IDs the entry's formal halves with this placement list (`acsl.uses`), in order."""
    uses = []
    for clause in (entry or {}).get("clauses") or []:
        if isinstance(clause, dict) and isinstance(clause.get("acsl"), dict) \
                and (placement is None or clause.get("proof_placement") == placement):
            uses += [u for u in clause["acsl"].get("uses") or [] if isinstance(u, str) and u not in uses]
    return uses


def pins(library, entry):
    """`pins.logic` of a proof of `entry`'s per-candidate formal halves: [{id, version, sha256}] (may be empty)."""
    found = files(library.root, library)
    return [found[u].pin() for u in used(entry) if u in found]


def lemma_names(text):
    """The lemma names a logic file states, in order."""
    try:
        toks = acsl_subset.tokens(text)
    except acsl_subset.AcslSyntaxError:
        return []
    return [toks[i + 1].text for i in range(len(toks) - 1) if toks[i].text == "lemma" and toks[i + 1].kind == "id"]


# --- swdb prove-logic ------------------------------------------------------------------------------------

def register_cli(commands):
    sub = commands.add_parser(
        "prove-logic", help="prove a logic file's lemmas, run its \\false check, or prove a fixture program with it",
        description="run Frama-C/WP on a logic-library file (its lemmas, or the \\false check) or on a fixture or "
                    "calibration C program that uses logic files, and write one proof record (never changed). Every "
                    "run takes the machine-wide verifier lock and the RSS watchdog.")
    sub.add_argument("--records", type=Path, default=paths.RECORDS)
    sub.add_argument("--runs-dir", type=Path, required=True, help="runs folder outside the repo for logs and reports")
    what = sub.add_mutually_exclusive_group(required=True)
    what.add_argument("--lemmas", metavar="LOGIC_ID", help="prove every lemma of this logic file")
    what.add_argument("--false-check", metavar="LOGIC_ID", help="check that WP cannot prove \\false from this file")
    what.add_argument("--program", type=Path, metavar="C_FILE", help="prove a fixture or calibration C program")
    sub.add_argument("--file", type=Path, help="--lemmas/--false-check: check this version of the file instead of "
                                                "the library's (a proposed version, before it enters the library)")
    sub.add_argument("--uses", action="append", default=[], metavar="LOGIC_ID",
                     help="--program: a logic file placed before the program (repeatable, in order)")
    sub.add_argument("--define", action="append", default=[], help="--program: a preprocessor constant NAME[=VALUE]")
    sub.add_argument("--program-id", help="--program: the subject ID (default: the file name)")
    sub.add_argument("--timeout", type=int, help="seconds per solver (default: the method version's "
                                                 f"wp_seconds_per_solver; {FALSE_SECONDS} for the \\false check)")
    sub.add_argument("--generate-scripts", action="store_true",
                     help="--lemmas: run the hint strategies (prover tip) and save the generated scripts into the "
                          "file's proofs folder; writes no record (a maintainer step, followed by a replay run)")
    sub.add_argument("--skip-subset-check", action="store_true",
                     help="negative controls only: run even when the file breaks the allowed-ACSL rules "
                          "(the record says so)")
    sub.add_argument("--id", help="proof record ID (default: a new one)")
    sub.add_argument("--method-version", metavar="ID",
                     help="run under this method version, draft or frozen (default: the current frozen one; fix-21)")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=prove_logic)


def prove_logic(args):
    from swdb import proof
    from swdb.cli import _require_valid
    from swdb.library import Library, default_root
    store = _require_valid(args.records)
    library = Library(default_root(args.records))
    method = proof._current_method(args.records, getattr(args, "method_version", None))
    runs = proof._outside_repo(args.runs_dir)
    found = files(library.root, library)
    if args.program is not None:
        return _program(args, store, library, method, runs, found)
    ident = args.lemmas or args.false_check
    logic = found.get(ident)
    if args.file is not None:          # a version that is not (yet) the library's file: checked before it enters
        if not args.file.is_file():
            raise Failure(f"no file {args.file}")
        if not re.fullmatch(r"logic\.[a-z0-9][a-z0-9._-]*", ident):
            raise Failure(f"{ident!r} is not a logic-file ID (logic.<name>)")
        home = logic.path if logic else Path(library.root) / SHARED / f"{ident[len('logic.'):]}.acsl"
        logic = LogicFile(ident, args.file.resolve(), owner=logic.owner if logic else None, home=home)
    if logic is None:
        raise Failure(f"no logic file {ident!r} (library/logic/<name>.acsl or <entry file>.acsl)")
    if logic.version is None:
        raise Failure(f"{logic.path} has no version line (`// version: 1.0` first)")
    problems = acsl_subset.LogicLibrary({ident: logic.text}).problems[ident]
    if problems and not args.skip_subset_check:
        raise Failure(f"{ident} breaks the allowed-ACSL rules ({problems[0][1]}); nothing proven")
    if args.lemmas:
        return _lemmas(args, store, library, method, runs, logic, bool(problems))
    return _false_check(args, store, library, method, runs, logic, bool(problems))


def _lemmas(args, store, library, method, runs, logic, bypassed):
    names = lemma_names(logic.text)
    if not names:
        raise Failure(f"{logic.id} states no lemma; nothing to prove")
    hints = logic.proofs / "hints.acsl"
    source = f"/*@\n{logic.text}\n*/\n" + (hints.read_text() if hints.is_file() else "")
    scripts = sorted((logic.proofs / "script").glob("*.json")) if (logic.proofs / "script").is_dir() else []
    if args.generate_scripts:
        result = _run_wp(args, store, library, method, runs, source, flags=[], provers="tip", scripts=[],
                         seconds=args.timeout, label=f"generate scripts {logic.id}")
        made = sorted((result["session"] / "script").glob("*.json"))
        target = logic.proofs / "script"
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        for path in made:
            shutil.copyfile(path, target / path.name)
        shutil.rmtree(result["scratch"], ignore_errors=True)
        return {"generated": [p.name for p in made], "folder": str(target)}
    result = _run_wp(args, store, library, method, runs, source, flags=[], provers="script," + ",".join(PROVERS),
                     scripts=scripts, seconds=args.timeout, label=f"lemmas {logic.id}")
    outcome = result["outcome"]
    goals = {g["goal"]: g for g in outcome["goals"]}
    missing = [n for n in names if not any(goal.endswith(f"lemma_{n}") for goal in goals)]
    verdict, failure_class, why = outcome["verdict"], outcome["failure_class"], outcome["why"]
    if verdict == "proven" and missing:
        verdict, failure_class, why = "not_proven", "unknown", f"no WP goal for lemma(s) {', '.join(missing)}"
    subject = _subject(logic, LEMMA_PARTS)
    record = _record(args, store, library, method, result, subject, verdict, failure_class,
                     pins_logic=[logic.pin()], contract=logic.owner, why=why, bypassed=bypassed,
                     settings={"scripts": [p.name for p in scripts], "hints": hints.is_file()})
    return _write(args, record)


def _false_check(args, store, library, method, runs, logic, bypassed):
    source = f"/*@\n{logic.text}\n*/\n" + false_check_lemma(logic.text)
    seconds = args.timeout or FALSE_SECONDS
    result = _run_wp(args, store, library, method, runs, source, flags=["-wp-prop", FALSE_GOAL],
                     provers=",".join(PROVERS), scripts=[], seconds=seconds, label=f"false check {logic.id}")
    outcome = result["outcome"]
    check = [g for g in outcome["goals"] if g["goal"].endswith(f"lemma_{FALSE_GOAL}")]
    counterexample = None
    if check and check[0]["status"] == "valid":
        verdict, failure_class = "refuted", None
        counterexample = {"goal": check[0]["goal"], "solver": check[0]["solver"], "seconds": check[0]["seconds"],
                          "statement": f"WP proved \\false from {logic.id} {logic.version} alone"}
        why = counterexample["statement"]
    elif check and outcome["failure_class"] in ("timeout", "unknown"):
        verdict, failure_class, why = "proven", None, ("no solver proved \\false within the budget (evidence, not "
                                                         "a consistency proof)")
    elif not check and outcome["failure_class"] is None:
        verdict, failure_class, why = "not_proven", "vacuous_pass", "WP reported no goal for the \\false check"
    else:
        verdict, failure_class, why = "not_proven", outcome["failure_class"] or "unknown", outcome["why"]
    subject = _subject(logic, FALSE_PARTS)
    record = _record(args, store, library, method, result, subject, verdict, failure_class,
                     pins_logic=[logic.pin()], contract=logic.owner, why=why, bypassed=bypassed,
                     counterexample=counterexample, settings={"wp_seconds_per_solver": seconds})
    written = _write(args, record)
    if verdict == "refuted":
        raise Failure(f"{logic.id} {logic.version} is refused: {why} (record {written['record']['id']}, "
                      f"{written['path']})")
    return written


def _program(args, store, library, method, runs, found):
    program = args.program.resolve()
    if not program.is_file():
        raise Failure(f"no program {args.program}")
    logic, bypassed = [], False
    for ident in args.uses:
        if ident not in found:
            raise Failure(f"no logic file {ident!r}")
        if found[ident].version is None:
            raise Failure(f"{found[ident].path} has no version line")
        problems = acsl_subset.LogicLibrary({ident: found[ident].text}).problems[ident]
        if problems and not args.skip_subset_check:
            raise Failure(f"{ident} breaks the allowed-ACSL rules ({problems[0][1]}); nothing proven")
        bypassed = bypassed or bool(problems)
        logic.append(found[ident])
    text = program.read_text()
    source = "".join(f"/*@\n{f.text}\n*/\n" for f in logic) + f"# 1 \"{program.name}\"\n" + text
    flags = ["-wp-rte", "-wp-prop=-@lemma"]
    for define in sorted(args.define):
        flags.append(f"-cpp-extra-args=-D{define}")
    result = _run_wp(args, store, library, method, runs, source, flags=flags, provers=",".join(PROVERS),
                     scripts=[], seconds=args.timeout, label=f"program {program.name}")
    outcome = result["outcome"]
    subject = {"kind": "calibration_program", "id": args.program_id or program.name}
    record = _record(args, store, library, method, result, subject, outcome["verdict"], outcome["failure_class"],
                     pins_logic=[f.pin() for f in logic], contract=None, why=outcome["why"], bypassed=bypassed,
                     code={"id": program.name, "sha256": artifacts.file_hash(program)},
                     constants=[{"name": d.split("=", 1)[0], "value": d.split("=", 1)[1] if "=" in d else "1"}
                                for d in sorted(args.define)],
                     settings={"uses": [f.id for f in logic]})
    return _write(args, record)


def _subject(logic, parts):
    if logic.owner is None:
        return {"kind": "method_part", "id": logic.id, "part": parts["shared"]}
    return {"kind": "contract_proof_part", "id": logic.owner, "part": parts["own"]}


def false_check_lemma(text):
    """The generated \\false-check lemma: every definition of `text` inside an uninterpreted wrapper.

    WP sends a solver only the definitions of the symbols a goal mentions (research 13, Q2), and a recursive
    definition becomes an axiom there. The wrappers keep each mention from being simplified away, and the
    hypothesis they form is satisfiable unless the definitions and lemmas are inconsistent."""
    binders, terms = [], []
    for position, (name, kind, result, params) in enumerate(_definitions(text)):
        names = []
        for pname, ptype in params:
            fresh = f"swdb_{position}_{pname}"
            binders.append(f"{ptype} {fresh}")
            names.append(fresh)
        call = f"{name}({', '.join(names)})" if params else name
        if kind == "predicate":
            terms.append(f"swdb_keep_integer({call} ? 1 : 0)")
        elif result == "real":
            terms.append(f"swdb_keep_real({call})")
        elif result in ("integer", "int", "unsigned", "long", "short", "char", "boolean"):
            terms.append(f"swdb_keep_integer({call})")
    if not terms:
        binders, terms = ["integer swdb_any"], ["swdb_keep_integer(swdb_any)"]
    return ("/*@ axiomatic SwdbFalseCheckKeep {\n"
            "      logic integer swdb_keep_integer(integer v);\n"
            "      logic integer swdb_keep_real(real v);\n    } */\n"
            f"/*@ lemma {FALSE_GOAL}: \\forall {', '.join(binders)};\n"
            f"      {' + '.join(terms)} == 0 ==> \\false; */\n")


def _definitions(text):
    """[(name, kind, result type, [(param, type)])] of the logic and predicate definitions of `text`."""
    toks = acsl_subset.tokens(text)
    found, i = [], 0
    while i < len(toks):
        word = toks[i].text
        if word in ("inductive", "axiomatic"):
            brace = next((j for j in range(i, len(toks)) if toks[j].text == "{"), len(toks))
            i = acsl_subset._close(toks, brace) + 1
            continue
        end = acsl_subset._statement_end(toks, i)
        if word in ("logic", "predicate"):
            stmt = toks[i + 1:end]
            eq = next((j for j, t in enumerate(stmt) if t.text == "="), None)
            if eq is not None:
                head = stmt[:eq]
                name, _labels, params = acsl_subset._head(head)
                at = next((j for j, t in enumerate(head) if t.text == name), 0)
                result = " ".join(t.text for t in head[:at]) if word == "logic" else ""
                found.append((name, word, result, [(p, " ".join(t.text for t in kind)) for p, kind in params]))
        i = end + 1
    return found


def _run_wp(args, store, library, method, runs, source, *, flags, provers, scripts, seconds, label):
    """One Frama-C/WP run in a fresh session under the verifier lock and RSS watchdog; returns its reading."""
    from swdb import rss_watchdog, verifier_lock, wp_adapter
    from swdb.framac import locate
    from swdb.proof import AdapterError, _cpu_seconds, _new_id
    try:
        tools = wp_adapter.WpAdapter(library, None, method)._tools()
    except AdapterError as exc:
        raise Failure(f"prove-logic: {exc}") from None
    rid = args.id or _new_id("logic")
    run = runs / rid
    run.mkdir(parents=True, exist_ok=False)
    scratch = run / "scratch"
    (scratch / "tmp").mkdir(parents=True)
    session = scratch / "session"
    (session / "script").mkdir(parents=True)
    for path in scripts:
        shutil.copyfile(path, session / "script" / path.name)
    (run / "wp_input.c").write_text(source)
    shutil.copyfile(run / "wp_input.c", scratch / "wp_input.c")
    seconds = seconds or tools["seconds"]
    settings_flags = [*tools["flags"], *wp_adapter.MACHDEP, "-wp-prover", provers, "-wp-timeout", str(seconds),
                      "-wp-par", "1", "-wp-session", "session", *flags]
    command = [*locate().command, *settings_flags, "-wp-report-json", "wp-goals.json", "wp_input.c",
               "-then", "-report-csv", "wp-properties.csv"]
    removed = sorted(k for k in os.environ if k.startswith("FRAMAC_WP"))
    env = {k: v for k, v in os.environ.items() if k not in removed}
    env["TMPDIR"] = str(scratch / "tmp")
    cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or wp_adapter.DEFAULT_CAP_BYTES)
    log = run / "frama-c.log"
    with verifier_lock.hold(f"swdb prove-logic {rid} ({label})"):
        load = os.getloadavg()[0]
        start, cpu = time.perf_counter(), _cpu_seconds()
        done = rss_watchdog.run(command, log=log, cap_bytes=cap, timeout=wp_adapter.DEFAULT_WALL_SECONDS,
                                cwd=scratch, env=env)
        wall, cpu = time.perf_counter() - start, _cpu_seconds() - cpu
    reports = [("wp_input", run / "wp_input.c"), ("wp_log", log)]
    for name in ("wp-goals.json", "wp-properties.csv"):
        if (scratch / name).exists():
            shutil.copyfile(scratch / name, run / name)
            reports.append((name.replace("-", "_").split(".")[0], run / name))
    outcome = wp_adapter.read_outcome(done, log.read_text(errors="replace"),
                                      run / "wp-goals.json" if (run / "wp-goals.json").exists() else None,
                                      run / "wp-properties.csv" if (run / "wp-properties.csv").exists() else None)
    adapter_log = run / "adapter.log"
    adapter_log.write_text(f"swdb prove-logic: {label}\ncommand: {shlex.join(map(str, command))}\n"
                           f"environment removed: {removed or 'none'}\nrss cap bytes: {cap}\n"
                           f"frama-c exit {done.exit_code}, wall {done.wall_seconds:.2f} s, peak rss "
                           f"{done.peak_rss_bytes}, out of memory {done.out_of_memory}\n"
                           f"outcome: {outcome['verdict']} {outcome['failure_class'] or ''} ({outcome['why']})\n")
    if provers != "tip":
        shutil.rmtree(scratch, ignore_errors=True)
    return {"id": rid, "run": run, "scratch": scratch, "session": session, "outcome": outcome, "tools": tools,
            "reports": reports, "adapter_log": adapter_log, "flags": settings_flags, "seconds": seconds,
            "wall": wall, "cpu": cpu, "load": load, "peak": done.peak_rss_bytes, "cap": cap, "removed": removed}


def _record(args, store, library, method, result, subject, verdict, failure_class, *, pins_logic, contract, why,
            bypassed, counterexample=None, code=None, constants=(), settings=None):
    from swdb import method_version, writer
    from swdb.proof import _job, _sha256          # one job block (ticket 12)
    from swdb.wp_adapter import SENTENCES
    na = {"not_applicable": "A logic-library proof pins no {}."}
    identities = result["tools"]["identities"]
    assumptions, tools = [], []
    for tool in ("frama-c-wp", *PROVERS):
        ident, sha, version = identities[tool]
        assumptions.append({"kind": "trusted_tool", "reference": {"id": ident, "sha256": sha},
                            "sentence": SENTENCES[tool].format(version=version)})
        tools.append(ident)
    contract_pin = ({"id": contract, "sha256": library.content_sha256(contract)} if contract else
                    {"not_applicable": "A shared logic file belongs to no contract."})
    pins = {
        "code": code or {"not_applicable": "A logic-library proof runs on no code."},
        "contract": contract_pin,
        "baseline_function": {"not_applicable": na["not_applicable"].format("baseline function")},
        "reference_semantics": {"not_applicable": na["not_applicable"].format("reference semantics")},
        "proof_semantics": {"not_applicable": na["not_applicable"].format("proof semantics")},
        "method_version": method_version.pin(method),
        "summaries": [],
        "minimum_bounds": {"not_applicable": na["not_applicable"].format("minimum bounds")},
        "predecessor_snapshot": {"not_applicable": na["not_applicable"].format("predecessor snapshot")},
        "build_constants": list(constants),
        "logic": pins_logic,
    }
    description = f"Written by swdb prove-logic: {why}."
    if bypassed:
        description += " Negative control: the allowed-ACSL check was skipped (--skip-subset-check)."
    record = {"kind": "proof", "schema_version": "0.4", "id": result["id"], "status": "draft",
              "created": writer.today(), "updated": writer.today(),
              "provenance": [{"id": "prove-logic", "kind": "agent_run", "description": description, "uri": None}],
              "subject": subject, "verdict": verdict}
    if counterexample:
        record["counterexample"] = counterexample
    if failure_class:
        record["failure_class"] = failure_class
    record["tools"] = tools
    record["goals"] = result["outcome"]["goals"]
    if verdict == "not_proven":
        record["unproven_properties"] = result["outcome"]["unproven"]
    record["settings"] = {"tool": "frama-c-wp", "flags": result["flags"], "session": "fresh",
                          "warning_levels": "default", "machdep": "x86_64",
                          "wp_seconds_per_solver": result["seconds"], "environment_removed": result["removed"],
                          "rss_cap_bytes": result["cap"], **(settings or {})}
    evidence = {"adapter_log": {"path": str(result["adapter_log"].resolve()), "sha256": _sha256(result["adapter_log"])},
                "reports": [{"name": name, "path": str(Path(path).resolve()), "sha256": _sha256(path)}
                            for name, path in result["reports"]]}
    load = round(result["load"], 3)
    record.update(pins=pins, bounds=dict(BOUNDS), assumptions=assumptions,
                  job=_job("wp", round(result["wall"], 6), round(result["cpu"], 6),
                           {"start": load, "end": round(os.getloadavg()[0], 3)}, result["peak"],
                           {"batch": f"batch.{result['id']}", "position": 1}),
                  evidence=evidence,
                  evidence_kind="execution" if method.data.get("evidence_kind") == "execution" else "contract_fixture")
    return record


def _write(args, record):
    from swdb.proof import _write as write
    return {"record": record, "path": write(args.records, record)}


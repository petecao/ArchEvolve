"""The real WP adapter: Frama-C/WP 33.0 on the C lowering of a candidate artifact's proof unit.

Created: 2026-10-14 ET (Probata proof of concept ticket 21, the A2 tracer). Design: formal-verification
map spec ("Verifier lineup and order": unbounded verifier, solver portfolio, pinned versions, failure
classes; "Proof-hint loop": anchors, frozen flags, verdict reading); map 11 items 1, 3, 8, 9, 10; 13
items 4, 6, 7; 16 items 3, 6. Format: docs/reference/format-v0.4-c-lowering-wp.md.

One job (`swdb prove --adapter wp`):
1. Find the C++ file of the candidate artifact's tree that defines the function; lower it
   (`swdb.c_lowering`). Outside the core subset: not proven, `unsupported_construct`; unparsable C++:
   `parse_error`.
2. Build WP's input: the C lowering with the contract's per-candidate formal halves at the unit's
   `contract` anchor, the logic-library files they use at `ghost.globals`, and fixture hints at their
   anchors (`--hint-file`; ticket 35 replaces them with hint records).
3. Check the installed tools against the pinned method version's lineup (Frama-C/WP, the three solvers,
   clang, the C lowering tool's ID and sha256); a mismatch runs nothing.
4. Run Frama-C/WP with the frozen settings in a fresh process in the job's scratch folder (TMPDIR too, so
   no WP or Why3 scratch survives), under the RSS watchdog (8 GiB) and the job's wall budget.
5. Minimal verdict reader: proven only when every property of this run's per-property report
   (`-report-csv`) is `Valid` and every goal of its per-goal report (`-wp-report-json`) passed; WP's
   consolidated summary line is never read. Ticket 36 owns the full reading rule.
6. Every outcome maps to a class of vocabulary `proof_failure_classes`, and that class's handler runs
   (`handler.json` in the runs folder). An outcome with no class reports `unclassified_wp_outcome`, which is
   not in the vocabulary, so `swdb prove` stops the batch. WP's "not proven" is never a refutation.
"""

import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from swdb import c_lowering, framac, paths, rss_watchdog, vocab, yamlio
from swdb.proof import AdapterError, Verdict

NAME = "wp"
PROVERS = ("alt-ergo", "z3", "cvc5")
WHY3_NAMES = {"Alt-Ergo": "alt-ergo", "Z3": "z3", "CVC5": "cvc5"}
FROZEN = (("-wp-cache", "none"), ("-wp-model", "+real"))
MACHDEP = ("-machdep", "x86_64")
LEMMAS_OUT = ("-wp-prop=-@lemma",)    # ticket 26: logic-library lemmas are proven once, with the method (prove-logic)
DEFAULT_WALL_SECONDS = 3600
DEFAULT_CAP_BYTES = 8 * 2**30                    # O9: the ~8 GB RSS watchdog
UNCLASSIFIED = "unclassified_wp_outcome"         # not a failure class: stops the batch (11 item 9)
SOURCE_SUFFIXES = (".cc", ".cpp", ".cxx", ".c")
HINT_KINDS = {"loop_head": ("loop invariant", "loop assigns", "loop variant"),
              "before": ("assert",), "after": ("assert",), "entry": ("assert",)}
FORBIDDEN_HINT = re.compile(r"(?:^|;|\*/|\n)\s*(admit|check|requires|ensures|assumes|axiom|axiomatic|lemma|ghost|"
                            r"behavior|predicate|logic|inductive|assigns|terminates|decreases)\b")
UNBOUNDED_RANGE = re.compile(r"\.\.\s*\]|\[\s*\.\.")
SENTENCES = {
    "c_lowering": "The C lowering tool (swdb lower, version {version}) lowers the C++ proof unit to C that behaves the "
                  "same; WP proves the C lowering, not the C++.",
    "clang": "clang {version} parses the C++ proof unit correctly for the C lowering tool.",
    "frama-c-wp": "Frama-C/WP {version} generates only sound proof obligations for the C lowering under its memory "
                  "model and the x86_64 machdep.",
    "alt-ergo": "Alt-Ergo {version} answers valid only for valid proof obligations.",
    "z3": "Z3 {version} answers valid only for valid proof obligations.",
    "cvc5": "CVC5 {version} answers valid only for valid proof obligations.",
}


class WpAdapter:
    """`swdb prove --adapter wp`: one WP job per call (records via swdb.proof)."""
    name = NAME
    real = True                                   # swdb prove takes the machine-wide verifier lock

    def __init__(self, library, contract, method, hints=None, defines=()):
        self.library, self.contract, self.method = library, contract, method
        self.hints_path = Path(hints) if hints else None
        self.hints = _read_hints(self.hints_path) if hints else []
        self.defines = tuple(defines)

    @classmethod
    def from_args(cls, args, script, *, library, contract, method):
        if script is not None:
            raise AdapterError("the wp adapter takes no --script (one WP job per call)")
        return cls(library, contract, method, hints=getattr(args, "hint_file", None),
                   defines=getattr(args, "define", None) or ())

    # --- the job --------------------------------------------------------------------------------
    def run(self, job):
        run_dir = Path(job.log).parent
        wp_dir = run_dir / "wp"
        wp_dir.mkdir(exist_ok=True)
        log = _Log(job.log)
        entry = self.library.get(self.contract) or {}
        unit = entry.get("proof_unit") or {}
        log.line(f"adapter: wp\nunit: {job.unit.candidate} {job.unit.function}\ncontract: {self.contract}")
        tools = self._tools()                     # missing or mismatched tools: no job, no record
        source = _unit_source(Path(job.unit.tree), job.unit.function)
        log.line(f"source: {source.relative_to(job.unit.tree)}")
        context = {"job": job, "wp_dir": wp_dir, "log": log, "reports": [], "tools": tools}
        try:
            lowering = c_lowering.lower(source, job.unit.function, defines=self.defines)
        except c_lowering.Unsupported as exc:
            return self._not_proven("unsupported_construct", str(exc), context)
        except c_lowering.ParseError as exc:
            return self._not_proven("parse_error", str(exc), context)
        except c_lowering.LoweringError as exc:
            raise AdapterError(str(exc)) from None
        if unit.get("function") not in (None, job.unit.function):
            raise AdapterError(f"contract {self.contract} states the proof unit {unit.get('function')}, not "
                               f"{job.unit.function}")
        c_path, anchors_path = lowering.write(wp_dir)
        context["reports"] += [("c_lowering", c_path), ("anchors", anchors_path)]
        context["c_lowering"] = {"id": c_path.name, "sha256": lowering.sha256}
        text = self._input(lowering, entry)
        input_path = wp_dir / "wp_input.c"
        input_path.write_text(text)
        context["reports"].append(("wp_input", input_path))
        if self.hints_path:
            shutil.copyfile(self.hints_path, wp_dir / "hints.yaml")
            context["reports"].append(("hints", wp_dir / "hints.yaml"))
        return self._wp(job, input_path, context)

    def _tools(self):
        """Installed versions and binary hashes, checked against the method version's lineup."""
        lineup = {}
        for row in self.method.data.get("lineup") or []:
            lineup.setdefault(row.get("tool"), row)
        frama, clang = framac.locate(), c_lowering.locate()
        if frama.missing:
            raise AdapterError(frama.missing)
        if clang.missing:
            raise AdapterError(clang.missing)
        found = {"frama-c-wp": (frama.version, _binary_sha256(frama.command)),
                 "clang": (clang.version, c_lowering.identity()["clang"]["sha256"])}
        found.update(_solvers())
        problems = []
        for tool in ("frama-c-wp", "clang", *PROVERS):
            pinned = (lineup.get(tool) or {}).get("version")
            have = found.get(tool, (None, None))[0]
            if have is None:
                problems.append(f"{tool} is not installed (Why3 config lists no such prover)")
            elif pinned != have:
                problems.append(f"{tool} {have} is installed but method version {self.method.id} pins {pinned}")
        lowering_id = c_lowering.identity()["c_lowering"]
        if lowering_id not in (self.method.data.get("c_lowering") or {}).get("translators", []):
            problems.append(f"the C lowering tool {lowering_id['id']} (sha256 {lowering_id['sha256'][:12]}...) is not "
                            f"a translator of method version {self.method.id}")
        flags = (lineup.get("frama-c-wp") or {}).get("flags") or []
        for flag, value in FROZEN:
            if not _has_flag(flags, flag, value):
                problems.append(f"method version {self.method.id} does not freeze {flag} {value} for frama-c-wp")
        if problems:
            raise AdapterError("; ".join(problems))
        seconds = ((self.method.data.get("budgets") or {}).get("wp_seconds_per_solver"))
        if not isinstance(seconds, int):
            raise AdapterError(f"method version {self.method.id} has no budgets.wp_seconds_per_solver")
        identities = {"c_lowering": (lowering_id["id"], lowering_id["sha256"], c_lowering.TOOL_VERSION)}
        for tool, (version, sha) in found.items():
            identities[tool] = (f"{tool}-{version}", sha, version)
        return {"flags": list(flags), "seconds": seconds, "identities": identities}

    def _input(self, lowering, entry):
        """WP's input file: contract at the unit's contract anchor, logic files at ghost.globals, hints at anchors."""
        clauses = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
                   and c.get("proof_placement") == "per_candidate"]
        if not clauses:
            raise AdapterError(f"contract {self.contract} has no per-candidate formal half to prove")
        texts = [c["acsl"]["text"].strip() for c in clauses]
        texts = sorted(texts, key=lambda t: 0 if t.startswith("requires") else 1)
        uses = []
        for clause in clauses:
            uses += [u for u in clause["acsl"].get("uses", []) if u not in uses]
        from swdb.formal_frame import logic_files
        files = logic_files(self.library.root, self.library)       # ticket 26: an entry's own file too
        inserts = {f"{lowering.function}.contract": ["/*@ " + "\n    ".join("\n".join(texts).splitlines()) + " */"],
                   "ghost.globals": [f"/*@\n{files[u].read_text()}\n*/" for u in uses]}
        kinds = {a["id"]: a["kind"] for a in lowering.anchors}
        for hint in self.hints:
            anchor, text = hint["anchor"], hint["acsl"].strip()
            if anchor not in kinds:
                raise AdapterError(f"hint anchor {anchor} is not an anchor of the C lowering of {lowering.function}")
            allowed = HINT_KINDS.get(kinds[anchor], ())
            if not text.startswith(allowed) or FORBIDDEN_HINT.search(text):
                raise AdapterError(f"hint at {anchor} ({kinds[anchor]}) may hold only {', '.join(allowed) or 'nothing'}")
            if UNBOUNDED_RANGE.search(text):                 # ticket 07: WP 33 aborts on `a[i ..]` in loop assigns
                raise AdapterError(f"hint at {anchor} has an unbounded range (`..]`); bound it (WP 33 cannot prove "
                                   "writes into an infinite assigns range)")
            inserts.setdefault(anchor, []).append("/*@ " + "\n    ".join(text.splitlines()) + " */")
        out = []
        for line in lowering.text.splitlines():
            match = c_lowering.ANCHOR_LINE.match(line)
            if match and match.group(1) in inserts and inserts[match.group(1)]:
                indent = line[:len(line) - len(line.lstrip())]
                out += [indent + block.replace("\n", "\n" + indent) for block in inserts[match.group(1)]]
            else:
                out.append(line)
        return "\n".join(out) + "\n"

    def _wp(self, job, input_path, context):
        tools, log, wp_dir = context["tools"], context["log"], context["wp_dir"]
        scratch = Path(job.scratch)
        shutil.copyfile(input_path, scratch / "wp_input.c")
        (scratch / "tmp").mkdir(exist_ok=True)
        goals_json, properties_csv = scratch / "wp-goals.json", scratch / "wp-properties.csv"
        settings_flags = [*tools["flags"], *MACHDEP, "-wp-prover", ",".join(PROVERS), "-wp-timeout",
                          str(tools["seconds"]), "-wp-par", "1", *LEMMAS_OUT]
        command = [*framac.locate().command, *settings_flags, "-wp-report-json", goals_json.name, "wp_input.c",
                   "-then", "-report-csv", properties_csv.name]
        removed = sorted(k for k in os.environ if k.startswith("FRAMAC_WP"))
        env = {k: v for k, v in os.environ.items() if k not in removed}
        env["TMPDIR"] = str(scratch / "tmp")
        cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or DEFAULT_CAP_BYTES)
        wall = job.budget_seconds or DEFAULT_WALL_SECONDS
        wp_log = wp_dir / "frama-c.log"
        log.line(f"command: {shlex.join(map(str, command))}\ncwd: scratch\nenvironment removed: {removed or 'none'}\n"
                 f"rss cap bytes: {cap}\nwall budget seconds: {wall}")
        context["reports"].append(("wp_log", wp_log))
        context["settings"] = {"tool": "frama-c-wp", "flags": settings_flags, "session": "fresh",
                               "warning_levels": "default", "machdep": "x86_64",
                               "wp_seconds_per_solver": tools["seconds"], "environment_removed": removed,
                               "rss_cap_bytes": cap, "hint_count": len(self.hints), "build_constants": list(self.defines)}
        result = rss_watchdog.run(command, log=wp_log, cap_bytes=cap, timeout=wall, cwd=scratch, env=env)
        context["peak"] = result.peak_rss_bytes
        log.line(f"frama-c exit {result.exit_code}, wall {result.wall_seconds:.2f} s, peak rss {result.peak_rss_bytes}, "
                 f"out of memory {result.out_of_memory}, timed out {result.timed_out}")
        for name, path in (("wp_goals", goals_json), ("wp_properties", properties_csv)):
            if path.exists():
                shutil.copyfile(path, wp_dir / path.name)
                context["reports"].append((name, wp_dir / path.name))
        outcome = read_outcome(result, wp_log.read_text(errors="replace"),
                               goals_json if goals_json.exists() else None,
                               properties_csv if properties_csv.exists() else None)
        context["goals"], context["unproven"] = outcome["goals"], outcome["unproven"]
        log.line(f"outcome: {outcome['verdict']} {outcome['failure_class'] or ''} ({outcome['why']})")
        if outcome["verdict"] == "proven":
            return self._verdict("proven", None, context)
        return self._not_proven(outcome["failure_class"], outcome["why"], context)

    # --- verdicts and handlers --------------------------------------------------------------------
    def _not_proven(self, failure_class, why, context):
        context.setdefault("goals", [])
        context.setdefault("unproven", [])
        handler = run_handler(failure_class, why, context)
        if handler:
            context["reports"].append(("handler", handler))
        return self._verdict("not_proven", failure_class, context)

    def _verdict(self, verdict, failure_class, context):
        identities = context["tools"]["identities"]
        assumptions, tools = [], []
        for tool in ("c_lowering", "clang", "frama-c-wp", *PROVERS):
            ident, sha, version = identities[tool]
            assumptions.append({"kind": "trusted_tool", "reference": {"id": ident, "sha256": sha},
                                "sentence": SENTENCES[tool].format(version=version)})
            tools.append(ident)
        fields = {"goals": context.get("goals", [])}
        if verdict == "not_proven":
            fields["unproven_properties"] = context.get("unproven", [])
        if context.get("settings"):
            fields["settings"] = context["settings"]
        pins = {"c_lowering": context["c_lowering"]} if context.get("c_lowering") else {}
        return Verdict(verdict=verdict, bounds={"threads": 1, "input_size": "unbounded"}, assumptions=assumptions,
                       failure_class=failure_class, tools=tuple(tools), peak_rss_bytes=context.get("peak"),
                       record_fields=fields, pins=pins, reports=tuple(context["reports"]))


# --- the minimal verdict reader -------------------------------------------------------------------------

CRASH = re.compile(r"Unexpected error|internal error|Fatal error|Stack overflow|Please report|Uncaught exception")
USER_ERROR = re.compile(r"User Error|annot-error|invalid user input|syntax error|Ignoring")


def read_outcome(result, log_text, goals_json, properties_csv):
    """{verdict, failure_class, why, goals, unproven} from one WP run (minimal reading; 36 owns the full rule)."""
    def outcome(verdict, failure_class, why, goals=(), unproven=()):
        return {"verdict": verdict, "failure_class": failure_class, "why": why, "goals": list(goals),
                "unproven": list(unproven)}
    if result.out_of_memory:
        return outcome("not_proven", "out_of_memory", "the RSS watchdog killed the job above its cap")
    if result.timed_out:
        return outcome("not_proven", "timeout", "the job ran out of its wall budget")
    if result.exit_code < 0 or CRASH.search(log_text):
        return outcome("not_proven", "tool_crash", f"Frama-C crashed (exit {result.exit_code})")
    if USER_ERROR.search(log_text):
        return outcome("not_proven", "parse_error", _first(log_text, USER_ERROR))
    if result.exit_code != 0:
        return outcome("not_proven", "tool_crash", f"Frama-C exited {result.exit_code} without a user error")
    if goals_json is None or properties_csv is None:
        return outcome("not_proven", UNCLASSIFIED, "WP exited 0 but wrote no per-property or per-goal report")
    goals = [_goal(g) for g in json.loads(goals_json.read_text() or "[]")]
    with open(properties_csv, newline="") as handle:
        properties = list(csv.DictReader(handle, delimiter="\t"))
    unproven = [{"property": row.get("property"), "kind": row.get("property kind"), "function": row.get("function"),
                 "line": int(row["line"]) if str(row.get("line", "")).isdigit() else None, "status": row.get("status")}
                for row in properties if row.get("status") != "Valid"]
    if not properties and not goals:
        return outcome("not_proven", "vacuous_pass", "WP reported no property and no goal", goals, unproven)
    failing = [g for g in goals if g["status"] != "valid"]
    if not unproven and not failing:
        return outcome("proven", None, "every property Valid and every goal passed", goals)
    statuses = {g["status"] for g in failing}
    for status, failure_class in (("failed", "solver_error"), ("timeout", "timeout"), ("stepout", "timeout"),
                                  ("unknown", "unknown")):
        if status in statuses:
            return outcome("not_proven", failure_class, f"{len(failing)} goal(s) not proven ({status})", goals, unproven)
    return outcome("not_proven", UNCLASSIFIED, f"properties not Valid with no failing goal: "
                   f"{sorted({u['status'] for u in unproven})}", goals, unproven)


def _goal(raw):
    solver, seconds = None, None
    for prover in raw.get("provers") or []:
        if prover.get("success"):
            solver = str(prover.get("prover", "")).split(":")[0].lower()
            seconds = float(prover.get("time") or 0)
            break
    status = "valid" if raw.get("passed") else str(raw.get("verdict") or "unknown").lower()
    return {"goal": raw.get("goal"), "property": raw.get("property"), "function": raw.get("function"),
            "status": status, "solver": solver, "seconds": seconds}


def _first(text, pattern):
    for line in text.splitlines():
        if pattern.search(line):
            return line.strip()[:400]
    return "Frama-C refused the input"


# --- handlers (map 11 item 9) ----------------------------------------------------------------------------

def run_handler(failure_class, why, context):
    """Run the handler of `failure_class` (its text from vocabulary proof_failure_classes); write handler.json."""
    vocabs, _problems = vocab.load_all(paths.VOCAB)
    entry = vocabs.entries.get("proof_failure_classes", {}).get(failure_class)
    if entry is None:
        return None                                # unclassified: swdb prove stops the batch
    wp_dir = context["wp_dir"]
    action = {"failure_class": failure_class, "why": why, "handler": entry.get("handler")}
    if failure_class in ("timeout", "unknown"):
        action["for_hint_loop"] = [g["goal"] for g in context.get("goals", []) if g["status"] != "valid"]
    elif failure_class == "out_of_memory":
        action["done"] = "class kept; on the Mac the ~8 GB cap stays, a rerun with more memory needs another host"
    else:                                          # parse error, unsupported construct, solver error, crash, vacuous pass
        reproduction = wp_dir / "reproduction"
        reproduction.mkdir(exist_ok=True)
        for name, path in context["reports"]:
            if name in ("wp_input", "c_lowering", "hints"):
                shutil.copyfile(path, reproduction / Path(path).name)
        if context.get("settings"):
            (reproduction / "command.txt").write_text(" ".join(context["settings"]["flags"]) + " wp_input.c\n")
        action["minimal_reproduction"] = sorted(p.name for p in reproduction.iterdir())
        action["regression_corpus"] = "add the case (input, class, cause) to tests/fixtures/proof/regression_corpus/"
    path = wp_dir / "handler.json"
    path.write_text(json.dumps(action, indent=1, sort_keys=True) + "\n")
    context["log"].line(f"handler ({failure_class}): {entry.get('handler')}")
    return path


# --- helpers -----------------------------------------------------------------------------------------------

class _Log:
    def __init__(self, path):
        self.path = Path(path)

    def line(self, text):
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(text.rstrip("\n") + "\n")


def _read_hints(path):
    try:
        data = yamlio.load(Path(path))
    except (OSError, ValueError) as exc:
        raise AdapterError(f"cannot read the hint file {path}: {exc}") from None
    hints = (data or {}).get("hints") if isinstance(data, dict) else None
    if not isinstance(hints, list) or not all(isinstance(h, dict) and isinstance(h.get("anchor"), str)
                                              and isinstance(h.get("acsl"), str) for h in hints):
        raise AdapterError(f"hint file {path} holds hints: [{{anchor, acsl}}, ...]")
    return hints


def _unit_source(tree, function):
    """The one C++ translation unit of the candidate artifact's tree that defines `function`."""
    pattern = re.compile(rf"(?m)^[^\n;{{}}#]*\b{re.escape(function)}\s*\([^;{{}}]*\)\s*(const\s*)?\{{")
    found = [p for p in sorted(tree.rglob("*")) if p.suffix in SOURCE_SUFFIXES and p.is_file()
             and pattern.search(p.read_text(errors="replace"))]
    if len(found) != 1:
        where = ", ".join(str(p.relative_to(tree)) for p in found) or "none"
        raise AdapterError(f"{function} must be defined in exactly one C++ file of {tree} (found: {where})")
    return found[0]


def _has_flag(flags, flag, value):
    return any(flags[i] == flag and flags[i + 1] == value for i in range(len(flags) - 1))


def why3_config():
    return Path(os.environ.get("WHY3CONFIG") or Path.home() / ".why3.conf")


def _solvers():
    """{tool: (version, sha256 of its binary)} from the Why3 configuration WP uses."""
    found, current = {}, {}
    try:
        text = why3_config().read_text()
    except OSError:
        return found
    for line in [*text.splitlines(), "[end]"]:
        line = line.strip()
        if line.startswith("["):
            name = WHY3_NAMES.get(current.get("name"))
            if name and name not in found and current.get("version"):
                binary = current.get("path") or (shlex.split(current.get("command", "")) or [""])[0]
                found[name] = (current["version"], _file_sha256(binary) if binary and Path(binary).is_file() else "0" * 64)
            current = {}
        elif "=" in line:
            key, value = line.split("=", 1)
            current[key.strip()] = value.strip().strip('"')
    return found


_SHA = {}


def _file_sha256(path):
    path = Path(path).resolve()
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _SHA:
        _SHA[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return _SHA[key]


def _binary_sha256(command):
    """sha256 of the Frama-C binary a command line runs (through `opam exec` when it is one)."""
    command = list(command)
    try:
        if command and Path(command[0]).name == "opam" and "--" in command:
            head = command[:command.index("--") + 1]
            done = subprocess.run([*head, "sh", "-c", f"command -v {shlex.quote(command[-1])}"], capture_output=True,
                                  text=True, timeout=60)
            binary = done.stdout.strip()
        else:
            binary = next((part for part in reversed(command) if Path(part).is_file()), None) or \
                shutil.which(command[-1])
        return _file_sha256(binary)
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        raise AdapterError(f"cannot find the Frama-C binary of {shlex.join(command)} to pin its sha256") from None

"""The proof_hinting agent role: one proof unit's failing WP goals in, one hint set out.

Created: 2026-10-14 ET (Probata proof of concept ticket 34). Design: formal-verification map spec
("Proof-hint loop": workspace, hint form; "Provider guard and workspaces"; O3), map 13 items 1, 6, 10, 13;
map 18 item 6; map 23 item 7. Format: docs/reference/format-v0.4-proof-hinting.md.

- **Launch.** `provider_roles.run("proof_hinting", Inputs(...), None, config, folder)`, the launcher every
  agent role uses (`rewrite.interpret`: pins, output check, retained call folder). Codex at its pin is the
  default (`default_config`). Ticket 37 calls it once per hint round.
- **Workspace.** A fixed layout of explicit files (`workspace_files`), written read-only; `workspace.json`
  holds the sha256 of every visible file and nothing else is visible. Hidden material (evaluator code,
  workload inputs, tests, negative controls, other candidate artifacts, counterexamples) is refused before
  any call opens, naming the file. The authors' accelerated code is visible only when the candidate
  artifact's record says the proof unit is that authors' function (map 18 item 6, narrow exception).
- **Output.** Only `{anchor, kind, text}` records (`provider_roles.HINT_OUTPUT_SCHEMA`); the hint set this
  module returns records the provider kind and each hint's provenance.
- **Frozen wrapper.** `swdb/proof_hint_wrapper.py`, an MCP stdio server the agent reaches inside its one
  provider call: it serves the visible files and runs the proof hint check and WP with the frozen flags,
  one verifier job at a time under the 8 GiB RSS watchdog. Its hash and its plan's hash are in
  `workspace.json`; its answers reach only the agent (never a verdict).
- **Mac confinement (O3, ADR 0006 exception).** Codex runs in its own sandbox, read-only, with its shell off;
  the wrapper is its only tool. On a Linux lab host the role is not built yet (its Landlock roots must admit
  the wrapper's verifiers) and refuses to start.
- **Audit.** Every shell command (a build first of all), file change, unknown tool, changed input, new file
  in the workspace or file beside it fails the call; `audit.json` records each attempt.
"""

import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

from swdb import artifacts, framac, provider_adapters, provider_login, provider_roles, provider_workspace, rewrite
from swdb import proof  # noqa: F401  (loads wp_adapter in the order proof.py expects)
from swdb import verifier_lock, wp_adapter
from swdb.cli import Failure

ROLE = provider_roles.ROLES["proof_hinting"]
SERVER = "swdb_proof_hint"
TOOLS = ("list_workspace", "read_workspace_file", "check_hints", "prove_hints")
WRAPPER = Path(__file__).with_name("proof_hint_wrapper.py")
WORKSPACE_FORMAT = "swdb.proof-hinting-workspace.v1"
PLAN_FORMAT = "swdb.proof-hint-wrapper-plan.v1"
HINT_SET_FORMAT = provider_workspace.HINT_SET_FORMAT
AUDIT_FORMAT = "swdb.provider-audit.v1"
DEFAULT_CAP_BYTES = wp_adapter.DEFAULT_CAP_BYTES
DEFAULT_WALL_SECONDS = 3600
CONTEXT_FILES = ("context/goals.json", "context/rejected_hints.json", "context/blamed_hints.json", "context/seeds.json")
CONTRACT_FILES = ("contract/formal_halves.acsl", "contract/unit_postcondition.acsl")
#: Hidden material by path (map 13 item 6): the category named in the refusal, then the folder names and test.
HIDDEN = (
    ("evaluator code", {"evaluator", "evaluators", "evaluations", "verifier", "verifiers"},
     lambda p: p.name.startswith(("verify", "verifier"))),
    ("a workload input", {"inputs", "workloads", "graphs"},
     lambda p: p.suffix.lower() in {".sg", ".wsg", ".csr", ".graph", ".bin", ".el", ".wel", ".mtx"}),
    ("a test", {"tests", "test", "testing"},
     lambda p: p.name.startswith("test_") or re.search(r"_tests?\.[A-Za-z]+$", p.name) is not None),
    ("a negative control", {"negative_controls", "negative-controls", "negctl", "negative_control"},
     lambda p: "negative_control" in p.name or "negctl" in p.name),
    ("another candidate artifact", {"candidates"}, lambda p: False),
)
#: WP options a method version may not set for the wrapper: verdicts come only from a fresh run with the
#: default warning levels (map 13 item 6; design "Three checks": frozen flags).
REFUSED_FLAG = re.compile(r"warn-key|^-wp-session|^-wp-cache-env|^-then|^-load|^-save|^-wp-(?:prover|timeout|par)$|"
                          r"^-machdep$")
BUILD = re.compile(r"(?:^|[\s/])(?:cc|c\+\+|gcc|g\+\+|clang|clang\+\+|make|cmake|ninja|ld|ar|nvcc|bazel|cargo|"
                   r"frama-c|why3|alt-ergo|z3|cvc5)(?:-\d[\d.]*)?(?:\s|$)")
#: What the launcher (`rewrite.interpret`) and this module write beside the workspace during a call.
LAUNCHER_FILES = frozenset({"prompt.txt", "provider.json", "stdout.txt", "stderr.txt", "partial_output.txt",
                            "provider-tmp", "guard", "audit.json"})
ROLE_PROMPT_HEAD = "Agent role: proof_hinting."
PROMPT = ROLE_PROMPT_HEAD + """ You are the proof-hint agent of Extensa Probata. WP (Frama-C) did not prove some goals
of one proof unit. Write proof hints that help WP prove every goal. You never change code: the C lowering,
the C++ proof unit and the contract are fixed.

Your only tools are the MCP tools of server "swdb_proof_hint" (you have no shell):
- list_workspace and read_workspace_file read the workspace (read-only);
- check_hints runs the proof hint check on a complete hint set (seconds);
- prove_hints runs the check, then WP with the frozen settings (minutes). Its answer is feedback for you,
  never a verdict: the loop decides from its own fresh run.

Workspace layout:
- lowering/<function>.c: the C lowering WP proves, with `/* swdb-anchor <id> */` lines; <function>.anchors.json
  lists every anchor with its kind. Hints go only at these anchors.
- proof_unit/...: the candidate artifact's C++ proof unit (for reading; WP proves the C lowering).
- contract/formal_halves.acsl and contract/unit_postcondition.acsl: what is proven. summaries/*.acsl: the
  summaries of called library operations (assumed, already proven).
- context/goals.json: the goals not proven, each with its kind and failure class.
- context/rejected_hints.json: earlier hints the proof hint check rejected, each with its rule;
  context/blamed_hints.json: earlier hints blamed for a goal not proven; context/seeds.json: seed hints.

A hint is {anchor, kind, text}: allowed kinds are loop invariant, loop assigns, integer loop variant,
assert, ghost declarations and statements, non-recursive predicate or logic definitions, lemmas (proven in
the same run) and \\wp::strategy hints. Never admit, axiom, recursive or inductive definitions, contracts,
ghost functions or body-less declarations. An assertion WP does not prove is not proven: it never helps.
Return only JSON: {"hints": [{"anchor": ..., "kind": ..., "text": ...}, ...]}, your complete hint set.
"""


@dataclass(frozen=True)
class Candidate:
    """The candidate artifact whose proof unit is hinted (from its record; built by the trusted caller).

    `files`: path in the artifact's tree -> sha256. `authors_function`: set only when the record says the
    candidate artifact is the authors' code, naming that function (the narrow guard exception)."""
    id: str
    files: dict
    authors_function: str = None


@dataclass
class WrapperPlan:
    """What the frozen wrapper runs: the WP input without hints, the frozen flags, the proof hint check."""
    base: str
    wp_flags: list
    check_path: Path
    check_function: str
    frama_c: list
    lock: str
    cap_bytes: int = DEFAULT_CAP_BYTES
    wall_seconds: int = DEFAULT_WALL_SECONDS
    env: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Inputs:
    files: dict
    candidate: Candidate
    plan: WrapperPlan


def default_config(command="codex"):
    """Codex at its pin (`provider_adapters.PINS["codex"]`), the role's default provider (map 23 item 7)."""
    return rewrite.configuration_from({"kind": "codex", "command": [command]})


def wrapper_plan(base, method_flags, seconds_per_solver, check, *, wall_seconds=DEFAULT_WALL_SECONDS):
    """The wrapper's frozen plan: the method version's WP flags (which must freeze `-wp-cache none` and leave
    the warning levels at their defaults), the x86_64 machdep, the three provers at `seconds_per_solver` and
    one WP worker. `check` is (path, function) of the proof hint check (ticket 35's; a scripted one in tests)."""
    flags = [str(f) for f in method_flags]
    for flag, value in wp_adapter.FROZEN:
        if not any(flags[i] == flag and flags[i + 1] == value for i in range(len(flags) - 1)):
            raise Failure(f"the wrapper's WP flags must freeze {flag} {value}")
    for index, flag in enumerate(flags):
        if flag == "-wp-cache" and flags[index + 1:index + 2] != ["none"] or flag.startswith("-") and REFUSED_FLAG.search(flag):
            raise Failure(f"the wrapper's WP flags may not set {flag} {flags[index + 1] if index + 1 < len(flags) else ''}"
                          .strip())
    if not isinstance(seconds_per_solver, int) or seconds_per_solver <= 0:
        raise Failure("the wrapper needs a positive integer WP time per solver")
    if check is None:
        raise Failure("the wrapper needs the proof hint check (ticket 35)")
    path, function = Path(check[0]).resolve(), check[1]
    if not path.is_file():
        raise Failure(f"the proof hint check is missing: {path}")
    tool = framac.locate()
    if tool.missing:
        raise Failure(tool.missing)
    keep = ("PATH", "HOME", "OPAMROOT", "OPAMSWITCH", "WHY3CONFIG", "LANG", "LC_ALL", "USER")
    cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or DEFAULT_CAP_BYTES)
    return WrapperPlan(base=base, wp_flags=[*flags, *wp_adapter.MACHDEP, "-wp-prover", ",".join(wp_adapter.PROVERS),
                                            "-wp-timeout", str(seconds_per_solver), "-wp-par", "1"],
                       check_path=path, check_function=function, frama_c=list(tool.command),
                       lock=str(verifier_lock.path()), cap_bytes=cap, wall_seconds=wall_seconds,
                       env={k: os.environ[k] for k in keep if k in os.environ})


def _hint(record, where, extra=()):
    keys = {"anchor", "kind", "text", *extra}
    if (not isinstance(record, dict) or set(record) != keys
            or not all(isinstance(record[k], str) and record[k] for k in ("anchor", "kind", "text"))):
        raise Failure(f"proof_hinting input {where} holds a malformed hint record")
    return record


def workspace_files(*, function, lowering, anchors, proof_unit_path, proof_unit_text, formal_halves,
                    unit_postcondition, summaries, goals, rejected, blamed, seeds):
    """The role's visible files at their fixed paths (built by the trusted caller, never by walking a tree)."""
    def dump(value):
        return json.dumps(value, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    files = {f"lowering/{function}.c": lowering, f"lowering/{function}.anchors.json": dump(anchors),
             f"proof_unit/{proof_unit_path}": proof_unit_text,
             "contract/formal_halves.acsl": formal_halves, "contract/unit_postcondition.acsl": unit_postcondition,
             "context/goals.json": dump(goals), "context/rejected_hints.json": dump(rejected),
             "context/blamed_hints.json": dump(blamed), "context/seeds.json": dump(seeds)}
    for name, text in sorted(summaries.items()):
        files[f"summaries/{name}.acsl"] = text
    return files


# --- the visible set ------------------------------------------------------------------------------------

def _hidden(name):
    path = Path(name)
    parts = set(path.parts[:-1])
    for category, folders, test in HIDDEN:
        if parts & folders or test(path):
            return category
    if set(path.parts) & provider_workspace.HIDDEN_DIRS:
        return "hidden SWDB material"
    if path.name in provider_workspace.INSTRUCTION_FILES:
        return "an agent instruction file"
    return None


def checked_files(files, candidate):
    """(function, proof unit path) after every visibility rule; a refusal names the file (before any call)."""
    if not isinstance(files, dict) or not files:
        raise Failure("proof_hinting needs a nonempty explicit files mapping")
    if not isinstance(candidate, Candidate):
        raise Failure("proof_hinting needs the candidate artifact's record (Candidate)")
    for name, text in files.items():
        provider_workspace.safe_name(name)
        if not isinstance(text, str) or "\0" in text:
            raise Failure(f"proof_hinting inputs must be text: {name}")
        category = _hidden(name)
        if category:
            raise Failure(f"proof_hinting refuses hidden material ({category}): {name}")
    # Map 13 item 10: a counterexample goes to counterexample-guided repair, never to the proof-hint agent.
    provider_workspace.refuse_counterexamples(files)
    lowerings = sorted(n for n in files if re.fullmatch(r"lowering/[A-Za-z_]\w*\.c", n))
    if len(lowerings) != 1:
        raise Failure("proof_hinting needs exactly one C lowering lowering/<function>.c")
    function = Path(lowerings[0]).stem
    units = sorted(n for n in files if n.startswith("proof_unit/"))
    allowed = {lowerings[0], f"lowering/{function}.anchors.json", *CONTRACT_FILES, *CONTEXT_FILES, *units}
    for name in sorted(files):
        if name not in allowed and not re.fullmatch(r"summaries/[\w.-]+\.acsl", name):
            raise Failure(f"proof_hinting refuses a file outside its workspace layout: {name}")
    for name in sorted(allowed - set(units)):
        if name not in files:
            raise Failure(f"proof_hinting workspace lacks {name}")
    if len(units) != 1:
        raise Failure("proof_hinting shows exactly one proof unit, the candidate artifact's: "
                      + (", ".join(units) or "none given"))
    unit = units[0][len("proof_unit/"):]
    digest = hashlib.sha256(files[units[0]].encode()).hexdigest()
    if candidate.files.get(unit) != digest:
        raise Failure(f"proof_hinting refuses hidden material (another candidate artifact): {units[0]} is not the "
                      f"proof unit of candidate artifact {candidate.id}")
    _context(files)
    _authors_code(files, candidate, function)
    return function, unit


def _context(files):
    def load(name):
        try:
            value = json.loads(files[name])
        except ValueError:
            raise Failure(f"proof_hinting input is malformed JSON: {name}") from None
        if not isinstance(value, list):
            raise Failure(f"proof_hinting input must be a list: {name}")
        return value
    for name in files:
        if name.endswith(".anchors.json"):
            try:
                data = json.loads(files[name])
            except ValueError:
                raise Failure(f"proof_hinting input is malformed JSON: {name}") from None
            if not isinstance(data, dict) or not isinstance(data.get("anchors"), list) or not all(
                    isinstance(a, dict) and isinstance(a.get("id"), str) for a in data["anchors"]):
                raise Failure(f"proof_hinting anchors file lists no anchors: {name}")
    for goal in load("context/goals.json"):
        if not isinstance(goal, dict) or not all(isinstance(goal.get(k), str) and goal[k]
                                                 for k in ("kind", "failure_class")):
            raise Failure("proof_hinting goals each need their kind and failure class: context/goals.json")
    for row in load("context/rejected_hints.json"):
        if not isinstance(row, dict) or not isinstance(row.get("rule"), str) or set(row) - {"hint", "rule", "detail"}:
            raise Failure("proof_hinting rejected hints each need their rejection rule: context/rejected_hints.json")
        _hint(row.get("hint"), "context/rejected_hints.json")
    for row in load("context/blamed_hints.json"):
        if not isinstance(row, dict) or not isinstance(row.get("reason"), str) or set(row) - {"hint", "reason"}:
            raise Failure("proof_hinting blamed hints each need a reason: context/blamed_hints.json")
        _hint(row.get("hint"), "context/blamed_hints.json")
    for row in load("context/seeds.json"):
        _hint(row, "context/seeds.json", extra=("source",))


def _authors_code(files, candidate, function):
    """The authors' accelerated functions stay hidden (map 18 item 6) except the one the candidate artifact is.

    The exception keys on the candidate artifact's record (`authors_function`), never on a name: it names
    the proof unit's own function, and every other authors' name stays refused."""
    allowed = set()
    if candidate.authors_function is not None:
        if candidate.authors_function != function:
            raise Failure(f"candidate artifact {candidate.id} is the authors' {candidate.authors_function}, but the "
                          f"proof unit is {function}")
        allowed = {function}
    for name, text in sorted(files.items()):
        for found in provider_roles.FORBIDDEN_SOURCE.finditer(text):
            if found.group(0) not in allowed:
                raise Failure(f"proof_hinting workspace shows the authors' accelerated code ({found.group(0)} in "
                              f"{name}); only the candidate artifact's own function may appear, and only when its "
                              "record says it is the authors' code")


# --- the workspace --------------------------------------------------------------------------------------

def prepare(inputs, folder, config):
    """Materialize the read-only workspace, the wrapper's state and `workspace.json` (raises before any call)."""
    if not isinstance(inputs, Inputs):
        raise Failure("proof_hinting takes proof_hinting.Inputs (files, candidate, wrapper plan)")
    function, unit = checked_files(inputs.files, inputs.candidate)
    plan = inputs.plan
    check_sha = artifacts.file_hash(plan.check_path)
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    root, home, state = folder / "workspace", folder / "provider-home", folder / "wrapper"
    root.mkdir()
    home.mkdir(mode=0o700)
    state.mkdir()
    visible = {}
    for name, text in sorted(inputs.files.items()):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        visible[name] = artifacts.file_hash(target)
    anchors = json.loads(inputs.files[f"lowering/{function}.anchors.json"])
    plan_data = {"format": PLAN_FORMAT, "root": str(root), "visible": visible, "candidate": inputs.candidate.id,
                 "function": function, "base": plan.base, "anchors": anchors, "wp_flags": list(plan.wp_flags),
                 "frama_c": list(plan.frama_c), "env": dict(plan.env), "lock": plan.lock,
                 "cap_bytes": plan.cap_bytes, "wall_seconds": plan.wall_seconds,
                 "check": {"path": str(plan.check_path), "function": plan.check_function, "sha256": check_sha},
                 "wrapper_sha256": artifacts.file_hash(WRAPPER), "server": SERVER, "tools": list(TOOLS)}
    plan_path = state / "plan.json"
    plan_path.write_text(json.dumps(plan_data, indent=1, sort_keys=True))
    _read_only(root)
    plan_path.chmod(0o444)
    workspace = provider_workspace.Workspace(root, home, folder, root, visible=dict(visible))
    workspace.metadata = {
        "format": WORKSPACE_FORMAT, "role": ROLE.name, "candidate": inputs.candidate.id, "function": function,
        "proof_unit": f"proof_unit/{unit}",
        "authors_code_exception": inputs.candidate.authors_function is not None,
        "root": str(root), "home": str(home), "read_only": True, "visible_files": dict(sorted(visible.items())),
        "visible_files_sha256": artifacts.digest(visible),
        "wrapper": {"path": "swdb/proof_hint_wrapper.py", "sha256": plan_data["wrapper_sha256"], "server": SERVER,
                    "tools": list(TOOLS), "plan": {"path": str(plan_path), "sha256": artifacts.file_hash(plan_path)},
                    "wp_flags": list(plan.wp_flags),
                    "proof_hint_check": {"path": str(plan.check_path), "function": plan.check_function,
                                         "sha256": check_sha}},
        "prompt_sha256": artifacts.digest(PROMPT), "output_schema_sha256": artifacts.digest(ROLE.output_schema),
        "confinement": confinement(config), "login_copy_deleted": False}
    (folder / "workspace.json").write_text(json.dumps(workspace.metadata, indent=2))
    return workspace


def _read_only(root):
    for path in sorted(root.rglob("*"), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    root.chmod(0o555)


def _writable(root):
    for path in [root, *root.rglob("*")]:
        if path.is_dir() and not path.is_symlink():
            path.chmod(stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)


def confinement(config):
    """How the provider is confined (O3): a fixture runs unconfined on a fixture host; real Codex on the Mac runs
    in its own read-only sandbox with its shell off. Anything else refuses to start."""
    kind = config.get("emulates", config["kind"])
    if config["kind"] == "external_fixture":
        return {"mode": "contract_fixture", "sandbox": "read-only (argv)", "shell": "off", "tools": [SERVER]}
    if kind != "codex":
        raise Failure("proof_hinting confinement is built for Codex only (O3); Claude is a sensitivity check that "
                      "needs its own confinement")
    if sys.platform != "darwin":
        raise Failure("proof_hinting on a Linux lab host is not built: its Landlock roots must admit the wrapper's "
                      "verifiers (ticket 34 builds the Mac confinement, design O3)")
    return {"mode": "codex_sandbox_mac", "sandbox": "read-only", "shell": "off", "tools": [SERVER],
            "adr": "ADR 0006 scoped Mac exception (O3)"}


def confine(argv, state):
    """The Codex argv of one proof_hinting call: Codex's own sandbox read-only instead of the guard's bypass,
    the shell off, and the frozen wrapper as the only (MCP) tool server."""
    head, prompt = list(argv[:-1]), argv[-1]
    head = [a for a in head if a != "--dangerously-bypass-approvals-and-sandbox"]
    out, index = [], 0
    while index < len(head):                       # code mode's namespace filter would hide the MCP tools
        if head[index] == "-c" and head[index + 1].startswith("features.code_mode.direct_only_tool_namespaces"):
            index += 2
            continue
        out.append(head[index])
        index += 1
    out += ["--sandbox", "read-only", "--disable", "shell_tool",
            "-c", f"mcp_servers.{SERVER}.command={json.dumps(sys.executable)}",
            "-c", f"mcp_servers.{SERVER}.args={json.dumps(['-I', str(WRAPPER), '--state', str(state)])}",
            "-c", f"mcp_servers.{SERVER}.tool_timeout_sec=3600", "-c", f"mcp_servers.{SERVER}.startup_timeout_sec=60"]
    start = prompt.find(ROLE_PROMPT_HEAD)
    return [*out, prompt[start:] if start >= 0 else prompt]


def _environment(home, folder, kind):
    tmp = folder / "provider-tmp"
    tmp.mkdir(exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(tmp), "LANG": "C.UTF-8",
           "DISABLE_TELEMETRY": "1", "DISABLE_ERROR_REPORTING": "1", "DISABLE_AUTOUPDATER": "1",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    env["CODEX_HOME" if kind == "codex" else "CLAUDE_CONFIG_DIR"] = str(home)
    return env


def _login(config, home):
    if config["kind"] == "external_fixture":
        return provider_login.start(config, home)
    # O3 (ADR 0006 Mac exception): no Landlock guard, so the session copy is taken directly.
    path = home / provider_login.login_name("codex")
    return path, provider_login.take_session_copy("codex", path, "proof_hinting provider login file is unavailable")


# --- one call -------------------------------------------------------------------------------------------

def run(inputs, config, folder, *, remaining_s=None):
    """One proof_hinting provider call; returns (hint set, metadata). Raises before the call on any refused input."""
    config = {**config, "workspace": True}
    confinement(config)                                   # refuses an unbuilt confinement before anything else
    workspace = prepare(inputs, folder, config)
    folder = workspace.folder
    before = {p.name for p in folder.iterdir()}
    response, metadata, error = None, {}, None
    try:
        workspace.login_path, workspace.login_copy = _login(config, workspace.home)
        kind = config.get("emulates", config["kind"])
        (folder / "guard" / "ephemeral-state").mkdir(parents=True)
        context = {"cwd": workspace.root, "env": _environment(workspace.home, folder, kind),
                   "schema": ROLE.output_schema, "wrap_command": lambda argv: confine(argv, folder / "wrapper"),
                   "guard_policy": workspace.metadata["confinement"], "cleanup": workspace.cleanup}
        response, metadata = rewrite.interpret(config, PROMPT, folder, remaining_s=remaining_s, run_context=context)
    except BaseException as exc:
        error = exc
    finally:
        workspace.cleanup()
        receipt = folder / "provider.json"
        if receipt.is_file():
            metadata = json.loads(receipt.read_text())
        audited = provider_adapters.get(config).audit_events
        audit = audit_call(folder / "stdout.txt", workspace, before, completed=error is None, events=audited)
        _writable(workspace.root)
        calls = folder / "wrapper" / "calls.jsonl"
        metadata.update(role=ROLE.name, workspace=True, workspace_manifest=workspace.metadata, audit=audit,
                        output_schema_sha256=artifacts.digest(ROLE.output_schema),
                        wrapper_calls={"count": len(calls.read_text().splitlines()) if calls.is_file() else 0,
                                       "path": str(calls), "sha256": artifacts.file_hash(calls) if calls.is_file() else None,
                                       "use": "agent feedback only; never read as a verdict"})
        (folder / "audit.json").write_text(json.dumps(audit, indent=2))
        receipt.write_text(json.dumps(metadata, indent=2))
        (folder / "workspace.json").write_text(json.dumps(workspace.metadata, indent=2))
    if not audit["passed"] and ((folder / "stdout.txt").is_file() or error is None):
        raise Failure("proof_hinting audit failed: " + "; ".join(audit["reasons"]))
    if error is not None:
        raise error
    identity = provider_adapters.identity(config)
    provider = {"kind": config["kind"], "resolved_kind": identity["resolved_kind"], "model": identity["model"],
                "effort": identity["effort"], "classification": provider_adapters.classification(config),
                "cli_version": metadata.get("cli_version")}
    hints = [{"anchor": h["anchor"], "kind": h["kind"], "text": h["text"],
              "provenance": {"by": "proof_hinting_agent", "provider_kind": identity["resolved_kind"]}}
             for h in response["hints"]]
    hint_set = {"format": HINT_SET_FORMAT, "role": ROLE.name, "candidate": inputs.candidate.id,
                "function": workspace.metadata["function"], "hints": hints, "provider": provider,
                "workspace_sha256": workspace.metadata["visible_files_sha256"]}
    return hint_set, metadata


# --- the audit ------------------------------------------------------------------------------------------

def audit_call(path, workspace, before, *, completed, events=True):
    """The role's audit receipt: the call's events (when the provider emits them) and the files after it."""
    violations = []

    def fail(code, reason, event):
        item = {"code": code, "reason": reason, "event": event}
        if item not in violations:
            violations.append(item)

    root = workspace.root
    count, terminal = 0, False
    if events and not Path(path).is_file():
        fail("missing_event_log", "provider event log is missing", 0)
    elif events:
        for number, line in enumerate(Path(path).read_text(errors="replace").splitlines(), 1):
            try:
                row = json.loads(line)
            except ValueError:
                fail("invalid_event_log", "provider event log contains an unparsed event", number)
                continue
            if not isinstance(row, dict):
                continue
            count += 1
            terminal = terminal or row.get("type") == "turn.completed"
            if row.get("type") in {"connection", "network_connection"}:
                fail("outbound_connection", "provider made an outbound connection outside its model API", number)
            item = row.get("item")
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "command_execution":
                command = str(item.get("command"))
                if BUILD.search(" " + command):
                    fail("build", f"provider started a build; proof_hinting builds nothing: {command}", number)
                else:
                    fail("shell_command", f"provider ran a command; proof_hinting has no shell: {command}", number)
            elif kind == "file_change":
                for change in item.get("changes") or [None]:
                    name = change.get("path") if isinstance(change, dict) else None
                    try:
                        target = (root / str(name)).resolve()
                        inside = target.is_relative_to(root.resolve())
                    except (OSError, ValueError):
                        inside = False
                    if inside:
                        fail("immutable_input", f"provider tried to edit a read-only workspace input: {name}", number)
                    else:
                        fail("external_write", f"provider tried to write outside the workspace: {name}", number)
            elif kind == "mcp_tool_call":
                if item.get("server") != SERVER or item.get("tool") not in TOOLS:
                    fail("forbidden_tool", f"provider used a tool other than the frozen wrapper: "
                                           f"{item.get('server')}.{item.get('tool')}", number)
            elif kind not in {"agent_message", "reasoning", "todo_list", "error"}:
                fail("forbidden_tool", f"provider used a forbidden tool: {kind}", number)
        if completed and not terminal:
            fail("invalid_event_log", "provider event log ends without its terminal event", 0)
    seen = set()
    for current in sorted(root.rglob("*")):
        rel = current.relative_to(root).as_posix()
        if current.is_file() or current.is_symlink():
            seen.add(rel)
            if rel not in workspace.visible:
                fail("new_file", f"a file appeared in the read-only workspace: {rel}", 0)
    for name, digest in sorted(workspace.visible.items()):
        if name not in seen or artifacts.file_hash(root / name) != digest:
            fail("immutable_input", f"a read-only workspace input changed: {name}", 0)
    expected = before | LAUNCHER_FILES
    for entry in sorted(p.name for p in workspace.folder.iterdir()):
        if entry not in expected:
            fail("external_write", f"a file appeared beside the workspace: {entry}", 0)
    receipt = {"format": AUDIT_FORMAT, "role": ROLE.name, "state": "passed" if not violations else "failed",
               "passed": not violations, "events": count, "reasons": list(dict.fromkeys(v["reason"] for v in violations)),
               "violations": violations, "raw_log": {"path": str(path)}}
    if Path(path).is_file():
        receipt["raw_log"].update(sha256=artifacts.file_hash(path), bytes=Path(path).stat().st_size)
    return receipt

"""The frozen wrapper of the proof_hinting role: an MCP stdio server the proof-hint agent calls in its one
provider call.

Created: 2026-10-14 ET (Probata proof of concept ticket 34; map 13 item 6; ticket 07c's in-call tool, made
frozen). Usage (by Codex, from `-c mcp_servers.swdb_proof_hint.*`): `python -I proof_hint_wrapper.py --state
<folder>`. Any other argument is refused: the agent cannot pass a flag. Format:
docs/reference/format-v0.4-proof-hinting.md.

Tools (each takes exactly the arguments named; any other argument, a flag included, is refused):
- `list_workspace {}` and `read_workspace_file {path}`: the visible files of `workspace.json`, each served
  only while its sha256 still matches;
- `check_hints {hints}`: the proof hint check (the plan's check; ticket 35 owns the real one);
- `prove_hints {hints}`: the check, then Frama-C/WP with the plan's frozen flags on the merged unit, as one
  real verifier job: the machine-wide verifier lock (a second job queues behind it) and the RSS watchdog.

Every answer is feedback for the agent only and says so; no record reads it as a verdict. Each call is
appended to `<state>/calls.jsonl`; WP scratch is deleted when its job ends.
"""

import hashlib
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

if __package__ in (None, ""):                         # run as a file under `python -I`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FEEDBACK = "Feedback for the proof-hint agent only, never a verdict: the proof-hint loop decides from its own fresh run."
HINT_KEYS = {"anchor", "kind", "text"}
ARGUMENTS = {"list_workspace": set(), "read_workspace_file": {"path"}, "check_hints": {"hints"},
             "prove_hints": {"hints"}}
HINTS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["hints"], "properties": {
    "hints": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                         "required": ["anchor", "kind", "text"],
                                         "properties": {k: {"type": "string"} for k in ("anchor", "kind", "text")}}}}}
TOOLS = [
    {"name": "list_workspace", "description": "List the read-only workspace's files with their sizes.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
     "annotations": {"readOnlyHint": True}},
    {"name": "read_workspace_file", "description": "Read one workspace file by its path from list_workspace.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["path"],
                     "properties": {"path": {"type": "string"}}}, "annotations": {"readOnlyHint": True}},
    {"name": "check_hints", "description": "Run the proof hint check on a COMPLETE hint set. Seconds. Runs no prover.",
     "inputSchema": HINTS_SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "prove_hints", "description": "check_hints, then WP with the frozen settings on the hinted unit; lists "
                                           "every goal not proven. Minutes. Feedback only, never a verdict.",
     "inputSchema": HINTS_SCHEMA, "annotations": {"readOnlyHint": True}},
]


class Refused(Exception):
    """A call the frozen wrapper does not run."""


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Wrapper:
    def __init__(self, state):
        self.state = Path(state)
        self.plan = json.loads((self.state / "plan.json").read_text())
        if _sha(__file__) != self.plan["wrapper_sha256"]:
            raise Refused("the wrapper differs from the frozen one named in workspace.json")
        self.calls = 0

    # --- tools -------------------------------------------------------------------------------------------
    def call(self, tool, arguments):
        if tool not in ARGUMENTS:
            raise Refused(f"unknown tool {tool}")
        if not isinstance(arguments, dict):
            raise Refused("tool arguments must be an object")
        extra = sorted(set(arguments) - ARGUMENTS[tool])
        if extra or set(arguments) != ARGUMENTS[tool]:
            raise Refused(f"the frozen wrapper's {tool} takes only {sorted(ARGUMENTS[tool]) or 'no arguments'}; "
                          f"no flag or option is accepted (refused: {', '.join(extra) or 'missing arguments'})")
        if tool == "list_workspace":
            root = Path(self.plan["root"])
            return "\n".join(f"{name}  {(root / name).stat().st_size} bytes" for name in sorted(self.plan["visible"]))
        if tool == "read_workspace_file":
            return self._read(arguments["path"])
        hints = self._hints(arguments["hints"])
        started = time.time()
        result = self._check(hints)
        entry = {"n": self.calls + 1, "tool": tool, "hints_sha256": hashlib.sha256(json.dumps(hints, sort_keys=True)
                 .encode()).hexdigest(), "check_passed": result["passed"], "rejections": result["rejections"]}
        if not result["passed"]:
            text = "Proof hint check FAILED:\n" + "\n".join(
                f"- hint {r.get('hint')}: rule {r.get('rule')} {r.get('detail', '')}".rstrip() for r in result["rejections"])
        elif tool == "check_hints":
            text = "Proof hint check passed."
        else:
            text, wp = self._prove(result["merged"])
            entry["wp"] = wp
        entry["wall_seconds"] = round(time.time() - started, 3)
        self._log(entry)
        return text + "\n" + FEEDBACK

    def _read(self, name):
        visible = self.plan["visible"]
        if name not in visible:
            raise Refused(f"not a workspace file: {name}")
        path = Path(self.plan["root"]) / name
        if _sha(path) != visible[name]:
            raise Refused(f"workspace file changed since the call started: {name}")
        return path.read_text()

    def _hints(self, hints):
        if not isinstance(hints, list) or not all(isinstance(h, dict) and set(h) == HINT_KEYS
                                                  and all(isinstance(h[k], str) for k in HINT_KEYS) for h in hints):
            raise Refused("hints must be a list of {anchor, kind, text} records and nothing else")
        return hints

    def _check(self, hints):
        check = self.plan["check"]
        if _sha(check["path"]) != check["sha256"]:
            raise Refused("the proof hint check differs from the frozen one named in workspace.json")
        spec = importlib.util.spec_from_file_location("swdb_frozen_proof_hint_check", check["path"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = getattr(module, check["function"])(self.plan["base"], self.plan["anchors"], hints)
        return {"passed": bool(result.get("passed")), "rejections": list(result.get("rejections") or []),
                "merged": result.get("merged")}

    def _prove(self, merged):
        from swdb import proof  # noqa: F401  (loads wp_adapter in the order proof.py expects)
        from swdb import rss_watchdog, verifier_lock, wp_adapter
        plan = self.plan
        scratch = self.state / f"scratch-{self.calls + 1}"
        scratch.mkdir()
        try:
            (scratch / "tmp").mkdir()
            (scratch / "wp_input.c").write_text(merged)
            command = [*plan["frama_c"], *plan["wp_flags"], "-wp-report-json", "wp-goals.json", "wp_input.c",
                       "-then", "-report-csv", "wp-properties.csv"]
            env = {**plan["env"], "TMPDIR": str(scratch / "tmp")}
            log = scratch / "frama-c.log"
            with verifier_lock.hold(f"proof_hinting {plan['candidate']}", lock=plan["lock"]) as held:
                result = rss_watchdog.run(command, log=log, cap_bytes=plan["cap_bytes"], timeout=plan["wall_seconds"],
                                          cwd=scratch, env=env)
            goals = scratch / "wp-goals.json"
            properties = scratch / "wp-properties.csv"
            outcome = wp_adapter.read_outcome(result, log.read_text(errors="replace"),
                                              goals if goals.exists() else None,
                                              properties if properties.exists() else None)
            wp = {"lock_waited_seconds": held["waited_seconds"], "peak_rss_bytes": result.peak_rss_bytes,
                  "exit_code": result.exit_code, "out_of_memory": result.out_of_memory,
                  "wall_seconds": round(result.wall_seconds, 3), "failure_class": outcome["failure_class"],
                  "goals": len(outcome["goals"]), "failing": len([g for g in outcome["goals"] if g["status"] != "valid"])}
            lines = [f"WP ran ({wp['wall_seconds']} s): {wp['goals'] - wp['failing']} of {wp['goals']} goals proven."]
            if outcome["failure_class"]:
                lines.append(f"Failure class: {outcome['failure_class']} ({outcome['why']}).")
            for goal in outcome["goals"]:
                if goal["status"] != "valid":
                    lines.append(f"- not proven [{goal['status']}]: {goal['goal']} ({goal['property']}, {goal['function']})")
            for prop in outcome["unproven"]:
                lines.append(f"- property {prop['status']}: {prop['property']} ({prop['kind']}, {prop['function']}, "
                             f"line {prop['line']})")
            if outcome["failure_class"] in {"parse_error", "tool_crash", "out_of_memory"}:
                lines.append(log.read_text(errors="replace")[-2000:])
            return "\n".join(lines), wp
        finally:
            shutil.rmtree(scratch, ignore_errors=True)        # verifier scratch is never kept

    def _log(self, entry):
        self.calls += 1
        with open(self.state / "calls.jsonl", "a") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    # --- MCP over stdio ----------------------------------------------------------------------------------
    def serve(self, stdin, stdout):
        def send(value):
            stdout.write(json.dumps(value) + "\n")
            stdout.flush()
        for line in stdin:
            try:
                message = json.loads(line)
            except ValueError:
                continue
            number, method = message.get("id"), message.get("method")
            if method == "initialize":
                send({"jsonrpc": "2.0", "id": number, "result": {
                    "protocolVersion": (message.get("params") or {}).get("protocolVersion", "2025-06-18"),
                    "capabilities": {"tools": {}}, "serverInfo": {"name": self.plan["server"], "version": "1"}}})
            elif method == "tools/list":
                send({"jsonrpc": "2.0", "id": number, "result": {"tools": TOOLS}})
            elif method == "tools/call":
                params = message.get("params") or {}
                try:
                    text, error = self.call(params.get("name"), params.get("arguments", {})), False
                except Refused as exc:
                    text, error = f"refused: {exc}", True
                send({"jsonrpc": "2.0", "id": number,
                      "result": {"content": [{"type": "text", "text": text}], "isError": error}})
            elif number is not None:
                send({"jsonrpc": "2.0", "id": number, "error": {"code": -32601, "message": f"not supported: {method}"}})


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "--state":
        extra = [a for a in argv if a != "--state"][1:] if "--state" in argv else argv
        sys.stderr.write("refused: the frozen wrapper takes only --state <folder>; no flag or option is accepted"
                         f" (refused: {' '.join(extra)})\n")
        return 2
    try:
        wrapper = Wrapper(argv[1])
    except (Refused, OSError, ValueError) as exc:
        sys.stderr.write(f"refused: {exc}\n")
        return 2
    wrapper.serve(sys.stdin, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())

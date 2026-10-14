"""A scripted provider for the proof_hinting role (Probata PoC ticket 34). Created: 2026-10-14 ET.

Runs as an `external_fixture` that emulates Codex, so it receives the Codex argv the role builds. Its plan
(argv[1], JSON) picks a mode:
- hints: return the plan's hints;
- wrapper: start the frozen wrapper from the argv's `-c mcp_servers.<name>.*` options (as Codex does),
  call its tools over MCP (the plan's `calls`), record the replies, then return the hints;
- edit_code / verdict: return edited code or a claimed verdict beside the hints;
- edit_input: try to write the C lowering and the proof unit, report each attempt as a file change;
- build: report a compiler command; write_outside: write beside the workspace, report the file change.
Every run appends its argv and working folder to the plan's `log` (JSON lines).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

if "--version" in sys.argv:
    print("proof-hinting-fixture-1")
    raise SystemExit(0)
plan = json.loads(Path(sys.argv[1]).read_text())
argv = sys.argv[2:]
with open(plan["log"], "a") as log:
    log.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "env_keys": sorted(os.environ)}) + "\n")


def event(item):
    print(json.dumps({"type": "item.completed", "item": item}), flush=True)


def option(name):
    """The value of `-c <name>=<json>` in the Codex argv."""
    for index, word in enumerate(argv):
        if word == "-c" and argv[index + 1].startswith(name + "="):
            return json.loads(argv[index + 1].split("=", 1)[1])
    raise SystemExit(f"fixture: no -c {name}")


def mcp(calls):
    server = plan["server"]
    command = option(f"mcp_servers.{server}.command")
    args = option(f"mcp_servers.{server}.args")
    child = subprocess.Popen([command, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    replies = []

    def ask(number, method, params):
        child.stdin.write(json.dumps({"jsonrpc": "2.0", "id": number, "method": method, "params": params}) + "\n")
        child.stdin.flush()
        return json.loads(child.stdout.readline())

    ask(0, "initialize", {"protocolVersion": "2025-06-18"})
    replies.append(ask(1, "tools/list", {}))
    for number, (tool, arguments) in enumerate(calls, 2):
        reply = ask(number, "tools/call", {"name": tool, "arguments": arguments})
        replies.append(reply)
        event({"type": "mcp_tool_call", "server": server, "tool": tool, "arguments": arguments,
               "status": "completed"})
    child.stdin.close()
    child.wait(timeout=60)
    Path(plan["replies"]).write_text(json.dumps(replies))


mode = plan["mode"]
result = {"hints": plan.get("hints", [])}
event({"type": "agent_message", "text": "fixture"})
if mode == "wrapper":
    mcp(plan["calls"])
elif mode == "edit_code":
    result["files"] = [{"path": "proof_unit/src/bfs.cc", "content": "int x;\n"}]
elif mode == "verdict":
    result["verdict"] = "proven"
elif mode == "edit_input":
    for name in plan["targets"]:
        try:
            with open(name, "a") as handle:
                handle.write("/* edited */\n")
            status = "completed"
        except OSError:
            status = "failed"
        event({"type": "file_change", "changes": [{"path": name, "kind": "update"}], "status": status})
elif mode == "build":
    event({"type": "command_execution", "command": "clang++ -c proof_unit/src/bfs.cc -o build/bfs.o",
           "exit_code": 1, "aggregated_output": ""})
elif mode == "write_outside":
    target = Path("..") / "outside.txt"
    try:
        target.write_text("written outside\n")
    except OSError:
        pass
    event({"type": "file_change", "changes": [{"path": str(target), "kind": "add"}], "status": "completed"})
final = argv[argv.index("--output-last-message") + 1]
Path(final).write_text(json.dumps(result))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}), flush=True)

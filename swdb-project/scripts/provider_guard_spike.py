"""Lane-confined provider guard feasibility receipts. Updated: 2026-09-30 ET.

Raw output stays under the supplied run folder on mbit10. This is a diagnostic
spike, not evaluation evidence for the generated toy source.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from swdb import provider_guard


SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["interpretation", "unresolved"],
          "properties": {"interpretation": {"type": "string"},
                         "unresolved": {"type": "array", "items": {"type": "string"}}}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("probe", "codex", "claude"))
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--readonly-sqlite-home", action="store_true",
                        help="Codex diagnostic: confine session state to an empty read-only guard folder")
    args = parser.parse_args()
    if args.readonly_sqlite_home and args.kind != "codex":
        parser.error("--readonly-sqlite-home is a Codex diagnostic")
    folder = args.runs_dir.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    workspace, home = folder / "workspace", folder / "provider-home"
    workspace.mkdir()
    home.mkdir(mode=0o700)
    (workspace / "probe.cc").write_text("int main() { return 0; }\n")
    cli = shutil.which(args.kind) if args.kind != "probe" else sys.executable
    if not cli:
        raise SystemExit("provider executable unavailable")
    config = {"kind": "external_fixture" if args.kind == "probe" else args.kind,
              "command": [cli], "workspace": True}
    # Identify the checkout before any credential copy exists to leak.
    receipt = {"kind": args.kind, "checkout": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    login = None
    if args.kind != "probe":
        original = Path(os.environ.get("CODEX_HOME", "/data1/yanruj/.codex")) / "auth.json" if args.kind == "codex" else Path(os.environ.get("CLAUDE_CONFIG_DIR", "/data1/yanruj/.claude")) / ".credentials.json"
        login = home / original.name
        try:
            shutil.copyfile(original, login)
            login.chmod(0o600)
        except BaseException:
            login.unlink(missing_ok=True)
            raise
    started = time.monotonic()
    child = None
    context = None
    try:
        context = provider_guard.context(config, workspace, home, folder, login_path=login, fixture=args.kind == "probe")
        receipt["guard_policy"] = context["guard_policy"]
        if args.kind == "probe":
            script = workspace / "probe.py"
            script.write_text('''import json,socket,pathlib
results={}
def check(name,call):
 try: call();results[name]="allowed"
 except OSError as e: results[name]="blocked:"+str(e.errno)
check("inside_read",lambda:pathlib.Path("probe.cc").read_text())
check("outside_read",lambda:pathlib.Path("/data1/yanruj/ArchEvolve/swdb-project/GLOSSARY.md").read_text())
check("outside_write",lambda:pathlib.Path("../forbidden.txt").write_text("no"))
check("outside_tcp",lambda:socket.create_connection(("1.1.1.1",80),5))
check("allowed_tcp",lambda:socket.create_connection(("1.1.1.1",443),5))
print(json.dumps(results))
''')
            command = [sys.executable, str(script)]
        else:
            from swdb import provider_adapters
            config["resolved_kind"] = args.kind
            config["budget_usd"] = 5
            adapter = provider_adapters.get(config)
            receipt["cli_version"] = adapter.version(config)
            prompt = "Read probe.cc, change main to return 1, compile it with g++ into build/probe, run it and confirm exit status 1. Work only here. Return interpretation and unresolved as JSON."
            (folder / "prompt.txt").write_text(prompt)
            command = adapter.command(config, prompt, folder, SCHEMA)
            if args.readonly_sqlite_home:
                state = folder / "guard" / "ephemeral-state"
                state.mkdir(exist_ok=True)
                command[-1:-1] = ["-c", "sqlite_home=" + json.dumps(str(state))]
                receipt["variant"] = {"sqlite_home": str(state), "writable": False}
        receipt["command"] = command
        with (folder / "stdout.txt").open("w") as stdout, (folder / "stderr.txt").open("w") as stderr, (folder / "prompt.txt").open() if args.kind == "claude" else open(os.devnull) as stdin:
            wrapped = context["wrap_command"](command)
            # This diagnostic also records execs to verify Claude's actual
            # shell-prefix launcher; environment values are omitted by strace.
            wrapped[wrapped.index("trace=connect")] = "trace=connect,execve,openat,readlink"
            tracer_index = wrapped.index(shutil.which("strace"))
            wrapped[tracer_index + 1:tracer_index + 1] = ["-s", "512"]
            child = subprocess.Popen(wrapped, cwd=workspace, env=context["env"],
                                     stdin=stdin, stdout=stdout, stderr=stderr, start_new_session=True)
            while child.poll() is None:
                context["monitor"](child)
                if time.monotonic() - started > 300:
                    raise TimeoutError("provider spike exceeded 300 seconds")
                time.sleep(.25)
        receipt["returncode"] = child.returncode
        if args.kind == "probe" and child.returncode == 0:
            result = json.loads((folder / "stdout.txt").read_text())
            receipt["checks"] = result
            receipt["passed"] = all(result[k] == "allowed" for k in ("inside_read", "allowed_tcp")) and all(result[k].startswith("blocked:") for k in ("outside_read", "outside_write", "outside_tcp"))
        elif args.kind != "probe":
            receipt["task"] = {"source_changed": "return 1" in (workspace / "probe.cc").read_text(),
                               "binary_exists": (workspace / "build/probe").is_file()}
            receipt["passed"] = child.returncode == 0 and all(receipt["task"].values())
            if not receipt["passed"] and child.returncode == 0:
                receipt["reason"] = "provider completed a turn but did not finish the requested toy edit/build"
    except Exception as exc:
        receipt["passed"] = False
        receipt["reason"] = str(exc)
    finally:
        try:
            try:
                if context and child:
                    context["stop_owned"](child)
            finally:
                if child:
                    from swdb.processes import stop_group
                    stop_group(child, grace_seconds=2)
            if context:
                receipt["guard_audit"] = context["finish"]()
                if not receipt["guard_audit"]["passed"]:
                    receipt["passed"] = False
                    receipt.setdefault("reason", "; ".join(receipt["guard_audit"]["reasons"]))
                if args.kind != "probe" and (folder / "stdout.txt").exists():
                    from swdb import provider_audit
                    receipt["event_audit"] = provider_audit.audit(folder / "stdout.txt", args.kind, workspace,
                        ["probe.cc"], home, (login,), ["probe.cc"], guard_reasons=receipt["guard_audit"]["reasons"])
                    receipt["passed"] = receipt.get("passed", False) and receipt["event_audit"]["passed"]
        except Exception as exc:
            receipt["passed"] = False
            receipt["reason"] = "provider spike cleanup failed: " + str(exc)
        finally:
            if login:
                login.unlink(missing_ok=True)
            receipt["wall_s"] = time.monotonic() - started
            receipt["raw_folder"] = str(folder)
            (folder / "receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({k: v for k, v in receipt.items() if k in {"kind", "passed", "returncode", "reason", "checks", "wall_s", "raw_folder"}}))
    return 0 if receipt.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())

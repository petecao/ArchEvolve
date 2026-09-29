"""Audit tool activity from retained provider events. Updated: 2026-09-29.

The audit complements confinement; a successful audit is not a correctness claim.
Only tool inputs are treated as actions, never a provider's quoted command output.
"""

import fnmatch
import json
import re
import shlex
from pathlib import Path

from swdb import artifacts


def audit(path, kind, workspace_root, visible_files, home_root=None, login_paths=(),
          editable_files=(), network_reasons=(), guard_reasons=()):
    """Return a JSON-compatible receipt, including failures and raw-log identity."""
    path, root = Path(path), Path(workspace_root).resolve()
    visible = set(visible_files)
    directories = {"."}
    for name in visible:
        directories.update(p.as_posix() for p in Path(name).parents)
    violations, events, commands, accesses = [], 0, 0, 0
    logins = {str(Path(p).resolve()) for p in login_paths if p}
    login_names = {Path(p).name for p in logins} | {"auth.json", ".credentials.json"}

    def fail(code, detail, event):
        item = {"code": code, "reason": detail, "event": event}
        if item not in violations:
            violations.append(item)

    def file_access(name, event, *, writing=False, cwd=None):
        nonlocal accesses
        accesses += 1
        if not isinstance(name, str) or not name.strip():
            fail("invalid_file_access", "provider tool has an invalid file path", event)
            return
        # Expansion is deliberately conservative: unknown homes cannot become roots.
        if name.startswith("~") or "$" in name or "\\" in name:
            fail("external_file_access", f"provider file access outside the visible set: {name}", event)
            return
        target = (Path(cwd or root) / name).resolve()
        try:
            rel = target.relative_to(root).as_posix()
        except ValueError:
            fail("external_file_access", f"provider file access outside the workspace: {name}", event)
            return
        if rel in visible or rel in directories:
            return
        if writing and any(fnmatch.fnmatchcase(rel, p) for p in editable_files):
            return
        # Providers may make and remove synthetic tests in the build directory.
        # Any surviving source helper still fails the final workspace diff check.
        if any(part in {"build", "dist", "__pycache__", ".pytest_cache", "CMakeFiles"} for part in Path(rel).parts):
            return
        # Temporary build outputs are visible only because the provider made them.
        from swdb.provider_workspace import generated_output
        if target.exists() and generated_output(target, rel):
            return
        fail("external_file_access", f"provider file access outside the visible set: {name}", event)

    def command(value, event, cwd=None, *, depth=0):
        nonlocal commands
        if depth == 0:
            commands += 1
        if depth > 8:
            fail("unparsed_command", "provider shell command nesting cannot be audited", event)
            return
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            value = shlex.join(value)
        if not isinstance(value, str) or not value.strip():
            fail("invalid_command", "provider event has an invalid command", event)
            return
        if (any(p in value for p in logins) or any(re.search(r"(?<![\w.-])" + re.escape(n) + r"(?![\w.-])", value)
                                                  for n in login_names)
                or re.search(r"(?:\$\{?(?:CODEX_HOME|CLAUDE_CONFIG_DIR)\}?|[~/]\.codex|[~/]\.claude)", value)):
            fail("login_file_access", "provider command touches the login file or provider home", event)
        try:
            lexer = shlex.shlex(value, posix=True, punctuation_chars="();<>|&\n")
            lexer.whitespace = " \t\r"
            lexer.whitespace_split = True
            lexer.commenters = ""
            tokens = list(lexer)
        except ValueError:
            fail("unparsed_command", "provider command cannot be audited", event)
            return
        executable_names = {Path(t).name for t in tokens}
        if (executable_names & {"curl", "wget", "pip", "pip3", "conda", "nc", "ncat", "netcat", "ssh", "scp", "sftp"}
                or re.search(r"\bgit\b[^;\n]*(?:\bclone\b|\bfetch\b|\bpull\b|\bpush\b|\bsubmodule\b)", value)
                or re.search(r"\b(?:npm|npx|pnpm|yarn|cargo|uv|brew|apt|apt-get)\b[^;\n]*\b(?:install|add|update|sync)\b", value)
                or re.search(r"\b(?:https?|ftp|ssh)://|\b(?:socket|urllib|requests|httpx)\s*[.(]|/dev/(?:tcp|udp)/", value)):
            fail("network_command", "provider ran a forbidden network command", event)
        working = root
        if isinstance(cwd, str):
            file_access(cwd, event)
            working = (root / cwd).resolve()
        # A shell's command-string operand is executable input, unlike other
        # quoted arguments or retained stdout. Recursively audit only that
        # operand, preserving the cwd established by preceding commands.
        shells = {"sh", "bash", "zsh", "dash", "ksh"}
        separators = {"&&", "||", ";", "|", "&", "\n"}
        def separator(token):
            return token in separators or bool(re.fullmatch(r"(?:&&|\|\||[;|&\n])+", token))

        bodies = set()
        start, executable, command_index, prefix = True, None, 0, None
        # Command paths are checked as well as file-tool paths. Shell redirections
        # and relative traversal count as accesses; system executable paths do not.
        for index, token in enumerate(tokens):
            if index in bodies:
                continue
            if separator(token):
                start, executable, prefix = True, None, None
                continue
            if depth and (token in {"{", "}"} or token.startswith("<<")
                          or re.fullmatch(r"[();<>|&\n]+", token) and any(c in token for c in "()")
                          or "$(" in token or "`" in token):
                fail("unparsed_command", "provider shell body has unsupported dynamic syntax", event)
            if depth and start and (token in {"<", ">", ">>", "<>"}
                                    or token.isdigit() and index + 1 < len(tokens)
                                    and tokens[index + 1] in {"<", ">", ">>", "<>"}):
                fail("unparsed_command", "provider shell body has an unsupported leading redirection", event)
            assignment = start and re.fullmatch(r"[A-Za-z_]\w*=.*", token, re.S)
            if assignment:
                # Literal assignments and exit-status capture do not execute a
                # command. Their later use as a target still fails closed below.
                rhs = token.split("=", 1)[1]
                if ("$" in rhs and rhs != "$?") or "`" in rhs:
                    fail("unparsed_command", "provider shell assignment cannot be resolved", event)
                continue
            if start and token in {"env", "exec", "command"}:
                prefix = token
                continue
            if start and prefix and token.startswith("-"):
                if token != "--" and not (prefix == "env" and token == "-i"):
                    fail("unparsed_command", "provider execution prefix cannot be resolved", event)
                continue
            is_executable = start
            if start:
                executable = Path(token).name
                command_index = index
                start = False
                if executable in shells:
                    body_index = None
                    for option_index in range(index + 1, len(tokens)):
                        option = tokens[option_index]
                        if option in {"--login", "--noprofile", "--norc", "--posix"}:
                            continue
                        if (not re.fullmatch(r"-[a-zA-Z]+", option)
                                or set(option[1:]) - set("abcefhlmnprstuvxBCEHPT")):
                            break
                        if "c" in option[1:]:
                            body_index = option_index + 1
                            break
                    if body_index is None or body_index >= len(tokens) or not tokens[body_index].strip():
                        fail("unparsed_command", "provider shell command body cannot be resolved", event)
                    else:
                        bodies.add(body_index)
                        command(tokens[body_index], event, str(working), depth=depth + 1)
                elif executable in {"fish", "csh", "tcsh"} or depth and executable in {"eval", "source", ".", "if", "for", "while", "until", "case",
                                              "select", "function", "coproc"}:
                    fail("unparsed_command", "provider shell body uses unsupported delegated execution", event)
                elif "$" in token or "`" in token:
                    fail("unparsed_command", "provider command target cannot be resolved", event)
            elif depth and ("$" in token or "`" in token):
                # Status reporting may consume scalar variables as data. Do not
                # treat them as filenames, or accept them for arbitrary tools.
                scalar = re.fullmatch(r"(?:\$[A-Za-z_]\w*|\$\{[A-Za-z_]\w*\}|\$\?)", token)
                end = next((i for i in range(index + 1, len(tokens)) if separator(tokens[i])), len(tokens))
                arguments = tokens[command_index + 1:end]
                numeric_test = executable in {"test", "["} and any(
                    t in {"-eq", "-ne", "-gt", "-ge", "-lt", "-le"} for t in arguments) and not any(
                    t in {"-e", "-f", "-d", "-r", "-w", "-x", "-s", "-L", "-h"} for t in arguments)
                if not scalar or not (executable in {"printf", "echo"} or numeric_test):
                    fail("unparsed_command", "provider shell argument cannot be resolved", event)
            candidate = token.lstrip("<>")
            if index and tokens[index - 1] in {"<", ">", ">>", "<>"}:
                if candidate not in {"/dev/null", "/dev/stdout", "/dev/stderr"}:
                    file_access(candidate, event, writing=tokens[index - 1] != "<", cwd=working)
                continue
            if index and tokens[index - 1] == "cd":
                file_access(candidate, event, cwd=working)
                working = (working / candidate).resolve()
                continue
            if candidate.startswith("/"):
                if is_executable:
                    continue
                if candidate in {"/dev/null", "/dev/stdout", "/dev/stderr"}:
                    continue
                file_access(candidate, event, cwd=working)
            elif candidate == ".." or candidate.startswith(("../", "~/")) or "/../" in candidate:
                file_access(candidate, event, cwd=working)
            elif (not candidate.startswith("-") and re.fullmatch(r"[\w.+@/-]+", candidate)
                  and ("/" in candidate or Path(candidate).suffix in {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".sh", ".json", ".yaml", ".el", ".graph"})):
                file_access(candidate, event, writing=bool(index and tokens[index - 1] in {">", ">>", "-o"}), cwd=working)

    def tool(name, inputs, event):
        if not isinstance(inputs, dict):
            fail("invalid_tool_event", "provider tool inputs cannot be audited", event)
            return
        if name == "StructuredOutput":
            # Claude's schema transport is validated by the adapter as the final
            # response; it grants no filesystem, execution, or network operation.
            return
        if name in {"Bash", "bash", "shell", "exec_command", "shell_command"}:
            command(inputs.get("command", inputs.get("cmd")), event,
                    inputs.get("cwd", inputs.get("workdir")))
            return
        if name in {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Glob", "Grep",
                    "read_file", "write_file", "edit_file", "list_directory"}:
            key = next((k for k in ("file_path", "path", "notebook_path") if k in inputs), None)
            file_access(inputs.get(key) if key else ".", event, writing=name in {"Write", "Edit", "MultiEdit", "write_file", "edit_file"})
            return
        fail("forbidden_tool", f"provider used a forbidden or unknown tool: {name}", event)

    if not path.is_file():
        fail("missing_event_log", "provider event log is missing", 0)
    else:
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                fail("invalid_event_log", "provider event log contains an unparsed event", number)
                continue
            if not isinstance(row, dict):
                fail("invalid_event_log", "provider event log contains a non-object event", number)
                continue
            events += 1
            item = row.get("item")
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type == "command_execution":
                    command(item.get("command"), number, item.get("cwd"))
                elif item_type == "file_change":
                    changes = item.get("changes")
                    if not isinstance(changes, list):
                        fail("invalid_tool_event", "provider file changes cannot be audited", number)
                    else:
                        for change in changes:
                            file_access(change.get("path") if isinstance(change, dict) else None, number, writing=True)
                elif item_type not in {"agent_message", "reasoning", "todo_list", "error"}:
                    fail("forbidden_tool", f"provider used a forbidden tool: {item_type}", number)
            message = row.get("message")
            content = message.get("content", []) if isinstance(message, dict) else row.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool(block.get("name"), block.get("input"), number)
            if row.get("type") in {"tool_use", "tool_call"}:
                tool(row.get("name"), row.get("input", row.get("arguments")), number)
            # Provider assertions cannot authorize a tool's connection. Legitimate
            # API transport is identified by the guard's independent network trace.
            if row.get("type") in {"connection", "network_connection"}:
                fail("outbound_connection", "provider made an outbound connection outside its model API", number)
    for reason in network_reasons:
        fail("outbound_connection", str(reason), 0)
    for reason in guard_reasons:
        text = str(reason)
        if re.search(r"resource limit|workspace exceeds|tool command exceeds|memory limit|thread limit", text, re.I):
            code = "resource_limit"
        elif "outbound connection is outside" in text:
            code = "outbound_connection"
        else:
            code = "guard_violation"
        fail(code, text, 0)
    receipt = {"format": "swdb.provider-audit.v1", "state": "passed" if not violations else "failed",
               "passed": not violations, "events": events, "commands": commands, "file_accesses": accesses,
               "reasons": list(dict.fromkeys(v["reason"] for v in violations)), "violations": violations,
               "raw_log": {"path": str(path)}}
    if path.is_file():
        receipt["raw_log"].update(sha256=artifacts.file_hash(path), bytes=path.stat().st_size)
    return receipt

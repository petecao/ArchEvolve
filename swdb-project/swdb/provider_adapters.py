"""Rewrite CLI adapters and immutable research settings. Updated 2026-10-05 ET.

The shared runner handles processes and retention; an adapter owns argv, transport,
version discovery and final-response decoding. Fixtures can use the identical CLI
contract without being classified as model-generated research evidence.

2026-10-05 ET (code review P1; agent-decided under Yan-Ru's delegation; revisable): every
provider-call stop that is not the model's work (usage limit, capacity, guard runtime limit,
login) is an `UncountedStop` carrying its call outcome, and `classify` is the one classifier
the Extensa campaign, its synthesis calls and the ticket 58 driver share. Before, the driver
recorded a capacity stop as `usage_limit` and counted a guard runtime-limit stop as failed.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from swdb.cli import Failure

PINS = {"codex": {"model": "gpt-5.6-sol", "effort": "xhigh"},
        "claude": {"model": "claude-sonnet-5-5", "effort": "high"}}
CODEX_DISABLED_FEATURES = (
    "apps", "plugins", "remote_plugin", "memories", "multi_agent", "multi_agent_v2",
    "hooks", "image_generation", "view_image", "browser_use", "browser_use_external",
    "browser_use_full_cdp_access", "computer_use", "in_app_browser",
    "skill_search", "skill_mcp_dependency_install", "workspace_dependencies",
    "shell_snapshot", "shell_snapshot_v2", "unified_exec",
)
USAGE_LIMIT = re.compile(
    r"usage[_ -]?limit|quota[_ -]?(?:exceeded|exhausted)|"
    r"(?:hit|reached|exceeded).*?(?:usage|chatgpt).*?limit|"
    r"(?:insufficient_quota|rate_limit_exceeded)|out of (?:usage|credits)", re.I)
#: Ticket 73 (2026-10-05 ET): transient provider-side unavailability. Extensa campaign a7's calls 4 and 5
#: ended with Codex's `{"type":"error","message":"Selected model is at capacity. ..."}` and were
#: counted as failed rewrites. Like USAGE_LIMIT, this is read only from error fields and stderr.
CAPACITY = re.compile(
    r"at capacity|\boverloaded|server[_ ]is[_ ]busy|temporarily unavailable|service[_ ]unavailable|"
    r"bad gateway|gateway time-?out|(?:status|http|code)\D{0,12}(?:502|503|504|529)\b|"
    r"stream disconnected before completion", re.I)


def codex_transport_schema(schema):
    """Omit only unsupported array uniqueness on the wire, retaining local checks."""
    result = json.loads(json.dumps(schema))
    def visit(node):
        if not isinstance(node, dict):
            return
        node.pop("uniqueItems", None)
        # Map keys are property/definition names, not schema keywords. Constant,
        # enum and example data likewise must not be interpreted as schemas.
        for key in ("properties", "patternProperties", "$defs", "definitions", "dependentSchemas"):
            for child in node.get(key, {}).values():
                visit(child)
        for key in ("items", "additionalItems", "contains", "additionalProperties", "propertyNames",
                    "unevaluatedItems", "unevaluatedProperties", "not", "if", "then", "else", "contentSchema"):
            child = node.get(key)
            for item in child if isinstance(child, list) else [child]:
                visit(item)
        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            for child in node.get(key, []):
                visit(child)
    visit(result)
    return result


#: The one login pattern (P1, 2026-10-05 ET). Codex reports an invalidated or reused OAuth refresh
#: token only on stderr: 401 `token_invalidated` / `refresh_token_reused` (ticket 58, attempt a1).
#: `classify` reads it from the exception text and the call folder's stderr.
LOGIN = re.compile(r"login|not logged in|unauthori[sz]ed|authentication|credentials|token_invalidated|"
                   r"refresh_token_reused", re.I)
#: Codex takes its prompt as one argument; Linux caps one argv element at 128 KiB.
PROMPT_ARGUMENT_LIMIT = 96 * 1024


class UncountedStop(Failure):
    """A provider call that stopped for a reason outside the model's work (decision D7).

    The call is recorded with `counted: false` and is never charged as a failed rewrite.
    `outcome` is the call-outcome value (`swdb.extensa.search.CallOutcome`) every caller records.
    The four leaves below are siblings: none is a special case of another."""
    outcome = None


class ProviderUnavailable(UncountedStop):
    """The provider cannot serve the call now (usage limit or capacity). ArchEvolve mode records
    either as `provider_unavailable`, which does not consume a repair. Raise one of its leaves."""


class UsageLimit(ProviderUnavailable):
    """The account's usage limit or quota is spent; retry later."""
    outcome = "usage_limit"


class ProviderCapacity(ProviderUnavailable):
    """Ticket 73: the provider is transiently unavailable (model at capacity, overloaded, 5xx).
    Not a usage limit: an Extensa campaign backs off and retries, uncounted."""
    outcome = "provider_capacity"


class GuardInfrastructure(UncountedStop):
    """Ticket 74: the provider guard stopped the call only for its own runtime limit on the provider
    (for example Codex's startup thread burst), never for anything the model did. Not a provider
    entitlement: an Extensa campaign retries the call, uncounted."""
    outcome = "guard_infrastructure"


class LoginRequired(UncountedStop):
    """The provider login is missing, malformed, refused, or kept where a lab host forbids it
    (`swdb.provider_login.provider_home`). The operator must log in; the run pauses, uncounted."""
    outcome = "login"


def classify(exc, call_folder=None, *, detailed=True):
    """The call outcome (`swdb.extensa.search.CallOutcome`) of one provider call.

    P1 (2026-10-05 ET): the one classifier for every provider call. None means the call completed.
    An `UncountedStop` names its own outcome. Any other failure is a login failure when the login
    pattern matches its text or the call folder's `stderr.txt`. With `detailed`, the rest is a
    timeout, malformed output, a guard or audit refusal, or a plain failure, as the Extensa campaign
    classified its calls since ticket 52; without it (a synthesis call, whose failure can also be the
    synthesized entry's own validation or certification), the rest is a plain failure.
    """
    from swdb.extensa.search import CallOutcome
    if exc is None:
        return CallOutcome.COMPLETED
    if isinstance(exc, UncountedStop) and exc.outcome:
        return CallOutcome(exc.outcome)
    text = str(exc)
    stderr = Path(call_folder) / "stderr.txt" if call_folder is not None else None
    if stderr is not None and stderr.is_file():
        text += "\n" + stderr.read_text(errors="replace")
    if LOGIN.search(text):
        return CallOutcome.LOGIN
    if not detailed:
        return CallOutcome.FAILED
    if "timed out" in text or "timeout" in text:
        return CallOutcome.TIMEOUT
    if "structured" in text or "JSON" in text:
        return CallOutcome.MALFORMED_OUTPUT
    if "guard" in text or "audit" in text:
        return CallOutcome.GUARD_REFUSED
    return CallOutcome.FAILED


def events(path):
    for line in Path(path).read_text(errors="replace").splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            yield value


def check_usage(folder):
    # Limit errors may arrive on stderr, in a failed event or in a nonzero exit.
    # Scan only error fields/events: source code or a normal response may quote the
    # words "usage limit" without indicating an actual entitlement failure.
    pieces = [(Path(folder) / "stderr.txt").read_text(errors="replace")]
    for event in events(Path(folder) / "stdout.txt"):
        if event.get("is_error") or event.get("type") in {"error", "thread.failed", "turn.failed"}:
            pieces.append(json.dumps(event))
        elif event.get("error"):
            pieces.append(json.dumps(event["error"]))
    text = "\n".join(pieces)
    if USAGE_LIMIT.search(text):
        raise UsageLimit("rewrite provider unavailable: usage limit reached; retry later")
    match = CAPACITY.search(text)
    if match:
        raise ProviderCapacity(f"rewrite provider temporarily unavailable ({match.group(0)}); retry later")


class Adapter:
    kind = "external_fixture"
    prompt_argument = False
    audit_events = False

    def launch_command(self, config):
        return list(config["command"])

    def command(self, config, prompt, folder, schema):
        return self.launch_command(config)

    def streaming(self, config):
        return False

    def version(self, config, env=None):
        return None

    def schema(self, config, schema):
        return schema

    def extract(self, config, folder):
        return json.loads((Path(folder) / "stdout.txt").read_text())

    def normalize(self, config, response):
        return response


class ClaudeAdapter(Adapter):
    kind = "claude"
    audit_events = True

    def streaming(self, config):
        return config.get("workspace", True) or config.get("output_format") == "stream-json"

    def command(self, config, prompt, folder, schema):
        output = ["stream-json", "--verbose", "--include-partial-messages"] if self.streaming(config) else ["json"]
        tools = "Read,Glob,Grep,Edit,Write,Bash" if config.get("workspace", True) else ""
        argv = [*config["command"], "-p", "--safe-mode", "--tools", tools,
                "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--no-session-persistence", "--output-format", *output,
                "--json-schema", json.dumps(schema), "--max-budget-usd", str(config["budget_usd"]),
                "--model", PINS[self.kind]["model"], "--effort", PINS[self.kind]["effort"]]
        if config.get("workspace", True):
            argv += ["--permission-mode", "bypassPermissions", "--disable-slash-commands",
                     "--setting-sources", ""]
        return argv

    def version(self, config, env=None):
        result = subprocess.run([*config["command"], "--version"], capture_output=True,
                                text=True, timeout=10, env=env)
        if result.returncode or not result.stdout.strip():
            raise Failure("could not capture rewrite provider CLI version")
        return result.stdout.strip()

    def extract(self, config, folder):
        if self.streaming(config):
            results = [e for e in events(Path(folder) / "stdout.txt") if e.get("type") == "result"]
            if not results:
                raise Failure("rewrite provider stream ended without a result event")
            response = results[-1]
        else:
            response = super().extract(config, folder)
        if response.get("is_error"):
            raise Failure("Claude returned an error; see retained provider output")
        return response.get("structured_output") or json.loads(response.get("result", "{}"))


class CodexAdapter(Adapter):
    kind = "codex"
    prompt_argument = True
    audit_events = True

    def streaming(self, config):
        return True

    def launch_command(self, config):
        """Skip only the official Linux npm wrapper's persistent Node parent."""
        command = list(config["command"])
        if config.get("kind") != self.kind or sys.platform != "linux" or len(command) != 1:
            return command
        targets = {"x86_64": ("codex-linux-x64", "x86_64-unknown-linux-musl"),
                   "aarch64": ("codex-linux-arm64", "aarch64-unknown-linux-musl")}
        target = targets.get(platform.machine())
        if target is None:
            return command
        try:
            wrapper = Path(shutil.which(command[0]) or command[0]).resolve(strict=True)
            if wrapper.parts[-4:] != ("@openai", "codex", "bin", "codex.js"):
                return command
            package = wrapper.parent.parent
            parent_metadata = json.loads((package / "package.json").read_text())
            if not isinstance(parent_metadata, dict) or parent_metadata.get("name") != "@openai/codex":
                return command
            name, triple = target
            # The installed wrapper resolves the nearest platform package with
            # Node's package lookup, then falls back to its own vendor directory.
            for parent in (wrapper.parent, *wrapper.parent.parents):
                if parent.name == "node_modules":
                    continue
                root = parent / "node_modules" / "@openai" / name
                manifest = root / "package.json"
                if manifest.is_file():
                    metadata = json.loads(manifest.read_text())
                    if not isinstance(metadata, dict):
                        return command
                    if metadata.get("name") != "@openai/" + name:
                        # npm aliases retain the underlying @openai/codex name.
                        # Bind that alias to the wrapper's exact dependency and
                        # its declared Linux architecture before selecting it.
                        cpu = "x64" if name.endswith("-x64") else "arm64"
                        version = parent_metadata.get("version")
                        expected = str(version) + "-linux-" + cpu
                        dependencies = parent_metadata.get("optionalDependencies")
                        if (not isinstance(version, str) or not version
                                or not isinstance(dependencies, dict)
                                or dependencies.get("@openai/" + name) != "npm:@openai/codex@" + expected
                                or metadata.get("name") != "@openai/codex"
                                or metadata.get("version") != expected
                                or metadata.get("os") != ["linux"] or metadata.get("cpu") != [cpu]):
                            return command
                    native = root / "vendor" / triple / "bin" / "codex"
                    break
            else:
                native = package / "vendor" / triple / "bin" / "codex"
            if native.is_file() and os.access(native, os.X_OK):
                return [str(native.resolve())]
        except (OSError, ValueError):
            pass
        return command

    def schema(self, config, schema):
        if not config.get("workspace", True) and config.get("edit_format") == "full_files":
            schema = json.loads(json.dumps(schema))
            schema["properties"]["files"] = {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["path", "content"],
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}}
        return schema

    def command(self, config, prompt, folder, schema):
        io_dir = Path(folder).resolve() / "provider-home"
        if not io_dir.is_dir():
            io_dir = Path(folder).resolve()
        schema_path = io_dir / "output-schema.json"
        schema_path.write_text(json.dumps(codex_transport_schema(schema)))
        # Linux caps a single argv element at 128 KiB; fail clearly rather than
        # silently truncate a legacy prompt containing full source bodies.
        if len(prompt.encode()) > PROMPT_ARGUMENT_LIMIT:
            raise Failure(f"Codex provider prompt exceeds the {PROMPT_ARGUMENT_LIMIT // 1024} KiB argv limit; "
                          "use a compact workspace request")
        if config.get("workspace", True):
            prompt = ("Use direct local shell and edit tool calls. Do not use the JavaScript exec or wait "
                      "tools: their additional runtime exceeds this session's 16-thread budget. " + prompt)
        # The guard supplies an empty read-only state directory. Codex 0.153
        # initializes process SQLite pools even for --ephemeral sessions; its
        # nonfatal unavailable-state fallback avoids those persistent workers.
        sqlite_home = Path(folder).resolve() / "guard" / "ephemeral-state"
        argv = [*self.launch_command(config), "exec", "--model", PINS[self.kind]["model"],
                "-c", "model_reasoning_effort=" + json.dumps(PINS[self.kind]["effort"]), "-c", 'web_search="disabled"',
                "-c", "sqlite_home=" + json.dumps(str(sqlite_home)),
                "-c", "analytics.enabled=false", "-c", 'otel.exporter="none"',
                "-c", 'otel.trace_exporter="none"', "-c", 'otel.metrics_exporter="none"',
                "-c", "skills.bundled.enabled=false", "-c", "skills.include_instructions=false",
                "-c", 'features.code_mode.direct_only_tool_namespaces=["functions"]',
                "-c", "project_doc_max_bytes=0", "--ignore-user-config", "--ignore-rules",
                "--ephemeral", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
                "--json", "--output-schema", str(schema_path), "--output-last-message",
                str(io_dir / "final-message.json")]
        for feature in CODEX_DISABLED_FEATURES:
            argv += ["--disable", feature]
        if not config.get("workspace", True):
            argv += ["--disable", "shell_tool", "--disable", "unified_exec"]
            prompt = "Do not call tools in prompt-only mode; return only the requested JSON. " + prompt
            if config.get("edit_format") == "full_files":
                prompt = ("CODEX STRICT OUTPUT CONTRACT: files is an array of objects containing only "
                          "path and content strings, each containing the complete new source text. "
                          "Use [] for no changed files. This takes precedence over files-map instructions. " + prompt)
        return [*argv, prompt]

    def version(self, config, env=None):
        return ClaudeAdapter.version(self, {**config, "command": self.launch_command(config)}, env)

    def extract(self, config, folder):
        rows = list(events(Path(folder) / "stdout.txt"))
        if any(row.get("type") in {"turn.failed", "thread.failed", "error"} for row in rows):
            raise Failure("Codex returned an error; see retained provider output")
        io_dir = Path(folder) / "provider-home"
        final = (io_dir if io_dir.is_dir() else Path(folder)) / "final-message.json"
        if not final.is_file():
            raise Failure("Codex ended without a retained final message")
        return json.loads(final.read_text())

    def normalize(self, config, response):
        if not config.get("workspace", True) and config.get("edit_format") == "full_files":
            files = response["files"]
            if len({item["path"] for item in files}) != len(files):
                raise Failure("Codex full_files contains duplicate paths")
            return {**response, "files": {item["path"]: item["content"] for item in files}}
        return response


ADAPTERS = {adapter.kind: adapter for adapter in (Adapter(), ClaudeAdapter(), CodexAdapter())}


def get(config):
    return ADAPTERS[config.get("emulates", config["kind"])]


def identity(config):
    kind = config.get("emulates", config["kind"])
    return {"resolved_kind": kind, **PINS.get(kind, {"model": None, "effort": None})}


def classification(config):
    return "contract_fixture" if config["kind"] == "external_fixture" else "rewrite_provider"

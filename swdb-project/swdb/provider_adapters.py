"""Rewrite CLI adapters and immutable research settings. Updated 2026-09-29 ET.

The shared runner handles processes and retention; an adapter owns argv, transport,
version discovery and final-response decoding. Fixtures can use the identical CLI
contract without being classified as model-generated research evidence.
"""
import json
import re
import subprocess
from pathlib import Path

from swdb.cli import Failure

PINS = {"codex": {"model": "gpt-5.6-sol", "effort": "xhigh"},
        "claude": {"model": "claude-sonnet-5-5", "effort": "high"}}
CODEX_DISABLED_FEATURES = (
    "apps", "plugins", "remote_plugin", "memories", "multi_agent", "multi_agent_v2",
    "hooks", "image_generation", "view_image", "browser_use", "browser_use_external",
    "browser_use_full_cdp_access", "computer_use", "in_app_browser", "code_mode_host",
    "skill_search", "skill_mcp_dependency_install", "workspace_dependencies",
)
USAGE_LIMIT = re.compile(
    r"usage[_ -]?limit|quota[_ -]?(?:exceeded|exhausted)|"
    r"(?:hit|reached|exceeded).*?(?:usage|chatgpt).*?limit|"
    r"(?:insufficient_quota|rate_limit_exceeded)|out of (?:usage|credits)", re.I)


class ProviderUnavailable(Failure):
    """A provider entitlement is unavailable; this is not a failed rewrite."""


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
    if USAGE_LIMIT.search("\n".join(pieces)):
        raise ProviderUnavailable("rewrite provider unavailable: usage limit reached; retry later")


class Adapter:
    kind = "external_fixture"
    prompt_argument = False
    audit_events = False

    def command(self, config, prompt, folder, schema):
        return list(config["command"])

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
        schema_path.write_text(json.dumps(schema))
        # Linux caps a single argv element at 128 KiB; fail clearly rather than
        # silently truncate a legacy prompt containing full source bodies.
        if len(prompt.encode()) > 96 * 1024:
            raise Failure("Codex prompt-only input exceeds 96 KiB argv limit; use workspace mode")
        argv = [*config["command"], "exec", "--model", PINS[self.kind]["model"],
                "-c", 'model_reasoning_effort="xhigh"', "-c", 'web_search="disabled"',
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
        return ClaudeAdapter.version(self, config, env)

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

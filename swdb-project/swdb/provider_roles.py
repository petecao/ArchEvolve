"""Role-specific inputs over the shared provider process, guard and audit.

Updated: 2026-10-03. Inputs are built by trusted SWDB callers, never copied by
walking a repository. Each file is explicit; real invocations require mbit10.
"""

import copy
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from swdb import artifacts, provider_adapters, provider_audit, provider_guard, provider_workspace, rewrite
from swdb.cli import Failure

FORBIDDEN_KEYS = {"evaluator", "verification", "correctness_check", "protections",
                  "workloads", "workload", "candidates", "candidate", "input_args",
                  "canonical_path", "command", "raw_artifact", "raw_artifacts", "artifact"}
FORBIDDEN_SOURCE = re.compile(r"\b(?:TDStepMAA|DOBFSMAA|TDStepMAA2|BCMAA)\b")
FILE_SCHEMA = {"type": "object", "additionalProperties": False,
               "required": ["path", "content"], "properties": {
                   "path": {"type": "string"}, "content": {"type": "string"}}}


@dataclass(frozen=True)
class Role:
    name: str
    output_schema: dict
    read_only: bool = True

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", self.name):
            raise Failure("agent role needs a canonical name")
        Draft202012Validator.check_schema(self.output_schema)


ROLES = {
    "rewriting": Role("rewriting", provider_workspace.FINAL_SCHEMA, read_only=False),
    "independent_test_generation": Role("independent_test_generation", {
        "type": "object", "additionalProperties": False, "required": ["tests", "unresolved"],
        "properties": {"tests": {"type": "array", "items": FILE_SCHEMA},
                       "unresolved": {"type": "array", "items": {"type": "string"}}}}),
    "synthesis": Role("synthesis", {
        "type": "object", "additionalProperties": False, "required": ["entry", "files", "unresolved"],
        "properties": {"entry": {"type": "object"}, "files": {"type": "array", "items": FILE_SCHEMA},
                       "unresolved": {"type": "array", "items": {"type": "string"}}}}),
}


def project(value):
    """A context projection never forwards evaluator identities or run paths."""
    if isinstance(value, dict):
        return {k: project(v) for k, v in value.items() if k not in FORBIDDEN_KEYS}
    if isinstance(value, list):
        return [project(v) for v in value]
    return copy.deepcopy(value)


def _inputs(files):
    if not isinstance(files, dict) or not files:
        raise Failure("agent role workspace input must be a nonempty explicit files mapping")
    result = {}
    total = 0
    for name, text in files.items():
        provider_workspace._safe_name(name)
        parts = Path(name).parts
        if (any(p in provider_workspace.HIDDEN_DIRS for p in parts)
                or Path(name).name in provider_workspace.INSTRUCTION_FILES
                or Path(name).suffix.lower() in {".csr", ".graph", ".sg", ".bin", ".so", ".dylib"}):
            raise Failure("agent role input names hidden evaluator, workload or candidate material: " + name)
        if not isinstance(text, str) or "\0" in text or FORBIDDEN_SOURCE.search(text):
            raise Failure("agent role inputs must be text without authors' accelerated code: " + name)
        if Path(name).suffix == ".json":
            try:
                parsed = json.loads(text)
            except ValueError:
                raise Failure("agent role JSON input is malformed: " + name) from None
            if project(parsed) != parsed:
                raise Failure("agent role JSON input exposes evaluator or workload fields: " + name)
        total += len(text.encode())
        if total > rewrite.JSON_OUTPUT_LIMIT:
            raise Failure("agent role workspace inputs exceed 10 MiB")
        result[name] = text
    return result


def prepare(role, files, folder, config):
    files = _inputs(files)
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    root, home = folder / "workspace", folder / "provider-home"
    root.mkdir(); home.mkdir(mode=0o700)
    workspace = provider_workspace.Workspace(root, home, folder, root)
    for name, content in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        workspace.visible[name] = artifacts.file_hash(target)
    kind = config.get("emulates", config["kind"])
    login_name = "auth.json" if kind == "codex" else ".credentials.json"
    workspace.login_path = home / login_name
    try:
        if config["kind"] == "external_fixture":
            workspace.login_path.write_text('{"fixture":true}\n')
        else:
            if provider_guard.abi() < 4:
                raise Failure("SWDB provider guard requires Linux Landlock ABI >= 4")
            original = (Path(os.environ.get("CODEX_HOME", str(Path.home()/".codex"))) / login_name
                        if kind == "codex" else
                        Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home()/".claude"))) / login_name)
            if original.is_symlink() or not original.is_file():
                raise Failure("agent role provider login file is unavailable")
            shutil.copyfile(original, workspace.login_path)
        workspace.login_path.chmod(0o600)
        workspace.metadata = {"format": "swdb.provider-role-workspace.v1", "role": role.name,
            "root": str(root), "home": str(home), "read_only": role.read_only,
            "source_files": [], "visible_files": sorted(files), "immutable_files": sorted(files),
            "input_sha256s": workspace.visible.copy(),
            "output_schema_sha256": artifacts.digest(role.output_schema), "login_copy_deleted": False,
            "dropped_build_outputs": []}
        (folder/"workspace.json").write_text(json.dumps(workspace.metadata, indent=2))
        return workspace
    except BaseException:
        workspace.cleanup()
        raise


def run(role, files, prompt, config, folder, *, remaining_s=None):
    """Run a named role with the rewrite launcher's pins, output checks and audit.

    Real lane refusal precedes credentials and workspace materialization. The
    input files are immutable; results are structured output. Synthetic build
    products are allowed by the existing guard, then excluded from the result.
    """
    if not isinstance(role, Role):
        role = ROLES.get(role)
    if role is None:
        raise Failure("unknown agent role")
    if not role.read_only:
        raise Failure("rewriting requires its proposal/source workspace input builder")
    if not config.get("workspace", True):
        raise Failure("agent roles require guarded workspace mode")
    lane = None
    if config["kind"] != "external_fixture":
        try:
            lane = provider_guard._lane()
        except provider_guard.GuardError as error:
            raise Failure(str(error)) from None
    workspace = prepare(role, files, folder, config)
    response, metadata, error, context = None, {}, None, None
    try:
        context = provider_guard.context(config, workspace.root, workspace.home, workspace.folder,
            login_path=workspace.login_path, fixture=config["kind"] == "external_fixture")
        context.update(schema=role.output_schema, cleanup=workspace.cleanup)
        instructions = (f"Agent role: {role.name}. Read only the explicit files in this workspace. "
                        "Do not edit input files or run profiling collectors. Return the requested JSON.\n" + prompt)
        response, metadata = rewrite.interpret(config, instructions, workspace.folder,
                                              remaining_s=remaining_s, run_context=context)
        provider_workspace.collect_diff(workspace, [])
    except BaseException as exc:
        error = exc
    finally:
        workspace.cleanup()
        receipt = workspace.folder / "provider.json"
        if receipt.is_file():
            metadata = json.loads(receipt.read_text())
        metadata.update(role=role.name, lane=lane, workspace=True, workspace_manifest=workspace.metadata,
                        output_schema_sha256=artifacts.digest(role.output_schema))
        if provider_adapters.get(config).audit_events:
            audit = provider_audit.audit(workspace.folder/"stdout.txt", config.get("emulates", config["kind"]),
                workspace.root, workspace.visible, workspace.home, (workspace.login_path,), [],
                guard_reasons=(metadata.get("guard_result") or {}).get("reasons", []), completed=error is None)
        else:
            audit = {"state": "fixture", "passed": True, "reasons": [],
                     "classification": "contract_fixture", "event_audit": "not applicable to plain JSON fixture"}
        metadata["audit"] = audit
        (workspace.folder/"audit.json").write_text(json.dumps(audit, indent=2))
        receipt.write_text(json.dumps(metadata, indent=2))
        (workspace.folder/"workspace.json").write_text(json.dumps(workspace.metadata, indent=2))
    if not audit["passed"] and ((workspace.folder/"stdout.txt").is_file() or error is None):
        raise Failure("provider role audit failed: " + "; ".join(audit["reasons"]))
    if error is not None:
        raise error
    return response, metadata


def rewriting(config, request, source, package, store, folder, **kwargs):
    """Existing rewriting input builder and output contract remain authoritative."""
    if config["kind"] != "external_fixture":
        try:
            provider_guard._lane()
        except provider_guard.GuardError as error:
            raise Failure(str(error)) from None
    metadata = {}
    schema = provider_workspace.FINAL_SCHEMA if config.get("workspace", True) else rewrite.output_schema(config)
    schema = provider_adapters.get(config).schema(config, schema)
    receipt = Path(folder)/"provider.json"
    try:
        response, metadata = rewrite.call(config, request, source, package, store, folder, **kwargs)
    finally:
        if receipt.is_file():
            metadata = json.loads(receipt.read_text())
        if metadata:
            metadata.update(role="rewriting", output_schema_sha256=artifacts.digest(schema))
            receipt.write_text(json.dumps(metadata, indent=2))
    return response, metadata

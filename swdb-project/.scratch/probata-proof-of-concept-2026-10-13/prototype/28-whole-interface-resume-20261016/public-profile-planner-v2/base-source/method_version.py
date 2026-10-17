"""Method-version files: `library/methods/<version>.yaml`, one reviewed file per method version.

Created: 2026-10-14 ET (Probata proof of concept ticket 11). Design: formal-verification map 26
item 3, S8, 25 item 2, 13 item 11, 15 item 9. Format: docs/reference/format-v0.4-method-version.md.

- A method-version file lists everything a candidate artifact's proofs use apart from the rewrite
  contract, the candidate artifact and the proof semantics. Its shape is
  `schemas/library/method_version.schema.json`; `swdb validate` checks every file.
- Every proof record pins one by ID and file sha256 (`pin`, `pin_problem`). Changing any byte makes
  a new method version (glossary): the fix for an edited file is a new file, never an edited record.
- Old files stay, so old pins still resolve.
- Lifecycle (`status`; fix-21, 2026-10-14 ET, main-session decision recorded in ticket 21): the current
  method version is the frozen one with the highest `sequence` (`current`). A draft is used only when
  named (`named`, `select`: `swdb prove --method-version <id>`, a campaign file's `method_version`); it
  never becomes current. A record under a draft keeps counting while the draft is newer than the
  current frozen version (`counting`). The freeze (ticket 59) is a new file with `status: frozen`.
- A draft may mark a section `{not_yet_built: <sentence>}`; a frozen file may not.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from swdb import artifacts, paths, yamlio
from swdb.problems import Problem

FOLDER = "methods"
SCHEMA = paths.HOME / "schemas" / "library" / "method_version.schema.json"
METADATA = ("id", "kind", "sequence", "status", "created", "evidence_kind", "description")
_REQUIRED = re.compile(r"^'(.+)' is a required property$")
_VALIDATOR = []


@dataclass(frozen=True)
class MethodVersion:
    id: str
    path: Path
    sha256: str
    data: dict


def _validator():
    if not _VALIDATOR:
        schema = json.loads(SCHEMA.read_text())
        Draft202012Validator.check_schema(schema)
        _VALIDATOR.append(Draft202012Validator(schema))
    return _VALIDATOR[0]


def sections():
    """The section names every method-version file holds (the schema's required keys, metadata aside)."""
    return [name for name in _validator().schema["required"] if name not in METADATA]


def is_not_yet_built(value):
    """True for a section marker {not_yet_built: <sentence>} (drafts only)."""
    return (isinstance(value, dict) and set(value) == {"not_yet_built"}
            and isinstance(value["not_yet_built"], str) and bool(value["not_yet_built"].strip()))


def load(library_root):
    """({id: MethodVersion}, [Problem]) for every file in <library>/methods/."""
    found, problems = {}, []
    folder = Path(library_root) / FOLDER
    for path in sorted(folder.glob("*.yaml")) if folder.is_dir() else []:
        try:
            data = yamlio.load(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            problems.append(Problem(str(path), "-", f"not valid YAML: {exc}"))
            continue
        if not isinstance(data, dict) or not isinstance(data.get("id"), str):
            problems.append(Problem(str(path), "id", "a method-version file is a mapping with a text ID"))
            continue
        if data["id"] in found:
            problems.append(Problem(str(path), "id", f"duplicate method-version ID {data['id']!r}"))
            continue
        found[data["id"]] = MethodVersion(data["id"], path, artifacts.file_hash(path), data)
    return found, problems


def current(library_root):
    """The current method version: the frozen one with the highest sequence, or None (a draft never is)."""
    versions, _problems = load(library_root)
    ranked = [v for v in versions.values()
              if v.data.get("status") == "frozen" and isinstance(v.data.get("sequence"), int)]
    return max(ranked, key=lambda v: v.data["sequence"]) if ranked else None


def named(library_root, ident):
    """The method version with this ID, draft or frozen, or None when no file holds it."""
    versions, _problems = load(library_root)
    return versions.get(ident)


def select(library_root, ident=None):
    """The method version a job runs under: the one named by `ident` (draft or frozen), else the current one.

    Raises LookupError with the reason when the named one has no file, or when none is named and no
    frozen one exists."""
    folder = Path(library_root) / FOLDER
    if ident is not None:
        found = named(library_root, ident)
        if found is None:
            raise LookupError(f"no method-version file {ident!r} in {folder}")
        return found
    found = current(library_root)
    if found is None:
        drafts = sorted(load(library_root)[0])
        named_only = (f"; a draft ({', '.join(drafts)}) is used only when named (--method-version <id>, or the "
                      "campaign file's method_version)") if drafts else ""
        raise LookupError(f"no frozen method-version file in {folder}{named_only}")
    return found


def counting(library_root):
    """{ID: file sha256} of the method versions whose proof records keep counting (ticket 10's level rule):
    the current frozen version, and each draft newer than it (pinned by name and not yet superseded)."""
    versions, _problems = load(library_root)
    now = current(library_root)
    found = {now.id: now.sha256} if now else {}
    for version in versions.values():
        sequence = version.data.get("sequence")
        if (version.data.get("status") == "draft" and isinstance(sequence, int)
                and (now is None or sequence > now.data["sequence"])):
            found[version.id] = version.sha256
    return found


def pin(version):
    """The proof-record pin of a method version: its ID and file sha256."""
    return {"id": version.id, "sha256": version.sha256}


def pin_problem(value, library_root):
    """Why a proof record's method_version pin does not resolve, or None.

    A {not_applicable} pin is accepted: records written before ticket 11 carry it (records never
    change, ADR 0016); `swdb prove` writes a real pin from ticket 11 on."""
    if not isinstance(value, dict) or "not_applicable" in value:
        return None
    versions, _problems = load(library_root)
    found = versions.get(value.get("id"))
    if found is None:
        return f"no method-version file {value.get('id')!r} in {Path(library_root) / FOLDER}"
    if found.sha256 != value.get("sha256"):
        return (f"the pinned sha256 does not match {found.path.name} (a method-version file is never edited "
                "in place: a change is a new method version)")
    return None


def validate(library_root):
    """Every problem with the method-version files of this library."""
    versions, problems = load(library_root)
    sequences = {}
    for version in versions.values():
        problems.extend(_file_problems(version))
        sequence = version.data.get("sequence")
        if version.data.get("status") != "frozen":
            continue                  # only frozen versions are ordered (`current`); a draft is used by name
        if isinstance(sequence, int) and sequence in sequences:
            problems.append(Problem(str(version.path), "sequence", f"sequence {sequence} is also used by {sequences[sequence]}"))
        sequences.setdefault(sequence, version.id)
    return problems


def _file_problems(version):
    data, where = version.data, str(version.path)
    found = []
    if version.id != f"method.{version.path.stem}":
        found.append(Problem(where, "id", f"the ID must be method.{version.path.stem} (the file name)"))
    unbuilt = {name for name in sections() if is_not_yet_built(data.get(name))}
    if unbuilt and data.get("status") != "draft":
        found += [Problem(where, name, "only a draft method version may mark a section not_yet_built")
                  for name in sorted(unbuilt)]
    # The schema checks every section except the marked ones, whose marker is the whole content.
    shown = {name: value for name, value in data.items() if name not in unbuilt}
    for problem in _validator().iter_errors(shown):
        required = _REQUIRED.match(problem.message)
        if required and not problem.path and required.group(1) in unbuilt:
            continue
        if required:
            field = ".".join([*map(str, problem.path), required.group(1)])
            reason = (problem.schema.get("x-required-reasons", {}).get(required.group(1))
                      or "required section is missing")
        else:
            field = ".".join(map(str, problem.path)) or "-"
            reason = problem.schema.get("x-reason") or problem.message
        found.append(Problem(where, field, reason))
    return found

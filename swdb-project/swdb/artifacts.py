"""Content-addressed source artifacts and evaluator-owned edit protections.

Metadata is stored through the normal record writer; these files live outside Git.
"""

import hashlib
import json
import os
import re
import shutil
from pathlib import Path, PurePosixPath

from swdb import paths
from swdb.cli import Failure

_IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist"}
_GENERATED = {".o", ".a", ".so", ".dylib", ".pyc"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative_path(text):
    p = PurePosixPath(text)
    if not text or p.is_absolute() or any(x in {"..", ".git"} for x in p.parts) or "\\" in text:
        raise Failure(f"unsafe artifact path: {text!r}")
    return p.as_posix()


def external_directory(path):
    path = Path(path).resolve()
    if path == paths.HOME or paths.HOME in path.parents:
        raise Failure("raw artifacts must be outside the repository")
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise Failure(f"source artifact unavailable: {root}")
    files = []
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            p = Path(current) / name
            if p.is_symlink():
                raise Failure(f"source snapshots do not admit symlinks: {p.relative_to(root)}")
        dirs[:] = sorted(d for d in dirs if d not in _IGNORED_DIRS)
        for name in sorted(names):
            p = Path(current) / name
            if p.suffix in _GENERATED or name == ".swdb.lock":
                continue
            if not p.is_file():
                raise Failure(f"source artifact contains a nonregular file: {p}")
            files.append({"path": p.relative_to(root).as_posix(), "sha256": file_hash(p),
                          "bytes": p.stat().st_size, "executable": bool(p.stat().st_mode & 0o111)})
    return sorted(files, key=lambda f: f["path"])


def identify(root):
    files = manifest(root)
    return {"path": str(Path(root).resolve()), "sha256": digest(files), "files": files}


def verify(artifact):
    current = identify(artifact["path"])
    if current["sha256"] != artifact["sha256"] or current["files"] != artifact["files"]:
        raise Failure("artifact content differs from its recorded source identity")
    return Path(current["path"])


def copy_snapshot(root, destination):
    files = manifest(root)
    if not files:
        raise Failure("source snapshot has no files")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for item in files:
        rel = item["path"]
        out = destination / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(root) / rel, out)
    result = identify(destination)
    if result["sha256"] != digest(files):
        raise Failure("source changed while materializing the snapshot")
    return result


def source_root(store, impl):
    app = store.application_of(impl)
    if not app or not app["source"].get("local_path"):
        raise Failure("implementation has no available application source snapshot")
    root = (paths.HOME / app["source"]["local_path"]).resolve()
    for code in impl["code"]:
        if code["root"] == "records":
            # Derived implementations need a complete application context, not a lone file.
            raise Failure("records-root source requires an application-backed snapshot before rewriting")
        entry = root / relative_path(code["path"])
        if not entry.is_file():
            raise Failure(f"implementation source is unavailable: {entry}")
        if code.get("sha256") and file_hash(entry) != code["sha256"]:
            raise Failure("implementation source hash differs from its authoritative record")
    return root


def protections(root, context):
    """Capture canonical verifier text and known harness/ROI controls before editing."""
    root = Path(root)
    guards = []
    verifier = (context.get("evaluator") or {}).get("verifier") or {}
    ref = verifier.get("code") or {}
    if ref.get("root") == "application":
        path = relative_path(ref["path"])
        text = (root / path).read_text()
        lines = ref.get("lines")
        fragment = "".join(text.splitlines(keepends=True)[lines[0]-1:lines[1]]) if lines else text
        if not fragment.strip():
            raise Failure("evaluator verifier source protection is empty")
        guards.append({"path": path, "kind": "verifier", "text": fragment})
    for f in manifest(root):
        path = f["path"]
        if Path(path).name in {"benchmark.h", "timer.h", "command_line.h"}:
            guards.append({"path": path, "kind": "file", "sha256": f["sha256"]})
        if Path(path).suffix in {".cc", ".cpp", ".h", ".hpp"}:
            text = (root / path).read_text(errors="replace")
            calls = re.findall(r"\bm5_(?:reset_stats|dump_stats|work_begin|work_end|exit)\s*\([^;]*\)\s*;", text)
            if calls:
                guards.append({"path": path, "kind": "roi_calls", "calls": calls})
    return guards


def check_protections(root, guards):
    for guard in guards:
        path = Path(root) / guard["path"]
        if not path.is_file():
            raise Failure(f"protected evaluator input removed: {guard['path']}")
        if guard["kind"] == "file":
            valid = file_hash(path) == guard["sha256"]
        else:
            text = path.read_text(errors="replace")
            if guard["kind"] == "verifier":
                valid = text.count(guard["text"]) == 1
            else:
                calls = re.findall(r"\bm5_(?:reset_stats|dump_stats|work_begin|work_end|exit)\s*\([^;]*\)\s*;", text)
                valid = calls == guard["calls"]
        if not valid:
            raise Failure(f"protected evaluator/ROI input changed: {guard['path']} ({guard['kind']})")

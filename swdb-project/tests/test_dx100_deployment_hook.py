"""Real Git-worktree fixtures, Updated 2026-10-08 ET; no actual deployment evidence."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts/deployment/dx100-binding/post-checkout"
CANDIDATE = "typed-library-bfs-gem5-20261003-a2.baseline"
SNAPSHOT = "bfs-dx100-compile-20260925-a1.source"
RECORD_PATHS = {
    "candidate": f"records/candidates/{CANDIDATE}.yaml",
    "snapshot": f"records/source_snapshots/{SNAPSHOT}.yaml",
    "implementation": "records/implementations/dx100-bfs-scalar.yaml",
    "application": "records/applications/dx100-gapbs.yaml",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(path):
    st = path.lstat()
    return {"dev": st.st_dev, "ino": st.st_ino, "mode": st.st_mode,
            "uid": st.st_uid, "gid": st.st_gid, "nlink": st.st_nlink,
            "size": st.st_size, "mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns}


def identity(path):
    return {key: stamp(path)[key] for key in ("dev", "ino", "mode", "uid", "gid")}


def run_git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], env=env,
                          capture_output=True, text=True, timeout=20)


@pytest.fixture
def deployment(tmp_path):
    base = tmp_path.resolve() / "private-base"
    base.mkdir(mode=0o700)
    repo = base / "repository"
    repo.mkdir()
    target = base / "protected-baseline"
    target.mkdir()
    files = []
    for number in range(53):
        rel = "benchmarks/gapbs/src/bfs.cc" if number == 0 else f"fixture/file-{number:02}.txt"
        file = target / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        raw = f"synthetic independent original file {number}\n".encode()
        file.write_bytes(raw)
        files.append({"path": rel, "sha256": sha(raw), "bytes": len(raw), "executable": False})
    files.sort(key=lambda row: row["path"])
    artifact = {"path": str(target), "files": files,
                "sha256": sha(json.dumps(files, sort_keys=True, separators=(",", ":")).encode())}
    context = {"application": "dx100-gapbs", "function": "DOBFS", "source": {"commit": "a" * 40}}
    records = {
        "candidate": {"kind": "candidate", "id": CANDIDATE, "artifact_role": "source_baseline",
                      "implementation": "dx100-bfs-scalar", "source_snapshot": SNAPSHOT,
                      "artifact": artifact, "context": context},
        "snapshot": {"kind": "source_snapshot", "id": SNAPSHOT, "implementation": "dx100-bfs-scalar",
                     "artifact": artifact, "context": context},
        "implementation": {"kind": "implementation", "id": "dx100-bfs-scalar", "application": "dx100-gapbs",
                           "function": "DOBFS", "code": [{"root": "application", "path": files[0]["path"],
                                                             "sha256": files[0]["sha256"]}]},
        "application": {"kind": "application", "id": "dx100-gapbs",
                        "source": {"local_path": "apps/dx100", "commit": "a" * 40}},
    }
    pins = {}
    for name, value in records.items():
        path = repo / "swdb-project" / RECORD_PATHS[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(value, sort_keys=True).encode()
        path.write_bytes(raw)
        pins[name] = {"path": "swdb-project/" + RECORD_PATHS[name], "bytes": len(raw), "sha256": sha(raw)}
    (repo / "swdb-project/.gitignore").write_bytes((ROOT / ".gitignore").read_bytes())
    assert run_git(repo, "init", "-q").returncode == 0
    assert run_git(repo, "add", ".").returncode == 0
    assert run_git(repo, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
                   "-c", "core.hooksPath=/dev/null", "commit", "-qm", "synthetic fixture only").returncode == 0
    revision = run_git(repo, "rev-parse", "HEAD").stdout.strip()
    hooks = base / "hooks"
    hooks.mkdir(mode=0o700)
    hook = hooks / "post-checkout"
    if HOOK.exists():
        shutil.copyfile(HOOK, hook)
        hook.chmod(0o700)
    control = base / "control"
    control.mkdir(mode=0o700)
    source = base / "fresh-source"
    git = Path(shutil.which("git")).resolve()
    python = Path(sys.executable).resolve()
    request = {
        "format": "swdb.dx100-source-deployment-request.v1", "uid": os.getuid(),
        "source": str(source), "expected_revision": revision,
        "private_base": {"path": str(base), "identity": identity(base)},
        "control_base": {"path": str(base), "identity": identity(base)},
        "control": {"path": str(control), "identity": identity(control)},
        "target": {"path": str(target), "stat": stamp(target)},
        "target_stats": {str(path.relative_to(target)): stamp(path)
                         for path in sorted(target.rglob("*"))},
        "records": pins,
        "hook": {"path": str(hook), "sha256": sha(hook.read_bytes()) if hook.exists() else "0" * 64},
        "git": {"path": str(git), "sha256": sha(git.read_bytes()), "stat": stamp(git)},
        "python": {"path": str(python), "sha256": sha(python.read_bytes()), "stat": stamp(python)},
    }
    request_path = control / "request.json"

    def execute(change=None, destination=None):
        if change:
            change(request)
        raw = json.dumps(request, sort_keys=True).encode()
        request_path.write_bytes(raw)
        request_path.chmod(0o600)
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update({"PATH": str(python.parent) + os.pathsep + env.get("PATH", ""),
                    "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath",
                    "GIT_CONFIG_VALUE_0": str(hooks), "SWDB_DX100_BINDING_REQUEST": str(request_path),
                    "SWDB_DX100_BINDING_REQUEST_SHA256": sha(raw), "PYTHONDONTWRITEBYTECODE": "1"})
        return run_git(repo, "worktree", "add", "--detach", str(destination or source), run_git(repo, "rev-parse", "HEAD").stdout.strip(), env=env)

    return {"execute": execute, "request": request, "source": source, "target": target,
            "repo": repo, "control": control, "base": base, "hook": hook}


def test_worktree_add_binds_exact_baseline_and_keeps_source_clean(deployment):
    result = deployment["execute"]()
    assert result.returncode == 0, result.stderr
    alias = deployment["source"] / "swdb-project/apps/dx100"
    assert alias.is_symlink(), "post-checkout must provision the fresh source"
    assert alias.readlink() == deployment["target"]
    assert run_git(deployment["source"], "status", "--porcelain").stdout == ""
    receipt = json.loads((deployment["control"] / "dx100-binding-original.json").read_bytes())
    assert receipt["outcome"] == "bound"
    assert receipt["target_file_count"] == 53
    assert "identity_sha256" not in receipt


def test_consumed_allocator_checkout_cannot_supply_the_application(deployment):
    consumed = deployment["base"] / "ArchEvolve-lanl-allocator-a2-20261006"
    deployment["target"].rename(consumed)
    def changed(request):
        request["target"] = {"path": str(consumed), "stat": stamp(consumed)}
        request["target_stats"] = {str(path.relative_to(consumed)): stamp(path)
                                   for path in sorted(consumed.rglob("*"))}
    result = deployment["execute"](changed)
    assert result.returncode != 0
    assert json.loads(result.stderr.splitlines()[-1])["error_sha256"] == sha(b"target_is_consumed_or_overlapping"), result.stderr
    assert not (deployment["source"] / "swdb-project/apps/dx100").exists()


def refusal(result, code):
    assert result.returncode != 0
    value = json.loads(result.stderr.splitlines()[-1])
    assert value["error_sha256"] == sha(code.encode()), result.stderr


def test_wrong_requested_revision_refuses_before_binding(deployment):
    refusal(deployment["execute"](lambda req: req.update(expected_revision="b" * 40)),
            "fresh_checkout_revision_mismatch")
    assert not (deployment["source"] / "swdb-project/apps/dx100").exists()


def test_same_size_content_change_cannot_be_approved_by_stat_refresh(deployment):
    file = deployment["target"] / "benchmarks/gapbs/src/bfs.cc"
    original = file.read_bytes()
    file.write_bytes(b"X" + original[1:])
    def refreshed(req):
        req["target_stats"]["benchmarks/gapbs/src/bfs.cc"] = stamp(file)
    refusal(deployment["execute"](refreshed), "target_full_manifest_mismatch")
    assert not (deployment["source"] / "swdb-project/apps/dx100").exists()


def test_existing_tracked_alias_is_never_overwritten(deployment):
    alias = deployment["repo"] / "swdb-project/apps/dx100"
    alias.parent.mkdir()
    alias.write_bytes(b"existing fixture must survive")
    assert run_git(deployment["repo"], "add", "-f", "swdb-project/apps/dx100").returncode == 0
    assert run_git(deployment["repo"], "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
                   "-c", "core.hooksPath=/dev/null", "commit", "-qm", "existing alias fixture").returncode == 0
    revision = run_git(deployment["repo"], "rev-parse", "HEAD").stdout.strip()
    refusal(deployment["execute"](lambda req: req.update(expected_revision=revision)), "alias_already_exists")
    assert (deployment["source"] / "swdb-project/apps/dx100").read_bytes() == b"existing fixture must survive"
    assert not (deployment["control"] / "dx100-binding-original.json").exists()


@pytest.mark.parametrize("name", ["pure-EF", "pure-ER", "unrelated-worktree"])
def test_other_worktree_creation_is_a_noop(deployment, name):
    other = deployment["base"] / name
    result = deployment["execute"](destination=other)
    assert result.returncode == 0, result.stderr
    assert not (other / "swdb-project/apps").exists()
    assert not deployment["source"].exists()
    assert not (deployment["control"] / "dx100-binding-original.json").exists()
    assert run_git(other, "status", "--porcelain").stdout == ""


def test_protected_target_symlink_is_refused(deployment):
    redirect = deployment["base"] / "redirect"
    redirect.symlink_to(deployment["target"], target_is_directory=True)
    refusal(deployment["execute"](lambda req: req["target"].update(path=str(redirect))),
            "noncanonical_or_redirected_path")
    assert not (deployment["source"] / "swdb-project/apps/dx100").exists()


def test_extra_file_cannot_disappear_from_full_target_manifest(deployment):
    extra = deployment["target"] / "extra.txt"
    extra.write_bytes(b"not in independent original manifest")
    def refreshed(req):
        req["target"]["stat"] = stamp(deployment["target"])
        req["target_stats"]["extra.txt"] = stamp(extra)
    refusal(deployment["execute"](refreshed), "target_full_manifest_mismatch")


def test_exact_alias_ignore_does_not_hide_another_application(deployment):
    result = deployment["execute"]()
    assert result.returncode == 0, result.stderr
    other = deployment["source"] / "swdb-project/apps/other-source.txt"
    other.write_bytes(b"unrelated source remains visible")
    assert run_git(deployment["source"], "status", "--porcelain", "--untracked-files=all").stdout == (
        "?? swdb-project/apps/other-source.txt\n")

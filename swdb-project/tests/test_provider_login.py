"""Provider login write-back and preflight (ticket 58 fix). Created: 2026-10-04 ET.

All login files here are fakes; no real credential is read or written.
"""

import json
import os
import stat
import threading
import time

import pytest

from swdb import provider_guard, provider_login, provider_roles


def fake(refresh="r0", access="a0"):
    return json.dumps({"auth_mode": "chatgpt", "OPENAI_API_KEY": None, "last_refresh": "2026-10-04T00:00:00Z",
                       "tokens": {"id_token": "i", "access_token": access, "refresh_token": refresh,
                                  "account_id": "x"}}).encode()


@pytest.fixture
def codex_home(tmp_path, monkeypatch):
    home = tmp_path / "codex-home"
    home.mkdir()
    (home / "auth.json").write_bytes(fake())
    (home / "auth.json").chmod(0o600)
    monkeypatch.setenv("CODEX_HOME", str(home))
    return home


def session(tmp_path, name="s1"):
    folder = tmp_path / name
    folder.mkdir()
    return provider_login.copy("codex", folder / "auth.json")


def test_refreshed_login_is_written_back_atomically(tmp_path, codex_home):
    handle = session(tmp_path)
    handle.path.write_bytes(fake("r1", "a1"))           # Codex refreshed inside the session
    receipt = handle.write_back()
    assert receipt["changed"] == "yes" and receipt["written_back"] is True
    assert (codex_home / "auth.json").read_bytes() == fake("r1", "a1")
    assert stat.S_IMODE((codex_home / "auth.json").stat().st_mode) == 0o600
    assert not [p for p in codex_home.iterdir() if p.name.startswith(".auth.json.swdb-")]
    assert "r1" not in json.dumps(receipt) and "a1" not in json.dumps(receipt)


def test_unchanged_login_is_left_alone(tmp_path, codex_home):
    before = (codex_home / "auth.json").stat()
    receipt = session(tmp_path).write_back()
    after = (codex_home / "auth.json").stat()
    assert receipt == {**receipt, "changed": "no", "written_back": False, "reason": "unchanged"}
    assert (before.st_ino, before.st_mtime_ns) == (after.st_ino, after.st_mtime_ns)


@pytest.mark.parametrize("data", [b"{not json", b"[]", json.dumps({"tokens": {"access_token": "a"}}).encode(),
                                  json.dumps({"tokens": {"access_token": "a", "refresh_token": ""}}).encode()])
def test_malformed_copy_is_not_written_back(tmp_path, codex_home, data):
    handle = session(tmp_path)
    handle.path.write_bytes(data)
    receipt = handle.write_back()
    assert receipt["changed"] == "yes" and not receipt["written_back"]
    assert receipt["reason"].startswith("malformed copy")
    assert (codex_home / "auth.json").read_bytes() == fake()


def test_newer_source_login_is_kept(tmp_path, codex_home):
    handle = session(tmp_path)
    (codex_home / "auth.json").write_bytes(fake("relogin"))    # `codex login` during the session
    handle.path.write_bytes(fake("r1"))
    receipt = handle.write_back()
    assert not receipt["written_back"] and "newer login kept" in receipt["reason"]
    assert (codex_home / "auth.json").read_bytes() == fake("relogin")


def test_concurrent_sessions_are_serialized(tmp_path, codex_home):
    first = session(tmp_path, "s1")
    # A second copy taken outside the session lock (a launcher predating ticket 62).
    (tmp_path / "s2").mkdir()
    second = provider_login.Copy("codex", codex_home / "auth.json", tmp_path / "s2" / "auth.json", first.snapshot_sha256)
    second.path.write_bytes(fake())
    first.path.write_bytes(fake("r1"))
    second.path.write_bytes(fake("r2"))
    results = {}
    with provider_login.locked(codex_home / "auth.json"):          # another session holds the lock
        worker = threading.Thread(target=lambda: results.setdefault("first", first.write_back()))
        worker.start()
        time.sleep(0.3)
        assert worker.is_alive() and (codex_home / "auth.json").read_bytes() == fake()
    worker.join(5)
    results["second"] = second.write_back()
    # The first refresh wins; the second session's copy is from the same, now superseded,
    # snapshot and never overwrites it.
    assert results["first"]["written_back"] and not results["second"]["written_back"]
    assert (codex_home / "auth.json").read_bytes() == fake("r1")


def test_role_workspace_cleanup_writes_back_then_deletes_copy(tmp_path, codex_home, monkeypatch):
    monkeypatch.setattr(provider_guard, "abi", lambda: 4)
    role = provider_roles.Role("read_only_fixture", {"type": "object"})
    workspace = provider_roles.prepare(role, {"code.cc": "source"}, tmp_path / "role", {"kind": "codex"})
    assert workspace.login_path.read_bytes() == fake()
    workspace.login_path.write_bytes(fake("r1"))
    workspace.cleanup()
    workspace.cleanup()                                         # idempotent
    manifest = workspace.metadata
    assert manifest["login_copy_deleted"] and not workspace.login_path.exists()
    assert manifest["login_writeback"]["written_back"] and manifest["login_writeback"]["changed"] == "yes"
    assert (codex_home / "auth.json").read_bytes() == fake("r1")
    assert "r1" not in json.dumps(manifest)


def other_account():
    data = json.loads(fake("r1"))
    data["tokens"]["account_id"] = "y"
    return json.dumps(data).encode()


def api_key_login():
    return json.dumps({"OPENAI_API_KEY": "sk-fixture"}).encode()


def changed_mode():
    data = json.loads(fake("r1"))
    data["auth_mode"] = "apikey"
    return json.dumps(data).encode()


@pytest.mark.parametrize("planted", [other_account, api_key_login, changed_mode])
def test_copy_with_another_identity_is_not_written_back(tmp_path, codex_home, planted):
    # 2026-10-04 ET (final code review): the provider controls its copy; only a token
    # refresh of the same account and login mode may cross back to the source login.
    handle = session(tmp_path)
    handle.path.write_bytes(planted())
    receipt = handle.write_back()
    assert receipt["changed"] == "yes" and not receipt["written_back"]
    assert (codex_home / "auth.json").read_bytes() == fake()
    assert handle.session_fd is None


def test_deeply_nested_copy_still_deletes_copy_and_links(tmp_path, codex_home, monkeypatch):
    # 2026-10-04 ET (final code review): RecursionError from json.loads escaped cleanup,
    # leaving the copy (and a hard link holding the original tokens) in place.
    monkeypatch.setattr(provider_guard, "abi", lambda: 4)
    role = provider_roles.Role("read_only_fixture", {"type": "object"})
    workspace = provider_roles.prepare(role, {"code.cc": "source"}, tmp_path / "role", {"kind": "codex"})
    stash = workspace.login_path.with_name("stash")
    os.link(workspace.login_path, stash)
    workspace.login_path.unlink()
    workspace.login_path.write_bytes(b"[" * 200000)
    os.link(workspace.login_path, workspace.login_path.with_name("stash2"))
    workspace.cleanup()
    assert workspace.metadata["login_copy_deleted"] and not workspace.login_path.exists()
    assert not stash.exists() and not stash.with_name("stash2").exists()
    assert not workspace.metadata["login_writeback"]["written_back"]
    assert (codex_home / "auth.json").read_bytes() == fake()
    assert workspace.login_copy.session_fd is None


def test_preflight_detects_missing_and_malformed_login(codex_home):
    good = provider_login.preflight("codex")
    assert good["state"] == "ok" and good["source_sha256"]
    (codex_home / "auth.json").write_bytes(b"{}")
    assert provider_login.preflight("codex")["state"] == "login"
    os.unlink(codex_home / "auth.json")
    assert provider_login.preflight("codex") == {"state": "login", "reason": "provider login file is unavailable",
                                                 "source_sha256": None}


def driver():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "tools" / "spec_enough_driver.py"
    spec = importlib.util.spec_from_file_location("spec_enough_driver_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_driver_preflight_pauses_uncounted_before_a_session(tmp_path, codex_home):
    from swdb.cli import Failure
    module, ledger_path = driver(), tmp_path / "ledger.json"
    ledger = {"calls": []}
    sha = module.login_preflight(ledger, ledger_path)
    assert sha and "preflights" not in ledger
    # A session with this exact login was refused: the next sample pauses without a call.
    ledger["calls"].append({"outcome": "login", "counted": False, "login_source_sha256": sha})
    with pytest.raises(Failure, match=r"paused \(login\); uncounted; preflight"):
        module.login_preflight(ledger, ledger_path)
    (codex_home / "auth.json").write_bytes(b"{broken")
    with pytest.raises(Failure, match="preflight: not valid JSON"):
        module.login_preflight(ledger, ledger_path)
    saved = json.loads(ledger_path.read_text())
    assert [p["outcome"] for p in saved["preflights"]] == ["login", "login"]
    assert all(p["counted"] is False for p in saved["preflights"])
    (codex_home / "auth.json").write_bytes(fake("relogged"))           # after `codex login`
    assert module.login_preflight(ledger, ledger_path) != sha


def _driver_args(module, tmp_path):
    return module.argparse.Namespace(campaign="extensa-gem5-bfs-20261004-s1", runs_root=tmp_path, attempt="a3",
                                     provider_config=tmp_path / "fixture.json", codex_command="codex",
                                     lane_seconds=10800, stop_after_failures=2)


def _quiet_driver(module, monkeypatch, run):
    from swdb import rewrite
    monkeypatch.setattr(module, "base_source", lambda scratch: {})
    monkeypatch.setattr(module, "arm_files", lambda arm, base: ({"spec/a.md": "spec"}, {}))
    monkeypatch.setattr(rewrite, "configuration", lambda path: {"kind": "external_fixture"})
    monkeypatch.setattr(module.provider_roles, "run", run)


def test_driver_stops_itself_after_two_failed_sessions(tmp_path, monkeypatch):
    """a3 (2026-10-04 ET): a systematic failure writes STOP-a3 and opens no third session."""
    from swdb.cli import Failure
    module, calls = driver(), []

    def failing(*args, **kwargs):
        calls.append(args[4])
        raise Failure("provider role audit failed: provider awk program cannot be audited")
    _quiet_driver(module, monkeypatch, failing)
    with pytest.raises(Failure, match="the first 2 sessions failed"):
        module.provider_stage(_driver_args(module, tmp_path))
    root = tmp_path / "extensa" / "extensa-gem5-bfs-20261004-s1"
    assert len(calls) == 2 and "systematic failure" in (root / "STOP-a3").read_text()
    with pytest.raises(Failure, match="stopped by STOP-a3"):      # the run's stop mechanism holds
        module.provider_stage(_driver_args(module, tmp_path))
    assert len(calls) == 2


def test_driver_recounts_hand_written_hunk_headers_only():
    """a3 (2026-10-04 ET): hand-written diffs miscount hunks; only the counts change."""
    from pathlib import Path
    module = driver()
    patch = "--- a/x\n+++ b/x\n@@ -13,6 +13,7 @@ tail\n a\n b\n+c\n\n d\n@@ -40,1 +41,1 @@\n-e\n+f\n"
    assert module.recount(patch) == ("--- a/x\n+++ b/x\n@@ -13,4 +13,5 @@ tail\n a\n b\n+c\n \n d\n"
                                     "@@ -40,1 +41,1 @@\n-e\n+f\n")
    reference = (Path(__file__).resolve().parents[1] / "library/dx100/peter-section5.patch").read_text()
    assert module.recount(reference) == reference


def test_driver_prompt_forbids_the_commands_the_audit_refused_in_a2():
    module = driver()
    for word in ("heredocs", "`awk`", "`git apply`", "`patch`", "Do not create files"):
        assert word in module.PROMPT


# --- ticket 62 (2026-10-04 ET): one provider session per login -------------------

HOLDER = """
import os, sys, time
sys.path.insert(0, sys.argv[1])
from swdb import provider_login
handle = provider_login.copy("codex", sys.argv[2])
print("held", flush=True)
time.sleep(float(sys.argv[3]))
handle.write_back()
"""


def test_session_lock_is_held_from_copy_until_write_back(tmp_path, codex_home, monkeypatch):
    monkeypatch.setenv("SWDB_SESSION_LOCK_TIMEOUT_S", "0.3")
    monkeypatch.setattr(provider_login, "SESSION_LOCK_POLL_S", 0.05)
    first = session(tmp_path, "s1")
    assert (codex_home / provider_login.SESSION_LOCK).is_file()
    assert first.session_lock["lock"] == provider_login.SESSION_LOCK and not first.session_lock["waited"]
    with pytest.raises(provider_login.Failure, match="another provider session holds swdb-session.lock"):
        session(tmp_path, "s2")
    receipt = first.write_back()
    assert receipt["session_lock"]["lock"] == provider_login.SESSION_LOCK
    second = session(tmp_path, "s3")                    # released: the next session starts at once
    second.release()
    second.release()                                    # idempotent


def test_session_lock_serializes_sessions_across_processes(tmp_path, codex_home):
    import subprocess
    import sys
    from pathlib import Path
    project = Path(__file__).resolve().parents[1]
    (tmp_path / "other").mkdir()
    holder = subprocess.Popen([sys.executable, "-c", HOLDER, str(project), str(tmp_path / "other" / "auth.json"), "1.0"],
                              stdout=subprocess.PIPE, text=True, env={**os.environ, "CODEX_HOME": str(codex_home)})
    try:
        assert holder.stdout.readline().strip() == "held"
        started = time.monotonic()
        handle = provider_login.acquire_session("codex", timeout_s=30, poll_s=0.05)
        waited = time.monotonic() - started
        provider_login.release_session(handle[0])
        assert handle[1]["waited"] and waited >= 0.5
    finally:
        holder.wait(10)


def test_failed_workspace_start_releases_the_session_lock(tmp_path, codex_home, monkeypatch):
    monkeypatch.setattr(provider_guard, "abi", lambda: 4)
    monkeypatch.setenv("SWDB_SESSION_LOCK_TIMEOUT_S", "0.2")
    role = provider_roles.Role("read_only_fixture", {"type": "object"})

    def broken_digest(value):
        raise RuntimeError("workspace setup failed after the login copy")
    monkeypatch.setattr(provider_roles.artifacts, "digest", broken_digest)
    with pytest.raises(RuntimeError):
        provider_roles.prepare(role, {"code.cc": "source"}, tmp_path / "role", {"kind": "codex"})
    session(tmp_path, "after").release()                 # prepare's cleanup released the lock


def test_prompt_context_releases_the_lock_when_the_guard_fails(tmp_path, codex_home, monkeypatch):
    monkeypatch.setattr(provider_guard, "abi", lambda: 4)
    monkeypatch.setenv("SWDB_SESSION_LOCK_TIMEOUT_S", "0.2")

    def refuse(*args, **kwargs):
        raise provider_guard.GuardError("guard refused")
    monkeypatch.setattr(provider_guard, "context", refuse)
    (tmp_path / "prompt").mkdir()
    with pytest.raises(provider_guard.GuardError):
        provider_guard.prompt_context({"kind": "codex"}, tmp_path / "prompt")
    session(tmp_path, "after").release()


def test_audit_refuses_an_unstatable_path_instead_of_crashing(tmp_path):
    """Ticket 58 a2 (2026-10-04 ET): an awk program parsed as a path raised ENAMETOOLONG."""
    from swdb import provider_audit
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "code.cc").write_text("x\n")
    log = tmp_path / "stdout.txt"
    event = {"type": "item.completed", "item": {"type": "command_execution", "command": "cat " + "x" * 4000 + ".cc"}}
    log.write_text(json.dumps(event) + "\n")
    receipt = provider_audit.audit(log, "codex", root, {"code.cc"}, completed=True)
    assert not receipt["passed"]
    assert any("cannot be resolved" in reason for reason in receipt["reasons"]), receipt["reasons"]

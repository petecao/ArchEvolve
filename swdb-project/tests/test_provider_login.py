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
    first, second = session(tmp_path, "s1"), session(tmp_path, "s2")
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

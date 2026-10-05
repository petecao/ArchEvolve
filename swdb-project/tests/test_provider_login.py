"""Provider login write-back and preflight (ticket 58 fix). Created: 2026-10-04 ET.
Updated: 2026-10-05 ET (code review H3 lab-host provider home, P7-P9 one login start, exclusive
0600 copy, directory fsync, J1/J6 LoginSpec and short-hash names, T5 event-driven lock tests).

All login files here are fakes; no real credential is read or written.
"""

import fcntl
import json
import os
import stat
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from conftest import REPO
from swdb import provider_adapters, provider_guard, provider_login, provider_roles
from swdb.cli import Failure
from testkit.drivers import campaign_root, driver_args, offline_inputs, spec_enough_driver


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
    monkeypatch.delenv(provider_login.LAB_HOST_ENV, raising=False)
    return home


@pytest.fixture
def lab_host(monkeypatch, tmp_path):
    """mbit10 as far as provider_login can tell, with $HOME in a temporary folder."""
    home = tmp_path / "user-home"
    home.mkdir()
    monkeypatch.setattr(provider_login, "socket", SimpleNamespace(gethostname=lambda: "mbit10.eecs.umich.edu"))
    monkeypatch.setenv("HOME", str(home))
    return home


def session(tmp_path, name="s1"):
    folder = tmp_path / name
    folder.mkdir()
    return provider_login.take_session_copy("codex", folder / "auth.json")


def test_refreshed_login_is_written_back_atomically(tmp_path, codex_home):
    handle = session(tmp_path)
    handle.path.write_bytes(fake("r1", "a1"))           # Codex refreshed inside the session
    receipt = handle.write_back()
    assert receipt["changed"] == "yes" and receipt["written_back"] is True
    assert (codex_home / "auth.json").read_bytes() == fake("r1", "a1")
    assert stat.S_IMODE((codex_home / "auth.json").stat().st_mode) == 0o600
    assert not [p for p in codex_home.iterdir() if p.name.startswith(".auth.json.swdb-")]
    assert "r1" not in json.dumps(receipt) and "a1" not in json.dumps(receipt)


def test_receipts_name_their_short_hashes_honestly(tmp_path, codex_home):
    """J6 (2026-10-05 ET): the 16-hex values are `*_short_hash`, never a field named `*_sha256`."""
    handle = session(tmp_path)
    assert len(handle.snapshot_short_hash) == provider_login.SHORT_HASH_DIGITS
    handle.path.write_bytes(fake("r1"))
    receipt = handle.write_back()
    hashes = {k: v for k, v in receipt.items() if k.endswith("short_hash") or "short_hash_" in k}
    assert set(hashes) == {"source_short_hash_before", "copy_short_hash", "source_short_hash_after"}
    assert all(len(v) == 16 and int(v, 16) >= 0 for v in hashes.values())
    assert not [k for k in receipt if "sha256" in k]
    assert provider_login.preflight("codex")["source_short_hash"] == hashes["source_short_hash_after"]


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


def test_concurrent_sessions_are_serialized(tmp_path, codex_home, monkeypatch):
    """T5 (2026-10-05 ET): the worker is observed reaching the write-back lock (an event set
    inside its flock call), not assumed to have reached it after a sleep."""
    first = session(tmp_path, "s1")
    # A second copy taken outside the session lock (a launcher predating ticket 62).
    (tmp_path / "s2").mkdir()
    second = provider_login.Copy("codex", codex_home / "auth.json", tmp_path / "s2" / "auth.json",
                                 first.snapshot_short_hash)
    second.path.write_bytes(fake())
    first.path.write_bytes(fake("r1"))
    second.path.write_bytes(fake("r2"))
    results, reached = {}, threading.Event()
    worker = threading.Thread(target=lambda: results.setdefault("first", first.write_back()))
    real_flock = fcntl.flock

    def flock(fd, operation):
        if threading.current_thread() is worker and operation == fcntl.LOCK_EX:
            reached.set()                              # the worker now blocks on the write-back lock
        return real_flock(fd, operation)
    monkeypatch.setattr(provider_login, "fcntl", SimpleNamespace(**{**vars(fcntl), "flock": flock}))
    with provider_login.locked(codex_home / "auth.json"):          # another session holds the lock
        worker.start()
        assert reached.wait(10)
        assert worker.is_alive() and (codex_home / "auth.json").read_bytes() == fake()
    worker.join(10)
    assert not worker.is_alive()
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
    assert good["state"] == "ok" and good["source_short_hash"]
    (codex_home / "auth.json").write_bytes(b"{}")
    assert provider_login.preflight("codex")["state"] == "login"
    os.unlink(codex_home / "auth.json")
    assert provider_login.preflight("codex") == {"state": "login", "reason": "provider login file is unavailable",
                                                 "source_short_hash": None}


# --- H3 (2026-10-05 ET): nothing under $HOME on a lab host ------------------------------------------

@pytest.mark.parametrize("kind, variable", [("codex", "CODEX_HOME"), ("claude", "CLAUDE_CONFIG_DIR")])
def test_lab_host_refuses_an_unset_provider_home_before_any_lock_or_copy(tmp_path, lab_host, monkeypatch,
                                                                         kind, variable):
    monkeypatch.delenv(variable, raising=False)
    (lab_host / ("." + kind)).mkdir()
    with pytest.raises(provider_adapters.LoginRequired, match=f"{variable} is unset"):
        provider_login.source(kind)
    with pytest.raises(provider_adapters.LoginRequired):
        provider_login.take_session_copy(kind, tmp_path / "copy")
    check = provider_login.preflight(kind)
    assert check["state"] == "login" and variable in check["reason"] and check["source_short_hash"] is None
    assert not [p for p in lab_host.rglob("*") if p.is_file()]        # no lock file under $HOME
    assert not (tmp_path / "copy").exists()


def test_lab_host_refuses_a_provider_home_under_home_even_through_a_link(tmp_path, lab_host, monkeypatch):
    inside = lab_host / ".codex"
    inside.mkdir()
    (inside / "auth.json").write_bytes(fake())
    link = tmp_path / "data1-codex"
    link.symlink_to(inside)
    for value in (inside, link, lab_host):
        monkeypatch.setenv("CODEX_HOME", str(value))
        with pytest.raises(provider_adapters.LoginRequired, match=r"resolves under \$HOME"):
            provider_login.take_session_copy("codex", tmp_path / "copy")
        assert provider_login.preflight("codex")["state"] == "login"
    assert sorted(p.name for p in inside.iterdir()) == ["auth.json"]        # no lock written there


def test_lab_host_accepts_a_provider_home_outside_home(tmp_path, lab_host, monkeypatch):
    home = tmp_path / "data1" / ".codex"
    home.mkdir(parents=True)
    (home / "auth.json").write_bytes(fake())
    monkeypatch.setenv("CODEX_HOME", str(home))
    (tmp_path / "s1").mkdir()
    handle = provider_login.take_session_copy("codex", tmp_path / "s1" / "auth.json")
    assert (home / provider_login.SESSION_LOCK).is_file()
    assert handle.write_back()["reason"] == "unchanged"


def test_the_lab_host_rule_can_be_forced_off_mbit10_but_not_switched_off_on_it(tmp_path, monkeypatch):
    home = tmp_path / "user-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.delenv(provider_login.LAB_HOST_ENV, raising=False)
    monkeypatch.setattr(provider_login, "socket", SimpleNamespace(gethostname=lambda: "fixture-mac.local"))
    # Mac development: an unset home is the user's default and stays usable.
    assert provider_login.source("codex") == home / ".codex" / "auth.json"
    monkeypatch.setenv(provider_login.LAB_HOST_ENV, "1")
    with pytest.raises(provider_adapters.LoginRequired):
        provider_login.source("codex")
    monkeypatch.setenv(provider_login.LAB_HOST_ENV, "0")
    monkeypatch.setattr(provider_login, "socket", SimpleNamespace(gethostname=lambda: "mbit10"))
    with pytest.raises(provider_adapters.LoginRequired):
        provider_login.source("codex")


# --- J1/P7/P9 (2026-10-05 ET): one login table, one start, an exclusive private copy ----------------

def test_an_unknown_provider_kind_is_refused_not_treated_as_claude():
    for call in (lambda: provider_login.login_name("gemini"), lambda: provider_login.problem("gemini", b"{}"),
                 lambda: provider_login.source("gemini")):
        with pytest.raises(Failure, match="unknown provider login kind"):
            call()
    claude = json.dumps({"claudeAiOauth": {"accessToken": "a", "refreshToken": "r", "expiresAt": 1}}).encode()
    assert provider_login.problem("claude", claude) is None
    assert provider_login.login_name("claude") == ".credentials.json" and provider_login.login_name("codex") == "auth.json"


@pytest.mark.parametrize("config, name", [({"kind": "external_fixture"}, ".credentials.json"),
                                          ({"kind": "external_fixture", "emulates": "codex"}, "auth.json"),
                                          ({"kind": "external_fixture", "emulates": "claude"}, ".credentials.json")])
def test_a_fixture_session_starts_with_a_private_placeholder_login(tmp_path, config, name):
    path, handle = provider_login.start(config, tmp_path)
    assert path == tmp_path / name and handle is None
    assert path.read_bytes() == provider_login.FIXTURE_LOGIN and stat.S_IMODE(path.stat().st_mode) == 0o600


def test_a_real_session_without_landlock_is_refused_before_any_lock_or_copy(tmp_path, codex_home, monkeypatch):
    monkeypatch.setattr(provider_guard, "abi", lambda: 3)
    with pytest.raises(Failure, match="Landlock ABI >= 4; refusing unguarded session"):
        provider_login.start({"kind": "codex"}, tmp_path)
    assert not (tmp_path / "auth.json").exists() and not (codex_home / provider_login.SESSION_LOCK).exists()


def test_the_login_copy_is_created_exclusively_with_mode_0600(tmp_path, codex_home, monkeypatch):
    previous = os.umask(0)                               # a permissive umask cannot widen the copy
    try:
        handle = session(tmp_path, "s1")
    finally:
        os.umask(previous)
    assert stat.S_IMODE(handle.path.stat().st_mode) == 0o600
    handle.release()
    (tmp_path / "s2").mkdir()
    target = tmp_path / "elsewhere"
    (tmp_path / "s2" / "auth.json").symlink_to(target)          # a planted link is never followed
    with pytest.raises(FileExistsError):
        provider_login.take_session_copy("codex", tmp_path / "s2" / "auth.json")
    assert not target.exists()
    session(tmp_path, "s3").release()                    # the refused start released the session lock


def test_write_back_fsyncs_the_folder_after_the_atomic_replace(tmp_path, codex_home, monkeypatch):
    seen = []
    monkeypatch.setattr(provider_login, "_fsync_directory",
                        lambda folder: seen.append((folder, (folder / "auth.json").read_bytes())))
    handle = session(tmp_path)
    handle.path.write_bytes(fake("r1"))
    assert handle.write_back()["written_back"]
    assert seen == [(codex_home, fake("r1"))]           # after the replace, on the login's own folder


def test_write_back_safely_records_a_failure_and_releases_the_lock(tmp_path, codex_home, monkeypatch):
    monkeypatch.setenv(provider_login.SESSION_LOCK_TIMEOUT_ENV, "0.2")
    handle = session(tmp_path)

    def broken(self):
        raise OSError("disk full")
    monkeypatch.setattr(provider_login.Copy, "_write_back", broken)
    assert handle.write_back_safely() == {"written_back": False, "reason": "write-back failed: OSError"}
    assert handle.session_fd is None
    session(tmp_path, "after").release()


# --- the ticket 58 driver's login handling -----------------------------------------------------------

def test_driver_preflight_pauses_uncounted_before_a_session(tmp_path, codex_home):
    module, ledger_path = spec_enough_driver(), tmp_path / "ledger.json"
    ledger = {"calls": []}
    short = module.login_preflight(ledger, ledger_path)
    assert short and "preflights" not in ledger
    # A session with this exact login was refused: the next sample pauses without a call.
    ledger["calls"].append({"outcome": "login", "counted": False, "login_source_short_hash": short})
    with pytest.raises(Failure, match=r"paused \(login\); uncounted; preflight"):
        module.login_preflight(ledger, ledger_path)
    (codex_home / "auth.json").write_bytes(b"{broken")
    with pytest.raises(Failure, match="preflight: not valid JSON"):
        module.login_preflight(ledger, ledger_path)
    saved = json.loads(ledger_path.read_text())
    assert [p["outcome"] for p in saved["preflights"]] == ["login", "login"]
    assert all(p["counted"] is False for p in saved["preflights"])
    (codex_home / "auth.json").write_bytes(fake("relogged"))           # after `codex login`
    assert module.login_preflight(ledger, ledger_path) != short


def test_driver_preflight_reads_the_legacy_hash_key_of_attempts_a1_to_a3(tmp_path, codex_home):
    module, ledger_path = spec_enough_driver(), tmp_path / "ledger.json"
    short = provider_login.preflight("codex")["source_short_hash"]
    ledger = {"calls": [{"outcome": "login", "counted": False, "login_source_sha256": short}]}
    with pytest.raises(Failure, match="already refused"):
        module.login_preflight(ledger, ledger_path)


def test_driver_stops_itself_after_two_failed_sessions(tmp_path, monkeypatch):
    """a3 (2026-10-04 ET): a systematic failure writes STOP-a3 and opens no third session."""
    from swdb import rewrite
    module, calls = spec_enough_driver(), []

    def failing(*args, **kwargs):
        calls.append(args[4])
        raise Failure("provider role audit failed: provider awk program cannot be audited")
    offline_inputs(module, monkeypatch)
    monkeypatch.setattr(rewrite, "configuration", lambda path: {"kind": "external_fixture"})
    monkeypatch.setattr(module.provider_roles, "run", failing)
    with pytest.raises(Failure, match="the first 2 sessions failed"):
        module.provider_stage(driver_args(module, tmp_path))
    assert len(calls) == 2 and "systematic failure" in (campaign_root(tmp_path) / "STOP-a3").read_text()
    with pytest.raises(Failure, match="stopped by STOP-a3"):      # the run's stop mechanism holds
        module.provider_stage(driver_args(module, tmp_path))
    assert len(calls) == 2


def test_driver_recounts_hand_written_hunk_headers_only():
    """a3 (2026-10-04 ET): hand-written diffs miscount hunks; only the counts change."""
    module = spec_enough_driver()
    patch = "--- a/x\n+++ b/x\n@@ -13,6 +13,7 @@ tail\n a\n b\n+c\n\n d\n@@ -40,1 +41,1 @@\n-e\n+f\n"
    assert module.recount(patch) == ("--- a/x\n+++ b/x\n@@ -13,4 +13,5 @@ tail\n a\n b\n+c\n \n d\n"
                                     "@@ -40,1 +41,1 @@\n-e\n+f\n")
    reference = (REPO / "library/dx100/peter-section5.patch").read_text()
    assert module.recount(reference) == reference


def test_driver_prompt_forbids_the_commands_the_audit_refused_in_a2():
    module = spec_enough_driver()
    for word in ("heredocs", "`awk`", "`git apply`", "`patch`", "Do not create files"):
        assert word in module.PROMPT


def test_driver_derives_the_aborted_control_total_from_the_plug_in():
    """P6 (2026-10-05 ET): the abort branch once hard-coded 16 (certify 1.0-1.1)."""
    from swdb import certification_legality, kernels
    module = spec_enough_driver()
    assert module.planned_controls() == (len(kernels.BFS.certification_controls)
                                         + len(certification_legality.CONTROLS)) * len(module.TILE_SIZES)


# --- ticket 62 (2026-10-04 ET): one provider session per login -------------------

HOLDER = """
import sys
sys.path.insert(0, sys.argv[1])
from swdb import provider_login
handle = provider_login.take_session_copy("codex", sys.argv[2])
print("held", flush=True)
sys.stdin.readline()                       # hold the session until the test releases it
handle.write_back()
"""


def test_session_lock_is_held_from_copy_until_write_back(tmp_path, codex_home, monkeypatch):
    monkeypatch.setenv(provider_login.SESSION_LOCK_TIMEOUT_ENV, "0.3")
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


def test_session_lock_serializes_sessions_across_processes(tmp_path, codex_home, monkeypatch):
    """T5 (2026-10-05 ET): the holder keeps its session until told to release it, and the waiter is
    observed refused at least once before then; no wall-clock threshold decides the outcome."""
    (tmp_path / "other").mkdir()
    holder = subprocess.Popen([sys.executable, "-c", HOLDER, str(REPO), str(tmp_path / "other" / "auth.json")],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                              env={**os.environ, "CODEX_HOME": str(codex_home)})
    refused, result = threading.Event(), {}

    def sleep(seconds):                                   # acquire_session sleeps only after a refusal
        refused.set()
        time.sleep(seconds)
    monkeypatch.setattr(provider_login, "time", SimpleNamespace(monotonic=time.monotonic, sleep=sleep))
    waiter = threading.Thread(target=lambda: result.update(
        handle=provider_login.acquire_session("codex", timeout_s=60, poll_s=0.01)))
    try:
        assert holder.stdout.readline().strip() == "held"
        waiter.start()
        assert refused.wait(30)
        assert waiter.is_alive() and "handle" not in result     # still waiting while the holder holds it
        holder.stdin.write("release\n")
        holder.stdin.flush()
        waiter.join(30)
        assert not waiter.is_alive()
        fd, receipt = result["handle"]
        provider_login.release_session(fd)
        assert receipt["waited"]
    finally:
        if holder.poll() is None:
            holder.stdin.close()
        holder.wait(10)


def test_failed_workspace_start_releases_the_session_lock(tmp_path, codex_home, monkeypatch):
    monkeypatch.setattr(provider_guard, "abi", lambda: 4)
    monkeypatch.setenv(provider_login.SESSION_LOCK_TIMEOUT_ENV, "0.2")
    role = provider_roles.Role("read_only_fixture", {"type": "object"})

    def broken_digest(value):
        raise RuntimeError("workspace setup failed after the login copy")
    monkeypatch.setattr(provider_roles.artifacts, "digest", broken_digest)
    with pytest.raises(RuntimeError):
        provider_roles.prepare(role, {"code.cc": "source"}, tmp_path / "role", {"kind": "codex"})
    session(tmp_path, "after").release()                 # prepare's cleanup released the lock


def test_prompt_context_releases_the_lock_when_the_guard_fails(tmp_path, codex_home, monkeypatch):
    monkeypatch.setattr(provider_guard, "abi", lambda: 4)
    monkeypatch.setenv(provider_login.SESSION_LOCK_TIMEOUT_ENV, "0.2")

    def refuse(*args, **kwargs):
        raise provider_guard.GuardError("guard refused")
    monkeypatch.setattr(provider_guard, "context", refuse)
    (tmp_path / "prompt").mkdir()
    with pytest.raises(provider_guard.GuardError):
        provider_guard.prompt_context({"kind": "codex"}, tmp_path / "prompt")
    assert not (tmp_path / "prompt" / "provider-home" / "auth.json").exists()
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

"""Provider login copies and their write-back. Created: 2026-10-04 ET.

A guarded provider session runs on a private copy of the provider login file
(Codex `auth.json`, Claude `.credentials.json`) in its own provider home. Codex
refreshes its OAuth tokens inside a session and persists the result only to the
login file in its home; the refresh token is single use. If the copy were simply
deleted, the source login would keep the consumed refresh token and every later
session would fail with 401 `token_invalidated` / `refresh_token_reused`
(ticket 58, attempt a1). So, when a session ends, a changed copy that is still a
well-formed login is written back to the source atomically under a file lock.

Token values are never logged or recorded: receipts hold only short file hashes
and changed/written flags.

Session lock (ticket 62, 2026-10-04 ET; agent-decided under Yan-Ru's delegation,
revisable): every real provider session holds an exclusive flock on
`swdb-session.lock` in the provider's home (CODEX_HOME / CLAUDE_CONFIG_DIR) from the
moment its login copy is taken until the copy has been written back. Two sessions on
one login therefore never overlap, across agents, clones and processes. A waiting
session polls up to `SWDB_SESSION_LOCK_TIMEOUT_S` seconds (default 3600) and then
fails before any provider call.
"""

import contextlib
import fcntl
import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from swdb.cli import Failure

LOCK_SUFFIX = ".swdb-lock"
SESSION_LOCK = "swdb-session.lock"
SESSION_LOCK_POLL_S = 5.0
#: Required nested string fields of a well-formed login, per provider.
EXPECTED = {"codex": ("tokens", ("access_token", "refresh_token")),
            "claude": ("claudeAiOauth", ("accessToken", "refreshToken"))}


def login_name(kind):
    return "auth.json" if kind == "codex" else ".credentials.json"


def source(kind):
    """The provider's own login file, from CODEX_HOME / CLAUDE_CONFIG_DIR."""
    if kind == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / login_name(kind)
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))) / login_name(kind)


def _sha(data):
    return hashlib.sha256(data).hexdigest()[:16] if data is not None else None


def problem(kind, data):
    """Why bytes are not a well-formed login (None when they are). Never echoes values."""
    try:
        parsed = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        return "not valid JSON"
    if not isinstance(parsed, dict):
        return "not a JSON object"
    key, fields = EXPECTED["codex" if kind == "codex" else "claude"]
    if kind == "codex" and key not in parsed and isinstance(parsed.get("OPENAI_API_KEY"), str) \
            and parsed["OPENAI_API_KEY"]:
        return None                        # API-key login: nothing to refresh
    inner = parsed.get(key)
    if not isinstance(inner, dict):
        return f"missing object {key!r}"
    missing = [name for name in fields if not isinstance(inner.get(name), str) or not inner[name]]
    if missing:
        return f"missing {key}.{'/'.join(missing)}"
    return None


@contextlib.contextmanager
def locked(path):
    """Exclusive advisory lock beside the source login; serializes write-backs."""
    path = Path(path)
    fd = os.open(path.with_name(path.name + LOCK_SUFFIX), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def session_lock_path(kind):
    """The one-session-per-login lock file in the provider's home."""
    return source(kind).parent / SESSION_LOCK


def acquire_session(kind, timeout_s=None, poll_s=SESSION_LOCK_POLL_S):
    """Hold the exclusive session lock of this login; return (fd, value-free receipt)."""
    if timeout_s is None:
        timeout_s = float(os.environ.get("SWDB_SESSION_LOCK_TIMEOUT_S", "3600"))
    path = session_lock_path(kind)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    started = time.monotonic()
    waited = False
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                waited = True
                if time.monotonic() - started >= timeout_s:
                    raise Failure(f"another provider session holds {SESSION_LOCK} on this login; "
                                  f"waited {timeout_s:.0f} s") from None
                time.sleep(poll_s)
        os.ftruncate(fd, 0)
        os.write(fd, f"pid={os.getpid()} host={os.uname().nodename}\n".encode())
    except BaseException:
        os.close(fd)
        raise
    return fd, {"lock": SESSION_LOCK, "waited": waited, "wait_s": round(time.monotonic() - started, 3)}


def release_session(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _atomic_write(path, data):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".swdb-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)
        raise


@dataclass
class Copy:
    """A private login copy and the source snapshot it was taken from."""
    kind: str
    source: Path
    path: Path
    snapshot_sha256: str
    session_fd: int = None
    session_lock: dict = field(default_factory=dict)

    def release(self):
        """Release the session lock (idempotent)."""
        fd, self.session_fd = self.session_fd, None
        if fd is not None:
            release_session(fd)

    def write_back(self):
        """Write back (see _write_back), then release the session lock."""
        try:
            receipt = self._write_back()
        finally:
            self.release()
        if self.session_lock:
            receipt["session_lock"] = dict(self.session_lock)
        return receipt

    def _write_back(self):
        """Return a value-free receipt; write a refreshed copy back to the source.

        Written only when the copy changed, is a well-formed login, and the source
        still holds the snapshot this session started from (compare-and-swap under
        the lock), so a newer login from `codex login` or another session wins.
        """
        receipt = {"source_sha256_before": self.snapshot_sha256, "changed": "no", "written_back": False}
        try:
            data = self.path.read_bytes() if not self.path.is_symlink() else None
        except FileNotFoundError:
            data = None
        if data is None:
            receipt["reason"] = "login copy missing"
            return receipt
        receipt["copy_sha256"] = _sha(data)
        if receipt["copy_sha256"] == self.snapshot_sha256:
            receipt["reason"] = "unchanged"
            return receipt
        receipt["changed"] = "yes"
        why = problem(self.kind, data)
        if why:
            receipt["reason"] = "malformed copy: " + why
            return receipt
        with locked(self.source):
            if self.source.is_symlink() or not self.source.is_file():
                receipt["reason"] = "source login unavailable"
                return receipt
            current = _sha(self.source.read_bytes())
            if current != self.snapshot_sha256:
                receipt.update(reason="source changed during session; newer login kept",
                               source_sha256_current=current)
                return receipt
            _atomic_write(self.source, data)
        receipt.update(written_back=True, reason="refreshed login written back",
                       source_sha256_after=receipt["copy_sha256"])
        return receipt


def copy(kind, destination, unavailable="provider login file is unavailable"):
    """Copy the source login to `destination` (mode 0600); return its Copy handle."""
    original = source(kind)
    if original.is_symlink() or not original.is_file():
        raise Failure(unavailable)
    # The session lock is taken before the copy and held until write_back/release.
    fd, receipt = acquire_session(kind)
    try:
        with locked(original):
            shutil.copyfile(original, destination)
        Path(destination).chmod(0o600)
        return Copy(kind, original, Path(destination), _sha(Path(destination).read_bytes()),
                    session_fd=fd, session_lock=receipt)
    except BaseException:
        release_session(fd)
        raise


def preflight(kind):
    """Fast, offline login check before any session is spent (no network, no values).

    Returns {"state": "ok"|"login", "reason", "source_sha256"}. A missing or malformed
    login is a login failure; a well-formed login can still be refused by the server,
    which callers detect by comparing `source_sha256` with a login known to have failed.
    """
    original = source(kind)
    if original.is_symlink() or not original.is_file():
        return {"state": "login", "reason": "provider login file is unavailable", "source_sha256": None}
    data = original.read_bytes()
    why = problem(kind, data)
    return {"state": "login" if why else "ok", "reason": why or "well-formed login",
            "source_sha256": _sha(data)}

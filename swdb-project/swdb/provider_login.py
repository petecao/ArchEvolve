"""Provider login copies and their write-back. Created: 2026-10-04 ET. Updated: 2026-10-05 ET.

A guarded provider session runs on a private copy of the provider login file
(Codex `auth.json`, Claude `.credentials.json`) in its own provider home. Codex
refreshes its OAuth tokens inside a session and persists the result only to the
login file in its home; the refresh token is single use. If the copy were simply
deleted, the source login would keep the consumed refresh token and every later
session would fail with 401 `token_invalidated` / `refresh_token_reused`
(ticket 58, attempt a1). So, when a session ends, a changed copy that is still a
well-formed login is written back to the source atomically under a file lock.

Token values are never logged or recorded: receipts hold only short file hashes
(the first 16 hex digits of a SHA-256, named `*_short_hash` since 2026-10-05; receipts
written before then call the same values `*_sha256`) and changed/written flags.

Session lock (ticket 62, 2026-10-04 ET; agent-decided under Yan-Ru's delegation,
revisable): every real provider session holds an exclusive flock on
`swdb-session.lock` in the provider's home (CODEX_HOME / CLAUDE_CONFIG_DIR) from the
moment its login copy is taken until the copy has been written back. Two sessions on
one login therefore never overlap, across agents, clones and processes. A waiting
session polls up to `SWDB_SESSION_LOCK_TIMEOUT_S` seconds (default
SESSION_LOCK_TIMEOUT_S) and then fails before any provider call. The write-back lock
`<login file>.swdb-lock` and the atomic write's temporary file live beside the login.

Provider home on lab hosts (code review H3, 2026-10-05 ET; agent-decided under Yan-Ru's
delegation, revisable): nothing may be written under $HOME on a lab host
(`.claude/rules/remote_server.md`), and the session lock, the write-back lock and the
refreshed login are all written in the provider home. On a lab host (a short host name
in LAB_HOSTS, or `SWDB_LAB_HOST=1`) CODEX_HOME / CLAUDE_CONFIG_DIR must therefore be set
and must not resolve to or under $HOME (or the account's home directory); otherwise the
session stops as a login failure before any lock or copy. Off lab hosts (the Mac) an unset
variable still means `~/.codex` / `~/.claude`, so local development needs no setting.

2026-10-05 ET (code review P7-P9, J1-J6): one `LoginSpec` per provider kind (an unknown
kind is refused, never treated as Claude); `start` is the one place a session's login file
is placed; `Copy.write_back_safely` the one write-back that never blocks cleanup; the copy is
created O_CREAT|O_EXCL with mode 0600 (no window with a wider mode, never through a planted
link) and the directory is fsynced after the atomic replace.
"""

import contextlib
import errno
import fcntl
import hashlib
import json
import os
import pwd
import socket
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from swdb.cli import Failure
from swdb.provider_adapters import LoginRequired

LOCK_SUFFIX = ".swdb-lock"
SESSION_LOCK = "swdb-session.lock"
SESSION_LOCK_POLL_S = 0.2  # short: a 5 s poll lost every gap between back-to-back sessions (a6, 2026-10-04)
SESSION_LOCK_TIMEOUT_S = 3600
SESSION_LOCK_TIMEOUT_ENV = "SWDB_SESSION_LOCK_TIMEOUT_S"
#: H3: hosts where nothing may be written under $HOME (`.claude/rules/remote_server.md`).
LAB_HOSTS = frozenset({"mbit10", "mbit9"})
LAB_HOST_ENV = "SWDB_LAB_HOST"
#: The placeholder login of a contract fixture that emulates no provider kind (its historical name).
FIXTURE_LOGIN_NAME = ".credentials.json"
FIXTURE_LOGIN = b'{"fixture":true}\n'
SHORT_HASH_DIGITS = 16


@dataclass(frozen=True)
class LoginSpec:
    """Where one provider kind keeps its login and what a token refresh may change (P8/J1)."""
    home_variable: str            # the provider's own home setting
    default_home: str             # its home below ~ when the variable is unset (never on a lab host)
    file_name: str                # the login file inside that home
    token_object: str             # the object holding the OAuth tokens
    required_tokens: tuple        # nonempty strings a well-formed login has in token_object
    refreshable_top: frozenset    # top-level keys a token refresh may change
    refreshable_tokens: frozenset  # keys inside token_object a token refresh may change
    api_key_field: str = None     # a top-level API key that makes a login with nothing to refresh


LOGINS = {
    "codex": LoginSpec("CODEX_HOME", ".codex", "auth.json", "tokens", ("access_token", "refresh_token"),
                       frozenset({"last_refresh"}), frozenset({"access_token", "refresh_token", "id_token"}),
                       api_key_field="OPENAI_API_KEY"),
    "claude": LoginSpec("CLAUDE_CONFIG_DIR", ".claude", ".credentials.json", "claudeAiOauth",
                        ("accessToken", "refreshToken"), frozenset(),
                        frozenset({"accessToken", "refreshToken", "expiresAt"})),
}


def login_spec(kind):
    try:
        return LOGINS[kind]
    except KeyError:
        raise Failure(f"unknown provider login kind: {kind!r}") from None


def login_name(kind):
    return login_spec(kind).file_name


def lab_host():
    """True on a lab host (H3): a short host name in LAB_HOSTS, or SWDB_LAB_HOST=1."""
    return socket.gethostname().split(".")[0] in LAB_HOSTS or os.environ.get(LAB_HOST_ENV) == "1"


def _home_roots():
    roots = {os.path.realpath(os.path.expanduser("~"))}
    with contextlib.suppress(KeyError):
        roots.add(os.path.realpath(pwd.getpwuid(os.getuid()).pw_dir))
    return roots


def provider_home(kind):
    """The provider's home: CODEX_HOME / CLAUDE_CONFIG_DIR, checked against the lab-host rule (H3)."""
    layout = login_spec(kind)
    value = os.environ.get(layout.home_variable)
    if not lab_host():
        return Path(value) if value else Path.home() / layout.default_home
    if not value:
        raise LoginRequired(f"provider login home {layout.home_variable} is unset; on a lab host it must name a "
                            "folder outside $HOME (for example under /data1/yanruj)")
    resolved = os.path.realpath(value)
    for root in _home_roots():
        if resolved == root or resolved.startswith(root.rstrip(os.sep) + os.sep):
            raise LoginRequired(f"provider login home {layout.home_variable} resolves under $HOME ({resolved}); "
                                "a lab host writes nothing there")
    return Path(value)


def source(kind):
    """The provider's own login file in its home."""
    return provider_home(kind) / login_name(kind)


def short_hash(data):
    """The first SHORT_HASH_DIGITS hex digits of a SHA-256 (a receipt value, never a full digest)."""
    return hashlib.sha256(data).hexdigest()[:SHORT_HASH_DIGITS] if data is not None else None


def problem(kind, data):
    """Why bytes are not a well-formed login (None when they are). Never echoes values."""
    layout = login_spec(kind)
    try:
        parsed = json.loads(data)
    except (ValueError, UnicodeDecodeError, RecursionError):
        # RecursionError: deeply nested input (a provider controls the copy's bytes).
        return "not valid JSON"
    if not isinstance(parsed, dict):
        return "not a JSON object"
    key = layout.token_object
    if layout.api_key_field and key not in parsed and isinstance(parsed.get(layout.api_key_field), str) \
            and parsed[layout.api_key_field]:
        return None                        # API-key login: nothing to refresh
    inner = parsed.get(key)
    if not isinstance(inner, dict):
        return f"missing object {key!r}"
    missing = [name for name in layout.required_tokens if not isinstance(inner.get(name), str) or not inner[name]]
    if missing:
        return f"missing {key}.{'/'.join(missing)}"
    return None


def identity_change(kind, before, after):
    """Why `after` is not a token refresh of the same login as `before` (None when it is).

    Added 2026-10-04 ET (final code review). The provider controls its login copy, so a
    session must not be able to plant a different account, login mode or API key in
    the user's source login: only the refreshable token fields may differ.
    """
    layout = login_spec(kind)
    try:
        old, new = json.loads(before), json.loads(after)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return "not valid JSON"
    key, top, inner = layout.token_object, layout.refreshable_top, layout.refreshable_tokens
    if not isinstance(old, dict) or not isinstance(new, dict) \
            or not isinstance(old.get(key), dict) or not isinstance(new.get(key), dict):
        return "not an OAuth login"
    if {k: v for k, v in old.items() if k not in top | {key}} \
            != {k: v for k, v in new.items() if k not in top | {key}}:
        return "account or login mode changed"
    if {k: v for k, v in old[key].items() if k not in inner} \
            != {k: v for k, v in new[key].items() if k not in inner}:
        return "account or login mode changed"
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


def acquire_session(kind, timeout_s=None, poll_s=None):
    """Hold the exclusive session lock of this login; return (fd, value-free receipt)."""
    if timeout_s is None:
        timeout_s = float(os.environ.get(SESSION_LOCK_TIMEOUT_ENV, SESSION_LOCK_TIMEOUT_S))
    if poll_s is None:
        poll_s = SESSION_LOCK_POLL_S
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


def _fsync_directory(folder):
    """Make a rename in `folder` durable (P9). A filesystem that cannot fsync a directory is accepted."""
    fd = os.open(folder, os.O_RDONLY)
    try:
        os.fsync(fd)
    except OSError as exc:
        if exc.errno not in (errno.EINVAL, errno.ENOTSUP, errno.EBADF):
            raise
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
    _fsync_directory(path.parent)


def create_private(path, data):
    """Create `path` with mode 0600 and write `data` (P9): exclusive, never through a symbolic link."""
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            fd = None
            handle.write(data)
    except BaseException:
        if fd is not None:
            os.close(fd)
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        raise


@dataclass
class Copy:
    """A private login copy and the source snapshot it was taken from."""
    kind: str
    source: Path
    path: Path
    snapshot_short_hash: str
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

    def write_back_safely(self):
        """`write_back` for cleanup paths (P7): an ordinary failure is recorded in the value-free
        receipt instead of raised, so it never blocks deleting the copy or the audit."""
        try:
            return self.write_back()
        except Exception as exc:
            self.release()
            return {"written_back": False, "reason": f"write-back failed: {type(exc).__name__}"}

    def _write_back(self):
        """Return a value-free receipt; write a refreshed copy back to the source.

        Written only when the copy changed, is a well-formed login, and the source
        still holds the snapshot this session started from (compare-and-swap under
        the lock), so a newer login from `codex login` or another session wins.
        """
        receipt = {"source_short_hash_before": self.snapshot_short_hash, "changed": "no", "written_back": False}
        try:
            data = self.path.read_bytes() if not self.path.is_symlink() else None
        except FileNotFoundError:
            data = None
        if data is None:
            receipt["reason"] = "login copy missing"
            return receipt
        receipt["copy_short_hash"] = short_hash(data)
        if receipt["copy_short_hash"] == self.snapshot_short_hash:
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
            current_bytes = self.source.read_bytes()
            current = short_hash(current_bytes)
            if current != self.snapshot_short_hash:
                receipt.update(reason="source changed during session; newer login kept",
                               source_short_hash_current=current)
                return receipt
            changed = identity_change(self.kind, current_bytes, data)
            if changed:
                receipt["reason"] = "not a token refresh of the source login: " + changed
                return receipt
            _atomic_write(self.source, data)
        receipt.update(written_back=True, reason="refreshed login written back",
                       source_short_hash_after=receipt["copy_short_hash"])
        return receipt


def take_session_copy(kind, destination, unavailable="provider login file is unavailable"):
    """Hold this login's session lock and copy the source login to `destination` (mode 0600).

    Returns the Copy handle; its `write_back` (or `release`) ends the session. Renamed from
    `copy` on 2026-10-05 ET (J6): it takes the session lock, not only a copy."""
    original = source(kind)
    if original.is_symlink() or not original.is_file():
        raise LoginRequired(unavailable)
    # The session lock is taken before the copy and held until write_back/release.
    fd, receipt = acquire_session(kind)
    try:
        with locked(original):
            data = original.read_bytes()
        create_private(destination, data)
        return Copy(kind, original, Path(destination), short_hash(data), session_fd=fd, session_lock=receipt)
    except BaseException:
        release_session(fd)
        raise


def start(config, home, unavailable="provider login file is unavailable"):
    """Place one session's login file in its fresh provider home; return (path, Copy or None).

    P7 (2026-10-05 ET): the one start shared by the rewriting workspace, the agent roles and
    prompt-only sessions. A contract fixture gets a placeholder file and no Copy. A real provider
    is refused before any login is copied unless the Linux Landlock guard (ABI >= 4) is available;
    it then holds the session lock and a private copy."""
    fixture = config["kind"] == "external_fixture"
    kind = config.get("emulates", config["kind"])
    home = Path(home)
    if fixture:
        path = home / (login_name(kind) if kind in LOGINS else FIXTURE_LOGIN_NAME)
        create_private(path, FIXTURE_LOGIN)
        return path, None
    path = home / login_name(kind)
    from swdb import provider_guard
    if provider_guard.abi() < 4:
        raise Failure("SWDB provider guard requires Linux Landlock ABI >= 4; refusing unguarded session")
    return path, take_session_copy(kind, path, unavailable)


def preflight(kind):
    """Fast, offline login check before any session is spent (no network, no values).

    Returns {"state": "ok"|"login", "reason", "source_short_hash"}. A missing or malformed
    login, or a provider home a lab host forbids (H3), is a login failure; a well-formed login
    can still be refused by the server, which callers detect by comparing `source_short_hash`
    with a login known to have failed.
    """
    try:
        original = source(kind)
    except LoginRequired as exc:
        return {"state": "login", "reason": str(exc), "source_short_hash": None}
    if original.is_symlink() or not original.is_file():
        return {"state": "login", "reason": "provider login file is unavailable", "source_short_hash": None}
    data = original.read_bytes()
    why = problem(kind, data)
    return {"state": "login" if why else "ok", "reason": why or "well-formed login",
            "source_short_hash": short_hash(data)}

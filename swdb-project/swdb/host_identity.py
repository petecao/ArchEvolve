"""The executing host's identity, for every SWDB decision keyed on it (2026-10-13 ET).

Code that only *records* the full host name as provenance (calibration contexts,
certification and library-operation records, host observations) still reads
`socket.gethostname()`; those modules' source digests are pinned by committed records,
and no policy depends on the value. `dx100_witness` and `provider_login` keep their own
reads for the same pinning reason and because their tests patch the module's `socket`.

Lab policy keys on the host name: on `mbit10` an evaluation must hold a socket lane, builds
and source snapshots live under `/data1/yanruj`, and a dispatch preflight reads NUMA memory.
The test suite must not inherit that policy just because it runs on mbit10, so the suite
runs as a *fixture host*: `tests/conftest.py` sets `SWDB_FIXTURE_HOST` for every `swdb`
child process and patches `socket.gethostname` in the test process itself.

The override is deliberately narrow:

- It is read once, when this module is imported. A test process imports SWDB before the
  suite sets the variable, so in-process tests keep steering the host through
  `socket.gethostname` (and can still opt into mbit10 behavior by patching it to `mbit10`).
- Its value must be a reserved fixture name (`swdb-fixture` or `swdb-fixture-<suffix>`).
  It can never claim a real host, so a fixture-host record can never pass for an mbit10
  record, and no committed machine record names a fixture host.
- Without the variable, every name comes from `socket.gethostname()` unchanged, so real
  hosts keep every guard they had.
"""

import os
import re
import socket

FIXTURE_HOST_ENV = "SWDB_FIXTURE_HOST"
FIXTURE_HOST_PATTERN = r"swdb-fixture(?:-[a-z0-9]+)*"


def fixture_override(environ=None):
    """The fixture host name `environ` requests, None when unset; refuse non-fixture names."""
    value = (os.environ if environ is None else environ).get(FIXTURE_HOST_ENV)
    if not value:
        return None
    if not re.fullmatch(FIXTURE_HOST_PATTERN, value):
        raise RuntimeError(f"{FIXTURE_HOST_ENV}={value!r} is not a fixture host name "
                           f"(expected {FIXTURE_HOST_PATTERN}); it cannot claim a real host")
    return value


_FIXTURE_HOST = fixture_override()


def full_name():
    """The host name as `socket.gethostname()` reports it, or the fixture host."""
    return _FIXTURE_HOST or socket.gethostname()


def short_name():
    """The host name up to its first dot (`mbit10`), or the fixture host."""
    return full_name().split(".")[0]

"""Frama-C 33.0 as the parser and type checker of formal halves (`swdb validate`).

Created: 2026-10-14 ET (Probata proof of concept ticket 20). Design: formal-verification map 16
items 1 and 5 (gate 1: a formal half parses and type-checks). Format:
docs/reference/format-v0.4-formal-frame.md.

- Where Frama-C comes from: `SWDB_FRAMA_C` (a command line; `none` means "treat as missing"), else
  the opam switch `framac-33`, else `frama-c` on PATH. Only version 33.0 counts.
- The check is a parse only (no WP, no prover): the x86_64 machdep WP runs use, annotation errors
  fatal (`-kernel-warn-key annot-error=abort`), in a fresh temporary folder.
- When Frama-C is missing the caller reports each formal half as unchecked, never as valid.
"""

import hashlib
import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

REQUIRED_VERSION = '33.0'
FLAGS = ('-machdep', 'x86_64', '-kernel-warn-key', 'annot-error=abort')
TIMEOUT_SECONDS = 120
_FOUND = {}
_CHECKED = {}


@dataclass(frozen=True)
class Tool:
    command: tuple      # the Frama-C command line, or () when missing
    version: str        # the version it reports, or '' when missing
    missing: str        # why it is unusable ('' when usable)


def locate():
    """The Frama-C this process uses (looked up once per process and SWDB_FRAMA_C value)."""
    key = os.environ.get('SWDB_FRAMA_C', '')
    if key in _FOUND:
        return _FOUND[key]
    if key == 'none':
        tool = Tool((), '', 'Frama-C disabled by SWDB_FRAMA_C=none')
    else:
        if key:
            command = tuple(shlex.split(key))
        elif shutil.which('opam') and _switch_exists():
            command = ('opam', 'exec', '--switch=framac-33', '--', 'frama-c')
        elif shutil.which('frama-c'):
            command = ('frama-c',)
        else:
            command = ()
        tool = _probe(command)
    _FOUND[key] = tool
    return tool


def _switch_exists():
    try:
        done = subprocess.run(['opam', 'switch', 'list', '--short'], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False
    return 'framac-33' in done.stdout.split()


def _probe(command):
    if not command:
        return Tool((), '', 'Frama-C not found (opam switch framac-33, frama-c on PATH or SWDB_FRAMA_C)')
    try:
        done = subprocess.run([*command, '-version'], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return Tool((), '', f'Frama-C did not start: {exc}')
    version = (done.stdout.split() or [''])[0]
    if done.returncode != 0 or not version:
        return Tool((), '', 'Frama-C did not report a version')
    if version != REQUIRED_VERSION:
        return Tool((), version, f'Frama-C {version} found; formal halves are checked with {REQUIRED_VERSION}')
    return Tool(tuple(command), version, '')


def typecheck(tool, source, includes=()):
    """None when Frama-C parses and type-checks the C file `source`, else its messages.

    `includes` are (name, path) pairs copied next to the file. Results are cached per process."""
    key = hashlib.sha256(repr((tool.command, source, [(n, Path(p).read_bytes()) for n, p in includes]))
                         .encode()).hexdigest()
    if key in _CHECKED:
        return _CHECKED[key]
    with tempfile.TemporaryDirectory(prefix='swdb-framac-') as folder:
        for name, path in includes:
            shutil.copyfile(path, Path(folder) / name)
        (Path(folder) / 'formal_half.c').write_text(source)
        try:
            done = subprocess.run([*tool.command, *FLAGS, 'formal_half.c'], cwd=folder, capture_output=True,
                                  text=True, timeout=TIMEOUT_SECONDS)
            output = done.stdout + done.stderr
            failed = done.returncode != 0 or 'Ignoring' in output
        except (OSError, subprocess.SubprocessError) as exc:
            output, failed = f'Frama-C did not finish: {exc}', True
    result = _messages(output) if failed else None
    _CHECKED[key] = result
    return result


def _messages(output):
    """Frama-C's error lines, one line each, without the boilerplate abort lines."""
    lines, current = [], []
    for raw in output.splitlines():
        line = raw.strip()
        if not line or line.startswith('[kernel] Parsing') or 'Frama-C aborted' in line \
                or 'treated as fatal error' in line:
            continue
        if raw.startswith('[') and current:
            lines.append(' '.join(current))
            current = []
        current.append(line)
    if current:
        lines.append(' '.join(current))
    return '; '.join(lines) or 'Frama-C failed without a message'

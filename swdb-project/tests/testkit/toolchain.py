"""Compilers and script modules for tests. Created 2026-10-05 ET (code review T3).

One definition of what several test modules repeated: the certification compiler (GCC with
OpenMP, skipping when absent), a host C++ compiler, and loading a script file as a module.
Updated 2026-10-12 ET (cpud review 8b): `toolchain_flags` for native runner tests on Linux.
"""

import importlib.util
import os
import shlex
import shutil

import pytest

# The header/library selectors the native runners accept in `--toolchain-flag` (their own allowlist).
TOOLCHAIN_PREFIXES = ('--gcc-install-dir=', '--gcc-toolchain=', '--sysroot=', '-resource-dir=', '-stdlib=')


def toolchain_flag_args(environ=None):
    """`--toolchain-flag=<flag>` arguments from `SWDB_TOOLCHAIN_FLAGS` (shell-split; empty when unset).

    On mbit10, clang 22 picks a GCC without libstdc++ headers unless every compile gets
    `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`, as every real calibration run passes:
    `SWDB_TOOLCHAIN_FLAGS=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`. The Mac needs none."""
    flags = shlex.split((os.environ if environ is None else environ).get('SWDB_TOOLCHAIN_FLAGS', ''))
    bad = [f for f in flags if not f.startswith(TOOLCHAIN_PREFIXES)]
    if bad:
        raise ValueError(f'SWDB_TOOLCHAIN_FLAGS may select headers/libraries only: {bad}')
    return ['--toolchain-flag=' + f for f in flags]


@pytest.fixture
def toolchain_flags():
    """Runner arguments that select this host's C++ headers and libraries (see `toolchain_flag_args`)."""
    return toolchain_flag_args()


def load_script(path, name=None):
    """Execute the script at `path` as a fresh module named `name` (default: its stem)."""
    spec = importlib.util.spec_from_file_location(name or path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_gcc_openmp():
    """The certification compiler (GCC with OpenMP); skips the calling test when it is absent."""
    from swdb import certification
    from swdb.cli import Failure
    try:
        return certification.compiler()
    except Failure:
        pytest.skip("certification requires GCC with OpenMP")


def find_cxx():
    """A host C++ compiler (clang++, else g++), or None."""
    return shutil.which("clang++") or shutil.which("g++")


@pytest.fixture
def gcc_openmp():
    return require_gcc_openmp()


@pytest.fixture
def cxx():
    """A host C++ compiler; skips the test when there is none."""
    compiler = find_cxx()
    if compiler is None:
        pytest.skip("C++ compiler unavailable")
    return compiler

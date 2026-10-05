"""Compilers and script modules for tests. Created 2026-10-05 ET (code review T3).

One definition of what several test modules repeated: the certification compiler (GCC with
OpenMP, skipping when absent), a host C++ compiler, and loading a script file as a module.
"""

import importlib.util
import shutil

import pytest


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

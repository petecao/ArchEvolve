"""Bounded-memory validation of artifact-size SG workloads. Updated 2026-09-25."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure

SOURCE = Path(__file__).resolve().parents[1] / "tools/bfs_native/sg_identity.cc"


def inspect(path, width, options):
    """Stream exact canonical bytes from a checked CSR reader into SHA256.

    The graph is mmap-backed by the helper; Python holds at most one 1 MiB block.
    Compile and validation have independent bounded wall budgets. The helper is
    rebuilt from the repository source, not accepted from a request executable.
    """
    options = options or {}
    if not isinstance(options, dict):
        raise Failure("parser options must be a mapping")
    work = options.get("work_dir")
    if not isinstance(work, str) or not Path(work).is_absolute():
        raise Failure("streaming SG verification requires parser.work_dir outside the repository")
    work = artifacts.external_directory(work)
    budgets = {}
    for name, default, cap in (("compile_timeout_s", 60, 600), ("timeout_s", 900, 7200)):
        value = options.get(name, default)
        if type(value) not in (int, float) or not 0 < value <= cap:
            raise Failure(f"parser.{name} must be positive and at most {cap}")
        budgets[name] = value
    compiler = shutil.which("c++") or shutil.which("g++")
    if not compiler:
        raise Failure("streaming SG verification requires a C++ compiler")
    source_hash = artifacts.file_hash(SOURCE)
    before = Path(path).stat()
    with tempfile.TemporaryDirectory(prefix="swdb-sg-", dir=work) as directory:
        binary = Path(directory) / "sg-identity"
        try:
            built = subprocess.run([compiler, "-std=c++11", "-O3", str(SOURCE), "-o", str(binary)],
                                   capture_output=True, text=True, timeout=budgets["compile_timeout_s"])
        except subprocess.TimeoutExpired:
            raise Failure("streaming SG parser compilation exceeded its wall budget") from None
        if built.returncode:
            raise Failure(f"streaming SG parser compilation failed: {built.stderr[-2000:]}")
        h = hashlib.sha256()
        expired = threading.Event()
        with tempfile.TemporaryFile(dir=directory) as diagnostics:
            process = subprocess.Popen([str(binary), str(path), str(width)], stdout=subprocess.PIPE,
                                       stderr=diagnostics, start_new_session=True)
            def timeout():
                expired.set()
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            timer = threading.Timer(budgets["timeout_s"], timeout)
            timer.start()
            try:
                for block in iter(lambda: process.stdout.read(1024*1024), b""):
                    h.update(block)
                process.wait()
            finally:
                timer.cancel()
                timer.join()
                process.stdout.close()
                if process.poll() is None:
                    process.kill()
                    process.wait()
            diagnostics.seek(0)
            detail = diagnostics.read(4096).decode(errors="replace")
        if expired.is_set():
            raise Failure("streaming SG validation exceeded its wall budget")
        if process.returncode:
            raise Failure(detail.strip() or "streaming SG validation failed")
        try:
            realized = json.loads(detail)
        except ValueError:
            raise Failure("streaming SG parser returned invalid dimensions") from None
    after = Path(path).stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise Failure("SG input changed during canonical verification")
    return {"num_vertices": realized["num_vertices"], "directed": realized["directed"],
            "_streaming": True, "canonical_sha256": h.hexdigest(), "realized": realized,
            "verification": {"method": "exact_mmap_csr_transpose_membership", "parser_sha256": source_hash,
                             "compiler": os.path.realpath(compiler), "budgets": budgets}}

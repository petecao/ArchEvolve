"""Commit-pinned copies of repository records and library (code review T4). Created 2026-10-05 ET.

Tests that read the repository's real evidence used to copy the live `records/` (and `library/`)
folder, so every later run committed to the repository could change what they read and break
them (for example ticket 57's recorded legality facts, or the typed-library recovery r1 records).
They now read those folders exactly as committed at a pinned commit, checked by git tree id, so
the evidence under test is fixed until a test deliberately moves its pin.
"""

import io
import subprocess
import tarfile
from pathlib import Path

import pytest

from conftest import REPO

#: yanrujhou_main when these pins were made (2026-10-05 ET, ticket 78 Linux verification recorded).
EVIDENCE_COMMIT = "03b9d3b6bf5845140b227300c1fbe76d08754870"
#: The commit before the typed-library a2 recovery r1 results were recorded (3e9061b, 2026-10-03).
PRE_RECOVERY_COMMIT = "6cfcd245ba34c8df5947307aad2cf2353400b281"
#: git tree ids of swdb-project/<folder> at those commits.
TREES = {(EVIDENCE_COMMIT, "records"): "0c35f25b352407519d76b1227c9b333113b5037e",
         (EVIDENCE_COMMIT, "library"): "663335076e1f1c42205c166d9a7549793ca101e3",
         (PRE_RECOVERY_COMMIT, "records"): "cc4349ecf42bf08bb3496e41fdc70bf576eb8aa4"}


def _git(*args, cwd=REPO):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=120)
    if result.returncode:
        pytest.fail(f"pinned repository content needs git history: git {' '.join(args[:2])} failed: "
                    + result.stderr.decode(errors="replace").strip()[:300])
    return result.stdout


def pinned_folder(folder, destination, *, commit=EVIDENCE_COMMIT):
    """Extract swdb-project/`folder` as committed at `commit` into destination/`folder`.

    The folder's git tree id must equal its pin in TREES, so the copy is exactly the pinned content."""
    prefix = _git("rev-parse", "--show-prefix").decode().strip()
    tree = _git("rev-parse", f"{commit}:{prefix}{folder}").decode().strip()
    assert tree == TREES[commit, folder], f"{folder} at {commit[:12]} is tree {tree}, not its pin"
    target = Path(destination) / folder
    target.mkdir(parents=True, exist_ok=False)
    # From a subdirectory, git archive keeps only paths under it; the tree's paths are relative.
    top = _git("rev-parse", "--show-toplevel").decode().strip()
    with tarfile.open(fileobj=io.BytesIO(_git("archive", "--format=tar", tree, cwd=top))) as archive:
        archive.extractall(target, filter="data")
    assert any(target.iterdir()), f"pinned {folder} at {commit[:12]} extracted nothing"
    return target

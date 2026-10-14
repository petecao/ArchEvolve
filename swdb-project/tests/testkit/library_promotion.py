"""Make a library entry shared and certified in a test store. Created 2026-10-14 ET (Probata PoC 63).

ArchEvolve mode uses shared certified contracts only (ADR 0007): `swdb promote` records Yan-Ru's review,
and a review needs an execution certification of the entry's current content. No certification runs in
these tests, so the receipt is a synthetic execution-envelope test double (as in test_library_submit);
the review itself is written by the real `swdb promote` command.
"""

from pathlib import Path

import yaml

from conftest import run_swdb


def execution_double(records, library, entry_id):
    """A synthetic execution-certification receipt of the entry's current content (test double only)."""
    from swdb.library import Library
    lib = Library(library)
    rid = f"certification.test-double.{entry_id.replace('.', '-')}"
    record = {"schema_version": "0.4", "kind": "certification", "id": rid, "status": "draft",
              "created": "2026-10-14", "updated": "2026-10-14",
              "provenance": [{"id": "fixture", "kind": "agent_run", "uri": None,
                              "description": "Synthetic execution-envelope test double only; no executed certification."}],
              "producer": {"name": "library-promotion-test-double", "role": "sw", "test_client": True},
              "entry": {"id": entry_id, "content_sha256": lib.content_sha256(entry_id)},
              "dependencies": lib.dependency_pins(entry_id),
              "command": {"version": "fixture", "sources_sha256": "0" * 64}, "host": {},
              "matrix": [{"status": "passed"}], "negative_controls": [{"status": "rejected"}],
              "verdict": "certified", "evidence_basis": "simulated", "evidence_kind": "execution"}
    folder = Path(records) / "certifications"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{rid}.yaml").write_text(yaml.safe_dump(record, sort_keys=False))
    return rid


def promote(records, library, entry_id):
    """The test double, then `swdb promote` (Yan-Ru's review): the entry is shared and certified."""
    execution_double(records, library, entry_id)
    promoted = run_swdb("promote", entry_id, "--records", records, "--library", library, "--format", "json")
    assert promoted.returncode == 0, promoted.stdout + promoted.stderr

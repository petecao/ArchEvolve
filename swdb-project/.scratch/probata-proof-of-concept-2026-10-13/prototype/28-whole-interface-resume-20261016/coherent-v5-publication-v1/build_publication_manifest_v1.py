"""Exact reviewed V5 publication selection; never stages or changes Git."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parents[1]
REPO = POC.parents[2]
SWDB = REPO / "swdb-project"
EXCLUDE = ("abi-retained-", "abi-role-transport-", "abi-memory-", "abi-enum-", "abi-small-",
           "finite-", "memory-unit-", "memory-normalized-", "normalized-unit-envelope-v4")
SEEDS = [
    WHOLE / "production-route-v5/source-packet-v5.json",
    WHOLE / "production-route-v5-independent-review/independent-production-route-v5-spec-review-20261016.json",
    WHOLE / "production-route-v5-independent-review/helper-byte-lineage-v5.json",
    POC / "evidence/t28-coherent-v5-root-standards-review-20261016.json",
    POC / "evidence/t28-coherent-v5-root-application-20261016.json",
    POC / "evidence/t28-coherent-v5-root-physical-import-smoke-20261016.json",
    POC / "evidence/resume-20261016-lane-coordination/t28-coherent-v5-complementary-standards-helper-lineage-20261016.json",
    WHOLE / "first-pair-planner-v3/source-packet-v3.json",
    POC / "evidence/t28-prospective-compiler-descriptor-root-selection-v1-20261016.json",
]
def sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(REPO).as_posix(), bytes=len(raw), sha256=sha(raw))
def declared(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str) and type(value.get("bytes")) is int:
            yield value
        for child in value.values(): yield from declared(child)
    elif isinstance(value, list):
        for child in value: yield from declared(child)

def build():
    assert REPO.name == "ArchEvolve" and POC.name == "probata-proof-of-concept-2026-10-13"
    application = json.loads((POC / "evidence/t28-coherent-v5-root-application-20261016.json").read_bytes())
    live = {}
    for row in application["applied_paths"]:
        path = REPO / row["path"]
        assert path.is_relative_to(SWDB / "swdb") and pin(path) == row
        live[row["path"]] = row
    assert len(live) == 50
    artifacts = {}; seen = set(); queue = list(SEEDS); external = set()
    while queue:
        path = queue.pop()
        if path in seen: continue
        seen.add(path)
        if not path.is_relative_to(SWDB) or not path.is_file():
            external.add(str(path)); continue
        if not path.is_relative_to(POC): continue
        if path.is_relative_to(WHOLE) and str(path.relative_to(WHOLE)).startswith(EXCLUDE): continue
        assert "__pycache__" not in path.parts and path.suffix != ".pyc"
        assert not path.is_relative_to(POC / "issues")
        assert path.name not in {"map.md", "resume.md", "execution-20261016.md"}
        raw = path.read_bytes(); artifacts[path.relative_to(REPO).as_posix()] = pin(path)
        if path.suffix != ".json": continue
        try: value = json.loads(raw)
        except (ValueError, UnicodeError): continue
        for row in declared(value):
            target = Path(row["path"])
            if not target.is_absolute(): continue
            # Live production baselines in old receipts are historical Git inputs;
            # only the exact fifty applied rows above are selected here.
            if target.is_relative_to(SWDB / "swdb"): continue
            if target.is_file():
                data = target.read_bytes()
                assert len(data) == row["bytes"] and sha(data) == row["sha256"], str(target)
            queue.append(target)
    artifacts[Path(__file__).resolve().relative_to(REPO).as_posix()] = pin(Path(__file__).resolve())
    assert not set(live) & set(artifacts)
    rows = [live[name] for name in sorted(live)] + [artifacts[name] for name in sorted(artifacts)]
    out = dict(schema="reviewed-coherent-V5-selective-publication-1", date="2026-10-16 ET",
        exact_applied_production_paths=50, reproducible_artifact_paths=len(artifacts),
        production_rows=[live[name] for name in sorted(live)], artifact_rows=[artifacts[name] for name in sorted(artifacts)],
        seeds=[pin(path) for path in SEEDS], historical_external_or_missing_reference_count=len(external),
        selection_policy="Fifty exact root-applied source files plus pinned local JSON dependency closure of selected reviewed V5/profile/control/lineage seeds; no directory-wide WIP selection.",
        excluded=["new ABI and finite successors", "root five shared trackers", "ticket25/vector preparation artifacts", "external Claude ticket7", "unselected live production modules", "all bytecode/caches", "remote raw payloads"],
        actual_public_Library_or_proof_acceptance=False, staged_committed_or_pushed=False,
        checkpoint_scope="Reviewed coherentV5 implementation and reproducible source preparation only. Public tests/profile and later reviewed ABI/finite union remain pending.")
    output = HERE / "publication-manifest-v1.json"
    output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    selected = sorted({row["path"] for row in rows} | {output.relative_to(REPO).as_posix()})
    encoded = b"".join(name.encode() + b"\0" for name in selected)
    (HERE / "publication-paths-v1.nul").write_bytes(encoded)
    temporary = Path("/private/tmp/probata-resume-20261016-t28-coherent-v5-publication-v1.paths0")
    with temporary.open("xb") as handle: handle.write(encoded)
    print(json.dumps(dict(manifest=pin(output), nul_path=str(temporary), nul_bytes=len(encoded), nul_sha256=sha(encoded),
        selected_paths=len(selected), production=50, artifacts=len(artifacts), payload_bytes=sum(row["bytes"] for row in rows)), sort_keys=True))
if __name__ == "__main__": build()

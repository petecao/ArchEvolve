"""One coherent future publication/source batch; no catalog or model writes."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def module(directory):
    path = ROOT.parent / directory / "materialize.py"
    spec = importlib.util.spec_from_file_location(directory, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def prepare(parent, output):
    output.mkdir(parents=True, exist_ok=False)
    first = module("smash_public_constructor_extent_2026_10_06").materialize(
        parent, output / "constructor"
    )
    second = module("smash_public_setbit_2026_10_07").materialize(
        output / "constructor/bitmap.h",
        output / "constructor/geometry_admission.h",
        output / "setter",
    )
    final = module("smash_public_packed_capacity_2026_10_07").materialize(
        output / "setter/bitmap.h",
        output / "setter/geometry_admission.h",
        output / "final",
    )
    receipt = {
        "publication_base": "1e12a4eb9364c3d30de756f632d19e45ec63bccb",
        "catalog_mutations": 0,
        "stages": [first, second, final],
        "next_input_scope": "complete same-ratio unsigned-long64 bitmap metadata only",
        "remaining": "CSR shape proof, defined NZA values, complete indexer EOF/consumer/wholekernel numerical correctness remain separate",
    }
    (output / "batch-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent-a081", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.parent_a081, a.output), indent=2))

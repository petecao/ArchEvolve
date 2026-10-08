"""Prepare a new CSR malformed-column regression from exact source bodies."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def function(text, marker):
    start = text.index(marker)
    brace = text.index("{", start)
    end = brace + 1
    depth = 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


def prepare(header, output):
    raw = header.read_bytes()
    if (
        hashlib.sha256(raw).hexdigest()
        != "ab6acdac30e7a4b747f1cbf84c96356ac70dd35a7a9e6e93c6555c750e710de4"
    ):
        raise ValueError("exact completed bitmap batch required")
    output.mkdir(parents=True, exist_ok=False)
    text = raw.decode()
    bodies = [
        function(text, name)
        for name in [
            "unsigned long* construct_bitmap(",
            "inline void set_bit(",
            "void construct_bitmap0_nza(",
        ]
    ]
    (output / "constructor-functions.inc").write_text(
        "\n\n".join(bodies) + "\n"
    )
    for name in [
        "csr_input_admission.h",
        "construct_csr_admitted.h",
        "test_constructor_admission.cc.txt",
    ]:
        target = output / (name[:-4] if name.endswith(".txt") else name)
        target.write_bytes((ROOT / name).read_bytes())
    geometry = (
        ROOT.parent
        / "smash_public_constructor_extent_2026_10_06/geometry_admission.h"
    )
    if (
        hashlib.sha256(geometry.read_bytes()).hexdigest()
        != "3d57d1b93c5625ec385916d25bc7799fb82b72f5f331b14718eeb4b5328fd41e"
    ):
        raise ValueError("geometry helper drift")
    (output / "geometry_admission.h").write_bytes(geometry.read_bytes())
    receipt = {
        "parent_sha256": hashlib.sha256(raw).hexdigest(),
        "files": {
            f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in output.iterdir()
        },
        "scope": "new malformed CSR column and pre-write admission only, no geometry-suite replay or values read",
    }
    (output / "fixture-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--header", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.header, a.output), indent=2))

"""Add an explicit, source-bound CSR admission entry point to the private batch."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def materialize(parent, geometry, output):
    expected = (
        "ab6acdac30e7a4b747f1cbf84c96356ac70dd35a7a9e6e93c6555c750e710de4"
    )
    if hashlib.sha256(parent.read_bytes()).hexdigest() != expected:
        raise ValueError("exact completed SMASH batch required")
    if (
        hashlib.sha256(geometry.read_bytes()).hexdigest()
        != "3d57d1b93c5625ec385916d25bc7799fb82b72f5f331b14718eeb4b5328fd41e"
    ):
        raise ValueError("geometry helper drift")
    output.mkdir(parents=True, exist_ok=False)
    for source in [
        parent,
        geometry,
        ROOT / "csr_input_admission.h",
        ROOT / "construct_csr_admitted.h",
    ]:
        (output / source.name).write_bytes(source.read_bytes())
    receipt = {
        "parent_sha256": expected,
        "files": {
            f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in output.iterdir()
        },
        "legacy_header_unchanged": True,
        "explicit_call": "include construct_csr_admitted.h after the original types/constructor; call construct_bitmap0_nza_admitted(format,matrix,row_words,column_words,value_words,declared_nnz)",
        "required_parser_obligation": "Retain original declared nnz and trusted allocated/initialized prefix lengths; original read_csr does not return them or certify successful conversions.",
        "scope": "Structural admission only; no value/NZA initialization, parser safety or wholekernel numerical grant",
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--geometry", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(materialize(a.parent, a.geometry, a.output), indent=2))

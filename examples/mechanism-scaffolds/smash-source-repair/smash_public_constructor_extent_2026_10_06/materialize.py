"""Compose constructor admission with the already reviewed typed-mask parent."""
import argparse
import hashlib
import json
from pathlib import Path

PARENT_SHA = "a08109ea94b515b9c7dbded5b5c07a4fefd4993debb312741bed08556f1c85a7"


def materialize(parent, output):
    raw = parent.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_SHA:
        raise ValueError("exact typed-mask/zero-CTZ parent required")
    text = raw.decode()
    anchor = "void construct_bitmap0_nza(smash* format, csr *matrix){"
    if text.count(anchor) != 1:
        raise ValueError("unique original constructor seam required")
    delta = '\n\t/* Reject unsupported geometry before any original constructor writes. */\n\tif (!smash_constructor_geometry_supported(matrix->size, format->compression_ratio0)) {\n\t\tfputs("Unsupported SMASH constructor geometry\\n", stderr);\n\t\texit(98);\n\t}\n'
    text = text.replace(anchor, anchor + delta)
    text = '#include "geometry_admission.h"\n' + text
    output.mkdir(parents=True, exist_ok=False)
    (output / "bitmap.h").write_text(text)
    helper = Path(__file__).parent / "geometry_admission.h"
    (output / helper.name).write_bytes(helper.read_bytes())
    receipt = {
        "parent_sha256": PARENT_SHA,
        "files": {
            f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in output.iterdir()
        },
        "scope": "geometry admission only; no ceil, padding, CSR value population or public indexer fix inferred",
        "exit_on_unsupported": 98,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(materialize(a.parent, a.output), indent=2))

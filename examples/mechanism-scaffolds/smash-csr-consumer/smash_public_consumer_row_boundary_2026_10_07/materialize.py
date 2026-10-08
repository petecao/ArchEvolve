"""One source-supported public consumer cursor comparison delta."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def materialize(source, output):
    binding = json.loads((ROOT / "source-start.json").read_text())
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["source_sha256"]:
        raise ValueError("exact pinned public consumer required")
    text = raw.decode()
    anchor = "if(j > matrix_smash.columns){ i++; j=0;}"
    if text.count(anchor) != 1:
        raise ValueError("unique public row-boundary condition required")
    changed = text.replace(anchor, "if(j >= matrix_smash.columns){ i++; j=0;}")
    output.mkdir(parents=True, exist_ok=False)
    target = output / "spmv_bitmap.c"
    target.write_text(changed)
    receipt = {
        "parent_sha256": binding["source_sha256"],
        "successor_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "delta": "one >= comparison; all other consumer source bytes unchanged",
        "scope": "Positive bound source dimensions/cursor/block extent; exact row rollover only. No payload, accumulation, NZA, indexer/ISA or wholekernel correctness grant.",
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(materialize(a.source, a.output), indent=2))

"""Versioned public setter-width delta on the reviewed constructor parent."""
import argparse
import hashlib
import json
from pathlib import Path


def materialize(parent, helper, output):
    raw = parent.read_bytes()
    if (
        hashlib.sha256(raw).hexdigest()
        != "b2fa27121a11e7b784dd36c725bd792cf8374ac87720cfe75f9be06db1d21063"
    ):
        raise ValueError("exact constructor admission parent")
    if (
        hashlib.sha256(helper.read_bytes()).hexdigest()
        != "3d57d1b93c5625ec385916d25bc7799fb82b72f5f331b14718eeb4b5328fd41e"
    ):
        raise ValueError("exact constructor helper")
    s = raw.decode()
    a = s.index("inline void set_bit(")
    b = s.index("inline void test_bit(", a)
    block = s[a:b]
    if (
        block.count("int mask;") != 1
        or block.count("0x0000000000000001 << mask") != 1
    ):
        raise ValueError("unique setter token sites")
    changed = block.replace("int mask;", "uint64_t mask;").replace(
        "0x0000000000000001 << mask", "UINT64_C(1) << mask"
    )
    output.mkdir(exist_ok=False, parents=True)
    (output / "bitmap.h").write_text(s[:a] + changed + s[b:])
    (output / helper.name).write_bytes(helper.read_bytes())
    result = {
        "parent_sha256": hashlib.sha256(raw).hexdigest(),
        "files": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in output.iterdir()
        },
        "changed_sites": 2,
        "preserved": "constructor admission, zero CTZ, indexer typed mask, public setter addressing",
        "not_granted": "index bounds, bitmap hierarchy, NZA values or fullkernel",
    }
    (output / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--helper", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(materialize(a.parent, a.helper, a.output), indent=2))

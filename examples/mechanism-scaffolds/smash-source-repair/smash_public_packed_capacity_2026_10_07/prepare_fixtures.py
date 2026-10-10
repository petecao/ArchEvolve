"""Recreate only the new finite source fixtures from exact private parents."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def function(text, marker):
    a = text.index(marker)
    b = text.index("{", a)
    end = b + 1
    depth = 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[a:end]


def prepare(parent, final, output):
    if (
        hashlib.sha256(parent.read_bytes()).hexdigest()
        != "56d6a6925f1c614eb951ded0e3769681dd8d19d12088dd547064192feae93c39"
    ):
        raise ValueError("setter parent drift")
    if (
        hashlib.sha256(final.read_bytes()).hexdigest()
        != "ab6acdac30e7a4b747f1cbf84c96356ac70dd35a7a9e6e93c6555c750e710de4"
    ):
        raise ValueError("final batch drift")
    output.mkdir(parents=True, exist_ok=False)
    names = [
        "unsigned long* construct_bitmap(",
        "inline void set_bit(",
        "inline int read_bit(",
        "void construct_bitmap1(",
    ]
    source = parent.read_text()
    parts = [function(source, n) for n in names]
    (output / "functions-original.inc").write_text("\n\n".join(parts) + "\n")
    parts[2] = (
        parts[2]
        .replace("int mask;", "uint64_t mask;")
        .replace("0x0000000000000001 << mask", "UINT64_C(1) << mask")
    )
    (output / "functions-reader-fixed.inc").write_text(
        "\n\n".join(parts) + "\n"
    )
    source = final.read_text()
    names += ["void construct_bitmap2("]
    (output / "functions-fixed.inc").write_text(
        "\n\n".join(function(source, n) for n in names) + "\n"
    )
    for name in ["allocation_fixture.cc", "fixed_allocation_fixture.cc"]:
        (output / name).write_bytes((ROOT / (name + ".txt")).read_bytes())
    result = {
        "output": str(output),
        "scope": "New tiny owned bitmap metadata fixtures only; no unaffected test replay",
        "files": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in output.iterdir()
        },
    }
    (output / "fixture-receipt.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--setter-parent", type=Path, required=True)
    p.add_argument("--final-header", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(
        json.dumps(
            prepare(a.setter_parent, a.final_header, a.output), indent=2
        )
    )

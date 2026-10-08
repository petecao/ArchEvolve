"""Extract the exact source loop for checked metadata-access regression."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def prepare(source, output):
    binding = json.loads((ROOT / "source-start.json").read_text())
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["source_sha256"]:
        raise ValueError("exact public consumer source required")
    text = raw.decode()
    start = text.index(
        "for(int e=0; e < matrix_smash.compression_ratio0; e++)"
    )
    brace = text.index("{", start)
    end = brace + 1
    depth = 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    loop = text[start:end]
    if hashlib.sha256(loop.encode()).hexdigest() != binding["loop_sha256"]:
        raise ValueError("exact public loop required")
    anchor = "if(j > matrix_smash.columns)"
    if loop.count(anchor) != 1:
        raise ValueError("unique boundary condition required")
    output.mkdir(parents=True, exist_ok=False)
    (output / "original-loop.inc").write_text(loop + "\n")
    (output / "fixed-loop.inc").write_text(
        loop.replace(anchor, "if(j >= matrix_smash.columns)") + "\n"
    )
    fixture = (ROOT / "metadata_fixture.cc.txt").read_text()
    (output / "metadata_fixture.cc").write_text(fixture)
    (output / "aligned_block_fixture.cc").write_text(
        fixture[: fixture.index("int main()")]
        + (ROOT / "aligned_block_main.cc.txt").read_text()
    )
    receipt = {
        "source_sha256": binding["source_sha256"],
        "loop_sha256": binding["loop_sha256"],
        "fixed_loop_sha256": hashlib.sha256(
            loop.replace(anchor, "if(j >= matrix_smash.columns)").encode()
        ).hexdigest(),
        "scope": "Integer cursor and checked symbolic access metadata only; no FP payload reads or arithmetic",
    }
    (output / "fixture-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.source, a.output), indent=2))

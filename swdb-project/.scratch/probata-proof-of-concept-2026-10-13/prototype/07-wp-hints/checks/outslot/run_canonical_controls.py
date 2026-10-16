"""2026-10-16 ET: pure generation controls; shared B + time/RSS guard required.

No compiler, verifier, provider, or native execution. Historical native receipts
remain evidence for their exact historical bytes, never for this successor.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
POC = HERE.parents[1]
CHECKOUT = next(p for p in HERE.parents if (p / ".git").exists())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists() or out == CHECKOUT or CHECKOUT in out.parents:
        raise ValueError("fresh output outside checkout required")
    out.mkdir(parents=True)
    rows = []

    def record(name, passed, **extra):
        rows.append({"name": name, "passed": bool(passed), **extra})
        (out / "controls.json").write_bytes((json.dumps({"proof_acceptance": False,
            "native_acceptance": False, "records": rows}, indent=2) + "\n").encode())
        if not passed:
            raise AssertionError(name)

    def run(name, argv, ok=True):
        r = subprocess.run([str(x) for x in argv], capture_output=True, timeout=30)
        (out / (name + ".stdout")).write_bytes(r.stdout)
        (out / (name + ".stderr")).write_bytes(r.stderr)
        record(name, (r.returncode == 0) == ok, returncode=r.returncode)
        return r

    historical = {directory: {str(f.relative_to(POC / directory)): f.read_bytes()
                  for f in (POC / directory).rglob("*") if f.is_file()}
                  for directory in ("standin_outslot", "standin_private_array")}
    trim = lambda raw: b"\n".join(line.rstrip(b" \t") for line in raw.split(b"\n"))
    stages = (("outslot", "abi-map.json"), ("private_array", "private-array-map.json"))
    for stage, map_name in stages:
        generated = out / stage
        run("generate-" + stage, [sys.executable, POC / (stage + "_lowering.py"), "--output", generated])
        manifest = json.loads((generated / map_name).read_bytes())
        for name, pin in manifest["output_pins"].items():
            raw = (generated / name).read_bytes()
            record(stage + "-pin-" + name, hashlib.sha256(raw).hexdigest() == pin)
            record(stage + "-trim-only-" + name, raw == trim(historical["standin_" + stage][name]))
            record(stage + "-no-trailing-" + name, raw == trim(raw))
            record(stage + "-reproduce-" + name,
                   raw == (POC / ("standin_" + stage + "_canonical") / name).read_bytes())
        record(stage + "-map-reproduce", (generated / map_name).read_bytes() ==
               (POC / ("standin_" + stage + "_canonical") / map_name).read_bytes())
        if stage == "outslot":
            for row in manifest["interfaces"]:
                text = (generated / row["file"]).read_bytes().decode("utf-8")
                pos = text.index("void " + row["new_name"] + "(")
                begin = text.rfind("/*@", 0, pos)
                record("final-contract-" + row["name"],
                       row["new_contract"] == text[begin + 3:text.index("*/", begin)].strip())
        else:
            for name, row in manifest["contract_changes"].items():
                text = (generated / "gapbs_models.h").read_bytes().decode("utf-8")
                pos = text.index("void " + name + "(")
                begin = text.rfind("/*@", 0, pos)
                record("final-private-contract-" + name,
                       row["new"] == text[begin + 3:text.index("*/", begin)].strip())
        changed = out / (stage + "-changed")
        source = POC / ("standin" if stage == "outslot" else "standin_outslot_canonical")
        shutil.copytree(source, changed)
        target = changed / "gapbs_models.h"
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
        refused = out / (stage + "-refused")
        run(stage + "-physical-refusal", [sys.executable, POC / (stage + "_lowering.py"),
            "--source", changed, "--output", refused], ok=False)
        record(stage + "-refusal-no-emission", not refused.exists())
    spec = importlib.util.spec_from_file_location("outslot", POC / "outslot_lowering.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record("canonical-idempotence", module.canonical_generated_text("x; \t\n\n") == "x;\n\n")
    try:
        module.canonical_generated_text("#define x \\  \nnext\n")
    except ValueError:
        record("new-splice-refused", True)
    else:
        record("new-splice-refused", False)
    for directory, before in historical.items():
        after = {str(f.relative_to(POC / directory)): f.read_bytes()
                 for f in (POC / directory).rglob("*") if f.is_file()}
        record(directory + "-historical-preserved", before == after)


if __name__ == "__main__":
    main()

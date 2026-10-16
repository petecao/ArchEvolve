"""2026-10-16 ET. Public generated-source controls, not ACSL proof.
Run only under B plus an external RSS/time guard. No compiler/native/formal tools.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
MODEL = HERE.parents[1]
CHECKOUT = next(p for p in HERE.parents if (p / ".git").exists())


def contract(text, name):
    pos = text.index("void " + name + "(")
    begin = text.rfind("/*@", 0, pos)
    return text[begin + 3:text.index("*/", begin)]


def expected_domains(text, family):
    # Independent source-effect checklist; exact contract logic remains a formal gate.
    name = "__dxc_" + family
    value = re.sub(r"\s+", "", contract(text, name))
    checks = {
        "stream_load": [r"requires\initialized(base+(dxc_reg[minimum]..dxc_reg[maximum]-1));",
                        r"requires\valid(dxc_tile_data[dst]+(0..TILE_SIZE-1));",
                        r"ensures\initialized(dxc_tile_data[dst]+(0..dxc_tile_len[dst]-1));"],
        "gather": [r"requires\valid_read(dxc_tile_data[index]+(0..dxc_tile_len[index]-1));",
                   r"requires\initialized(dxc_tile_data[index]+(0..dxc_tile_len[index]-1));",
                   r"requires\forallintegeri;0<=i<dxc_tile_len[index]==>\initialized(base+dxc_tile_data[index][i]);",
                   r"requires\valid(dxc_tile_data[dst]+(0..TILE_SIZE-1));",
                   r"ensures\initialized(dxc_tile_data[dst]+(0..dxc_tile_len[dst]-1));"],
        "range_loop": [r"requires\valid_read(dxc_tile_data[lower]+(0..dxc_tile_len[lower]-1));",
                       r"requires\valid_read(dxc_tile_data[upper]+(0..dxc_tile_len[upper]-1));",
                       r"requires\initialized(dxc_tile_data[lower]+(0..dxc_tile_len[lower]-1));",
                       r"requires\initialized(dxc_tile_data[upper]+(0..dxc_tile_len[upper]-1));",
                       r"requires\valid(dxc_tile_data[rows]+(0..TILE_SIZE-1));",
                       r"requires\valid(dxc_tile_data[columns]+(0..TILE_SIZE-1));",
                       r"ensures\initialized(dxc_tile_data[rows]+(0..dxc_tile_len[rows]-1));",
                       r"ensures\initialized(dxc_tile_data[columns]+(0..dxc_tile_len[columns]-1));"],
    }
    return [x for x in checks[family] if x not in value]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--legacy", action="store_true")
    ap.add_argument("--families", nargs="+", default=["stream_load", "gather", "range_loop"])
    a = ap.parse_args(); out = a.output.resolve()
    if out.exists() or out == CHECKOUT or CHECKOUT in out.parents:
        raise ValueError("fresh external output required")
    if shutil.disk_usage(out.parent).free < 50 * 1024**3: raise ValueError("50GiB disk floor")
    out.mkdir(); deadline = time.monotonic() + 165; rows = []
    def record(name, ok, **fields):
        rows.append(dict(name=name, passed=bool(ok), **fields))
        (out / "controls.json").write_text(json.dumps(dict(records=rows, proof_acceptance=False), indent=2)+"\n")
        if not ok: raise AssertionError(name)
    def run(label, argv, fail=False):
        r = subprocess.run([str(x) for x in argv], capture_output=True, timeout=max(.01, deadline-time.monotonic()))
        (out / (label+".stdout")).write_bytes(r.stdout); (out / (label+".stderr")).write_bytes(r.stderr)
        record(label, (r.returncode != 0) if fail else (r.returncode == 0), argv=[str(x) for x in argv], returncode=r.returncode)
    generator = MODEL / ("private_array_lowering.py" if a.legacy else "device_init_domains.py")
    shutil.copyfile(generator, out / "generator-source.py")
    shutil.copyfile(__file__, out / "control-source.py")
    initial_generator_sha = hashlib.sha256(generator.read_bytes()).hexdigest()
    generated = out / "generated"
    run("generate-public", [sys.executable, "-B", generator, "--output", generated])
    text = (generated / "dxc_summaries.h").read_text()
    for family in a.families:
        missing = expected_domains(text, family)
        record("source-effect-domain-"+family, not missing, missing=missing,
               boundary="structural source contract checklist, not a logical initializedness proof")
    if a.legacy: return
    record("generator-retained-unchanged", hashlib.sha256(generator.read_bytes()).hexdigest()==initial_generator_sha)
    old = MODEL / "standin_private_array_canonical"
    for name in ["gapbs_models.h", "tdstep_standin.c", "bfs_unit.h"]:
        record("unchanged-"+name, (generated/name).read_bytes()==(old/name).read_bytes())
    tokens = lambda s: re.findall(r"\w+|[^\s]", re.sub(r"/\*.*?\*/|//[^\n]*", "", s, flags=re.S))
    record("unchanged-device-C-tokens", tokens(text)==tokens((old/"dxc_summaries.h").read_text()))
    manifest = json.loads((generated/"device-init-map.json").read_bytes())
    restored = text
    for name, change in manifest["contract_changes"].items():
        record("exact-contract-map-"+name, change["new"] in text and change["old"] in (old/"dxc_summaries.h").read_text())
        record("preserve-old-clauses-"+name, change["new"].replace(change["added_requires"], "", 1).replace(change["added_ensures"], "", 1)==change["old"])
        restored = restored.replace(change["new"], change["old"], 1)
    record("only-three-contract-insertions", restored==(old/"dxc_summaries.h").read_text())
    record("no-untouched-tail-initialization", not re.search(r"ensures\s+\\initialized\([^;]*TILE_SIZE", text))
    record("no-proof-or-TD-promotion", manifest["proof_acceptance"] is False and manifest["TD_or_counted_admissible"] is False)
    twice = out/"twice"; run("deterministic-generate", [sys.executable,"-B",generator,"--output",twice])
    record("deterministic-output", {p.name:p.read_bytes() for p in generated.iterdir()}=={p.name:p.read_bytes() for p in twice.iterdir()})
    # Physical input mutations must refuse before output creation.
    for label, mutate in [("CRLF",lambda b:b.replace(b"\n",b"\r\n")),("altered-byte",lambda b:b+b" "),("non-UTF8",lambda b:b+b"\xff")]:
        source=out/("input-"+label);shutil.copytree(old,source)
        p=source/"dxc_summaries.h";p.write_bytes(mutate(p.read_bytes()));dest=out/("refused-"+label)
        run(label+"-refused",[sys.executable,"-B",generator,"--source",source,"--output",dest],fail=True)
        record(label+"-no-emission",not dest.exists())
    run("existing-output-refused",[sys.executable,"-B",generator,"--output",generated],fail=True)
    record("historical-input-retained",all(hashlib.sha256((old/n).read_bytes()).hexdigest()==h for n,h in manifest["input_pins"].items()))
    print(json.dumps(dict(passed=len(rows), proof_acceptance=False, output=str(out))))


if __name__ == "__main__": main()

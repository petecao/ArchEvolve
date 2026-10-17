"""Read retained ticket27 artifacts into compact metadata; created 2026-10-15 ET.

Run on the producer host. This checks bytes and reports actual outcomes; it neither
changes proof records nor treats pytest success as a theorem/model agreement.
Usage: python summarize_acceptance.py /external/run > /external/run/summary.json
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    cache, mismatches, references, records = {}, [], 0, []

    def actual(path):
        path = str(path)
        if path not in cache:
            try:
                with open(path, "rb") as stream:
                    cache[path] = hashlib.file_digest(stream, "sha256").hexdigest()
            except OSError as exc:
                cache[path] = "unavailable: " + str(exc)
        return cache[path]

    def verify(path, expected, context):
        nonlocal references
        references += 1
        got = actual(path)
        if got != expected:
            mismatches.append({"path": str(path), "expected": expected, "actual": got, "context": context})

    def physical_pins(value, context):
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and value["path"].startswith("/") and "sha256" in value:
                verify(value["path"], value["sha256"], context)
            for key, item in value.items():
                if isinstance(key, str) and key.startswith("/") and isinstance(item, str) and len(item) == 64:
                    verify(key, item, context)
                else:
                    physical_pins(item, context)
        elif isinstance(value, list):
            for item in value:
                physical_pins(item, context)

    # pytest creates *current symlinks; one immutable record counts once.
    paths = {p.resolve() for p in (run / "pytest").glob("*/records/proofs/proof.dx100-fixtures*.yaml")}
    for path in sorted(paths):
        row = yaml.safe_load(path.read_text())
        physical_pins(row, row["id"])
        goals, settings, pins = row.get("goals", []), row.get("settings", {}), row["pins"]
        ordinary = [g for g in goals if not g.get("smoke")]
        smoke = [g for g in goals if g.get("smoke")]
        setup = row.get("proof_setup_check", {})
        example = row.get("counterexample") or {}
        records.append({"path": str(path), "sha256": actual(path), "id": row["id"],
            "test": path.parents[2].name, "subject": row["subject"], "bounds": row.get("bounds"),
            "adapter": row.get("job", {}).get("adapter"), "verdict": row["verdict"],
            "failure_class": row.get("failure_class"), "evidence_kind": row.get("evidence_kind"),
            "setup": {"verdict": setup.get("verdict"), "check": setup.get("check"),
                      "runs": len(setup.get("runs", []))},
            "verdict_reading": row.get("verdict_reading"),
            "ordinary": {"valid": sum(g["status"] == "valid" for g in ordinary), "total": len(ordinary)},
            "smoke": {"valid": sum(g["status"] == "valid" for g in smoke), "total": len(smoke)},
            "open": [g for g in goals if g["status"] != "valid"],
            "pins": pins, "tools": row.get("tools"),
            "initialized_goals": sum("initialized" in g["goal"] for g in ordinary),
            "rte_goals": sum("rte" in g["goal"] for g in ordinary),
            "assumption_kinds": sorted({a["kind"] for a in row.get("assumptions", [])}),
            "flags": settings.get("flags"), "verifier_launched": settings.get("verifier_launched"),
            "build_constants": settings.get("build_constants"), "forms": settings.get("forms"),
            "counterexample": ({"property": example.get("property"),
                "replayed": (example.get("replay") or {}).get("replayed")} if example else None),
            "job": row.get("job"),
            "artifacts": len(row.get("evidence", {}).get("reports", []))})

    tests = Counter()
    report = run / "report.jsonl"
    if report.exists():
        for line in report.read_text().splitlines():
            item = json.loads(line)
            if item.get("$report_type") == "TestReport" and item.get("when") == "call":
                tests[item["outcome"]] += 1

    def read(name):
        path = run / name
        return path.read_text().strip() if path.exists() else None

    output = {"created": "2026-10-15 ET", "scope": "retained fixture outcomes and physical-byte audit only",
        "run": str(run), "source_commit": read("source-commit.txt"), "shard": read("shard.txt"),
        "selection": read("selection.txt"), "exit_code": read("exit-code.txt"),
        "pytest_call_outcomes": dict(tests), "records": records,
        "physical_pins": {"references": references, "unique_files": len(cache), "mismatches": mismatches},
        "metadata_audit": "passed" if records and not mismatches else "incomplete_or_mismatched"}
    print(json.dumps(output, indent=2))
    return 0 if records and not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())

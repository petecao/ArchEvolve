"""2026-10-16 ET. Narrow V2 review repair; no compiler/project imports."""
import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ORIGIN = "dbcb5d35c6a575884265f0e6c0e49e5603a71f6d392cff1915d6aeda61e1159b"


def prepare():
    source = (HERE / "whole_interface_v2.py").read_text()
    if hashlib.sha256(source.encode()).hexdigest() != ORIGIN:
        raise ValueError("frozen V2 binder differs")
    begin = source.index("    def pure(node):\n")
    end = source.index("    for argument in arguments:\n", begin)
    old = source[begin:end]
    new = old.replace('            "UnaryExprOrTypeTraitExpr": (0, 1),\n', '')
    new = new.replace('        elif kind == "UnaryExprOrTypeTraitExpr":\n            _need(node.get("name") in ("sizeof", "alignof"), "source type-trait expression refused")\n', '')
    new = new.replace('        _need("volatile" not in node.get("type", {}).get("qualType", ""), "volatile source argument refused")\n',
        '        actual_type = node.get("type", {})\n'
        '        _need(isinstance(actual_type, dict), "source argument type metadata differs")\n'
        '        for spelling in ("qualType", "desugaredQualType"):\n'
        '            value = actual_type.get(spelling, "")\n'
        '            _need(isinstance(value, str) and "volatile" not in value, "volatile source argument refused")\n')
    if new == old or "UnaryExprOrTypeTraitExpr" in new:
        raise ValueError("narrow type-trait repair did not apply")
    repaired = source[:begin] + new + source[end:]
    ast.parse(repaired)
    (HERE / "whole_interface_v3.py").write_text(repaired)
    delta = {"date": "2026-10-16 ET", "origin_sha256": ORIGIN,
        "repaired_sha256": hashlib.sha256(repaired.encode()).hexdigest(), "old": old, "new": new,
        "review_findings": ["Unneeded type-trait AST expressions may hide evaluated VLA bounds outside inner traversal",
                            "Typedef-hidden volatile reads require checking desugaredQualType as well as qualType"],
        "scope": "Only local argument grammar changed; no source/value/native packet mutation or public admission"}
    (HERE / "whole-interface-v3-inverse-delta.json").write_text(json.dumps(delta, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    prepare()

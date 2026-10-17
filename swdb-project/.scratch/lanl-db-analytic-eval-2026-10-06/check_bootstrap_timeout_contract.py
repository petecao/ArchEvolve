"""2026-10-09 ET: isolated real-helper/original-consumer regression.

Runs the actual helper bootstrap function with retained metadata and isolated
read/fresh-route adapters. It never invokes main, remote I/O, or index controls.
Original consumer checks are extracted unchanged from their ASTs.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def consumer_check(source):
    tree = ast.parse(source.read_bytes())
    checks = [node for node in ast.walk(tree)
              if isinstance(node, ast.Expr)
              and isinstance(node.value, ast.Call)
              and isinstance(node.value.func, ast.Name)
              and node.value.func.id == "require"
              and any(isinstance(child, ast.Attribute)
                      and child.attr == "timeout_family"
                      for child in ast.walk(node))]
    assert len(checks) == 1, "one exact original timeout-family check"
    return compile(ast.fix_missing_locations(ast.Module(body=checks,
                                                        type_ignores=[])),
                   str(source), "exec")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--outer", type=Path, required=True)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument("--apply-fix", action="store_true")
    args = parser.parse_args()
    for path, size, digest in (
        (args.outer, 34658, "59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544"),
        (args.envelope, 38790, "1ee5ffbdf1ef322cfd5bfec4b6e402c29d23c776e855f01d25208ebbece0fcfc"),
    ):
        body = path.read_bytes()
        assert len(body) == size and sha(body) == digest, "exact original consumer source"
    raw = args.helper.read_bytes()
    assert len(raw) == 28658 and sha(raw) == "b27ca6f053fbad92347cd045fe6144168ae011a045a96a37343c81716bc92ca8"
    before = "'--timeout-family','GNU'"
    after = "'--timeout-family','parent_reviewed_GNU_coreutils_timeout'"
    source = raw.decode()
    assert source.count(before) == 1
    if args.apply_fix:
        source = source.replace(before, after)
    namespace = {"__name__": "isolated_bootstrap_contract"}
    exec(compile(source, str(args.helper), "exec"), namespace)
    originals = Path(__file__).parent / "evidence/17-approved-identity-and-first-index-inputs-20261009-a5/originals"
    data = json.loads((originals / "14-bootstrap-parent-input.json").read_bytes())
    names = {"author_preparation_plan": "10-index-author-action-plan.json",
             "specification_original": "09-index-author-specification.json",
             "request_original": "12-index-request.json",
             "author_custody_original": "13-author-custody.json"}
    bodies = {data[key]["path"]: (originals / name).read_bytes()
              for key, name in names.items()}

    def isolated_read(pin):
        body = bodies[pin["path"]]
        assert len(body) == pin["bytes"] and sha(body) == pin["sha256"]
        return body

    namespace["read"] = isolated_read
    namespace["metadata_route"] = lambda pin, name: None
    namespace["fresh"] = lambda value, other=(): Path(value)
    _, generated = namespace["bootstrap"](data, data["campaign"],
                                           data["parent_attestation"])
    plan = json.loads(generated["index-bootstrap-action-plan.json"])
    argv = plan["config_template"]["argv"]
    family = argv[argv.index("--timeout-family") + 1]
    checks = [consumer_check(args.outer), consumer_check(args.envelope)]
    count = 0
    for check in checks:
        for value in (family, "GNU", "arbitrary_alias"):
            accepted = True
            try:
                exec(check, {"args": SimpleNamespace(timeout_family=value),
                             "require": namespace["need"]})
            except namespace["Refused"] as error:
                accepted = False
                assert sha(str(error).encode()) == "9231e3ca8a3f084363b770fb8d2575077d4859512c3513feec5c2c357482a704"
            if value == family:
                assert accepted, "generated helper family rejected by original consumer"
            else:
                assert not accepted, "original consumer unexpectedly accepted an alias"
            count += 1
    assert len(argv) == 60 and plan["bootstrap_script_argument_count"] == 56
    assert namespace["digest"](argv) == plan["complete_bootstrap_argv_sha256"]
    assert namespace["digest"](plan["direct_GNU_envelope_argv"]) == plan["direct_GNU_envelope_argv_sha256"]
    print(json.dumps({"result": "PASS", "consumer_cases": count,
                      "generated_argv_and_digests": "PASS",
                      "isolated_metadata_only": True,
                      "helper_sha256": sha(source.encode()),
                      "helper_bytes": len(source.encode())}))


if __name__ == "__main__":
    main()

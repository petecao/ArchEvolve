"""2026-10-16 ET. Deterministic source-only copy and exact inlet patch."""
import ast
import hashlib
import json
from pathlib import Path
import difflib
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'abi-retained-replay-v1/controls/compiler_unit_adapter_v3.py'
if not BASE.exists():
    policy=json.loads((HERE.parent/'abi-retained-replay-v1/controls/policy.json').read_bytes())
    BASE=HERE.parent/'abi-retained-replay-v1/controls'/Path(policy['controls']['legacy']['path']).name
raw=BASE.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
text=raw.decode()
inlet=(HERE/'enum_inlet.py').read_text()
changes=[
('def observed_abi(raw, *, probe_path, api):',inlet+'\n\ndef observed_abi(raw, *, probe_path, api):'),
('    need(sha(Path(probe_path).read_bytes()) == ABI_PROBE_SHA, "exact physical ABI probe required")',
 '    probe_bytes = Path(probe_path).read_bytes()\n    need(sha(probe_bytes) == ABI_PROBE_SHA, "exact physical ABI probe required")\n    enum_profile = _enum_profile(raw, probe_path)'),
('    need(set(selected) == expected, "complete ABI probe root census required")',
 '    need(set(selected) == expected, "complete ABI probe root census required")\n    if enum_profile is not None:\n        need([root.get("name") for root in roots] == ["dws_probe_" + key for key in (*TYPE_KEYS, *ABI_INTS)],\n             "complete ordered original enum probe roots required")'),
('        constants = [node for node in root.get("inner", []) if node.get("kind") == "ConstantExpr"]',
 '        if enum_profile is not None:\n            integers[key] = _enum_source_value(root, key, enum_profile[1], probe_bytes)\n            continue\n        constants = [node for node in root.get("inner", []) if node.get("kind") == "ConstantExpr"]'),
('    return {"abi": abi, "raw_probe_sha256": sha(raw), "root_count": len(roots), "constants": integers,\n        "runtime_float_environment_observed": False, "public_admission": False}',
 '    observation = {"abi": abi, "raw_probe_sha256": sha(raw), "root_count": len(roots), "constants": integers,\n        "runtime_float_environment_observed": False, "public_admission": False}\n    if enum_profile is not None:\n        original = {"first-source-v10": (127394, "0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15"),\n                    "memory-source-g642": (127541, "493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c")}[enum_profile[0]]\n        observation["semantic_enum_interpretation"] = {\n            "schema": "exact-probe-enum-integral-cast-interpretation-1", "family": enum_profile[0],\n            "selected_original_ABI": {"bytes": original[0], "sha256": original[1]},\n            "role_derived_strict_ABI": {"bytes": len(raw), "sha256": sha(raw)},\n            "original_probe": {"path": enum_profile[1], "bytes": len(probe_bytes), "sha256": sha(probe_bytes)},\n            "interpreted_constants_canonical_sha256": sha(json.dumps(integers, sort_keys=True, separators=(",", ":")).encode()),\n            "enum_count": len(integers), "interpretation_is_reversible_AST_transport": False,\n            "input_AST_mutated": False, "ConstantExpr_own_APValue_only": True,\n            "exact_source_type_and_uint32_cast_checked": True,\n            "physical_reader_pin_required_from_enclosing_producer_manifest": True}\n    return observation'),
]
for old,new in changes:
 assert text.count(old)==1,old
 text=text.replace(old,new)
ast.parse(text)
(HERE/'base-source.py').write_bytes(raw)
(HERE/'proposed/compiler_unit_adapter_v4.py').write_text(text)
(HERE/'exact-delta.json').write_text(json.dumps({'date':'2026-10-16 ET','changes':[{'old':old,'new':new} for old,new in changes]},sort_keys=True,indent=2)+'\n')
(HERE/'proposed.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),text.splitlines(True),fromfile='compiler_unit_adapter_v3.py',tofile='compiler_unit_adapter_v4.py')))
print(json.dumps({'bytes':len(text.encode()),'sha256':hashlib.sha256(text.encode()).hexdigest()}))

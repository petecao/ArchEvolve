"""Only checked-source per-owner bounds; preserve the normal adapter path."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'production-route-v3/proposed/swdb/cbmc_adapter.py'
TARGET = HERE / 'proposed/swdb/cbmc_adapter.py'
old = OLD.read_text()
before = '''                loops = dx100_checked_adapter.model_loops(self,tools,scratch,code.lowering.whole_source,context)
            else:
                loops = self._model_loops(tools, scratch, code.model)
            if loops:
                flags += ["--unwindset", ",".join(f"{loop}:{code.model.unwind}" for loop in loops)]'''
after = '''                loops = dx100_checked_adapter.model_loops(self,tools,scratch,code.lowering.whole_source,context)
                bound_rows = dx100_checked_adapter.helper_loop_bounds(code.lowering.whole_source,loops,context)
                if bound_rows:
                    flags += ["--unwindset", ",".join(f"{row['loop']}:{row['unwind']}" for row in bound_rows)]
            else:
                loops = self._model_loops(tools, scratch, code.model)
                if loops:
                    flags += ["--unwindset", ",".join(f"{loop}:{code.model.unwind}" for loop in loops)]'''
assert old.count(before) == 1
new = old.replace(before, after, 1)
assert TARGET.read_text() in (old, new)
TARGET.write_text(new)
assert new.replace(after, before, 1) == old
(HERE / 'checked-unwind-inverse-v4.json').write_text(json.dumps({'schema': 'checked-source-unwind-inverse-4',
    'predecessor_sha256': hashlib.sha256(old.encode()).hexdigest(), 'successor_sha256': hashlib.sha256(new.encode()).hexdigest(),
    'before': before, 'after': after, 'exact_predecessor_restored': True,
    'nonchecked_default_loop_flags_unchanged': True, 'unwinding_assertions_removed': False}, sort_keys=True, indent=2) + '\n')
print(json.dumps({'cbmc_adapter_sha256': hashlib.sha256(new.encode()).hexdigest()}))

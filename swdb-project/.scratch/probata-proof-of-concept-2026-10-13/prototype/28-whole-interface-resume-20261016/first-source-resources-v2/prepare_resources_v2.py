"""Source-only count-scanning-helper correction; V1 is retained unchanged."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'first-source-resources-v1'
text = (OLD / 'resource_profile_v1.py').read_text(); edits = []


def replace(old, new):
    global text
    assert text.count(old) == 1, old[:100]
    text = text.replace(old, new, 1); edits.append({'old': old, 'new': new})


replace('EVALUATION_HELPER_UNWIND = 20 * NODE_CAPACITY + 1',
    "EVALUATION_HELPER_UNWIND = 20 * NODE_CAPACITY + 1\n"
    "COUNT_SCANNING_HELPER_UNWIND = NODE_CAPACITY + 1\n"
    "OWNER_UNWIND = {'dxm_cover': EVALUATION_HELPER_UNWIND, 'dxm_cpu_write': COUNT_SCANNING_HELPER_UNWIND,\n"
    "                'dxm_device_write': COUNT_SCANNING_HELPER_UNWIND}")
replace("('four_stream_loads', 4, 58)", "('four_initialized_register_stream_loads', 4, 58)")
replace("'schema': 'dx100-first-source-resource-profile-1'", "'schema': 'dx100-first-source-resource-profile-2'")
replace("'helper_owner_unwind': {'dxm_cover': EVALUATION_HELPER_UNWIND},",
    "'helper_owner_unwind': dict(OWNER_UNWIND),\n"
    "        'stream_load_setup_source_basis': {'source_initializers': {'min_reg': 0, 'max_reg': 2, 'stride': 1},\n"
    "            'dtype': 'int32_t', 'before_all_four_loads': 'checked original source/model state, not an assumed initialized payload',\n"
    "            'initialized_setup_nodes': 30, 'generic_missing_register_setup_nodes': 33, 'two_lane_nodes_each': 14},")
replace("and 'dxm_cover' in helper_functions", "and set(OWNER_UNWIND) <= set(helper_functions)")
replace("EVALUATION_HELPER_UNWIND if owner == 'dxm_cover' else DEFAULT_HELPER_UNWIND",
    'OWNER_UNWIND.get(owner, DEFAULT_HELPER_UNWIND)')
ast.parse(text); (HERE / 'resource_profile_v2.py').write_text(text)
restored = text
for row in reversed(edits):
    assert restored.count(row['new']) == 1
    restored = restored.replace(row['new'], row['old'], 1)
assert restored == (OLD / 'resource_profile_v1.py').read_text()
(HERE / 'inverse-v2.json').write_text(json.dumps({'schema': 'first-source-resource-v2-inverse-1', 'edits': edits,
    'exact_V1_restored': True, 'backend_and_capacity_assertions_unchanged': True}, sort_keys=True, indent=2) + '\n')
test = (OLD / 'test_resources_v1.py').read_text().replace('resource_profile_v1.py', 'resource_profile_v2.py')
test = test.replace("['dxp_find', 'dxm_cover', 'dws_prepare_receiver_v1']",
    "['dxp_find', 'dxm_cover', 'dws_prepare_receiver_v1', 'dxm_cpu_write', 'dxm_device_write']")
test = test.replace("for bad in (['unknown.0']", "for bad in (['unknown.0']")
(HERE / 'test_resources_v2.py').write_text(test)
print(json.dumps({'module_sha256': hashlib.sha256(text.encode()).hexdigest(), 'actual_executed': False}))

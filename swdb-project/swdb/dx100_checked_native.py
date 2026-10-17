"""Fixed first-source and selected-memory original C++ runtime views.

2026-10-16 ET. Shared concrete model/owned mapping remain explicit premises;
sampled projection agreement is not independent hardware or compiler evidence.
"""
import hashlib
import json
from pathlib import Path

from swdb import dx100_checked_source as source
from swdb._dx100_whole import runtime_projection_v3 as first
from swdb._dx100_whole import runtime_projection_v4 as memory

FIRST_SHA = 'e60e1ed82a0bbc4983bb4acd9ca0204fd4238ef8ed555c9dc4a2ab8800a07284'
MEMORY_SHA = '56077c3476ba0f4af3b06089e937a0a5723318f7927ba81ea45c8556251cb7de'
FIRST_KIND = 'dx100-whole-source-preserving-cxx-v3'
MEMORY_KIND = 'dx100-whole-selected-memory-cxx-v4'


def view(unit):
    source.need(type(unit) is source.SourceUnit, 'checked source unit required')
    policy = json.loads(unit.policy_json)
    selected = policy['native_projection']
    is_first = unit.function == source.FUNCTION
    source.need(policy['function'] == unit.function and unit.function in source.UNIT_FUNCTIONS,
                'exact selected source/function native view required')
    projection = first if is_first else memory
    kind, expected_sha = (FIRST_KIND, FIRST_SHA) if is_first else (MEMORY_KIND, MEMORY_SHA)
    source.need(type(selected) is dict and set(selected) == {'kind', 'producer', 'assertion_header'}
                and selected['kind'] == kind and selected['producer']['sha256'] == expected_sha,
                'fixed source-specific reviewed C++ projection selection required')
    reads = source.Inputs(unit.selection.library)
    raw = reads.absolute(selected['producer'], limit=4 * 1024 * 1024)
    actual = Path(projection.__file__)
    source.need(source.receiver.Pin.parse(selected['producer']).path == str(actual)
                and hashlib.sha256(raw).hexdigest() == expected_sha,
                'actual physical imported C++ projection producer differs')
    source.need(selected['assertion_header'] == unit.statement_preparation['assertion_header_pin'],
                'C++ assertion header selection differs from complete source lowering')
    prepared = unit.receiver_preparation
    receiver = {'binding': json.loads(prepared.binding_json), 'c_text': prepared.c_text,
        'draw_plan': json.loads(prepared.draw_plan_json), 'integration': json.loads(prepared.integration_plan_json)}
    inputs = {'source_path': Path(unit.certificate['captured_source_path']), 'normalized_tu': unit.normalized_tu,
        'caller': policy['caller_mangled'], 'declarations': source.binder.inventory(unit.selection.project),
        'abi': unit.abi, 'atlas': unit.atlas, 'allocations': list(unit.allocations), 'thread': policy['thread'],
        'unit_preparation': unit.unit_preparation, 'statement_preparation': unit.statement_preparation,
        'assertion_header_pin': selected['assertion_header'], 'receiver': receiver,
        'receiver_policy_pin': json.loads(unit.receiver_policy_pin_json)}
    if is_first:
        result = first.projection(actual.parent, unit.selection.project, **inputs)
    else:
        result = memory.memory_projection(actual.parent, unit.selection.project, function=unit.function, **inputs)
    source.need(type(result) is dict and set(result) == {'cxx_text', 'runtime_header', 'edit_manifest', 'runtime_identity'},
                'closed original-source C++ view result required')
    source.need(result['cxx_text'].count('#include "dws_original_runtime.hpp"') == 1,
                'fixed generated C++ header include required')
    reads.recheck()
    return result


def check_generated_header(unit, root, expected):
    """Check the actual native include, not merely a metadata header hash."""
    path = Path(root) / 'dws_original_runtime.hpp'
    raw = expected.encode('utf-8')
    pin = source.receiver.Pin(str(path), len(raw), hashlib.sha256(raw).hexdigest())
    source.receiver.check_file(pin)
    return pin.row()

"""Fixed source-preserving native view of the first checked source fixture.

The same concrete model is an explicit owned premise on both sides. Agreement
is a projection check over sampled choices, never independent hardware evidence.
"""
import hashlib
import json
from pathlib import Path

from swdb import dx100_checked_source as source
from swdb._dx100_whole import runtime_projection_v2 as projection

PROJECTION_SHA = '645b34878191a695fb61bd6dbf2dd3bcb0f984199482c9611a19b9f9a3a4e69b'
KIND = 'dx100-whole-source-preserving-cxx-v2'


def view(unit):
    source.need(type(unit) is source.SourceUnit, 'checked source unit required')
    policy = json.loads(unit.policy_json)
    selected = policy['native_projection']
    source.need(type(selected) is dict and set(selected) == {'kind', 'producer', 'assertion_header'}
        and selected['kind'] == KIND and selected['producer']['sha256'] == PROJECTION_SHA,
        'fixed reviewed C++ projection selection required')
    reads = source.Inputs(unit.selection.library)
    raw = reads.absolute(selected['producer'], limit=4 * 1024 * 1024)
    actual = Path(projection.__file__)
    source.need(source.receiver.Pin.parse(selected['producer']).path == str(actual)
        and hashlib.sha256(raw).hexdigest() == PROJECTION_SHA,
        'actual imported C++ projection producer differs')
    source.need(selected['assertion_header'] == unit.statement_preparation['assertion_header_pin'],
        'C++ assertion header selection differs from complete source lowering')
    prepared = unit.receiver_preparation
    receiver = {'binding': json.loads(prepared.binding_json), 'c_text': prepared.c_text,
        'draw_plan': json.loads(prepared.draw_plan_json), 'integration': json.loads(prepared.integration_plan_json)}
    result = projection.projection(Path(projection.__file__).parent, unit.selection.project,
        source_path=Path(unit.certificate['captured_source_path']), normalized_tu=unit.normalized_tu,
        caller=policy['caller_mangled'], declarations=source.binder.inventory(unit.selection.project),
        abi=unit.abi, atlas=unit.atlas, allocations=list(unit.allocations), thread=policy['thread'],
        unit_preparation=unit.unit_preparation, statement_preparation=unit.statement_preparation,
        assertion_header_pin=selected['assertion_header'], receiver=receiver,
        receiver_policy_pin=json.loads(unit.receiver_policy_pin_json))
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

"""2026-10-16 ET. Explicit symbolic floating mode for six original copy bodies.

This is a mode/source eligibility boundary, not an ownership or proof admission.
The six complete original units, including all ACSL clauses, stay unchanged.
The normal adapter and setup gates remain responsible for every actual tool,
driver, flag, source-domain, property, runtime and record check.
"""
import hashlib
import json
from pathlib import Path

from swdb import std_models


METHOD = 'method.wp-vector-float-copy-v1'
PARENT = {'id': 'swdb-std-models-2',
          'sha256': 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'}
ELEMENTS = ('float', 'double')
MEMBERS = ('ctor_count', 'ctor_count_value', 'copy_ctor')
NAMES = tuple('std_vector_' + element + '_' + member
              for element in ELEMENTS for member in MEMBERS)


class Refused(ValueError):
    """The explicit mode, complete original source or certificate is unavailable."""


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity():
    return {'id': 'vector-float-copy-mode-1', 'sha256': _sha(Path(__file__).read_bytes())}


def _float_flags(flags):
    if not isinstance(flags, (list, tuple)) or not all(isinstance(flag, str) for flag in flags):
        raise Refused('symbolic floating mode flags must be a string argv sequence')
    positions = [index for index, flag in enumerate(flags) if flag.startswith('-wp-model')]
    if (len(positions) != 1 or flags[positions[0]] != '-wp-model'
            or positions[0] + 1 >= len(flags) or flags[positions[0] + 1] != '+float'):
        raise Refused('requires exactly one canonical -wp-model +float without overrides or real erasure')


def selected(method):
    """Select only this explicit fixture; preserve every old method's real policy."""
    data = getattr(method, 'data', None)
    method_id = getattr(method, 'id', None)
    if not isinstance(data, dict):
        if method_id == METHOD:
            raise Refused('explicit floating method has no valid method data')
        return False
    lowering = data.get('c_lowering')
    rows = lowering.get('translators') if isinstance(lowering, dict) else None
    requested = [row for row in rows if isinstance(row, dict) and row.get('id') == identity()['id']] \
        if isinstance(rows, list) else []
    if method_id != METHOD and not requested:
        return False
    models = data.get('models')
    lineup = data.get('lineup')
    frama = [row for row in lineup if isinstance(row, dict) and row.get('tool') == 'frama-c-wp'] \
        if isinstance(lineup, list) else []
    if (method_id != METHOD or data.get('id') != METHOD
            or data.get('evidence_kind') != 'contract_fixture' or requested != [identity()]
            or not isinstance(models, dict) or models.get('std_vector') != PARENT
            or std_models.identity() != PARENT or len(frama) != 1 or frama[0].get('version') != '33.0'):
        raise Refused('floating copy mode requires its explicit Frama-C 33 fixture and current checker/model pins')
    _float_flags(frama[0].get('flags'))
    return True


def model_option(method):
    """Expected model selector for future coordinated adapter/setup integration."""
    return '+float' if selected(method) else '+real'


def check_source(method, name, source, flags):
    """Bind the selected mode to a complete exact original copy-only C unit.

    No C is changed, no finite premise is added and no generic source gate is
    bypassed. An actual generation must still bind its selected float theories,
    driver and complete tasks before any nonfinite coverage can be adopted.
    """
    if not selected(method):
        raise Refused('floating copy source requires the explicit opt-in method')
    _float_flags(flags)
    if name not in NAMES or not isinstance(source, str) or source != std_models.model_text(name):
        raise Refused('requires one complete pinned original float/double count, value or copy body')
    element = next(element for element in ELEMENTS if name.startswith('std_vector_' + element + '_'))
    return {'version': 1, 'checker': identity(), 'parent_model': std_models.identity(),
        'method': METHOD, 'function': name, 'element_type': element,
        'original_source_sha256': _sha(source), 'model_option': '+float',
        'intended_value_sort': 'f32' if element == 'float' else 'f64',
        'source_modified': False, 'original_acsl_clauses_modified': False,
        'finite_or_non_NaN_requires_added': False,
        'actual_driver_and_goal_evidence_required': True,
        'source_or_lifetime_or_caller_admitted': False,
        'IEEE_bit_payload_preservation_proved': False,
        'pending': ['actual installed WP model and complete driver/import/task binding',
            'original ACSL real promotion including unspecified nonfinite values',
            'source storage, initialization, allocator freshness/framing/freeability and lifetime',
            'source-to-symbolic float store correspondence and implementation representation',
            'every ordinary/RTE/frame/init goal and normal consistency control'],
        'semantic_scope': 'symbolic same-format copy/store; no C floating arithmetic or format conversion',
        'comparison_boundary': 'plain ACSL logical equality is distinct from C IEEE eq_float/eq_double',
        'representation_boundary': 'no physical NaN payload, signaling state or signed-zero bit guarantee',
        'solver_boundary': 'version/driver names alone establish no native IEEE capability or proof result'}


def check_certificate(method, name, source, flags, certificate):
    expected = check_source(method, name, source, flags)
    try:
        same = type(certificate) is dict and _json(certificate) == _json(expected)
    except (TypeError, ValueError):
        same = False
    if not same:
        raise Refused('floating mode source, type, model, certificate or pending duties changed')

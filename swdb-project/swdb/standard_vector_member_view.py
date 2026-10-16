"""Exact nonallocating vector member domains; created 2026-10-16 ET.

The original C contracts stay intact. A typed contiguous vector-storage domain
qualifies pointer formation; it is not a theorem about arbitrary incoming C
pointers. Every source caller must discharge that domain separately. The four
registered payload types are preserved without reading or converting elements.
This module alone neither runs a verifier nor admits a caller dependency.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from swdb import std_models

MODEL_SHA256 = 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'
METHOD = 'method.wp-vector-member-source-v1'
ELEMENTS = ('int', 'float', 'double', 'int *')
MEMBERS = ('data', 'size', 'empty', 'begin', 'end', 'operator_index', 'at', 'clear')
NAMES = tuple('std_vector_' + std_models._mangle(t) + '_' + member
              for t in ELEMENTS for member in MEMBERS)


class Refused(ValueError):
    """An exact member body, qualified domain or dependency is unavailable."""


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False))


def identity():
    return {'id': 'standard-vector-member-view-1', 'sha256': _sha(Path(__file__).read_bytes())}


def selected(method):
    data = getattr(method, 'data', None)
    method_id = getattr(method, 'id', None)
    if not isinstance(data, dict):
        if method_id == METHOD:
            raise Refused('explicit vector member method has no valid method data')
        return False
    lowering = data.get('c_lowering') or {}
    if not isinstance(lowering, dict):
        raise Refused('vector member method lowering data must be an object')
    rows = lowering.get('translators') or []
    if not isinstance(rows, list):
        raise Refused('vector member method translators must be a list')
    requested = [row for row in rows if isinstance(row, dict) and row.get('id') == identity()['id']]
    if method_id != METHOD and not requested:
        return False
    if (method_id != METHOD or data.get('id') != METHOD
            or data.get('evidence_kind') != 'contract_fixture' or requested != [identity()]):
        raise Refused('vector member domain requires its explicit fixture method and exact current checker pin')
    return True


def _member(name):
    if name not in NAMES:
        raise Refused('only the registered nonallocating vector members and exact element types are qualified')
    for element in ELEMENTS:
        prefix = 'std_vector_' + std_models._mangle(element) + '_'
        if name.startswith(prefix) and name[len(prefix):] in MEMBERS:
            return element, name[len(prefix):], prefix[:-1]
    raise Refused('ambiguous vector member type')


def _contract(text, name):
    start = text.index('/*@ requires ')
    stop = text.rindex('static ', start, text.index(name + '('))
    return text[start:stop]


@dataclass(frozen=True)
class View:
    name: str
    element: str
    member: str
    original: str
    text: str
    certificate: dict
    pins: dict


def wp_view(name, text):
    element, member, vector = _member(name)
    if std_models.identity()['sha256'] != MODEL_SHA256 or text != std_models.model_text(name):
        raise Refused('the complete original vector model source and contract must match the pinned version')
    original_contract = _contract(text, name)
    transformed = text
    obligations, removed = [], []
    if member == 'at':
        guard = '  if (n >= this->size) SWDB_MODEL_FAIL("' + std_models.OUT_OF_RANGE + '");'
        if text.count(guard) != 1 or '&& n < this->size;' not in original_contract:
            raise Refused('the exact defensive at guard and original bounds precondition are required')
        transformed = text.replace(guard, '  /*@ assert at_guard_false: n < this->size; */')
        obligations.append('at_guard_false')
        removed.append('defensive abort branch under proven negated guard')
    domain = {'receiver': 'this', 'vector_type': vector, 'element_type': element,
        'storage': 'this->data', 'elements': r'\at(this->capacity,Pre)',
        'live_size': r'\at(this->size,Pre)', 'same_typed_array_required': True,
        'null_case': 'capacity zero has null data; guarded end performs no null pointer arithmetic',
        'lifetime': 'receiver and original typed element array remain live throughout the nonallocating call',
        'initialization': 'unchanged original readable/valid predicate; no finite or integer payload surrogate',
        'caller_discharge': 'required from actual source vector storage; never inferred from a generic pointer'}
    certificate = {'version': 1, 'check': identity(), 'model': std_models.identity(), 'member': name,
        'element_type': element, 'original_text_sha256': _sha(text), 'view_text_sha256': _sha(transformed),
        'original_contract_sha256': _sha(original_contract),
        'view_contract_sha256': _sha(_contract(transformed, name)),
        'typed_input_domain': domain, 'domain_role': 'qualified original C member body; source caller discharge required',
        'caller_domain_discharge_required': True, 'caller_admission_established': False,
        'acsl_input_premises_added': [], 'body_operations_removed': removed, 'obligations': obligations,
        'guard_elision_obligation': 'at_guard_false' if member == 'at' else None,
        'original_native_and_cbmc_body_unchanged': True,
        'payload_operations': 'none: preserves int, float, double and int-pointer element storage exactly',
        'references': ['https://timsong-cpp.github.io/cppwp/n4659/vector.data',
            'https://timsong-cpp.github.io/cppwp/n4659/vector.access',
            'https://timsong-cpp.github.io/cppwp/n4659/sequence.reqmts']}
    pins = {'standard_vector_member_view_check': identity(),
        'standard_vector_member_view_certificate': {'id': 'standard-vector-member-domain-1',
            'sha256': _digest(certificate)}}
    return View(name, element, member, text, transformed, certificate, pins)


def check_view(name, view):
    if type(view) is not View or view != wp_view(name, std_models.model_text(name)):
        raise Refused('vector member original source, contract, type, view or domain changed')


def _children(node):
    return [row for row in node.get('inner', []) if isinstance(row, dict) and row.get('kind')]


def _strip(node):
    while node.get('kind') in {'ImplicitCastExpr', 'ParenExpr'}:
        children = _children(node)
        if len(children) != 1 or (node.get('kind') == 'ImplicitCastExpr'
                and node.get('castKind') not in {'LValueToRValue', 'NoOp'}):
            return {}
        node = children[0]
    return node


def qualified_origin(view, function, node, definitions):
    """Only the exact parsed this->data field has this qualified storage domain.

    The caller must check the complete input equals HEADERS + view.text and
    check_view before using this function. Generic pointer origins stay closed.
    """
    check_view(view.name, view)
    if function != view.name or view.member not in {'end', 'at', 'operator_index'}:
        return None
    definition = definitions.get(function) or {}
    if definition.get('kind') != 'FunctionDecl' or definition.get('name') != function:
        return None
    owners = [row for row in _children(definition)
        if row.get('kind') == 'ParmVarDecl' and row.get('name') == 'this']
    vector = view.certificate['typed_input_domain']['vector_type']
    if len(owners) != 1 or (owners[0].get('type') or {}).get('qualType') != 'const ' + vector + ' *':
        return None
    if not isinstance(owners[0].get('id'), str) or not owners[0]['id']:
        return None
    node = _strip(node)
    children = _children(node)
    if not (node.get('kind') == 'MemberExpr' and node.get('name') == 'data' and node.get('isArrow') is True
            and len(children) == 1):
        return None
    field_type = ''.join((node.get('type') or {}).get('qualType', '').split())
    expected_type = ''.join((view.element + '*').split())
    if field_type not in {expected_type, expected_type + 'const'}:
        return None
    receiver = _strip(children[0])
    ref = receiver.get('referencedDecl') or {}
    if (receiver.get('kind') != 'DeclRefExpr' or ref.get('kind') != 'ParmVarDecl'
            or ref.get('id') != owners[0]['id']):
        return None
    return {'kind': 'qualified_standard_vector_member', 'root': 'this->data',
        'element_type': view.element, 'elements': r'\at(this->capacity,Pre)', 'relative_offset': '0',
        'certificate': view.pins['standard_vector_member_view_certificate'],
        'caller_domain_discharge_required': True}


def check_record(name, data):
    """Verify a body's exact qualification; this does not prove a caller domain."""
    view = wp_view(name, std_models.model_text(name))
    if not isinstance(data, dict):
        raise Refused('vector member proof record is missing or malformed')
    code = {'id': name, 'sha256': view.certificate['original_text_sha256']}
    pins = data.get('pins') or {}
    settings = data.get('settings') or {}
    if not isinstance(pins, dict) or not isinstance(settings, dict):
        raise Refused('vector member proof pins/settings must be objects')
    if (data.get('verdict') != 'proven' or data.get('subject') != {'kind': 'c_model', 'id': name}
            or pins.get('code') != code or pins.get('contract') != code
            or pins.get('std_models') != std_models.identity()
            or any(pins.get(key) != value for key, value in view.pins.items())
            or settings.get('standard_vector_member_view') != view.certificate):
        raise Refused('vector member proof lacks its exact current body/type/domain qualification')
    return view.certificate


def require_caller_discharge(name, data):
    check_record(name, data)
    raise Refused('qualified vector member body needs actual source caller storage/lifetime discharge; generic dependency refused')

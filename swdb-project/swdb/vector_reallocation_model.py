"""Explicit v3 vector reallocation-domain candidate; created 2026-10-16 ET.

This qualified contract is separate from the original v2 catalog. Preparation
does not prove its body or discharge a caller's allocation/liveness obligations.
"""
import hashlib
import re
from pathlib import Path

from swdb import std_models

PARENT = {'id': 'swdb-std-models-2',
          'sha256': 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'}
MEMBERS = {'std_vector_int_realloc_v3_' + member: 'std_vector_int_' + member
           for member in ('ctor_count_value', 'grow', 'reserve', 'dtor')}
DOMAIN = r'''/* Explicit v3 unary reallocation domain. It does not grant exclusive ownership.
   Distinct allocation bases are required: byte-disjoint ranges can share a free. */
/*@ predicate std_vector_int_reallocatable_v3(std_vector_int *v) =
      std_vector_int_valid(v) &&
      (v->capacity == 0 || (\freeable(v->data) &&
        \base_addr(v) != \base_addr(v->data)));
*/
'''


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def identity():
    return {'id': 'vector-reallocation-domain-3',
            'sha256': hashlib.sha256(Path(__file__).read_bytes() + PARENT['sha256'].encode()).hexdigest()}


def _qualify(source, original):
    text = source
    if original in ('std_vector_int_grow', 'std_vector_int_reserve'):
        text = text.replace('requires std_vector_int_valid(this)',
                            'requires std_vector_int_reallocatable_v3(this)')
    if original != 'std_vector_int_dtor':
        text = text.replace('ensures std_vector_int_valid(this)',
                            'ensures std_vector_int_reallocatable_v3(this)')
    if original == 'std_vector_int_ctor_count_value':
        text = text.replace('    ensures std_vector_int_reallocatable_v3(this)',
                            '    ensures this->capacity == n;\n'
                            '    ensures std_vector_int_reallocatable_v3(this)', 1)
    # Reserve's helper call and definition use the same qualified contract.
    for qualified, parent in MEMBERS.items():
        text = text.replace(parent + '(', qualified + '(')
    return text


def model_text(name):
    original = MEMBERS.get(name)
    if original is None:
        return None
    if std_models.identity() != PARENT:
        raise ValueError('qualified v3 domain requires independent remapping after the original model changes')
    source = std_models.model_text(original)
    header = std_models._vector_types('std_vector_int', 'int')
    if not source.startswith(header):
        raise ValueError('the original vector source header changed')
    return _qualify(source.replace(header, header + '\n' + DOMAIN, 1), original)


def _restore(qualified, original):
    text = qualified.replace('\n' + DOMAIN, '', 1)
    for renamed, parent in MEMBERS.items():
        text = text.replace(renamed + '(', parent + '(')
    text = text.replace('requires std_vector_int_reallocatable_v3(this)',
                        'requires std_vector_int_valid(this)')
    text = text.replace('ensures std_vector_int_reallocatable_v3(this)',
                        'ensures std_vector_int_valid(this)')
    if original == 'std_vector_int_ctor_count_value':
        text = text.replace('    ensures this->capacity == n;\n', '', 1)
    return text


def certificate(name):
    source, qualified = std_models.model_text(MEMBERS[name]), model_text(name)
    restored = _restore(qualified, MEMBERS[name])
    if restored != source:
        raise ValueError('inverse contract/name qualification must restore the entire original source')
    pieces = std_models._vector_unit(re.fullmatch(r'(std_vector_int)_(\w+)', MEMBERS[name]))
    bodies = []
    for function, piece in pieces:
        if function.endswith('_types'):
            continue
        mapped = _qualify(piece, MEMBERS[name])
        inverse = _restore(mapped, MEMBERS[name])
        if piece != inverse or '{' not in piece:
            raise ValueError('every original helper body must have an exact inverse-qualified correspondence')
        bodies.append({'original_function': function,
                       'qualified_function': next((q for q, p in MEMBERS.items() if p == function), function),
                       'body_sha256': digest(piece.split('{', 1)[1]),
                       'inverse_qualified_body_sha256': digest(inverse.split('{', 1)[1]),
                       'original_fragment_sha256': digest(piece), 'qualified_fragment_sha256': digest(mapped)})
    old_body = source.split('static void ' + MEMBERS[name] + '(', 1)[1].split('{', 1)[1]
    new_body = qualified.split('static void ' + name + '(', 1)[1].split('{', 1)[1]
    for renamed, parent in MEMBERS.items():
        new_body = new_body.replace(renamed + '(', parent + '(')
    if old_body != new_body:
        raise ValueError('the qualified domain may not silently change the original executable body')
    return {'version': 3, 'original_member': MEMBERS[name], 'qualified_member': name,
            'parent_model': dict(PARENT), 'original_source_sha256': digest(source),
            'qualified_source_sha256': digest(qualified), 'body_sha256': digest(old_body),
            'inverse_qualified_source_sha256': digest(restored), 'executable_bodies': bodies,
            'unary_role': 'reallocation eligibility; not exclusive ownership',
            'caller_discharge': 'required; not assumed', 'original_contract_proved': False,
            'allocation_identity_condition': 'capacity>0 implies receiver and backing allocation bases differ',
            'alias_policy': 'escaped raw aliases remain legal before release and stale afterward',
            'pending': ['complete original source/clause/RTE/init/frame/lifetime map under the new contract',
                        'fresh unbounded body proof', 'source-derived caller eligibility and cross-view liveness accounting'],
            'proof_status': 'unsupported preparation; no verifier launch or model-body proof'}

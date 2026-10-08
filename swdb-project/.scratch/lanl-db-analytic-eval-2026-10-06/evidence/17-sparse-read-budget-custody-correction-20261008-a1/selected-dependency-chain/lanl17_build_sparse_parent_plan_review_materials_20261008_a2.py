"""2026-10-08 ET. SOURCE ONLY; NOT RUN.

Fixed local assembly of unsealed parent-plan/review materials. No SSH, Git,
target imports, subset search, real plan/review seals or selected control call.
All current observations and semantic conclusions must be supplied explicitly.
"""
import argparse
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

BASE = Path('/data1/yanruj')
RAW = Path('/data/yanruj/EvolveSWDB_runs')
PRIMARY = BASE/'ArchEvolve'
O1 = 'ArchEvolve-lanl-count-20261006'
GUARD_SHA = 'd75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'
O5_SHA = '098f874bbfe5469090f4320911288fcdee5bee268631f96a40a45a55279b08ad'
FIXED = {
    'O5': (22858530, O5_SHA),
    'RAW_materials': (310610, '985cb06d4c866e832ef22e5f245db357237358d1f1d95b33fc61f63cf36d3e5e'),
    'O7_addendum': (8001, '8e1f44130acda4c93d2e4924618646a4967277fc91257b9c4784ab86e780505a'),
    'source_proof_map': (324823, '0cd4b124d7c93635eb7d699e9fc73b9cb73236c34c143148ff10e62515308444'),
    'all707': (735828, 'f20d893b54f66862c3906eccbf5da255691b0932c8ce68debc4ffb7a7cfbf663'),
    'protected_worksheet': (15036, '33e60d72ca292fed9a88f32980fde0ffb27456e7444abd06be2a4bea7ebc764f'),
    'common_configuration': (14661, '1891bebe4f3a8fbbf8c1ee9c5813b8ac2e6617cdabe0b11e76da5cb837bdc83a'),
}
FIELDS = ('dev','ino','mode','nlink','uid','gid','size','mtime_ns','ctime_ns')
PROOF_FIELDS = ('row','receipt_key','commit','relative_path','sha256','receipt_json_path')
COVERAGE_KEYS = ('control_siblings_complete_review','pending_alias_coverage_review',
                 'receipt_source_proofs_complete_review','original_raw_files_complete_review')
ONE = 32*1024*1024
TOTAL = 128*1024*1024
OUTPUT = 2*1024*1024
SECONDS = 120


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def stamp(s):
    return {key: getattr(s, 'st_'+key) for key in FIELDS}


def route(value, local=False):
    p = Path(value)
    require(type(value) is str and p.is_absolute() and str(p) == value
            and '..' not in p.parts, 'literal_canonical_route_required')
    if local:
        require(p == Path('/private/tmp') or Path('/private/tmp') in p.parents,
                'local_input_or_output_outside_private_tmp')
        require(not any(q.is_symlink() for q in (p, *p.parents)), 'local_route_redirect')
        require(p.resolve(strict=True) == p, 'local_route_changed')
    return p


def remote_pin(value):
    require(type(value) is dict and set(value) >= {'path','bytes','sha256'}, 'file_pin_required')
    p = route(value['path'])
    require(p != BASE and (BASE in p.parents or RAW in p.parents), 'remote_pin_outside_original_roots')
    require(type(value['bytes']) is int and 0 <= value['bytes'] <= 512*1024*1024
            and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'remote_pin_size_or_SHA')
    if 'stat' in value:
        s = value['stat']
        require(set(s) == set(FIELDS) and all(type(s[k]) is int for k in FIELDS)
                and s['size'] == value['bytes'] and s['uid'] == 114316761 and s['nlink'] == 1,
                'ordinary_original_stat_shape')
    return copy.deepcopy(value)


def bare_pin(value):
    return {key: copy.deepcopy(value[key]) for key in ('path','bytes','sha256','stat') if key in value}


class OriginalBytes:
    def __init__(self):
        self.deadline = time.monotonic()+SECONDS
        self.bytes = 0
        self.witnesses = {}

    def left(self):
        require(time.monotonic() < self.deadline, 'local_metadata_deadline')

    def read(self, value, cap=ONE):
        self.left()
        p = route(value['path'], True)
        before = p.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                and before.st_nlink == 1 and before.st_size <= cap,
                'local_original_owner_type_link_bound')
        fd = os.open(p, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            require(stamp(os.fstat(fd)) == stamp(before), 'local_open_changed')
            parts = []
            count = 0
            while True:
                self.left()
                piece = os.read(fd, min(1024*1024, cap-count+1))
                if not piece:
                    break
                count += len(piece)
                self.bytes += len(piece)
                require(count <= cap and self.bytes <= TOTAL, 'local_read_budget')
                parts.append(piece)
            raw = b''.join(parts)
            require(count == before.st_size and stamp(os.fstat(fd)) == stamp(before)
                    == stamp(p.lstat()), 'local_returned_bytes_changed')
        finally:
            os.close(fd)
        require(count == value['bytes'] and sha(raw) == value['sha256'], 'original_local_byte_pin_changed')
        self.witnesses[str(p)] = (stamp(before), sha(raw), len(raw))
        return raw

    def final(self):
        # Rehash originals/source/request; never rely on a separate initial read.
        for name, (s, digest, size) in list(self.witnesses.items()):
            self.read({'path': name, 'bytes': size, 'sha256': digest})
            require(self.witnesses[name][0] == s, 'original_input_interval_changed')


def guard_constants(raw):
    tree = ast.parse(raw)
    result = {}
    # These five exact selected assignments are literal data, not executable AST.
    for key in ('ROWS','RECEIPTS','FUTURE_SOURCE_HASHES','RETIREMENT_RAW_LIBRARY_PINS','RETIREMENT_OPERATION'):
        nodes = [n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == key for t in n.targets)]
        require(len(nodes) == 1, 'closed_guard_data_assignment')
        result[key] = ast.literal_eval(nodes[0].value)
    require(len(result['ROWS']) == 18 and len(result['RECEIPTS']) == 22
            and len(result['FUTURE_SOURCE_HASHES']) == 13
            and len(result['RETIREMENT_RAW_LIBRARY_PINS']) == 22, 'selected_guard_data_shape')
    return result


def assemble(request, docs, constants):
    """Return an UNSEALED noncircular configuration and review-body material.

    Supplied parent conclusions are copied, not derived from byte matches.
    This function never produces an identity_sha256 or a usable parent_review_pin.
    """
    require(request['format'] == 'swdb.sparse-parent-plan-materials-request.v1'
            and request['sealed'] is False and 'identity_sha256' not in request,
            'explicit_unsealed_materials_request_required')
    selected = request['selected_rows']
    rows = constants['ROWS']
    receipts = constants['RECEIPTS']
    require(type(selected) is list and selected and len(set(selected)) == len(selected)
            and set(selected) <= set(rows) and O1 not in selected,
            'explicit_ordered_unprotected_subset_required')
    expected = request['expected_primary']
    require(re.fullmatch('[0-9a-f]{40}', expected), 'actual_delivered_revision_required')
    timestamp = datetime.datetime.fromisoformat(request['checked_at'])
    require(timestamp.tzinfo is not None, 'explicit_fresh_parent_time_required')
    # Freshness is ultimately enforced on native host by the selected guard.
    o = docs['O5']
    require(o['sealed'] is False and 'identity_sha256' not in o
            and o['observation_complete_within_finite_scope'] is True
            and o['stable_at_end_of_observation'] is True and o['gaps'] == []
            and o['expected_primary'] == expected and 'failure' not in o,
            'genuine_complete_original_O5_required')
    require(request['allocation_observation_pin']['sha256'] == O5_SHA
            and request['allocation_observation_pin']['bytes'] == FIXED['O5'][0]
            and request['allocation_observation_pin']['original_json_policy'] == 'original_unsealed',
            'O5_original_remote_pin_and_policy_required')
    allocation_pin = remote_pin(request['allocation_observation_pin'])
    allocation = copy.deepcopy(request['allocation_decision'])
    require(allocation['final_R17_revision'] == expected and allocation['selected_rows'] == selected
            and allocation['observation_file_sha256'] == O5_SHA
            and type(allocation['minimal_selected_subset']) is bool,
            'explicit_parent_allocation_decision_binding')
    require(type(request['fresh_capacity_and_cost']) is dict
            and request['fresh_capacity_and_cost']['selected_rows'] == selected
            and request['fresh_capacity_and_cost']['checked_at'] == request['checked_at'],
            'current_free_cost_and_subset_materials_missing')
    # Exact parent statements are required; no implicit True/empty/acceptance.
    coverage = copy.deepcopy(request['coverage'])
    require(set(coverage) == set(COVERAGE_KEYS), 'four_explicit_parent_coverage_objects_required')
    for key, value in coverage.items():
        require(type(value) is dict and type(value['complete']) is bool
                and type(value['review_basis']) is str and value['review_basis']
                and 'parent_review_identity_sha256' not in value, 'parent_coverage_basis_or_pending_link')
    require(type(coverage['pending_alias_coverage_review']['no_queued_source_consumers']) is bool,
            'explicit_parent_queue_conclusion_required')
    review_facts = copy.deepcopy(request['parent_review_facts'])
    require(set(review_facts) >= {'accepted_for_exact_subset','accepted_library_preserving_sparse_scope',
                                'final14_completed_and_released'}
            and all(type(review_facts[k]) is bool for k in ('accepted_for_exact_subset',
                     'accepted_library_preserving_sparse_scope','final14_completed_and_released')),
            'explicit_parent_review_semantics_required')
    require(not any(k in review_facts for k in ('identity_sha256','reviewed_configuration_sha256',
                                               'format','canonical_ensure_ascii')),
            'review_writer_fields_cannot_be_supplied_or_rewritten')

    raw_materials = docs['RAW_materials']
    addendum = docs['O7_addendum']
    require(len(raw_materials['RAW_file_materials']) == 107
            and len(raw_materials['all_184_preserved_source_proof_materials']) == 184,
            'original_material_count_changed')
    fresh_o7 = {p['path']: p['separate_fresh_query_original_file_pin']
                for p in addendum['four_original_inputs']}
    raw_pins = []
    leaf_custody = []
    for m in raw_materials['RAW_file_materials']:
        pin = m.get('O5_original_file_pin')
        if pin is None:
            pin = fresh_o7[m['path']]
        pin = remote_pin(bare_pin(pin))
        require(pin['path'] == m['path'] and pin['sha256'] == m['original_sha256'], 'original_RAW_material_pin_changed')
        for association in m['original_receipt_associations']:
            key = association['receipt_key']
            require(key in receipts, 'original_RAW_receipt_key_changed')
            raw_pins.append({**pin, 'receipt_key': key,
                             'original_receipt_json_path': copy.deepcopy(association['receipt_json_path'])})
            leaf_custody.append({'path': pin['path'], 'receipt_key': key,
                                 'original_association': copy.deepcopy(association)})
    require(len(raw_pins) == 158, 'original_RAW_association_multiplicity_changed')
    mandatory = {str(RAW/name) for r in receipts.values() for name in r['raw_names']}
    justified = {m['path'] for m in raw_materials['six_separately_justified_original_receipt_control_routes']}
    justified.add(raw_materials['additional_O7_original_input_route']['path'])
    full_roots = request['reviewed_full_RAW_roots']
    require(type(full_roots) is list and len(set(full_roots)) == len(full_roots)
            and mandatory|justified <= set(full_roots), 'original_RAW_routes_not_silently_omitted')
    for value in full_roots:
        p = route(value)
        require(p.parent == RAW and p.name.startswith(('lanl-','lanl17-')),
                'literal_full_RAW_route_required')
    siblings = [p for p in full_roots if p not in mandatory]
    require(all(any(Path(p['path']).is_relative_to(Path(root)) for root in full_roots)
                for p in raw_pins), 'original_RAW_pin_outside_explicit_full_scope')

    source_map = docs['source_proof_map']
    proof_materials = source_map['candidate_receipt_source_file_proofs']
    require(len(proof_materials) == 184, 'source_proof_original_count_changed')
    proofs = [{k: copy.deepcopy(p[k]) for k in PROOF_FIELDS}
              for p in proof_materials if p['row'] in selected]
    for proof in proofs:
        require(proof['commit'] == rows[proof['row']]['head']
                and proof['receipt_key'] in rows[proof['row']]['receipts'], 'source_proof_original_scope')

    history_doc = docs['all707']
    entries = history_doc['prior_697_exact_observed_pin_bindings']+history_doc['new_10_current_delivered_archive_bindings']
    require(len(entries) == 707, 'all707_original_binding_count_changed')
    history_pins = {r['current_O5_file_pin']['path']: r['current_O5_file_pin'] for r in entries
                    if set(r['current_O5_file_pin']['candidate_reference_rows']) & set(selected)}
    require(len(history_pins) == len([r for r in entries
            if set(r['current_O5_file_pin']['candidate_reference_rows']) & set(selected)]),
            'duplicate_current_history_pin')
    approvals = request['historical_file_reviews']
    require(type(approvals) is dict and set(approvals) == set(history_pins),
            'explicit_review_for_every_current_selected_literal_file_required')
    history = []
    for path in sorted(history_pins):
        review = approvals[path]
        pin = bare_pin(history_pins[path])
        require(review['sha256'] == pin['sha256'] and review['bytes'] == pin['bytes']
                and review['handling'] == 'historical_only_not_dereferenced'
                and type(review['review_basis']) is str and review['review_basis'],
                'per_file_historical_semantics_must_be_parent_supplied')
        history.append({**remote_pin(pin), 'handling': review['handling'], 'review_basis': review['review_basis']})

    future = copy.deepcopy(request['future_source_pin_choices'])
    require(set(future) == set(constants['FUTURE_SOURCE_HASHES']), 'thirteen_explicit_future_choices_required')
    actual_choices = o['observations']['future_13_source_pins']['exact_R3_expected_pin_sources']
    for name, pin in future.items():
        remote_pin(pin)
        require(pin['sha256'] == constants['FUTURE_SOURCE_HASHES'][name]['sha256']
                and pin['bytes'] == constants['FUTURE_SOURCE_HASHES'][name]['bytes']
                and bare_pin(pin) in [bare_pin(p) for p in actual_choices[name]],
                'chosen_future_source_must_be_an_observed_exact_original')
        require(not any(Path(pin['path']).is_relative_to(BASE/n) for n in selected),
                'future_source_inside_selected_scope')
    pending = copy.deepcopy(request['pending_control_files'])
    for pin in pending:
        remote_pin(pin)
        require(type(pin['dereferenced_paths']) is list, 'explicit_pending_dereference_list_required')
        for value in pin['dereferenced_paths']:
            p = route(value)
            require(not any(p.is_relative_to(BASE/n) for n in selected), 'pending_control_inside_selected_scope')
    consumers = copy.deepcopy(request['relevant_privileged_consumers'])
    require(type(consumers) is list and len({v['pid'] for v in consumers}) == len(consumers),
            'explicit_unique_consumer_inventory_required')
    for value in consumers:
        require('parent_review_identity_sha256' not in value and value['identified_as_owned_consumer'] is True
                and type(value['review_basis']) is str and value['review_basis'], 'explicit_consumer_basis_required')
        remote_pin(value['identification_file_pin'])
    worksheet = docs['protected_worksheet']
    common = docs['common_configuration']['configuration_inventory']['common_configuration']
    common_pin = bare_pin(common)
    common_pin['stat'] = {key: common['stat']['st_'+key] for key in FIELDS}
    protected_files = copy.deepcopy(request['protected_file_pins'])
    protected_by_path = {v['path']: v for v in protected_files}
    require(len(protected_by_path) == len(protected_files), 'protected_pin_duplicate')
    required_protected = worksheet['copier_13_original_paths']+[
        worksheet['hook_protected_file_pin'], worksheet['request_protected_file_pin'],
        worksheet['publication_original_protected_file_pin']]
    required_protected += worksheet['future13_original_physical_aliases']
    for pin in required_protected:
        require(pin['path'] in protected_by_path
                and all(protected_by_path[pin['path']][k] == pin[k] for k in ('path','bytes','sha256')),
                'original_staged_copies_hook_request_publication_aliases_not_dropped')
    for pin in protected_files:
        remote_pin(pin)
    for field in ('account_service_identification_pin','portal_service_review_pin'):
        remote_pin(request[field])
    native = request['native_git_pin']
    require({k: native[k] for k in ('path','bytes','sha256')} ==
            {k: docs['common_configuration']['native']['git'][k] for k in ('path','bytes','sha256')},
            'native_Git_original_pin_must_match')
    extra = request['additional_protected_paths']
    require(type(extra) is list and str(BASE/O1) in extra
            and set(worksheet['both_source_snapshots_still_protected']) <= set(extra)
            and worksheet['hooks_protected_directory'] in extra
            and worksheet['deployment_protected_directory'] in extra,
            'original_protected_source_and_deployment_routes_required')
    absent = request['reserved_absent_paths']
    require(absent == worksheet['future_absent_scientific_routes'], 'parent_explicit_reserved_family_changed')
    for value in extra+absent:
        p = route(value)
        require(not any(p.is_relative_to(BASE/n) or (BASE/n).is_relative_to(p) for n in selected),
                'additional_protection_overlaps_selection')

    configuration = {
        'format': 'swdb.library-preserving-sparse-retirement-parent-plan.v1',
        'canonical_ensure_ascii': True, 'checked_at': request['checked_at'],
        'expected_primary': expected, 'selected_rows': selected, 'guard_source_sha256': GUARD_SHA,
        'selection_reason': request['selection_reason'], 'allocation_decision': allocation,
        'allocation_observation_pin': allocation_pin, 'native_git_pin': copy.deepcopy(native),
        'raw_control_sibling_paths': siblings, 'original_raw_file_pins': raw_pins,
        'historical_reference_files': history, 'pending_control_files': pending,
        'future_source_pins': future, 'receipt_source_file_proofs': proofs,
        'relevant_privileged_consumers': consumers,
        'account_service_identification_pin': copy.deepcopy(request['account_service_identification_pin']),
        'portal_service_review_pin': copy.deepcopy(request['portal_service_review_pin']),
        'additional_protected_paths': extra, 'reserved_absent_paths': absent,
        'protected_file_pins': protected_files, 'common_configuration_pin': common_pin,
        'retained_raw_library_aliases': copy.deepcopy(constants['RETIREMENT_RAW_LIBRARY_PINS']),
        'retirement_operation': copy.deepcopy(constants['RETIREMENT_OPERATION']),
        'shared_config_and_main_index_must_remain_exact': True,
        'parent_supplied_fresh_capacity_and_cost': copy.deepcopy(request['fresh_capacity_and_cost']),
        **coverage,
    }
    require(type(configuration['selection_reason']) is str and configuration['selection_reason'],
            'parent_concrete_selection_reason_required')
    config_sha = sha(canonical(configuration))
    review_body = {'format':'swdb.library-preserving-sparse-retirement-parent-review.v1',
                   'canonical_ensure_ascii':True, 'reviewed_configuration_sha256':config_sha, **review_facts}
    return {'format':'swdb.unsealed-sparse-parent-plan-review-materials.v1', 'sealed':False,
            'configuration_without_only_review_backlinks':configuration,
            'parent_review_body_without_identity':review_body,
            'parent_supplied_fresh_capacity_cost_materials':copy.deepcopy(request['fresh_capacity_and_cost']),
            'original_RAW_leaf_associations':leaf_custody,
            'original_receipt_policy_materials_unchanged':copy.deepcopy(
                raw_materials['original_receipt_byte_and_leaf_reconciliation']),
            'counts':{'selected_rows':len(selected),'original_RAW_files':107,
                      'RAW_receipt_associations':len(raw_pins),'selected_source_proofs':len(proofs),
                      'selected_literal_history_files':len(history),'full_RAW_roots':len(full_roots)},
            'required_later_parent_publication':[
                'Require final current facts and all explicit parent semantic conclusions accepted; these materials grant no authority.',
                'Seal review_body whole-minus-identity with canonical True; publish and obtain its exact original path/bytes/SHA.',
                'Create a deep copy of configuration. Add parent_review_identity_sha256 to its four coverage objects and every explicit Consumer, using that review identity.',
                'Add parent_review_pin with review path/bytes/SHA/format/identity/canonical_ensure_ascii True. Seal plan whole-minus-identity canonical True.',
                'Native publication must preserve the supplied checked_at/freshness, original pin policies and byte provenance; a renamed stale observation is not fresh.',
                'Before invocation, recheck actual plan/read/stat/walk costs and current private guard/wrapper paths. No actual plan or review seal is emitted here.'
            ],
            'eligibility_minimality_queue_coverage_are_supplied_parent_semantics':True,
            'no_remote_physical_or_index_recovery_cap_fit_capacity_or_science_admission':True}


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', required=True)
    p.add_argument('--request-sha256', required=True)
    p.add_argument('--source-sha256', required=True)
    p.add_argument('--guard-source', required=True)
    p.add_argument('--output-directory', required=True)
    a = p.parse_args()
    require(re.fullmatch('[0-9a-f]{64}', a.request_sha256)
            and re.fullmatch('[0-9a-f]{64}', a.source_sha256), 'explicit_parent_source_request_pins')
    io = OriginalBytes()
    own = Path(__file__).absolute()
    own_pin = {'path':str(own),'bytes':own.lstat().st_size,'sha256':a.source_sha256}
    io.read(own_pin, OUTPUT)
    request_path = route(a.request, True)
    request_pin = {'path':str(request_path),'bytes':request_path.lstat().st_size,'sha256':a.request_sha256}
    request = strict(io.read(request_pin, 16*1024*1024))
    require(set(request['original_local_inputs']) == set(FIXED), 'seven_explicit_original_metadata_inputs')
    docs = {}
    for name, (size, digest) in FIXED.items():
        pin = request['original_local_inputs'][name]
        require(pin['bytes'] == size and pin['sha256'] == digest, 'immutable_original_input_pin')
        docs[name] = strict(io.read(pin))
    guard = Path(a.guard_source)
    guard_pin = {'path':str(guard),'bytes':180887,'sha256':GUARD_SHA}
    constants = guard_constants(io.read(guard_pin, OUTPUT))
    materials = assemble(request, docs, constants)
    materials['original_local_input_pins'] = copy.deepcopy(request['original_local_inputs'])
    materials['builder_original_source_pin'] = own_pin
    materials['request_original_pin'] = request_pin
    raw = canonical(materials)+b'\n'
    require(len(raw) <= OUTPUT, 'unsealed_material_output_bound')
    output = Path(a.output_directory)
    require(output.is_absolute() and output.parent == Path('/private/tmp') and str(output) == a.output_directory
            and not os.path.lexists(output), 'fresh_direct_local_output_required')
    route(str(output.parent), True)
    io.final()
    os.mkdir(output, 0o700)
    path = output/'materials.json'
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    readback_pin = {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
    io.read(readback_pin, OUTPUT)
    io.final()
    print(json.dumps({'format':materials['format'],'sealed':False,'original_output_pin':readback_pin,
                      'actual_plan_or_review_seal_generated':False}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if isinstance(error, SystemExit):
            raise
        # Preserve original inputs and any fresh partial; no raw exception prose.
        print(json.dumps({'sealed':False,'error_class':type(error).__name__,
                          'error_sha256':sha(str(error).encode()),'partial_output_not_admission':True},sort_keys=True))
        raise SystemExit(1)

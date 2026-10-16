"""2026-10-16 ET. Synthetic fixed-order trace source; no actual acceptance.

Each source imports bodyless scalar ghost queries. No header call, CPU pointer
access or actual concurrent source operation is thereby certified.
"""
from trace_fixture import QUERY_PROTOTYPES


def case(name, actions, predicate='1', *, expected='proven', failure=None):
    return {'name': name, 'actions': actions, 'predicate': predicate,
            'expected_verdict': expected, 'expected_property': failure}


C = 'swdb_t28_'
CASES = [
    case('same_thread_read_read', [
        ('claim', [0, 0, 4]), ('cpu_write', [0, 0, 7]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'),
        ('cpu_read', [0, 0], 'observed'), ('wait', [0]),
        ('result', ['command'], 'gathered')], 'observed == 7 && gathered == 7'),
    case('same_thread_write_during_gather', [
        ('claim', [0, 0, 4]), ('issue', [0, 1, 0, 0, 0, 4, 0]),
        ('cpu_write', [0, 0, 11]), ('wait', [0])],
        expected='refuted', failure='same_thread_read_footprint_write'),
    case('same_thread_read_during_store', [
        ('claim', [0, 0, 4]), ('issue', [0, 2, 0, 0, 0, 4, 9]),
        ('cpu_read', [0, 0]), ('wait', [0])],
        expected='refuted', failure='store_footprint_cpu_access'),
    case('other_thread_read_during_store', [
        ('claim', [0, 0, 4]), ('issue', [0, 2, 0, 0, 0, 4, 9]),
        ('cpu_read', [1, 0]), ('wait', [0])],
        expected='refuted', failure='store_footprint_cpu_access'),
    case('other_thread_cas_history_union', [
        ('claim', [0, 0, 4]), ('cpu_write', [0, 0, 7]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'),
        ('cpu_cas', [1, 0, 7, 11], 'success'), ('wait', [0]),
        ('result', ['command'], 'observed')],
        'success == 1 && (observed == 7 || observed == 11)'),
    case('other_thread_cas_issue_only', [
        ('claim', [0, 0, 4]), ('cpu_write', [0, 0, 7]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'),
        ('cpu_cas', [1, 0, 7, 11]), ('wait', [0]),
        ('result', ['command'], 'observed')], 'observed == 7', expected='refuted', failure='postcondition'),
    case('failed_cas_adds_no_history', [
        ('claim', [0, 0, 4]), ('cpu_write', [0, 0, 7]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'),
        ('cpu_cas', [1, 0, 6, 11], 'success'), ('wait', [0]),
        ('result', ['command'], 'observed')], 'success == 0 && observed == 7'),
    case('preissue_visibility_excludes_older_value', [
        ('claim', [0, 0, 4]), ('cpu_write', [0, 0, 3]), ('cpu_write', [0, 0, 7]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'), ('wait', [0]),
        ('result', ['command'], 'observed')], 'observed == 7'),
    case('preissue_visibility_old_value', [
        ('claim', [0, 0, 4]), ('cpu_write', [0, 0, 3]), ('cpu_write', [0, 0, 7]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'), ('wait', [0]),
        ('result', ['command'], 'observed')], 'observed == 3', expected='refuted', failure='postcondition'),
    case('history_result_freezes_at_cover', [
        ('claim', [0, 0, 4]), ('cpu_write', [0, 0, 7]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'),
        ('cpu_write', [1, 0, 11]), ('wait', [0]), ('result', ['command'], 'first'),
        ('cpu_write', [1, 0, 13]), ('result', ['command'], 'second')],
        '(first == 7 || first == 11) && second == first'),
    case('region_stall_cross_thread_covers_store', [
        ('claim', [0, 0, 4]), ('claim', [1, 1, 4]),
        ('issue', [0, 2, 0, 0, 0, 4, 9], 'first'),
        ('issue', [1, 1, 0, 0, 1, 4, 0]),
        ('pending', ['first'], 'pending'), ('cpu_read', [1, 0], 'visible'), ('wait', [1])],
        'pending == 0 && visible == 9'),
    case('region_read_read_does_not_cover', [
        ('claim', [0, 0, 4]), ('claim', [1, 1, 4]),
        ('issue', [0, 1, 0, 0, 0, 4, 0], 'first'),
        ('issue', [1, 1, 0, 0, 1, 4, 0]), ('pending', ['first'], 'pending'),
        ('wait', [0]), ('wait', [1])], 'pending == 0', expected='refuted', failure='postcondition'),
    case('region_other_write_does_not_cover', [
        ('claim', [0, 0, 4]), ('claim', [1, 1, 4]),
        ('issue', [0, 2, 0, 0, 0, 4, 9], 'first'),
        ('issue', [1, 2, 1, 1, 1, 4, 11]), ('pending', ['first'], 'pending'),
        ('wait', [0]), ('wait', [1])], 'pending == 0', expected='refuted', failure='postcondition'),
    case('other_thread_ownership_command', [
        ('claim', [0, 0, 4]), ('issue', [1, 1, 0, 0, 0, 4, 0]), ('wait', [0])],
        expected='refuted', failure='tile_ownership'),
    case('other_thread_ownership_tile_read', [
        ('claim', [0, 0, 4]), ('tile_read', [1, 0, 4])],
        expected='refuted', failure='tile_ownership'),
    case('disjoint_thread_tiles', [
        ('claim', [0, 0, 4]), ('claim', [1, 1, 4]),
        ('issue', [0, 1, 0, 0, 0, 4, 0]), ('issue', [1, 1, 1, 1, 1, 4, 0]),
        ('wait', [0]), ('wait', [1]), ('tile_read', [0, 0, 4]), ('tile_read', [1, 1, 4])]),
    case('pair_8byte_second_half_cpu_read', [
        ('claim', [0, 0, 8]), ('issue', [0, 1, 0, 0, 0, 8, 0]),
        ('tile_read', [0, 1, 4]), ('wait', [0])],
        expected='refuted', failure='pending_tile_write'),
    case('pair_4byte_other_half_cpu_read', [
        ('claim', [0, 0, 8]), ('issue', [0, 1, 0, 0, 0, 4, 0]),
        ('tile_read', [0, 1, 4]), ('wait', [0])]),
    case('pair_8byte_second_half_command', [
        ('claim', [0, 0, 8]), ('issue', [0, 1, 0, 0, 0, 8, 0]),
        ('issue', [0, 1, 1, 1, 1, 4, 0]), ('wait', [0]), ('wait', [1])],
        expected='refuted', failure='pending_tile_write'),
    case('pair_4byte_other_half_command', [
        ('claim', [0, 0, 8]), ('issue', [0, 1, 0, 0, 0, 4, 0]),
        ('issue', [0, 1, 1, 1, 1, 4, 0]), ('wait', [0]), ('wait', [1])]),
    case('pair_8byte_missing_second_owner', [
        ('claim', [0, 0, 4]), ('issue', [0, 1, 0, 0, 0, 8, 0]), ('wait', [0])],
        expected='refuted', failure='tile_ownership'),
    case('pair_4byte_one_owner', [
        ('claim', [0, 0, 4]), ('issue', [0, 1, 0, 0, 0, 4, 0]), ('wait', [0])]),
    case('pair_second_half_wait_covers', [
        ('claim', [0, 0, 8]), ('issue', [0, 1, 0, 0, 0, 8, 0], 'command'),
        ('wait', [1]), ('pending', ['command'], 'pending')], 'pending == 0'),
    # A bounded branch witnesses readiness's two answers. It claims no polling
    # termination or fairness and does not invent a public header operation.
    case('logical_ready_one_covers_zero_requires_wait', [
        ('claim', [0, 0, 4]), ('issue', [0, 1, 0, 0, 0, 4, 0], 'command'),
        ('ready', [0], 'ready'), ('pending', ['command'], 'pending'), ('wait', [0])],
        '(ready == 0 && pending == 1) || (ready == 1 && pending == 0)'),
    case('logical_ready_may_not_be_assumed_zero', [
        ('claim', [0, 0, 4]), ('issue', [0, 1, 0, 0, 0, 4, 0]),
        ('ready', [0], 'ready'), ('wait', [0])], 'ready == 0', expected='refuted', failure='postcondition'),
]


def source(row):
    lines = ['/* 2026-10-16 ET. Synthetic abstract trace: ' + row['name'] + '. */']
    lines += [prototype + ';' for prototype in QUERY_PROTOTYPES.values()]
    lines.append('int trust_fixture(void) {')
    for action in row['actions']:
        name, arguments = action[:2]
        expression = C + name + '(' + ', '.join(map(str, arguments)) + ')'
        lines.append('  ' + ('int ' + action[2] + ' = ' if len(action) == 3 else '') + expression + ';')
    lines += ['  return ' + row['predicate'] + ';', '}', '']
    return '\n'.join(lines)


def contract_transform(contract):
    contract['proof_unit'].pop('array_domains', None)
    contract['concurrency_frame'] = []
    contract['provenance']['origin']['intrinsic_specification'] = 'ticket28-synthetic-memory-trace-only'
    contract['clauses'][0]['statement'] = 'The bounded synthetic abstract event trace satisfies its named property.'


def prove(tmp_path, row, *, actual_environment):
    """Root-only helper; no fallback actual or scripted tool environment."""
    if not isinstance(actual_environment, dict) or not actual_environment:
        raise ValueError('explicit root-admitted actual environment is mandatory')
    from testkit.dx100_trust import run_semantics_fixture
    from trace_fixture import transform
    return run_semantics_fixture(tmp_path, 'cbmc', source=source(row), semantics_transform=transform,
                                 contract_transform=contract_transform,
                                 postcondition=r'assigns \nothing; ensures \result == 1;',
                                 tool_environment=actual_environment)

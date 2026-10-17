"""2026-10-16 ET. Exact public assertion AST suffix; passive inputs only."""
def audit_public_assertions_v1(record, entry, row, semantics):
    assert record['pins']['proof_semantics'] == {'id': ENTRY, 'sha256': hashlib.sha256(semantics.read_bytes()).hexdigest()}
    assert entry['description'] == SCOPE
    assert len(entry['calls']) == 26 and all((call['supported'] is False for call in entry['calls']))
    assert {q['query']: q['prototype'] for q in entry['queries']} == QUERY_PROTOTYPES
    assert all((q['contract'] == WP_REFUSAL for q in entry['queries']))
    assert entry['wp'] == {} and 'layout' not in entry['model']
    assert record['verdict'] == row['expected_verdict'], record
    settings = record['settings']
    assert settings['verifier_launched'] is True
    assert record['proof_setup_check']['verdict'] == 'passed'
    initialized = settings['bounded_initialization']
    assert initialized['verdict'] == 'passed' and initialized['model_policy']['id'] == POLICY_ID
    assert initialized['model_policy']['calls'] == sorted(QUERY_PROTOTYPES)
    assert settings['agreement']['verdict'] == 'agree' and settings['agreement']['runs'] > 0
    semantics_settings = settings['proof_semantics']
    assert semantics_settings['scope'] == 'synthetic abstract scalar event trace only'
    assert semantics_settings['exit_check'] == 'no pending abstract command at unit exit'
    assert semantics_settings['native_address_abi'] == 'scalar abstract cell/region/tile IDs; no caller pointer mapping'
    assert semantics_settings['counterexample_scope'] == 'abstract-model trace only; no hardware counterexample or source refinement'
    imports = semantics_settings['source_imports']
    expected_calls = {'swdb_t28_' + action[0] for action in row['actions']}
    assert {i['binding']['name'] for i in imports} == expected_calls
    assert all((i['binding'] and (not i['reason']) for i in imports))
    reports = {}
    for pin in [record['evidence']['adapter_log'], *record['evidence']['reports']]:
        path = Path(pin['path'])
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == pin['sha256']
        reports.setdefault(pin.get('name'), []).append(pin)
    assert len(reports.get('cbmc_input', [])) == len(reports.get('cbmc_output', [])) == 1
    text = Path(reports['cbmc_input'][0]['path']).read_text()
    assert '  swdb_dx_init();' in text and '  swdb_dx_check_exit();' in text
    assert len(re.findall('  dx_tile_data\\[[0-3]\\]\\[0\\] = \\(int\\) swdb_next\\(\\);', text)) == 4
    assert text.count('/* swdb-anchor trust_fixture.contract */') == 1
    native_outputs = [pin for name in ('differential_c_output', 'differential_cxx_output') for pin in reports.get(name, [])]
    assert len(native_outputs) == 2
    for pin in native_outputs:
        output = Path(pin['path']).read_text()
        assert 'swdb.oracle_capacity' not in output and 'swdb.ghost_capacity' not in output
        assert ' end=done' in output or row['expected_property'] not in (None, 'postcondition')
    assumptions = record['assumptions']
    rules = {rule['id']: rule for rule in entry['rules'] if rule.get('record_assumption') is True}
    assert {'synthetic_trace_scope', 'trace_domain', 'history_visibility'} | set(TRUST) <= rules.keys()
    for name, rule in rules.items():
        assert any((a['reference'] == {'id': ENTRY + '#' + name, 'sha256': record['pins']['proof_semantics']['sha256']} and a['sentence'] == rule['statement'] for a in assumptions))
    inherited = [a['sentence'] for a in assumptions if a['reference']['id'].split('#')[-1] in TRUST]
    assert len(inherited) == 5 and all(('Retained unused boundary entry' in sentence for sentence in inherited))
    assert not any((a['kind'] == 'reduction' or "each command's values as if it finished at issue" in a['sentence'] or "Native agreement and replay use Clang's flat" in a['sentence'] for a in assumptions))
    goals = record['goals']
    assert goals and (not any((g['status'] not in ('success', 'failure') for g in goals)))
    assert not any((g['status'] == 'failure' and (g['property'] in ('swdb.oracle_capacity', 'swdb.ghost_capacity', 'swdb.dx100_memory_domain') or '.unwind.' in g['goal']) for g in goals))
    if row['expected_verdict'] == 'proven':
        assert 'counterexample' not in record and 'unreplayed_counterexample' not in record
        assert any((g['property'] == 'swdb_reach.end' and g['status'] == 'failure' for g in goals))
        assert all((g['status'] == 'success' or g['property'].startswith('swdb_reach.') for g in goals))
    else:
        witness = record['counterexample']
        assert witness['replay']['replayed'] is True and witness['replay']['sanitizer'] is None
        expected = ENTRY + '#' + row['expected_property'] if row['expected_property'] != 'postcondition' else 'contract.dx100_trust_fixture#result.ensures1'
        assert witness['property'] == expected
        assert witness['property'] in witness['replay']['failed']
    assert (semantics.parent.parent / 'proof_units/trust.cc').read_text() == source(row)

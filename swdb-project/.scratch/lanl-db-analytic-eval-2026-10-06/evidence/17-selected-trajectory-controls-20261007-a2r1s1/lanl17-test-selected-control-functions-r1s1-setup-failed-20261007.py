"""One isolated, synthetic regression; never import a prepared module or main.

Only AST-extracted projection/path/receipt functions execute. No actual inputs,
SWDB imports, Store, native/compiler/provider commands, SSH or staging.
"""
import argparse, ast, copy, datetime, hashlib, json, os, pathlib, re, subprocess, sys, tempfile
from types import SimpleNamespace

SOURCES = {
    'a2_collector': ('/private/tmp/lanl17_compact_attempt_custody_a2_20261007.py', 'edb822dc9b69796321e86ed042ad8debda33d00479d25f10fbc856b4d8e65780'),
    'r1_collector': ('/private/tmp/lanl17_compact_attempt_custody_a2r1_20261007.py', 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'),
    'r1s1_auditor': ('/private/tmp/lanl17_selected_record_trajectory_auditor_a2r1s1_20261007.py', '6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'),
}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(v): return sha(json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())

def inputs():
    answer = {}
    for name, (path, expected) in SOURCES.items():
        raw = pathlib.Path(path).read_bytes()
        assert sha(raw) == expected, 'Reviewed source hash differs: ' + name
        answer[name] = {'path': path, 'sha256': expected, 'bytes': len(raw)}
    return answer

def isolated_namespace(tree, functions, constants=(), classes=()):
    selected = []
    for name in functions:
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
        assert len(nodes) == 1, 'Exact named pure function required: ' + name
        selected.append(copy.deepcopy(nodes[0]))
    for name in classes:
        nodes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name]
        assert len(nodes) == 1
        selected.append(copy.deepcopy(nodes[0]))
    namespace = {'json': json, 'hashlib': hashlib, 'pathlib': pathlib, 're': re, 'os': os, 'copy': copy}
    for name in constants:
        nodes = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
        assert len(nodes) == 1
        namespace[name] = ast.literal_eval(nodes[0].value)
    # This executes only the named AST definitions, never source imports/main.
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), '<selected-pure-definitions>', 'exec'), namespace)
    return namespace, {n.name: sha(ast.dump(n, include_attributes=False).encode()) for n in selected}

def refuses(action, label):
    try:
        action()
    except (ValueError, KeyError, TypeError, OSError):
        return {'case': label, 'state': 'refused_as_required'}
    raise AssertionError('Required refusal did not occur: ' + label)

def child():
    pinned_before = inputs()
    trees = {key: ast.parse(pathlib.Path(row['path']).read_text()) for key, row in pinned_before.items()}
    original, old_ast = isolated_namespace(trees['a2_collector'], ['candidate', 'calls'], ['CANDIDATE_KEYS', 'CALL_KEYS'])
    current, new_ast = isolated_namespace(trees['r1_collector'],
        ['require', 'sha', 'digest', 'safe_code', 'public_token', 'public_scalar', 'public_fields', 'excluded_fields', 'candidate', 'calls', 'checked_path', 'pin'],
        ['CANDIDATE_KEYS', 'CALL_KEYS', 'MAX_BYTES'])
    sentinels = {key: 'SYNTHETIC_PRIVATE_' + key.upper() for key in ('knobs', 'contracts', 'failed_checks', 'level_mix', 'classification')}
    candidate = {'id': 'fixture.candidate', 'class': 'fixture.workload', 'level': 'rejected',
        'artifact_sha256': 'a' * 64, 'patch_sha256': 'b' * 64,
        'knobs': {'private': sentinels['knobs']}, 'contracts': [sentinels['contracts']],
        'certification': {'record': 'fixture.certification', 'outcome': 'rejected', 'level_at_summary': 'rejected', 'failed_checks': [{'private': sentinels['failed_checks']}]},
        'comparisons': [{'baseline_role': 'code_base', 'comparison': 'fixture.comparison', 'baseline_evaluation': 'fixture.baseline',
            'ratio': 2.0, 'lower': 2.0, 'verdict': 'gain', 'level_mix': {'private': sentinels['level_mix']}}],
        'selection': {'ratio': 2.0, 'lower': 2.0, 'verdict': 'gain'}}
    calls = [{'role': 'rewriting', 'invocation': 'fixture.call1', 'outcome': 'completed', 'counted': True,
        'model': 'fixture-model', 'effort': 'xhigh', 'classification': {'private': sentinels['classification']}}]
    original_objects = copy.deepcopy((candidate, calls))
    red = {'candidate': original['candidate'](candidate), 'calls': original['calls'](calls)}
    red_text = json.dumps(red, sort_keys=True)
    try:
        assert not any(token in red_text for token in sentinels.values()), 'Original a2 copies synthetic nested private values'
    except AssertionError:
        red_case = {'case': 'original_a2_nested_projection_preservation', 'state': 'RED_reproduced_as_expected',
            'synthetic_sentinel_dimensions_disclosed': [key for key, token in sentinels.items() if token in red_text]}
    else:
        raise AssertionError('Original a2 RED was not reproduced')
    green = {'candidate': current['candidate'](candidate), 'calls': current['calls'](calls)}
    assert not any(token in json.dumps(green, sort_keys=True) for token in sentinels.values())
    excluded = green['candidate']['excluded_provider_values']
    assert excluded['knobs']['semantic_sha256'] == digest(candidate['knobs']) and excluded['contracts']['semantic_sha256'] == digest(candidate['contracts'])
    assert green['candidate']['certification']['excluded_metadata']['failed_checks']['semantic_sha256'] == digest(candidate['certification']['failed_checks'])
    assert green['candidate']['comparisons'][0]['excluded_metadata']['level_mix']['semantic_sha256'] == digest(candidate['comparisons'][0]['level_mix'])
    assert green['calls'][0]['excluded_metadata']['classification']['semantic_sha256'] == digest(calls[0]['classification'])
    assert all(x['values_exported'] is False for x in [*excluded.values(), green['candidate']['certification']['excluded_metadata']['failed_checks'], green['candidate']['comparisons'][0]['excluded_metadata']['level_mix'], green['calls'][0]['excluded_metadata']['classification']])
    assert (candidate, calls) == original_objects, 'Projection mutated original synthetic objects'
    rows = [red_case, {'case': 'r1_nested_projection_preservation', 'state': 'GREEN', 'excluded_dimensions': 5,
        'all_excluded_digests_exact': True, 'original_synthetic_objects_unchanged': True}]

    # Lift only the exact path-only prefix; never execute validate_source's Git.
    validate = next(n for n in trees['r1_collector'].body if isinstance(n, ast.FunctionDef) and n.name == 'validate_source')
    binding_body = copy.deepcopy(validate.body[:4])
    assert ast.unparse(binding_body[-1]).startswith("require(project == expected_project,")
    binding_body.append(ast.Return(value=ast.Name(id='project', ctx=ast.Load())))
    binding = ast.FunctionDef(name='synthetic_project_binding', args=copy.deepcopy(validate.args), body=binding_body, decorator_list=[])
    main = next(n for n in trees['r1_collector'].body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    first = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'output' for t in n.targets) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == 'checked_path')
    last = next(i for i in range(first, len(main.body)) if isinstance(main.body[i], ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'invocations' for t in main.body[i].targets))
    destination_body = copy.deepcopy(main.body[first:last])
    destination_body.append(ast.Return(value=ast.Name(id='output', ctx=ast.Load())))
    destination = ast.FunctionDef(name='synthetic_destination', args=ast.arguments(posonlyargs=[], args=[ast.arg(arg='a'), ast.arg(arg='campaign'), ast.arg(arg='source')], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=destination_body, decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[binding, destination], type_ignores=[])), '<selected-path-fragments>', 'exec'), current)

    with tempfile.TemporaryDirectory(prefix='lanl17-pure-regression-', dir='/private/tmp') as folder:
        base = pathlib.Path(folder)
        source = base / 'synthetic-source'; project = source / 'swdb-project'; project.mkdir(parents=True)
        clone_project = base / 'other-clone' / 'swdb-project'; clone_project.mkdir(parents=True)
        campaign = base / 'synthetic-campaign'; campaign.mkdir()
        scope = {'actual_git_worktree_root': str(source), 'actual_project_directory': str(project)}
        assert current['synthetic_project_binding'](SimpleNamespace(project=str(project)), {'source': str(source)}) == project
        rows.append({'case': 'exact_synthetic_manifest_project_binding', 'state': 'GREEN'})
        rows.append(refuses(lambda: current['synthetic_project_binding'](SimpleNamespace(project=str(clone_project)), {'source': str(source)}), 'different_same-shaped_clone_project'))
        fresh = base / 'fresh-custody'
        assert current['synthetic_destination'](SimpleNamespace(output=str(fresh)), campaign, scope) == fresh and not fresh.exists()
        rows.append({'case': 'normal_fresh_private_tmp_destination', 'state': 'GREEN', 'destination_not_created': True})
        alias = base / 'symlink-parent'; alias.symlink_to(source, target_is_directory=True)
        rows.append(refuses(lambda: current['synthetic_destination'](SimpleNamespace(output=str(alias / 'escape')), campaign, scope), 'symlink_ancestor_destination'))
        rows.append(refuses(lambda: current['synthetic_destination'](SimpleNamespace(output=str(project / 'escape')), campaign, scope), 'destination_inside_source_project'))
        rows.append(refuses(lambda: current['synthetic_destination'](SimpleNamespace(output=str(campaign / 'escape')), campaign, scope), 'destination_inside_campaign'))
        rows.append(refuses(lambda: current['checked_path'](base / '..' / 'escape'), 'lexical_parent_traversal'))
        synthetic_input = project / 'input.json'; synthetic_input.write_text('{}')
        rows.append(refuses(lambda: current['pin'](alias / 'swdb-project' / 'input.json'), 'symlink_ancestor_input'))

        audit, audit_ast = isolated_namespace(trees['r1s1_auditor'], ['require', 'need', 'sha', 'strict_json', 'digest', 'receipt_seal'], classes=['Refused', 'Pending'])
        reader_node = next(n for n in trees['r1s1_auditor'].body if isinstance(n, ast.ClassDef) and n.name == 'Reader')
        methods = [copy.deepcopy(next(n for n in reader_node.body if isinstance(n, ast.FunctionDef) and n.name == name)) for name in ('raw', 'json', 'sealed_json')]
        selected_reader = ast.ClassDef(name='SyntheticSelectedReader', bases=[], keywords=[], body=methods, decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[selected_reader], type_ignores=[])), '<selected-receipt-methods>', 'exec'), audit)
        reader = audit['SyntheticSelectedReader']()
        def receipt_pin(name, value, **extra):
            path = base / (name + '.json'); raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode(); path.write_bytes(raw)
            return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw), **extra}
        value = {'format': 'swdb.synthetic-control-custody.v1', 'synthetic': True, 'counter': 1, 'unicode': '\u03b1'}
        identity = audit['digest'](value, ensure_ascii=False); value['identity_sha256'] = identity
        valid = receipt_pin('valid', value, identity_sha256=identity, canonical_ensure_ascii=False)
        assert reader.sealed_json(valid) == value
        rows.append({'case': 'valid_explicit_original_canonical_policy_seal', 'state': 'GREEN'})
        rows.append(refuses(lambda: reader.sealed_json({k: v for k, v in valid.items() if k != 'identity_sha256'}), 'missing_claimed_identity_pin'))
        rows.append(refuses(lambda: reader.sealed_json({k: v for k, v in valid.items() if k != 'canonical_ensure_ascii'}), 'missing_original_canonical_policy'))
        rows.append(refuses(lambda: reader.sealed_json({**valid, 'canonical_ensure_ascii': 0}), 'nonboolean_canonical_policy'))
        rows.append(refuses(lambda: reader.sealed_json({**valid, 'canonical_ensure_ascii': True}), 'wrong_original_canonical_policy'))
        tampered = {**value, 'counter': 2}; bad = receipt_pin('tampered', tampered, identity_sha256=identity, canonical_ensure_ascii=False)
        rows.append(refuses(lambda: reader.sealed_json(bad), 'self_claimed_seal_payload_tamper_even_with_matching_file_pin'))
        rows.append(refuses(lambda: reader.sealed_json({**valid, 'sha256': '0' * 64}), 'original_file_sha_tamper'))
        unsealed = {'format': 'swdb.campaign-export.v1', 'campaign': 'fixture.campaign', 'dry_run': False, 'candidates': [], 'records': []}
        plain = receipt_pin('original-unsealed-public-format', unsealed)
        assert reader.json(plain) == unsealed and 'identity_sha256' not in reader.json(plain)
        rows.append({'case': 'original_unsealed_public_campaign_export_parse', 'state': 'GREEN', 'identity_not_invented': True, 'not_candidate_or_campaign_admission': True})
    assert inputs() == pinned_before, 'Prepared source originals changed during synthetic regression'
    result = {'format': 'swdb.lanl17-selected-pure-synthetic-regression.v1', 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'state': 'passed', 'sources': pinned_before, 'isolated_child': True, 'prepared_module_or_main_imports': 0,
        'actual_campaign_or_dependency_inputs_read': 0, 'store_native_compiler_provider_ssh_or_staging_actions': 0,
        'original_source_bytes_unchanged': True, 'selected_definition_AST_sha256': {'a2': old_ast, 'r1': new_ast, 'r1s1': audit_ast},
        'lifted_path_fragment_AST_sha256': {'project_binding': sha(ast.dump(binding, include_attributes=False).encode()), 'destination': sha(ast.dump(destination, include_attributes=False).encode())},
        'selected_receipt_method_AST_sha256': {n.name: sha(ast.dump(n, include_attributes=False).encode()) for n in methods}, 'cases': rows,
        'scope': 'One synthetic pure-function/path/seal regression only. Not actual host/account execution, campaign/dependency admission, full reader/main execution or scientific success.'}
    result['identity_sha256'] = digest(result)
    print(json.dumps(result, indent=2, allow_nan=False))

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--child', action='store_true'); parser.add_argument('--output'); args = parser.parse_args()
    if args.child:
        child(); return
    assert args.output
    output = pathlib.Path(args.output); assert output.is_absolute() and not output.exists() and not output.is_symlink()
    before = inputs()
    completed = subprocess.run([sys.executable, '-I', '-B', str(pathlib.Path(__file__).resolve()), '--child'], capture_output=True, timeout=30)
    assert completed.returncode == 0, completed.stderr.decode(errors='replace')
    value = json.loads(completed.stdout)
    assert value['state'] == 'passed' and value['identity_sha256'] == digest({k: v for k, v in value.items() if k != 'identity_sha256'})
    assert inputs() == before
    value['regression_source'] = {'path': str(pathlib.Path(__file__).resolve()), 'bytes': pathlib.Path(__file__).stat().st_size, 'sha256': sha(pathlib.Path(__file__).read_bytes())}
    value['child_exit_code'] = completed.returncode; value['child_stderr_bytes'] = len(completed.stderr)
    value['identity_sha256'] = digest({k: v for k, v in value.items() if k != 'identity_sha256'})
    with output.open('x') as handle: handle.write(json.dumps(value, indent=2, allow_nan=False) + '\n')
    raw = output.read_bytes()
    print(json.dumps({'output': str(output), 'file_sha256': sha(raw), 'bytes': len(raw), 'identity_sha256': value['identity_sha256'], 'cases': len(value['cases']), 'actual_admission': False}))

if __name__ == '__main__': main()

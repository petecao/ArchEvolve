def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if sha(args.expected) != EXPECTED_SHA256:
        raise ValueError('frozen compiler-only expectation differs')
    expected = json.loads(args.expected.read_bytes()); policy = expected['resource_policy']
    need(policy['root_headroom_bytes'] == 4194304 and policy['root_post_exit_reserve_bytes'] == 524288,
         'fixed root sibling/finalization headroom required')
    project = args.project.resolve(); repo = project.parent; out = args.output.resolve()
    if str(project) != expected['remote_project'] or out.exists() or out.is_relative_to(repo):
        raise ValueError('exact immutable source and fresh external output required')
    launch = linux_admission(expected, repo, out)
    out.mkdir(parents=True); os.chdir(project)
    started = time.monotonic(); deadline = started+policy['profile_seconds']
    result = {'date': '2026-10-16 ET', 'scope': expected['scope'],
        'source_commit': expected['source_commit'], 'producer_complete': False,
        'source_receipts': [], 'linux_launch': launch,
        'compiler_observation_only': True, 'proof_record_created': False,
        'source_or_member_or_Typed_or_caller_admission': False,
        'verifier_or_native_user_program_executed': False}
# __UNCHANGED_NESTED_GUARDS__
    try:
        bounded_json(out/'root-siblings-before.json', root_sibling_census(out, policy), out, policy)
        source_check(); bounded_json(out/'runtime.json', runtime_check(), out, policy)
        ambient = sorted(k for k in os.environ if k.startswith(('FRAMAC_WP', 'WP_')) or k == 'SWDB_PROOF_REPORT_OUT')
        if ambient:
            raise ValueError('ambient proof selectors refused')
        shutil.copyfile(__file__, out/'entry.py'); shutil.copyfile(args.expected, out/'expected.json')
        import base64
        staged = {}
        for key in ('fixture', 'worker'):
            row = expected[key]; raw = base64.b64decode(row['base64'], validate=True)
            need(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
                 'exact compiler-only staged input differs')
            path = out/row['name']; bounded_bytes(path, raw, out, policy); staged[key] = path
        sys.dont_write_bytecode = True; sys.path.insert(0, str(project))
        from swdb import rss_watchdog
        directory = out/'compiler'; directory.mkdir(); (directory/'tmp').mkdir()
        environment = dict(os.environ, SWDB_FRAMA_C='none', SWDB_CBMC='none',
            SWDB_CLANG='clang++', PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(directory/'tmp'))
        command = [sys.executable, '-I', '-B', str(staged['worker']), '--project', str(project),
            '--source', str(staged['fixture']), '--output', str(directory), '--expected', str(out/'expected.json')]
        bounded_json(directory/'command.json', {'argv': command, 'cwd': str(directory),
            'worker': pin(staged['worker']), 'fixture': pin(staged['fixture']),
            'verifier_selectors': {'SWDB_FRAMA_C': 'none', 'SWDB_CBMC': 'none'}}, out, policy)
        resources = guarded_compiler(command, directory, environment, policy,
            min(policy['leaf_timeout_seconds'], remaining()-10), rss_watchdog, out)
        bounded_json(directory/'resources.json', resources, out, policy)
        if resources['exit_code'] or any(resources[key] for key in ('timed_out','out_of_memory','output_limit')):
            raise ValueError('compiler observation failed; preserve original partial evidence')
        needed = ('original-lowering.c', 'lowering-metadata.json', 'anchors.json',
                  'original-function-ast.json', 'compiler-before.json', 'compiler-after.json', 'observation.json')
        need(all((directory/name).is_file() for name in needed), 'complete original compiler observation absent')
        before = json.loads((directory/'compiler-before.json').read_bytes())
        after = json.loads((directory/'compiler-after.json').read_bytes())
        need(before == after == {'runtime': expected['linux_project_identity_derivation']['runtime'],
            'identity': expected['linux_project_identity_derivation']['predicted_identity']},
            'compiler/source identity at observation points differs')
        observation = json.loads((directory/'observation.json').read_bytes())
        need(observation['source_sha256'] == expected['fixture']['sha256'] and
             observation['lowered_sha256'] == sha(directory/'original-lowering.c') and
             observation['source_or_member_or_caller_admitted'] is False,
             'source/C observation pin or admission differs')
        for key in ('fixture','worker'):
            need(sha(staged[key]) == expected[key]['sha256'], 'staged compiler-only input changed')
        source_check(); runtime_check()
        result.update(producer_complete=True, source_after_clean=True,
            artifacts=[pin(directory/name) for name in needed], observation=observation,
            classification='Original compiler/source metadata retained; no proof or source rule admitted.')
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error),
            primary_error=preserve_primary_error(out, error, policy))
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        result['within_profile_budget'] = time.monotonic() < deadline-1
        if not result['within_profile_budget']:
            result['producer_complete'] = False
        bounded_json(out/'result.json', result, out, policy, reserve=False)
        bounded_json(out/'root-siblings-after.json', root_sibling_census(out, policy), out, policy, reserve=False)
        bounded_json(out/'artifact-manifest.json', [{'relative': str(p.relative_to(out)), **pin(p)}
            for p in sorted(out.rglob('*')) if p.is_file() and p != out/'artifact-manifest.json'], out, policy, reserve=False)
        settled = raw_bytes(out); siblings = root_sibling_census(out, policy)
        if settled > policy['output_budget_bytes']-policy['root_headroom_bytes'] or \
                settled+siblings['bytes']+policy['root_post_exit_reserve_bytes'] > policy['output_budget_bytes'] or \
                time.monotonic() >= deadline:
            raise ValueError('strict final aggregate extent or deadline exceeded')
    return 0 if result['producer_complete'] and result['within_profile_budget'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

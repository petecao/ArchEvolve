"""2026-10-16 ET. Inert standalone nine-duty owned-header mathematical normal-WP profile (no layout execution).

Fresh public prepare/check plus unchanged normal command, flag/lineup policies,
native reader and outcome reading. No admitted model/View, public proof record,
universal setup attestation, source correspondence or caller acceptance.
"""
import argparse
import hashlib
import json
import os
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

EXPECTED_SHA256 = '__EXPECTED_SHA256__'

# __REVIEWED_HELPERS__

# __OWNED9_RUNTIME_AND_QUOTA__

# 2026-10-16 ET. Prospective C layout guards; source/Typed admission stays false.
def layout_dependencies(path, source):
    raw=path.read_bytes()
    if len(raw)>1048576 or b'\0' in raw:
        raise ValueError('bounded layout dependency file required')
    text=raw.decode().replace('\\\n',' ')
    target,separator,body=text.partition(':')
    if separator!=':' or target.strip()!='layout-object':
        raise ValueError('exact layout dependency target required')
    if any(c in body for c in (chr(92),chr(34),chr(39))):
        raise ValueError('unsupported layout dependency escaping')
    names=body.split()
    if not names or len(names)>512 or len(set(names))!=len(names):
        raise ValueError('layout dependency membership absent/duplicate/oversized')
    paths=[]
    for name in names:
        p=Path(name)
        if not p.is_absolute() or any(c in name for c in '\n\r\0$:*?[]'):
            raise ValueError('unsupported layout dependency spelling')
        paths.append(p)
    if source not in paths:
        raise ValueError('actual complete layout source missing from dependencies')
    return paths


def layout_pin(path):
    aliases=[]
    for candidate in reversed((path,*path.parents)):
        st=candidate.lstat()
        if stat.S_ISLNK(st.st_mode):
            aliases.append({'path':str(candidate),'literal_target':os.readlink(candidate)})
    physical=path.resolve(strict=True);before=physical.lstat()
    def stable(s):
        return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if not stat.S_ISREG(before.st_mode) or before.st_size>16*1024*1024:
        raise ValueError('bounded regular layout dependency required')
    fd=os.open(physical,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        if stable(os.fstat(fd))!=stable(before):raise ValueError('layout dependency open identity changed')
        h=hashlib.sha256();size=0
        while True:
            block=os.read(fd,65536)
            if not block:break
            size+=len(block)
            if size>16*1024*1024:raise ValueError('layout dependency grew past cap')
            h.update(block)
        if stable(os.fstat(fd))!=stable(before):raise ValueError('layout dependency changed during read')
    finally:os.close(fd)
    if stable(physical.lstat())!=stable(before) or path.resolve(strict=True)!=physical:
        raise ValueError('layout dependency replaced or redirected')
    if any(os.readlink(row['path'])!=row['literal_target'] for row in aliases):
        raise ValueError('layout dependency alias changed')
    return {'path':str(path),'physical':str(physical),'bytes':size,'sha256':h.hexdigest(),
            'aliases':aliases,'stable':stable(before)}


def layout_checks(inputs,manifest,expected,out,policy,remaining,rss_watchdog):
    selected=expected['layout_policy'];driver=Path(selected['driver']['path'])
    if sha(driver)!=selected['driver']['sha256']:
        raise ValueError('selected C layout driver changed')
    base=out/'layout';base.mkdir();results=[]
    for member in manifest['source_members']:
        source=inputs/member['view_path']
        if sha(source)!=member['view_sha256']:
            raise ValueError('complete original C/layout source differs')
        root=base/member['function'];root.mkdir()
        common=[str(driver),'--target='+selected['target'],'-resource-dir='+selected['resource_dir'],
                '-std=c11','-x','c','-MT','layout-object']
        phases=[];snapshots=None;dependencies=None
        for phase in ('dependencies','syntax'):
            directory=root/phase;directory.mkdir();(directory/'tmp').mkdir()
            depfile=directory/'headers.d'
            flags=['-M'] if phase=='dependencies' else ['-fsyntax-only','-MD']
            argv=[*common,*flags,'-MF',str(depfile),str(source)]
            timeout=min(selected['phase_seconds'],remaining())
            bounded_json(directory/'command.json',{'argv':argv,'cwd':str(directory),'input':pin(source),
                'phase':phase,'timeout_seconds':timeout,'compiler_only':True,'executes_generated_program':False},out,policy)
            env={**os.environ,'TMPDIR':str(directory/'tmp')}
            result=guarded_generation(argv,directory,env,policy,timeout,rss_watchdog,out)
            bounded_json(directory/'resources.json',result,out,policy);raw_bytes(out)
            if (result['exit_code']!=0 or result['timed_out'] or result['out_of_memory'] or result['output_limit']):
                raise ValueError('actual complete original C layout phase failed: '+member['function']+'/'+phase)
            current=layout_dependencies(depfile,source)
            if phase=='dependencies':
                dependencies=current;snapshots=[layout_pin(path) for path in dependencies]
                if sum(r['bytes'] for r in snapshots)>128*1024*1024:
                    raise ValueError('layout dependency aggregate cap exceeded')
            elif current!=dependencies or [layout_pin(path) for path in current]!=snapshots:
                raise ValueError('actual C syntax dependencies differ before/after use')
            phases.append({'phase':phase,'command':pin(directory/'command.json'),'resources':result,'dependency_file':pin(depfile)})
        if sha(driver)!=selected['driver']['sha256'] or sha(source)!=member['view_sha256']:
            raise ValueError('layout driver or complete source changed')
        row={'function':member['function'],'original':member['original_sha256'],'view':member['view_sha256'],
            'C_layout_assertions_passed':True,'source_contract_or_body_proven':False,'native_Cpp_ABI_claim':False,
            'phases':phases,'physical_dependencies':snapshots}
        bounded_json(root/'result.json',row,out,policy);results.append(row)
    if len(results)!=8:raise ValueError('all eight actual C layout source guards required')
    bounded_json(base/'result.json',{'checks':results,'compiler_only':True,'executes_generated_program':False,
        'scope':'Selected C model layout only; original ACSL comments are not proved by syntax acceptance. Actual source/Typed/padding/ownership/caller derivation remains pending. Declared physical dependencies checked immediately before/after syntax use; compiler/loader/between-check TCB retained.'},out,policy)
    return {'units':8,'result':pin(base/'result.json'),'C_layout_assertions_passed':True,'source_or_Typed_or_caller_admission':False}



def canonical_check(packets, expected, directory):
    manifest = packets.check(directory, elements=tuple(expected['elements']))
    physical = [{'path': str(p.relative_to(directory)), 'bytes': p.stat().st_size,
                 'sha256': sha(p)} for p in sorted(directory.rglob('*')) if p.is_file()]
    if manifest != expected['canonical_manifest'] or physical != expected['canonical_files']:
        raise ValueError('fresh complete owned-source-view canonical packet differs')
    rows = manifest['obligations']
    if len(rows) != 9 or [r['id'] for r in rows] != expected['target_ids'] or any(
            r['kind'] != 'check_lemma' or r['status'] != 'pending' or r['dependencies'] for r in rows):
        raise ValueError('all nine independent pending check lemmas are required')
    if manifest['source_typed_bridge_established'] is not False or \
            manifest['current_model_records_admitted'] or manifest['caller_premises_added']:
        raise ValueError('owned-source-view packet falsely broadens admission')
    return manifest


def normal_task_census(directory, target, inventory, output_root, policy):
    """Streaming metadata over retained tasks; independent term audit still required."""
    goals = inventory['goals']
    properties = inventory['properties']
    if inventory.get('complete') is not True or not goals or \
            len({g['goal'] for g in goals}) != len(goals) or \
            len({p['property'] for p in properties}) != len(properties):
        raise ValueError('native complete goal/property census missing or duplicated')
    by_property = {p['property']: p for p in properties}
    missing = sorted({d for p in properties for d in p['dependencies'] if d not in by_property})
    origins = sorted({p['origin'] for p in properties if p['origin'] is not None and p['origin'] not in by_property})
    lemmas = [p for p in properties if p.get('kind') == 'lemma']
    ordinary = [g for g in goals if not g['smoke']]
    if missing or origins or len(lemmas) != 1 or not ordinary or any(
            g['property'] != lemmas[0]['property'] for g in ordinary) or \
            not lemmas[0]['property'].endswith('_'+target['goal']) or \
            lemmas[0].get('dependencies') or lemmas[0].get('extern'):
        raise ValueError('sole source-owned independent check lemma or dependency closure differs')
    standard = json.loads((directory/'wp-goals.json').read_bytes())
    if len({g['goal'] for g in standard}) != len(standard) or \
            {g['goal'] for g in standard} != {g['goal'] for g in goals}:
        raise ValueError('complete native/standard goal census differs')
    peers = {g['goal']: g for g in standard}
    for g in goals:
        if any(g.get(k) != peers[g['goal']].get(k) for k in ('property','function','line','smoke','passed')):
            raise ValueError('native/standard goal binding differs: '+g['goal'])
    log_path = directory/'frama-c.log'
    exports = []
    current = None
    offset = line_number = 0
    marker = re.compile(rb'^\s*(?:\[wp(?::[^\]]+)?\]\s*)?EXPORT GOAL\s+(\S+)\s*$')
    declaration = re.compile(rb'^\s*(?:\[wp:print-generated\]\s*)?(use|clone|axiom|goal|constant|function|predicate|type|theory)\s+([^\s:(=]+)')
    with log_path.open('rb') as stream:
        for line in stream:
            line_number += 1
            match = marker.match(line)
            if match:
                if current is not None:
                    current.update(end_byte=offset, sha256=current.pop('_hash').hexdigest())
                    exports.append(current)
                ident = match.group(1).decode()
                owners = [g['goal'] for g in goals if g['goal'].endswith('_'+ident)]
                if len(owners) != 1:
                    raise ValueError('actual common export has no unique native owner: '+ident)
                current = {'export_id': ident, 'goal': owners[0], 'begin_byte': offset,
                           'begin_line': line_number, '_hash': hashlib.sha256(),
                           'declarations': [], 'theory_seen': False, 'goal_seen': False, 'end_seen': False}
            if current is not None:
                current['_hash'].update(line)
                parsed = declaration.match(line)
                if parsed:
                    kind, name = (part.decode(errors='replace') for part in parsed.groups())
                    current['declarations'].append({'kind': kind, 'name': name, 'line': line_number,
                                                   'line_sha256': hashlib.sha256(line).hexdigest()})
                    current['theory_seen'] |= kind == 'theory'
                    current['goal_seen'] |= kind == 'goal'
                current['end_seen'] |= bool(re.match(rb'^\s*end\s*$', line))
            offset += len(line)
    if current is not None:
        current.update(end_byte=offset, sha256=current.pop('_hash').hexdigest())
        exports.append(current)
    if any(not all(row[k] for k in ('theory_seen','goal_seen','end_seen')) for row in exports):
        raise ValueError('retained common task fragment is incomplete')
    exported = {row['goal'] for row in exports}
    inventory_only = [g for g in goals if g['goal'] not in exported]
    missing_tasks = [g['goal'] for g in inventory_only if not (
        g['results'] == ['valid'] and any(p['prover'] == 'qed' and p.get('success') == 1
                                       for p in peers[g['goal']].get('provers', [])))]
    census = {'target': target['id'], 'native_goal_count': len(goals),
              'native_property_count': len(properties), 'ordinary_count': len(ordinary),
              'smoke_count': sum(bool(g['smoke']) for g in goals), 'log': pin(log_path),
              'common_exports': exports, 'internal_qed_inventory_only': [g['goal'] for g in inventory_only],
              'missing_noninternal_tasks': missing_tasks,
              'extern_properties': [p['property'] for p in properties if p['extern']],
              'property_dependencies': [{'property': p['property'], 'variant': p['property_variant'],
                  'origin': p['origin'], 'dependencies': p['dependencies'], 'extern': p['extern']}
                  for p in properties],
              'scope': 'Complete actual census and declaration positions only. Original full log, prover files, native properties and CSV retained. Imported definitions/axioms/hypotheses require independent cold interpretation; no source/caller proof or automatic semantic acceptance.'}
    bounded_json(directory/'task-census.json', census, output_root, policy)
    if missing_tasks:
        raise ValueError('actual required common tasks missing; preserve partial census')
    return census


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if sha(args.expected) != EXPECTED_SHA256:
        raise ValueError('reviewed nine-duty source/layout expectation bytes differ')
    expected = json.loads(args.expected.read_bytes()); policy = expected['resource_policy']
    need(policy['root_headroom_bytes'] == 4194304 and policy['root_post_exit_reserve_bytes'] == 524288,
         'exact root sibling and post-exit metadata headroom required')
    project = args.project.resolve(); repo = project.parent; out = args.output.resolve()
    if str(project) != expected['remote_project'] or out.exists() or out.is_relative_to(repo):
        raise ValueError('exact immutable source and fresh external profile required')
    launch = linux_admission(expected, repo, out)
    out.mkdir(parents=True); os.chdir(project)
    started = time.monotonic(); deadline = started+policy['profile_seconds']
    result = {'created': '2026-10-16 ET', 'scope': expected['scope'],
              'source_commit': expected['source_commit'], 'producer_complete': False,
              'all_nine_producer_proven': False, 'proof_acceptance': False,
              'source_typed_bridge_established': False, 'caller_acceptance': False,
              'body_acceptance': False, 'public_proof_record_created': False,
              'universal_proof_setup_attested': False, 'independent_task_hypothesis_review_pending': True,
              'linux_launch': launch, 'source_receipts': [], 'runs': [],
              'unexecuted': list(expected['target_ids'])}
    def remaining():
        value = deadline-time.monotonic()
        if value <= 0:
            raise TimeoutError('whole standalone profile budget spent')
        return value
    def source_check():
        command = ['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
                   '-c', 'core.preloadIndex=false', '-c', 'core.fsmonitor=false',
                   '-c', 'index.threads=1', '-C', str(repo)]
        head = subprocess.check_output([*command, 'rev-parse', 'HEAD'], text=True, timeout=30).strip()
        dirty = subprocess.check_output([*command, 'status', '--porcelain', '--untracked-files=all'], text=True, timeout=30)
        if head != expected['source_commit'] or dirty:
            raise ValueError('selected source is not exact and clean')
        for row in expected['source_blobs']+expected['test_helper_pins']:
            if sha(project/row['relative']) != row['sha256']:
                raise ValueError('selected source input changed: '+row['relative'])
        closure = consumer_closure(project, repo, expected)
        path = out/('source-consumers-'+str(len(result['source_receipts']))+'.json')
        bounded_json(path, closure, out, policy); result['source_receipts'].append(pin(path))
    def runtime_check():
        selected = {}
        for name, row in expected['tools'].items():
            path = shutil.which(name)
            if path is None or Path(path).resolve() != Path(row['path']).resolve() or sha(path) != row['sha256']:
                raise ValueError('selected physical tool changed: '+name)
            selected[name] = pin(Path(path).resolve())
        for row in expected['wp_artifacts']:
            if sha(row['path']) != row['sha256']:
                raise ValueError('selected WP artifact changed')
        prefix = Path(expected['linux_prefix'])
        for key, root in [('why3_stdlib', prefix/'share/why3/stdlib'),
                          ('wp_why3_support', prefix/'share/frama-c/share/wp/why3'),
                          ('why3_drivers', prefix/'share/why3/drivers')]:
            surface(root, expected['portable_import_surfaces'][key])
        for row in expected['runtime_sources']:
            if sha(prefix/'lib/frama-c-wp/core'/row['name']) != row['sha256']:
                raise ValueError('selected runtime source changed: '+row['name'])
        if sha(expected['why3_config']['path']) != expected['why3_config']['sha256']:
            raise ValueError('selected Why3 configuration changed')
        selected['why3_packages'] = why3_runtime_check(expected)
        selected['why3_elf_candidates'] = why3_dependency_check(expected)
        return selected
    try:
        bounded_json(out/'root-siblings-before.json', root_sibling_census(out, policy), out, policy)
        source_check(); bounded_json(out/'runtime.json', runtime_check(), out, policy)
        ambient = sorted(k for k in os.environ if k.startswith(('FRAMAC_WP','WP_')) or k == 'SWDB_PROOF_REPORT_OUT')
        if ambient:
            raise ValueError('forbidden ambient WP selectors: '+','.join(ambient))
        shutil.copyfile(__file__, out/'entry.py'); shutil.copyfile(args.expected, out/'expected.json')
        os.environ.update(SWDB_FRAMA_C=expected['tools']['frama-c']['path'], SWDB_CBMC='none',
            SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'], WHY3CONFIG=expected['why3_config']['path'],
            SWDB_WHY3_CONFIG=expected['why3_config']['path'], PYTHONDONTWRITEBYTECODE='1',
            SWDB_FIXTURE_HOST='swdb-fixture-host', SWDB_VERIFIER_RSS_CAP_BYTES=str(policy['cap_bytes']))
        sys.dont_write_bytecode = True; sys.path[:0] = [str(project), str(project/'tests')]
        from swdb import vector_owned_source_view as packets
        from swdb import heap_model_view as engine, proof_setup, wp_adapter, c_lowering, stdlib_provenance, framac, method_version, rss_watchdog
        from swdb.library import Library
        inputs = out/'canonical-inputs'; manifest = packets.prepare(inputs, elements=tuple(expected['elements']))
        if manifest != canonical_check(packets, expected, inputs):
            raise ValueError('fresh public prepare/check results differ')
        bounded_json(out/'canonical-precheck.json', {'manifest': pin(inputs/'manifest.json'),
            'checker': packets.identity(), 'target_ids': expected['target_ids'],
            'canonical_files': expected['canonical_files'], 'old_proofs_imported': 0}, out, policy)
        compiler = stdlib_provenance.runtime_identity(c_lowering.locate()); lowering = c_lowering.identity()
        if {k: compiler[k] for k in expected['linux_clang_components']} != expected['linux_clang_components'] or \
                compiler != expected['linux_project_identity_derivation']['runtime'] or \
                lowering != expected['linux_project_identity_derivation']['predicted_identity']:
            raise ValueError('fresh source/context compiler composite differs')
        bounded_json(out/'compiler-runtime.json', {'runtime': compiler, 'identity': lowering}, out, policy)
        result['layout'] = {'executed': False, 'units': 0, 'C_layout_assertions_adopted': False,
                            'scope': 'Math-only namespace repair; previous V2 layout observations remain separate and require complete dependency cold closure.'}
        import yaml
        from swdb import std_models
        seed_root = out/'workspace'; seed_root.mkdir(exist_ok=False)
        records = seed_root/'records'; (records/'proofs').mkdir(parents=True)
        library = seed_root/'library'; methods = library/'methods'; methods.mkdir(parents=True)
        inherited = project/'tests/fixtures/proof/methods/contract-fixture-1.yaml'
        lineup_path = project/'library/methods/probata-draft-1.yaml'
        # Only ordinary fixture method metadata is copied. No test module,
        # test builder, catalog proof, contract or candidate is imported.
        method_data = yaml.safe_load(inherited.read_bytes())
        method_data['lineup'] = yaml.safe_load(lineup_path.read_bytes())['lineup']
        wp_rows = [row for row in method_data['lineup'] if row['tool']=='frama-c-wp']
        if len(wp_rows) != 1:
            raise ValueError('one normal source-pinned WP lineup required')
        wp_rows[0]['flags'] += ['-rte-initialized', '@all', '-wp-no-filter-init']
        method_data['c_lowering']['translators'] = [lowering['c_lowering']]
        method_data['models'].update(std_vector=std_models.identity(), std_pair=std_models.identity())
        method_data.update(id=expected['method_id'], sequence=3,
            description='Standalone conditional owned-header nine-duty native mathematical profile. No body/caller/model admission. '+json.dumps(expected['explicit_method_binding'], sort_keys=True))
        method_path = methods/'wp-owned-source9-v1.yaml'
        method_path.write_text(yaml.safe_dump(method_data, sort_keys=False))
        seed = SimpleNamespace(root=seed_root, records=records)
        method = method_version.select(seed.root/'library', expected['method_id'])
        adapter = wp_adapter.WpAdapter(Library(seed.root/'library'), 'standalone-owned-source-view', method, records=seed.records)
        tools = adapter._tools(); flags = engine.flags(tools)
        if tools['seconds'] != 30 or tools['provers'] != ['alt-ergo','z3','cvc5'] or \
                any(x.startswith(('-wp-prop','-wp-fct')) or x in {'-wp-gen','-wp-no-why3-detect'} for x in flags):
            raise ValueError('complete unchanged normal proof portfolio required')
        proof_setup._wp_flags(flags, out); proof_setup._lineup(method, adapter, tools, flags)
        bounded_json(out/'method.json', {'pin': method_version.pin(method), 'method': method_data,
            'inherited': pin(inherited), 'lineup_source': pin(lineup_path), 'flags': flags, 'tools': tools,
            'policy': 'Actual ordinary flag/lineup functions only; no universal setup certificate claimed.'}, out, policy)
        reader_dir = out/'reader'; reader_dir.mkdir()
        reader = proof_setup.compile_report_module(reader_dir, timeout=min(120, remaining()))
        foundation = engine.foundations(framac.locate().command, out/'foundation', deadline)
        bounded_json(out/'foundation.json', foundation, out, policy)
        for row in manifest['obligations']:
            remaining(); canonical_check(packets, expected, inputs); runtime_check()
            directory = out/('leaf-'+row['id']); directory.mkdir(); (directory/'tmp').mkdir()
            path = directory/'wp_input.c'; path.write_bytes((inputs/row['path']).read_bytes())
            invocation = engine.command(framac.locate().command, flags, inputs, reader)
            proof_setup._wp_flags(invocation, directory); proof_setup._lineup(method, adapter, tools, flags)
            if sha(path) != row['sha256'] or invocation != engine.command(framac.locate().command, engine.flags(tools), inputs, reader):
                raise ValueError('complete normal command or fresh input changed before launch')
            timeout = min(policy['leaf_timeout_seconds'], remaining())
            bounded_json(directory/'command.json', {'argv': invocation, 'cwd': str(directory),
                'timeout_seconds': timeout, 'input': pin(path), 'selected_id': row['id']}, out, policy)
            environment = {**os.environ, 'TMPDIR': str(directory/'tmp'),
                           'SWDB_PROOF_REPORT_OUT': str(directory/'wp-inventory.json')}
            ACTIVE_LEAF.update(directory=directory, target=row['id'], input_sha256=row['sha256'])
            try:
                resource_result = guarded_generation(invocation, directory, environment, policy, timeout, rss_watchdog, out)
            finally:
                ACTIVE_LEAF.clear()
            raw_bytes(out)  # strict after the guarded process tree has settled

            bounded_json(directory/'resources.json', resource_result, out, policy)
            if resource_result['out_of_memory'] or resource_result['timed_out'] or resource_result['output_limit']:
                raise ValueError('leaf resource boundary hit; preserve all partial artifacts')
            outcome = wp_adapter.read_outcome(SimpleNamespace(**resource_result),
                (directory/'frama-c.log').read_text(errors='replace'),
                directory/'wp-goals.json' if (directory/'wp-goals.json').exists() else None,
                directory/'wp-properties.csv' if (directory/'wp-properties.csv').exists() else None,
                inventory=directory/'wp-inventory.json' if (directory/'wp-inventory.json').exists() else None)
            bounded_json(directory/'outcome.json', outcome, out, policy)
            if not all((directory/name).is_file() for name in ('wp-goals.json','wp-properties.csv','wp-inventory.json','wp-normalized.c')):
                raise ValueError('actual complete native/ordinary/property/normalized reports absent')
            inventory = json.loads((directory/'wp-inventory.json').read_bytes())
            census = normal_task_census(directory, row, inventory, out, policy)
            result['runs'].append({'id': row['id'], 'cwd': str(directory), 'input': pin(path),
                'resources': resource_result, 'outcome': outcome, 'census': pin(directory/'task-census.json'),
                'ordinary_goals': census['ordinary_count'], 'smoke_goals': census['smoke_count']})
            result['unexecuted'].remove(row['id']); bounded_json(out/'result.json', result, out, policy)
        source_check(); runtime_check(); canonical_check(packets, expected, inputs)
        if list((seed.records/'proofs').glob('*.yaml')):
            raise ValueError('standalone profile unexpectedly created a public proof record')
        result.update(producer_complete=True, all_nine_producer_proven=all(r['outcome']['verdict']=='proven' for r in result['runs']),
            source_after_clean=True, raw_bytes=raw_bytes(out),
            classification='Nine fresh producer outcomes retained. Independent complete source/runtime/resource/task/hypothesis review required; no proof/source/Typed/body/caller/public-record acceptance.')
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
        result['primary_error'] = preserve_primary_error(out, exc, policy)
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        result['within_profile_budget'] = time.monotonic() < deadline-1
        if not result['within_profile_budget']:
            result['producer_complete'] = False
        # The result and manifest retain independent cold-review requirements.
        # Reserve is checked before each write and exact final size is checked
        # after fsync; profile completion also requires a strict settled walk.
        bounded_json(out/'result.json', result, out, policy, reserve=False)
        bounded_json(out/'root-siblings-after.json', root_sibling_census(out, policy), out, policy, reserve=False)
        bounded_json(out/'artifact-manifest.json', [{'relative': str(p.relative_to(out)), **pin(p)}
            for p in sorted(out.rglob('*')) if p.is_file() and p != out/'artifact-manifest.json'], out, policy, reserve=False)
        settled = raw_bytes(out)
        siblings = root_sibling_census(out, policy)
        if (settled > policy['output_budget_bytes']-policy['root_headroom_bytes']
                or settled+siblings['bytes']+policy['root_post_exit_reserve_bytes'] > policy['output_budget_bytes']
                or time.monotonic() >= deadline):
            raise ValueError('final settled raw budget or post-fsync profile deadline exceeded')
    return 0 if result['producer_complete'] and result['within_profile_budget'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

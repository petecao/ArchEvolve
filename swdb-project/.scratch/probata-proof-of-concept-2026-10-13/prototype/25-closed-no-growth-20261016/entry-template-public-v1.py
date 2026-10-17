"""2026-10-16 ET. Complete projected-C normal-WP observation, never caller admission.

Fresh original lowering/provenance and public closed-view checks precede the
unchanged normal portfolio. Every native/property/task row remains available.
The constructor dependency and source allocation/Typed/lifetime bridge stay open.
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

# __LINEAGE__

# __COMMON_EXPORTS__


def closed_census(directory, expected, output_root, policy):
    inventory = json.loads((directory/'wp-inventory.json').read_bytes())
    goals, properties = inventory['goals'], inventory['properties']
    standard = json.loads((directory/'wp-goals.json').read_bytes())
    native = {g['goal']: g for g in goals}
    peers = {g['goal']: g for g in standard}
    by_property = {p['property']: p for p in properties}
    root = expected['function']
    if inventory.get('complete') is not True or not goals or len(native) != len(goals) or \
            len(peers) != len(standard) or len(by_property) != len(properties) or set(native) != set(peers) or \
            any(g['function'] != root for g in standard):
        raise ValueError('complete unique original-root native/standard census differs')
    missing = sorted({d for p in properties for d in p['dependencies'] if d not in by_property})
    origins = sorted({p['origin'] for p in properties if p['origin'] is not None and p['origin'] not in by_property})
    if missing or origins or not any(not g['smoke'] for g in goals) or not any(g['smoke'] for g in goals):
        raise ValueError('complete ordinary/smoke/property origin/dependency closure differs')
    input_path = directory/'wp_input.c'
    lines = input_path.read_text().splitlines()
    calls = []
    for g in goals:
        if g['property'] not in by_property or any(g.get(k) != peers[g['goal']].get(k)
                for k in ('property','line','smoke','passed')):
            raise ValueError('native/standard goal property/result binding differs')
        if g['function'] == root:
            continue
        # Preserve Frama-C's actual callee owner. The sole surviving source call
        # is bound independently to the ordinary caller precondition and site.
        callee = 'std_vector_int_ctor_count_value'
        p = by_property[g['property']]
        match = re.fullmatch(re.escape(callee)+r'_wp_smoke_dead_call_s(\d+)', g['property'])
        contexts = [p for p in properties if isinstance(p.get('call_context'), dict) and
                    p['call_context']['caller'] == root and p['call_context']['callee'] == callee and p['line'] == g['line']]
        if g['function'] != callee or not g['smoke'] or match is None or \
                p['property_variant'] != 'IPOther' or p['property_export_origin'] != 'wp-smoke-reference' or \
                p['status_registered'] is not False or p['description'] != 'wp_smoke_dead_call' or \
                p['source_file'] != str(input_path) or p['extern'] or p['dependencies'] or p['origin'] is not None or \
                len(contexts) != 1 or contexts[0]['call_context']['statement_id'] != int(match.group(1)) or \
                contexts[0]['call_context']['source_file'] != str(input_path) or \
                lines[g['line']-1].strip() != expected['constructor_call']:
            raise ValueError('foreign goal lacks exact surviving constructor call/statement/source binding')
        ordinary = [n for n in goals if not n['smoke'] and n['property'] == contexts[0]['property'] and n['function'] == root]
        if len(ordinary) != 1:
            raise ValueError('surviving constructor call ordinary precondition is missing')
        calls.append({'native_callee_owner': g['function'], 'standard_caller_owner': peers[g['goal']]['function'],
                      'goal': g['goal'], 'property': g['property'], 'source_line': g['line'],
                      'statement_id': int(match.group(1)), 'ordinary_precondition_goal': ordinary[0]['goal']})
    if len(calls) != 1:
        raise ValueError('exactly one surviving constructor call smoke is required')
    # Reuse the reviewed streaming export observer after the source-root census.
    # Its mathematical ownership preamble is deliberately not reused here.
    exports = common_exports(directory, goals, peers)
    census = {'native_goals': len(goals), 'native_properties': len(properties),
              'ordinary_count': sum(not g['smoke'] for g in goals), 'smoke_count': sum(bool(g['smoke']) for g in goals),
              'call_bindings': calls, 'common_exports': exports['common_exports'],
              'internal_qed_inventory_only': exports['internal_qed_inventory_only'],
              'missing_noninternal_tasks': exports['missing_noninternal_tasks'],
              'log': pin(directory/'frama-c.log'),
              'extern_properties': [p for p in properties if p['extern']],
              'property_dependencies': [{'property': p['property'], 'variant': p['property_variant'],
                  'origin': p['origin'], 'dependencies': p['dependencies'], 'extern': p['extern']} for p in properties],
              'scope': 'All actual rows retained without owner rewriting/filtering. Common declarations are an index, not a semantic hypothesis audit. Original constructor summaries and allocator TCB are explicit hypotheses; complete cold interpretation and source bridge remain pending.'}
    bounded_json(directory/'task-census.json', census, output_root, policy)
    if census['missing_noninternal_tasks']:
        raise ValueError('noninternal native obligations have no retained common task')
    return census


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('expected','project','output'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    if sha(args.expected) != EXPECTED_SHA256:
        raise ValueError('reviewed projected-C expectation differs')
    expected = json.loads(args.expected.read_bytes()); policy = expected['resource_policy']
    project = args.project.resolve(); repo = project.parent; out = args.output.resolve()
    if str(project) != expected['remote_project'] or out.exists() or out.is_relative_to(repo):
        raise ValueError('exact immutable source and fresh external diagnostic required')
    launch = linux_admission(expected, repo, out)
    out.mkdir(parents=True); os.chdir(project)
    started = time.monotonic(); deadline = started+policy['profile_seconds']
    result = {'created':'2026-10-16 ET', 'scope':expected['scope'], 'source_commit':expected['source_commit'],
              'producer_complete':False, 'projected_c_producer_verdict':None, 'proof_acceptance':False,
              'source_typed_bridge_established':False, 'caller_acceptance':False, 'body_acceptance':False,
              'public_proof_record_created':False, 'universal_proof_setup_attested':False,
              'independent_task_hypothesis_review_pending':True, 'linux_launch':launch, 'source_receipts':[]}
    def remaining():
        left = deadline-time.monotonic()
        if left <= 0:
            raise TimeoutError('whole projected-C profile budget spent')
        return left
    def source_check():
        prefix = ['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.preloadIndex=false',
                  '-c','core.fsmonitor=false','-c','index.threads=1','-C',str(repo)]
        head = subprocess.check_output([*prefix,'rev-parse','HEAD'],text=True,timeout=min(30,remaining())).strip()
        dirty = subprocess.check_output([*prefix,'status','--porcelain','--untracked-files=all'],text=True,timeout=min(30,remaining()))
        if head != expected['source_commit'] or dirty:
            raise ValueError('selected source is not exact and clean')
        for row in expected['source_blobs']+expected['test_helper_pins']:
            if (project/row['relative']).is_symlink() or sha(project/row['relative']) != row['sha256']:
                raise ValueError('source input changed: '+row['relative'])
        closure = consumer_closure(project,repo,expected)
        path = out/('source-consumers-'+str(len(result['source_receipts']))+'.json')
        bounded_json(path,closure,out,policy); result['source_receipts'].append(pin(path))
    def runtime_check():
        selected = {}
        for name,row in expected['tools'].items():
            path = shutil.which(name)
            if path is None or Path(path).resolve() != Path(row['path']).resolve() or sha(path) != row['sha256']:
                raise ValueError('physical tool changed: '+name)
            selected[name] = pin(Path(path).resolve())
        prefix = Path(expected['linux_prefix'])
        for row in expected['wp_artifacts']:
            if sha(row['path']) != row['sha256']:
                raise ValueError('selected WP artifact changed')
        for key,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
            surface(root,expected['portable_import_surfaces'][key])
        for row in expected['runtime_sources']:
            if sha(prefix/'lib/frama-c-wp/core'/row['name']) != row['sha256']:
                raise ValueError('selected runtime source changed: '+row['name'])
        if sha(expected['why3_config']['path']) != expected['why3_config']['sha256']:
            raise ValueError('selected Why3 config changed')
        return selected
    try:
        source_check(); bounded_json(out/'runtime.json',runtime_check(),out,policy)
        if any(k.startswith(('FRAMAC_WP','WP_')) or k == 'SWDB_PROOF_REPORT_OUT' for k in os.environ):
            raise ValueError('ambient WP override present')
        shutil.copyfile(__file__,out/'entry.py'); shutil.copyfile(args.expected,out/'expected.json')
        os.environ.update(SWDB_FRAMA_C=expected['tools']['frama-c']['path'],SWDB_CBMC='none',
            SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'],WHY3CONFIG=expected['why3_config']['path'],
            SWDB_WHY3_CONFIG=expected['why3_config']['path'],PYTHONDONTWRITEBYTECODE='1',
            SWDB_FIXTURE_HOST='swdb-fixture-host',SWDB_VERIFIER_RSS_CAP_BYTES=str(policy['cap_bytes']))
        sys.dont_write_bytecode=True; sys.path[:0]=[str(project),str(project/'tests')]
        from swdb import c_lowering,stdlib_provenance,hint_check,vector_reallocation_closed_view as closed
        from swdb import heap_model_view as engine,proof_setup,wp_adapter,framac,method_version,rss_watchdog,std_models
        from swdb.library import Library
        source=project/expected['source_relative']
        if sha(source) != expected['source_sha256']:
            raise ValueError('original source differs')
        compiler=stdlib_provenance.runtime_identity(c_lowering.locate()); lowering=c_lowering.identity()
        if compiler != expected['linux_project_identity_derivation']['runtime'] or lowering != expected['linux_project_identity_derivation']['predicted_identity']:
            raise ValueError('fresh compiler/source/context composite differs')
        bounded_json(out/'compiler-runtime.json',{'runtime':compiler,'identity':lowering},out,policy)
        original=c_lowering.lower(source,expected['function'])
        if original.sha256 != expected['lowered_sha256'] or lineage(json.loads(original.anchors_json)) != expected['cached_anchor_lineage']:
            raise ValueError('fresh original lowering/source/event lineage differs')
        problem=stdlib_provenance.check(original.stdlib_provenance,c_lowering.locate(),source,
            models=tuple(sorted(set((*original.models,*original.std_models)))),substitutions=original.stdlib_substitutions)
        if problem:
            raise ValueError('fresh original-TU provenance differs: '+problem)
        view=closed.prepare(original,source,expected['contract_clauses'])
        closed.check(original,source,view,expected['contract_clauses'])
        if hashlib.sha256(view.text.encode()).hexdigest() != expected['projected_sha256'] or \
                view.certificate['source_typed_bridge_established'] is not False or view.certificate['current_proof_records_admitted'] or \
                view.certificate['caller_premises_added'] or tuple(view.models) != ('swdb_alloc_int','std_vector_int_ctor_count_value'):
            raise ValueError('fresh public source projection changed or broadened admission')
        block='/*@ '+'\n    '.join(expected['contract_clauses'])+' */'
        merged=hint_check.wp_base(view.text,original.anchors,{expected['function']+'.contract':[block]})
        if hashlib.sha256(merged.encode()).hexdigest() != expected['wp_input_sha256']:
            raise ValueError('unchanged original three-clause contract insertion differs')
        for name,data in [('original.cc',source.read_bytes()),('lowering.original.c',original.text.encode()),('anchors.fresh.json',original.anchors_json.encode()),('projected.c',view.text.encode())]:
            bounded_bytes(out/name,data,out,policy)
        bounded_json(out/'closed-view-certificate.json',view.certificate,out,policy)
        from test_standard_member_contracts import _member_seed
        seed=initialize_workspace(out,_member_seed)
        import yaml
        inherited=seed.root/'library/methods/wp-tracer-fixture.yaml'; method_data=yaml.safe_load(inherited.read_bytes())
        if method_data['c_lowering']['translators'] != [lowering['c_lowering']]:
            raise ValueError('unchanged seed compiler context differs')
        method_data.update(id=expected['method_id'],sequence=3,description=expected['scope'])
        (seed.root/'library/methods/wp-closed-no-growth-v1.yaml').write_text(yaml.safe_dump(method_data,sort_keys=False))
        method=method_version.select(seed.root/'library',expected['method_id'])
        adapter=wp_adapter.WpAdapter(Library(seed.root/'library'),'standalone-closed-no-growth',method,records=seed.records)
        tools=adapter._tools(); flags=engine.flags(tools)
        if tools['seconds'] != 30 or tools['provers'] != ['alt-ergo','z3','cvc5'] or any(x.startswith(('-wp-prop','-wp-fct')) or x in {'-wp-gen','-wp-no-why3-detect'} for x in flags):
            raise ValueError('normal complete proof portfolio differs')
        proof_setup._wp_flags(flags,out); proof_setup._lineup(method,adapter,tools,flags)
        bounded_json(out/'method.json',{'pin':method_version.pin(method),'method':method_data,'inherited':pin(inherited),'flags':flags,'tools':tools},out,policy)
        reader_dir=out/'reader';reader_dir.mkdir();reader=proof_setup.compile_report_module(reader_dir,timeout=min(120,remaining()))
        bounded_json(out/'foundation.json',engine.foundations(framac.locate().command,out/'foundation',deadline),out,policy)
        directory=out/'projected-c';directory.mkdir();(directory/'tmp').mkdir()
        bounded_bytes(directory/'wp_input.c',merged.encode(),out,policy)
        command=[*framac.locate().command,'-machdep','x86_64','wp_input.c','-print','-ocode','wp-normalized.c','-then',
                 *flags,'-wp-fct',expected['function'],'-wp-report-json','wp-goals.json','-then','-load-module',str(reader),
                 '-report','-report-untried','-report-csv','wp-properties.csv']
        proof_setup._wp_flags(command,directory);proof_setup._lineup(method,adapter,tools,flags)
        runtime_check();remaining();closed.check(original,source,view,expected['contract_clauses'])
        timeout=min(policy['leaf_timeout_seconds'],remaining())
        bounded_json(directory/'command.json',{'argv':command,'cwd':str(directory),'timeout_seconds':timeout,'input':pin(directory/'wp_input.c')},out,policy)
        environment={**os.environ,'TMPDIR':str(directory/'tmp'),'SWDB_PROOF_REPORT_OUT':str(directory/'wp-inventory.json')}
        observed=guarded_generation(command,directory,environment,policy,timeout,rss_watchdog,out)
        bounded_json(directory/'resources.json',observed,out,policy);result['resources']=observed
        if observed['out_of_memory'] or observed['timed_out'] or observed['output_limit']:
            raise ValueError('native resource boundary hit; preserve all partial evidence')
        if any(not (directory/name).is_file() for name in ('wp-goals.json','wp-properties.csv','wp-inventory.json','wp-normalized.c')):
            raise ValueError('complete native/ordinary/property/normalized reports absent')
        # Existing primitive allocator/free TCB only. The constructor body is
        # deliberately not an admitted extern/body dependency in this diagnostic.
        allocator={name:{'id':name,'sha256':hashlib.sha256(text.encode()).hexdigest()} for name,text in std_models.allocator('int')}
        bounded_json(out/'unproved-dependencies.json',{'allocator_library_TCB':allocator,'constructor_model':{'name':'std_vector_int_ctor_count_value','sha256':hashlib.sha256(std_models.model_text('std_vector_int_ctor_count_value').encode()).hexdigest(),'current_body_record_admitted':False},'source_allocation_typed_lifetime_bridge_established':False},out,policy)
        outcome=wp_adapter.read_outcome(SimpleNamespace(**observed),(directory/'frama-c.log').read_text(errors='replace'),directory/'wp-goals.json',directory/'wp-properties.csv',inventory=directory/'wp-inventory.json',extern_contracts=allocator)
        bounded_json(directory/'outcome.json',outcome,out,policy)
        census=closed_census(directory,expected,out,policy)
        result.update(projected_c_producer_verdict=outcome['verdict'],census=pin(directory/'task-census.json'),ordinary_goals=census['ordinary_count'],smoke_goals=census['smoke_count'])
        source_check();runtime_check();closed.check(original,source,view,expected['contract_clauses'])
        if list((seed.records/'proofs').glob('*.yaml')) or sha(directory/'wp_input.c') != expected['wp_input_sha256']:
            raise ValueError('diagnostic created a public record or changed frozen input')
        result.update(producer_complete=True,source_after_clean=True,raw_bytes=raw_bytes(out),classification='Complete projected-C diagnostic only. No constructor body dependency, source allocation/Typed/lifetime bridge, original source/caller acceptance or public proof record.')
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(elapsed_seconds=time.monotonic()-started,within_profile_budget=time.monotonic()<=deadline)
        bounded_json(out/'result.json',result,out,policy,reserve=False)
        bounded_json(out/'artifact-manifest.json',[{'relative':str(p.relative_to(out)),**pin(p)} for p in sorted(out.rglob('*')) if p.is_file() and p != out/'artifact-manifest.json'],out,policy,reserve=False)
    return 0 if result['producer_complete'] and result['within_profile_budget'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

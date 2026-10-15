#!/usr/bin/env python3
"""Exact-source original ticket24 matrix; created 2026-10-15 ET.

Run serially inside the owner's verified socket_lane.sh lease. All raw output,
proof records and candidates remain in --output, outside the checkout. Each
swdb prove retains its normal shared verifier lock, 8 GiB RSS cap and all goals.
This runner uses the existing public candidate/prove test builders unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(REPO/'tests')]
from swdb import c_lowering, framac  # noqa: E402
from test_wp_subset import (Seed, build_subset_seed, GROUPS, MODELS, SUMMARIES,
                            TERMINAL_CONTROLS, summary_id)  # noqa: E402
from conftest import run_swdb  # noqa: E402


class MatrixSeed(Seed):
    """Keep long original goal inventories within an explicit outer command budget."""

    def __init__(self, root, candidates, public_timeout_seconds):
        super().__init__(root, candidates)
        self.public_timeout_seconds = public_timeout_seconds

    def swdb(self, command, *args):
        return run_swdb(command, '--records', self.records, *args,
                        timeout=self.public_timeout_seconds)


def git(*words):
    return subprocess.check_output(['git', *words], cwd=REPO, text=True).strip()


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def audit(record, expected, *, actual=True, ordinary_open=None):
    goals = record.get('goals', [])
    errors = []
    if record.get('verdict') != expected:
        errors.append('unexpected verdict')
    ordinary = [g for g in goals if not g.get('smoke')]
    smoke = [g for g in goals if g.get('smoke')]
    settings = record.get('settings',{})
    flags = settings.get('flags',[])
    if actual:
        if settings.get('verifier_launched') is not True or record.get('proof_setup_check',{}).get('verdict') != 'passed':
            errors.append('actual verification/setup did not run')
        required = ['-wp-rte','-wp-no-filter-init','-wp-smoke-tests']
        if any(flag not in flags for flag in required):
            errors.append('mandatory RTE/init/smoke flags absent')
        for flag,value in [('-rte-initialized','@all'),('-wp-cache','none'),('-machdep','x86_64')]:
            if not any(f==flag and flags[i+1:i+2]==[value] for i,f in enumerate(flags)):
                errors.append('mandatory flag differs: '+flag)
        if not ordinary or not smoke:
            errors.append('actual ordinary/smoke goal inventory is empty')
        if expected == 'not_proven':
            if record.get('failure_class') not in {'timeout','unknown','solver_error','vacuous_pass'}:
                errors.append('seeded negative failed before semantic verification')
            open_goals = [g for g in ordinary if g['status'] != 'valid']
            expected_goals = (ordinary_open,) if isinstance(ordinary_open,str) else tuple(ordinary_open or ())
            if not open_goals or expected_goals and not any(
                    token in g.get('goal','') for g in open_goals for token in expected_goals):
                errors.append('seeded negative lacks its attributable ordinary open obligation')
    elif (record.get('failure_class') != 'unsupported_construct' or settings.get('verifier_launched') or goals):
        errors.append('deliberate lifetime refusal unexpectedly ran or changed failure class')
    if expected == 'proven':
        if not goals or not any(g.get('smoke') for g in goals) or any(g['status'] != 'valid' for g in goals):
            errors.append('safe proof lacks all-goal/smoke Valid acceptance')
        if record.get('proof_setup_check',{}).get('verdict') != 'passed':
            errors.append('safe setup did not pass')
    reports = record.get('evidence',{}).get('reports',[])
    if actual and not {'wp_goals','wp_properties','wp_inventory','wp_normalized'}.issubset({r['name'] for r in reports}):
        errors.append('actual WP reports are incomplete')
    files = []
    for report in reports:
        path = Path(report['path'])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != report['sha256']:
            errors.append('report hash differs: '+str(path))
        files.append({'name':report['name'],'path':str(path),'sha256':digest})
    return {'id':record['id'],'verdict':record['verdict'],'failure_class':record.get('failure_class'),
            'ordinary_valid':sum(not g.get('smoke') and g['status']=='valid' for g in goals),
            'ordinary_open':[g for g in goals if not g.get('smoke') and g['status']!='valid'],
            'smoke_valid':sum(bool(g.get('smoke')) and g['status']=='valid' for g in goals),
            'smoke_open':[g for g in goals if g.get('smoke') and g['status']!='valid'],
            'initialization_goals':sum('rte_initialization' in g.get('goal','') for g in goals),
            'pins':record.get('pins',{}),'assumptions':record.get('assumptions',[]),
            'settings':record.get('settings',{}),'reports':files,'errors':errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--groups', default='templates,classes,new_array,omp,floats,std_models,atomics,dxc_summary,maa_summary')
    parser.add_argument('--stop-on-failure', action='store_true')
    parser.add_argument('--public-timeout-seconds', type=int, default=1800,
                        help='outer public-command budget; per-goal solver limits remain unchanged')
    args = parser.parse_args()
    if not 600 <= args.public_timeout_seconds <= 7200:
        parser.error('--public-timeout-seconds must be between 600 and 7200')
    commit = git('rev-parse','HEAD')
    if commit != args.expected_commit:
        parser.error('source HEAD differs from --expected-commit')
    if git('status','--porcelain','--untracked-files=no'):
        parser.error('tracked source is dirty')
    output = args.output.resolve()
    if output == REPO or REPO in output.parents or output.exists():
        parser.error('--output must be a fresh directory outside the checkout')
    missing = [c_lowering.locate().missing, framac.locate().missing]
    if any(missing):
        parser.error('required compiler/verifier unavailable: '+repr(missing))
    groups = args.groups.split(',')
    if not groups or set(groups)-set(GROUPS):
        parser.error('unknown group selection')
    output.mkdir(parents=True)
    os.environ['SWDB_VERIFIER_RSS_CAP_BYTES'] = '8589934592'
    # Test fixtures always use their fixture host; the outer wrapper alone owns
    # physical socket confinement and records the live lab-host preflight.
    from swdb import host_identity
    os.environ[host_identity.FIXTURE_HOST_ENV] = 'swdb-fixture-host'
    manifest = {'created':'2026-10-15 ET','commit':commit,'groups':groups,'workers':1,
                'rss_cap_bytes':8589934592,'public_timeout_seconds':args.public_timeout_seconds,
                'output':str(output),'sources':{}}
    for name in git('ls-files','swdb','tests','library','schemas').splitlines():
        path = REPO/name
        if path.is_file():
            manifest['sources'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    dump(output/'source-manifest.json',manifest)
    result = {'commit':commit,'rows':[],'phase':'building_original_candidate_seed','complete':False,'success':False}
    dump(output/'matrix.json',result)
    print('START original candidate seed (public submission/validation)',flush=True)
    seed_started = time.monotonic()
    seed_path = output/'seed'
    seed_path.mkdir()
    seed = MatrixSeed(seed_path,build_subset_seed(seed_path),args.public_timeout_seconds)
    dump(output/'candidates.json',seed.candidates)
    result['seed_wall_seconds'] = time.monotonic()-seed_started
    result['phase'] = 'actual_proof_matrix'
    dump(output/'matrix.json',result)
    print('PASS original candidate seed '+str(round(result['seed_wall_seconds'],2))+'s',flush=True)
    models, summaries = {}, {}
    def run(label, action, expected, validate=None, *, actual=True, ordinary_open=None):
        started = time.monotonic()
        print('START '+label, flush=True)
        row = {'label':label,'expected':expected}
        try:
            record = action()
            row.update(audit(record,expected,actual=actual,ordinary_open=ordinary_open))
            path = seed.records/'proofs'/(record['id']+'.yaml')
            row['record'] = {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            if validate:
                validate(record)
        except Exception:
            row['errors'] = [traceback.format_exc()]
        row['wall_seconds'] = time.monotonic()-started
        result['rows'].append(row)
        dump(output/'matrix.json',result)
        print(('FAIL ' if row.get('errors') else 'PASS ')+label+' '+str(round(row['wall_seconds'],2))+'s',flush=True)
        if row.get('errors') and args.stop_on_failure:
            raise RuntimeError(label+' failed; see matrix.json')
        return row
    for group in groups:
        for name in MODELS.get(group,[]):
            if name not in models:
                models[name] = run('model:'+name,lambda n=name:seed.prove('--model',n),'proven')
        entries = {'dxc_summary':['dxc_tile_size'],'maa_summary':['maa_const','maa_indirect_load']}.get(group,[])
        for name in entries:
            if name not in summaries:
                summaries[name] = run('summary:'+name,lambda n=name:seed.prove('--summary',summary_id(n)),'proven')
        def validate(record):
            pinned = {p['id']:p for p in record['pins'].get('models',[])}
            assert set(pinned)==set(MODELS.get(group,[])),('model closure',group,pinned)
            for name,pin in pinned.items():
                assert pin['proof_record']==models[name]['id'] and pin['sha256']==models[name]['pins']['code']['sha256']
            pinned = {p['id']:p for p in record['pins'].get('summaries',[])}
            assert set(pinned)=={summary_id(n) for n in entries},('summary closure',group,pinned)
            for name in entries:
                assert pinned[summary_id(name)]['proof_record']==summaries[name]['id']
        run(group+':safe',lambda g=group:seed.unit(g),'proven',validate)
        goal = {'classes':'loop_invariant','templates':'ensures','new_array':'rte_mem_access',
                # The unchanged original hints can carry the postcondition even
                # when the seed falsifies invariant establishment. Keep that
                # failed invariant as attributable negative evidence.
                'omp':('loop_invariant','ensures'),'floats':('loop_invariant','ensures'),
                'std_models':'ensures','atomics':'ensures',
                'dxc_summary':'ensures','maa_summary':'ensures'}[group]
        run(group+':seeded',lambda g=group:seed.unit(g,candidate='bug'),'not_proven',ordinary_open=goal)
        if group=='new_array':
            for negative in ['new_out_of_range','new_after_delete',*[f'new_{n}' for n in TERMINAL_CONTROLS]]:
                run(negative,lambda n=negative:seed.unit(n),'not_proven',actual=negative=='new_out_of_range',
                    ordinary_open='rte_mem_access' if negative=='new_out_of_range' else None)
    result['complete'] = True
    result['phase'] = 'finished'
    result['success'] = all(not row.get('errors') for row in result['rows'])
    dump(output/'matrix.json',result)
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

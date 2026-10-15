#!/usr/bin/env python3
"""Finite original C++/ordinary-C comparisons; created 2026-10-15 ET.

Ticket22's native differential subcheck, without its bounded proof job. Domain
and contract harness are reused; the full original TU replaces the C++ cutter
because synthesized C member names do not exist in the original C++ AST.
No verifier, proof record, WP checking view or summary stub is used.
"""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import shlex
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import sys
import time
import traceback

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(REPO/'tests')]
from swdb import c_lowering, cbmc_adapter as cb, cbmc_translator as tr  # noqa: E402
from test_wp_subset import GROUPS, GROUP_FILES, SEEDED_BUGS, summary_id  # noqa: E402

FIXTURES = REPO/'tests/fixtures/proof/lowering'
NAMES = ('classes','templates','new_array','std_models','omp','atomics','floats','dxc_summary','maa_summary')
# Finite native extents, not minimum symbolic proof bounds. Original size
# preconditions are unchanged; all their legal sizes are available to draw.
SIZES = {'classes':{'n':4}, 'new_array':{'n':100}, 'std_models':{'n':4},
         'omp':{'n':100}, 'floats':{'n':4}}
CAPACITY = {'classes':4, 'new_array':0, 'std_models':4, 'omp':100,
            'atomics':1, 'floats':4, 'maa_summary':1}
FLAGS = ['-DSWDB_NATIVE','-DSWDB_DIFFERENTIAL','-O0','-fwrapv','-w',
         '-fsanitize=address,undefined','-fno-sanitize-recover=all']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


def pin(path):
    return {'path':str(path.resolve()), 'sha256':sha(path.read_bytes())}


def git(*args):
    return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()


def audit(path):
    """Recheck every retained file reference, including source and tools."""
    refs = []
    def visit(value):
        if isinstance(value,dict):
            if {'path','sha256'} <= value.keys():
                refs.append(value)
            for item in value.values():
                visit(item)
        elif isinstance(value,list):
            for item in value:
                visit(item)
    visit(json.loads(path.read_text()))
    errors = []
    for ref in refs:
        file = Path(ref['path'])
        if not file.is_file() or sha(file.read_bytes()) != ref['sha256']:
            errors.append('artifact hash differs: '+str(file))
    return errors, len(refs)


def known_undefined(group, case, values):
    """Source-specific exclusions; never additional contract assumptions.

    The pinned shared seed binds these classifications. Inputs remain present
    in domain.txt; ASan alone cannot diagnose invalid pointer formation.
    """
    if case != 'seeded':
        return None
    n = values.get('n')
    if group == 'new_array' and n is not None and 1 <= n <= 100 and -100 <= values['k'] <= 100:
        return 'original seeded i<=n writes buf[n] outside new int[n]'
    if group == 'std_models' and n == 0 and -1000 <= values['x'] <= 1000 and -1000 <= values['y'] <= 1000:
        return 'original seeded std::copy forms a-1 outside its array object'
    if group == 'maa_summary' and n == 2147483647:
        return 'original seeded n+1 overflows signed int (excluded despite -fwrapv)'
    return None


def execute(binary, lines, directory, side):
    """Ticket22 restart scheme, retaining both ASan and UBSan diagnostics.

    The common harness flushes completed rows. A sanitizer abort excludes its
    current input, then resumes at the next. The outer caller supplies RSS/wall
    guarding. No successful row is inferred from a sanitizer failure.
    """
    rows, undefined, diagnostics, segments, start = [], set(), [], [], 0
    env = {**os.environ,'ASAN_OPTIONS':'detect_leaks=0:abort_on_error=0:symbolize=0',
           'UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=0'}
    while start < len(lines):
        done = subprocess.run([str(binary)],input=''.join(' '.join(map(str,line))+'\n' for line in lines[start:]),
                              capture_output=True,text=True,timeout=600,env=env)
        stdout = directory/f'{side}-segment-{start}.out'
        stderr = directory/f'{side}-segment-{start}.err'
        stdout.write_text(done.stdout); stderr.write_text(done.stderr)
        segments.append({'stdout':pin(stdout),'stderr':pin(stderr),'exit_code':done.returncode})
        complete = [line for line in done.stdout.splitlines() if re.search(r' end=\S+$',line)]
        if any(not re.match(rf'^run {k}:',line) for k,line in enumerate(complete)):
            raise RuntimeError('native output has missing, duplicated or reordered row indexes')
        rows.extend(re.sub(r'^run \d+:',f'run {start+k}:',row) for k,row in enumerate(complete))
        if done.returncode == 0 and len(complete) == len(lines)-start:
            break
        if not any(token in done.stderr for token in ('AddressSanitizer','UndefinedBehaviorSanitizer','runtime error:')):
            raise RuntimeError(f'{side} native process exited {done.returncode}: '+done.stderr[-1000:])
        index = start+len(complete)
        if index >= len(lines):
            raise RuntimeError('sanitizer report after all rows completed')
        rows.append(f'run {index}: sanitizer')
        undefined.add(index)
        diagnostic = directory/f'{side}-sanitizer-{index}.txt'
        diagnostic.write_text(done.stderr)
        diagnostics.append(pin(diagnostic))
        start = index+1
    return rows, undefined, diagnostics, segments


def original_clauses(group, interface):
    original = [{'id':name,'role':role,'acsl':{'text':text}} for name,role,text in GROUPS[group][1]]
    normalized = json.loads(json.dumps(original))
    # The shared parser supports p[0], not unary *p. These are the same lvalue
    # for its initialized, separate, positive-capacity interface buffers.
    for row in normalized:
        for name,_ctype,pointer in interface.parameters:
            if pointer:
                row['acsl']['text'] = re.sub(r'\*\s*'+re.escape(name)+r'\b',name+'[0]',row['acsl']['text'])
    return original,normalized


def compare(group, case, source, output, fault):
    directory = output/(group+'-'+case)
    directory.mkdir()
    function = GROUPS[group][0]
    summaries = {'__dxc_tile_size':summary_id('dxc_tile_size'), 'maa_const_i32':summary_id('maa_const'),
                 'maa_indirect_load_i32':summary_id('maa_indirect_load')}
    lowering = c_lowering.lower(source,function,summaries=summaries)
    code = cb.Code(lowering,source,())
    if fault:
        for old,new in fault.get('replace',[]):
            if code.text.count(old) != 1:
                raise RuntimeError('fault must match exactly one lowering occurrence: '+old)
            code.text = code.text.replace(old,new,1)
    interface = code.interface(function)
    original,normalized = original_clauses(group,interface)
    contract = directory/'contract.json'; dump(contract,{'original':original,'native_normalized':normalized})
    harness,plan = tr.harness(interface,tr.clauses('fixture.'+group,normalized),
                              sizes=SIZES.get(group,{}),cap=CAPACITY.get(group,0))
    harness_file = directory/'harness.c'; harness_file.write_text(harness)
    lines,sampled,domain = cb._domain(plan)
    domain_file = directory/'domain.txt'
    domain_file.write_text(''.join(' '.join(map(str,line))+'\n' for line in lines))
    excluded = {k:why for k,line in enumerate(lines)
                if (why:=known_undefined(group,case,dict(zip((d['name'] for d in plan.draws),line))))}
    active = [k for k in range(len(lines)) if k not in excluded]
    feed = [lines[k] for k in active]
    impls = (FIXTURES/'summary_impls.cc').read_text() if group in {'dxc_summary','maa_summary'} else ''
    texts = {'c':tr.prelude()+code.c_text()+impls+harness,
             'cxx':tr.prelude()+source.read_text()+harness}
    row = {'group':group,'case':case,'function':function,'source':{},'contract':pin(contract),
           'harness':pin(harness_file),'bounds':{'threads':1,**SIZES.get(group,{})},
           'physical_array_capacity':CAPACITY.get(group,0),
           'domain':{'artifact':pin(domain_file),'requested_runs':len(lines),'sampled':sampled,
                     'sampling_seed':22 if sampled else None,'choices':domain,'draws':plan.draws},
           'known_undefined_exclusions':{'runs':len(excluded),'indexes':list(excluded),
                                         'reasons':sorted(set(excluded.values()))},
           'outputs':{},'compiles':{},'sanitizer_diagnostics':[], 'formal_verifier_launched':False}
    observed,ub = {},{}
    clang = c_lowering.locate()
    for side in ('c','cxx'):
        path = directory/('unit.c' if side=='c' else 'unit.cc'); path.write_text(texts[side])
        row['source'][side] = pin(path)
        binary = directory/side
        compiler = clang.command[0].replace('clang++','clang') if side=='c' else clang.command[0]
        dependency_file = directory/(side+'.d')
        command = [compiler,'-MD','-MF',str(dependency_file),'-Wl,-t','-x','c' if side=='c' else 'c++','-std=gnu11' if side=='c' else '-std=gnu++17',
                   *FLAGS,str(path),'-o',str(binary)]
        done = subprocess.run(command,capture_output=True,text=True,timeout=300)
        log = directory/(side+'-compile.txt'); log.write_text(done.stdout+done.stderr)
        row['compiles'][side] = {'command':command,'log':pin(log),'exit_code':done.returncode}
        if done.returncode:
            raise RuntimeError(f'{side} compilation failed: '+done.stderr[-1500:])
        dependencies = shlex.split(dependency_file.read_text().replace('\\\n','').split(':',1)[1])
        row['compiles'][side]['headers'] = [pin(Path(name)) for name in sorted(set(dependencies))]
        row['compiles'][side]['binary'] = pin(binary)
        libraries = set()
        for line in (done.stdout+'\n'+done.stderr).splitlines():
            candidate = line.split('(',1)[0].strip()
            if candidate.endswith(('.a','.tbd','.dylib','.so')) and Path(candidate).is_file():
                libraries.add(candidate)
        row['compiles'][side]['link_inputs'] = [pin(Path(name)) for name in sorted(libraries)]
        native,undefined,diagnostics,segments = execute(binary,feed,directory,side)
        ub[side] = {active[k] for k in undefined}
        remapped = {active[k]:re.sub(r'^run \d+:',f'run {active[k]}:',text) for k,text in enumerate(native)}
        observed[side] = [remapped[k] if k in remapped else f'run {k}: excluded-known-undefined' for k in range(len(lines))]
        raw = directory/(side+'-raw.out')
        raw.write_text(''.join(Path(segment['stdout']['path']).read_text() for segment in segments))
        stream = directory/(side+'.out'); stream.write_text('\n'.join(observed[side])+'\n')
        row['outputs'][side] = {'raw':pin(raw),'comparison_stream':pin(stream),
                                'segments':segments,'sanitizer_indexes':sorted(ub[side])}
        row['sanitizer_diagnostics'].extend(diagnostics)
    union = ub['c']|ub['cxx']|set(excluded)
    defined,infeasible,mismatch = [],[],None
    for k,(c,cxx) in enumerate(zip(observed['c'],observed['cxx'])):
        if k in union:
            continue
        if c != cxx and mismatch is None:
            mismatch = {'index':k,'oracle':lines[k],'c':c,'cxx':cxx}
        if c.endswith(' end=infeasible') and cxx.endswith(' end=infeasible'):
            infeasible.append(k)
        elif c.endswith(' end=done') and cxx.endswith(' end=done'):
            defined.append(k)
    for side in observed:
        defined_path = directory/(side+'-defined.out')
        defined_path.write_text(''.join(observed[side][k]+'\n' for k in defined))
        row['outputs'][side]['defined'] = pin(defined_path)
        row['outputs'][side]['defined_sha256'] = sha(defined_path.read_bytes())
    row.update(defined_comparisons=len(defined), precondition_excluded_runs=len(infeasible),
               undefined_behavior_runs=len(union),executed_runs_per_side=len(active),
               sanitizer_asymmetry=sorted(ub['c']^ub['cxx']))
    if mismatch:
        row.update(comparison='c_lowering_disagreement',first_difference=mismatch)
    elif row['sanitizer_asymmetry']:
        row['comparison'] = 'one_sided_undefined_behavior'
    elif defined:
        row['comparison'] = 'agree_on_defined_inputs'
    elif group=='new_array' and case=='seeded' and excluded:
        row['comparison'] = 'excluded_undefined_only'
    else:
        row['comparison'] = 'no_defined_coverage'
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-commit')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--groups',default=','.join(NAMES))
    parser.add_argument('--cases',default='safe,seeded')
    parser.add_argument('--lowering-fault',type=Path,help='negative-control JSON: C-only exact replace pairs')
    parser.add_argument('--audit-report',type=Path)
    args = parser.parse_args()
    if args.audit_report:
        errors,count = audit(args.audit_report)
        print(json.dumps({'references':count,'errors':errors}))
        return 1 if errors else 0
    if not args.expected_commit or not args.output:
        parser.error('--expected-commit and --output required')
    if git('rev-parse','HEAD') != args.expected_commit:
        parser.error('source HEAD differs from --expected-commit')
    groups,cases = args.groups.split(','),args.cases.split(',')
    if not groups or len(groups)!=len(set(groups)) or set(groups)-set(NAMES) or not cases or set(cases)-{'safe','seeded'}:
        parser.error('unknown or duplicate group/case')
    output = args.output.resolve()
    if output.exists() or output==REPO or REPO in output.parents:
        parser.error('--output must be a fresh directory outside the checkout')
    tool = c_lowering.locate()
    if tool.missing:
        parser.error(str(tool.missing))
    output.mkdir(parents=True)
    manifest = {'kind':'finite_native_cpp_c_agreement','created':datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M ET'),'commit':args.expected_commit,
                'formal_verifier_launched':False,'complete':False,'success':False,'rows':[],
                'boundary':'finite observed IEEE/native outputs only; no formal C++ theorem, WP-view agreement or proof verdict',
                'native_policy':{'flags':FLAGS,'openmp_threads':1,'stubs':False,'sampling':'ticket22 _domain seed22',
                                 'known_undefined':'explicit source-specific exclusions remain in requested domain',
                                 'signed_overflow':'-fwrapv retained from ticket22; known original overflow excluded',
                                 'system_libraries':'link-time SDK stubs and physical libraries hashed; dyld-cache runtime bytes are not independently hashed'},
                'platform':{'uname':list(os.uname()),'system_version':pin(Path('/System/Library/CoreServices/SystemVersion.plist')) if sys.platform=='darwin' else None},
                'sources':[],'tools':{'python':{**pin(Path(sys.executable).resolve()),'version':sys.version}},'tracked_status':git('status','--porcelain','--untracked-files=no')}
    for name in git('ls-files','swdb','tests/fixtures/proof/lowering','tests/test_wp_subset.py').splitlines():
        path = REPO/name
        if path.is_file():
            manifest['sources'].append(pin(path))
    manifest['sources'].append(pin(Path(__file__)))
    for side,command in [('cxx',tool.command[0]),('c',tool.command[0].replace('clang++','clang'))]:
        path = Path(command).resolve()
        version = subprocess.check_output([str(path),'--version'],text=True)
        manifest['tools'][side] = {**pin(path),'version':version}
        configs = re.findall(r'^Configuration file: (.+)$',version,re.M)
        manifest['tools'][side]['configuration_files'] = [pin(Path(name)) for name in configs]
    original = '\n'.join((FIXTURES/name).read_text() for name in GROUP_FILES)
    seeded = original
    for before,after in SEEDED_BUGS:
        if before not in seeded:
            raise RuntimeError('shared seed no longer matches: '+before)
        seeded = seeded.replace(before,after,1)
    sources = {}
    for case,text in [('safe',original),('seeded',seeded)]:
        path = output/(case+'.cc'); path.write_text(text); sources[case]=path
        manifest['sources'].append(pin(path))
    if args.lowering_fault:
        manifest['lowering_fault'] = pin(args.lowering_fault)
    fault = json.loads(args.lowering_fault.read_text()) if args.lowering_fault else None
    dump(output/'agreement.json',manifest)
    started = time.monotonic()
    try:
        for group,case in itertools.product(groups,cases):
            print('START '+group+':'+case,flush=True)
            row = compare(group,case,sources[case],output,fault)
            manifest['rows'].append(row)
            dump(output/'agreement.json',manifest)
            print(row['comparison']+' '+group+':'+case+' defined='+str(row['defined_comparisons']),flush=True)
            if row['comparison'] not in {'agree_on_defined_inputs','excluded_undefined_only'}:
                break
        manifest['complete'] = len(manifest['rows'])==len(groups)*len(cases)
        manifest['success'] = manifest['complete'] and all(r['comparison'] in
            {'agree_on_defined_inputs','excluded_undefined_only'} for r in manifest['rows'])
    except Exception:
        manifest['error'] = traceback.format_exc()
    manifest['wall_seconds'] = time.monotonic()-started
    dump(output/'agreement.json',manifest)
    errors,count = audit(output/'agreement.json')
    manifest['physical_reference_audit'] = {'count':count,'errors':errors}
    if errors:
        manifest['success'] = False
    dump(output/'agreement.json',manifest)
    return 0 if manifest['success'] else 1


if __name__=='__main__':
    raise SystemExit(main())

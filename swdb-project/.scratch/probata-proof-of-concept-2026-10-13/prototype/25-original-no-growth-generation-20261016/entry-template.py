"""2026-10-16 ET. Inert ORIGINAL no-growth WP generation observation.

Generation-only, never a proof job or source-runtime correspondence theorem.
The admitted invocation freshly lowers the source and retains every root goal.
"""
import argparse
import dataclasses
import hashlib
import json
import os
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_SHA256 = '__EXPECTED_SHA256__'

# __REVIEWED_HELPERS__


def lineage(anchors):
    """Host-independent source/anchor lineage; complete certificates stay retained."""
    direct = ('tool', 'function', 'c_lowering_sha256', 'anchors', 'models', 'std_models', 'allocation')
    candidate = anchors['vector_reallocation_candidate']
    keys = ('count', 'receiver', 'alias', 'reserve_request', 'observation', 'guard',
            'entry_obligations', 'call_obligations', 'scalar_read_obligation',
            'lowered_lifetime', 'source_sha256', 'lowered_sha256')
    return {**{key: anchors[key] for key in direct},
            'candidate_source_events': {key: candidate[key] for key in keys}}


def guarded_generation(command, directory, environment, policy, timeout, watchdog, output_root):
    """RSS guard plus a live raw-output allowance; all child output is retained."""
    def setup():
        resource.setrlimit(resource.RLIMIT_FSIZE, (policy['output_budget_bytes'], policy['output_budget_bytes']))

    started = time.monotonic()
    timed_out = output_limit = False
    with (directory/'frama-c.log').open('wb') as log:
        process = subprocess.Popen(command, cwd=directory, env=environment, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=setup)
        with watchdog.TreeWatch(process.pid, policy['cap_bytes']) as watch:
            while process.poll() is None:
                timed_out = time.monotonic()-started > timeout
                output_limit = raw_bytes(output_root) > policy['output_budget_bytes']
                if timed_out or output_limit:
                    descendants = watchdog.tree(process.pid)
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    watch._kill(descendants)
                    break
                time.sleep(0.1)
            process.wait()
        if watch.error:
            raise RuntimeError(watch.error)
    return {'exit_code': process.returncode, 'peak_rss_bytes': watch.peak,
            'out_of_memory': watch.tripped, 'timed_out': timed_out,
            'output_limit': output_limit, 'wall_seconds': time.monotonic()-started}


def raw_bytes(root):
    return sum(path.stat().st_size for path in root.rglob('*') if path.is_file())


def task_census(directory, function):
    """Retain exact common-theory log segments; no solver-task/proof inference."""
    inventory_path = directory/'wp-inventory.json'
    inventory = json.loads(inventory_path.read_bytes())
    goals = inventory.get('goals', [])
    if inventory.get('complete') is not True or not goals or len({g['goal'] for g in goals}) != len(goals):
        raise ValueError('fresh native goal census is absent/incomplete/duplicated')
    if any(g.get('function') != function for g in goals):
        raise ValueError('generated obligation escaped the sole original root function')
    if not any(not g.get('smoke') for g in goals) or not any(g.get('smoke') for g in goals):
        raise ValueError('complete ordinary and smoke goal families must remain present')
    required = ('wp-normalized.c', 'wp-properties.csv', 'wp-goals.json')
    if any(not (directory/name).is_file() for name in required):
        raise ValueError('fresh normalized C/property CSV/WP JSON is missing')
    # build_proof_task calls task_of_wpo before the Generate early return.
    # print-generated prints that common theory to the log, not a driver task.
    raw = (directory/'frama-c.log').read_bytes()
    pattern = rb'(?m)^\s*(?:\[wp(?::[^\]]+)?\]\s*)?EXPORT GOAL\s+(\S+)\s*$'
    markers = list(re.finditer(pattern, raw))
    task_dir = directory/'common-tasks'; task_dir.mkdir(exist_ok=False)
    rows = []
    for index, marker in enumerate(markers):
        stop = markers[index+1].start() if index+1 < len(markers) else len(raw)
        segment = raw[marker.start():stop]
        ident = marker.group(1).decode()
        owned = [g for g in goals if g['goal'].endswith('_'+ident)]
        if len(owned) != 1:
            raise ValueError('common task has no unique native goal owner: '+ident)
        if not re.search(rb'(?m)^\s*(?:\[wp:print-generated\]\s*)?theory\s+\w+', segment) or \
                not re.search(rb'(?m)^\s*goal\s+', segment) or not re.search(rb'(?m)^\s*end\s*$', segment):
            raise ValueError('common theory diagnostic is incomplete: '+ident)
        path = task_dir/('%03d-common-log-fragment.txt' % index)
        path.write_bytes(segment)
        rows.append({'export_id': ident, 'goal': owned[0]['goal'], 'fragment': pin(path),
                     'source_log_byte_range': [marker.start(), stop]})
    exported = [row['goal'] for row in rows]
    if len(set(exported)) != len(exported):
        raise ValueError('multiple common exports for a native goal; census needs review')
    missing = [g['goal'] for g in goals if 'valid' not in g.get('results', []) and g['goal'] not in exported]
    result = {'inventory': pin(inventory_path), 'goal_count': len(goals),
              'ordinary_count': sum(not g.get('smoke') for g in goals),
              'smoke_count': sum(bool(g.get('smoke')) for g in goals),
              'common_task_count': len(rows), 'common_tasks': rows,
              'missing_noninternal_tasks': missing,
              'internal_simplifier_goals': [g['goal'] for g in goals if g['goal'] not in exported and 'valid' in g.get('results', [])],
              'scope': 'Generation census only. Internal Valid/smoke statuses never become proof acceptance.'}
    write(directory/'task-census.json', result)
    if not rows or missing:
        raise ValueError('required common tasks are missing; retain partial census')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if sha(args.expected) != EXPECTED_SHA256:
        raise ValueError('generation expectation bytes differ')
    expected = json.loads(args.expected.read_bytes())
    policy = expected['resource_policy']
    project = args.project.resolve(); repo = project.parent; out = args.output.resolve()
    if str(project) != expected['remote_project'] or out.exists() or out.is_relative_to(repo):
        raise ValueError('exact source and fresh external output required')
    launch = linux_admission(expected, repo, out)
    out.mkdir(parents=True); os.chdir(project)
    started = time.monotonic(); deadline = started+policy['profile_seconds']
    result = {'scope': expected['scope'], 'source_commit': expected['source_commit'],
              'generation_complete': False, 'source_runtime_correspondence_proved': False,
              'caller_acceptance': False, 'model_acceptance': False, 'ticket_closure': False,
              'public_proof_record_created': False, 'solver_proof_requested': False,
              'linux_launch': launch, 'source_receipts': []}

    def remaining():
        left = deadline-time.monotonic()
        if left <= 0:
            raise TimeoutError('whole generation profile budget spent')
        return left

    def source_check():
        prefix = ['/usr/bin/git', '--no-replace-objects', '-C', str(repo)]
        head = subprocess.check_output([*prefix, 'rev-parse', 'HEAD'], text=True, timeout=min(30, remaining())).strip()
        dirty = subprocess.check_output([*prefix, 'status', '--porcelain', '--untracked-files=all'], text=True, timeout=min(30, remaining()))
        if head != expected['source_commit'] or dirty:
            raise ValueError('generation source is not the exact clean immutable commit')
        for row in expected['source_blobs']:
            path = project/row['relative']
            if path.is_symlink() or not path.is_file() or sha(path) != row['sha256']:
                raise ValueError('generation source package differs: '+row['relative'])
        closure = consumer_closure(project, repo, expected)
        path = out/('source-consumers-%d.json' % len(result['source_receipts']))
        write(path, closure); result['source_receipts'].append(pin(path))

    def runtime_check():
        selected = {}
        for name, row in expected['tools'].items():
            path = shutil.which(name)
            if path is None or Path(path).resolve() != Path(row['path']).resolve() or sha(path) != row['sha256']:
                raise ValueError('selected tool physical bytes differ: '+name)
            selected[name] = pin(Path(path).resolve())
        if Path(sys.executable).resolve() != Path(expected['linux_launch_binding']['python']).resolve():
            raise ValueError('selected Python interpreter differs')
        for row in expected['wp_artifacts']:
            if sha(row['path']) != row['sha256']:
                raise ValueError('selected WP artifact differs')
        prefix = Path(expected['linux_prefix'])
        roots = [('why3_stdlib', prefix/'share/why3/stdlib'),
                 ('wp_why3_support', prefix/'share/frama-c/share/wp/why3'),
                 ('why3_drivers', prefix/'share/why3/drivers')]
        for key, path in roots:
            surface(path, expected['portable_import_surfaces'][key])
        for row in expected['runtime_sources']:
            if sha(prefix/'lib/frama-c-wp/core'/row['name']) != row['sha256']:
                raise ValueError('selected runtime/generation source differs: '+row['name'])
        if sha(expected['why3_config']['path']) != expected['why3_config']['sha256']:
            raise ValueError('selected Why3 config differs')
        return selected

    def budget():
        size = raw_bytes(out.parent)
        if size > policy['output_budget_bytes']:
            raise ValueError('raw-output allowance exceeded')
        return size

    try:
        source_check(); write(out/'runtime.json', runtime_check())
        ambient = sorted(k for k in os.environ if k.startswith(('FRAMAC_WP', 'WP_')) or k == 'SWDB_PROOF_REPORT_OUT')
        if ambient:
            raise ValueError('ambient WP override names: '+','.join(ambient))
        shutil.copyfile(__file__, out/'entry.py'); shutil.copyfile(args.expected, out/'expected.json')
        os.environ.update(SWDB_FRAMA_C=expected['tools']['frama-c']['path'],
                          SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'],
                          WHY3CONFIG=expected['why3_config']['path'],
                          SWDB_WHY3_CONFIG=expected['why3_config']['path'], PYTHONDONTWRITEBYTECODE='1')
        sys.dont_write_bytecode = True; sys.path.insert(0, str(project))
        from swdb import c_lowering, stdlib_provenance, hint_check, heap_model_view, proof_setup, rss_watchdog
        source = project/expected['source_relative']
        if sha(source) != expected['source_sha256']:
            raise ValueError('original caller source differs')
        compiler = stdlib_provenance.runtime_identity(c_lowering.locate())
        if compiler != expected['linux_project_identity_derivation']['runtime'] or \
                c_lowering.identity() != expected['linux_project_identity_derivation']['predicted_identity']:
            raise ValueError('fresh Linux compiler/source/context composite differs')
        write(out/'compiler-runtime.json', {'runtime': compiler, 'identity': c_lowering.identity()})
        lowered = c_lowering.lower(source, expected['function'])
        if lowered.sha256 != expected['lowered_sha256'] or lowered.text.encode() != bytes.fromhex(expected['cached_lowered_hex']):
            raise ValueError('fresh ORIGINAL lowering is not byte-identical to retained source lineage')
        anchors = json.loads(lowered.anchors_json)
        if lineage(anchors) != expected['cached_anchor_lineage']:
            raise ValueError('fresh original root anchors/models/source events differ')
        if lowered.vector_reallocation_candidate.get('verdict') != 'pending' or \
                lowered.vector_reallocation_candidate.get('reserve_request') != 'count' or \
                lowered.vector_reallocation_candidate.get('observation') != 'captured alias':
            raise ValueError('fresh closed original no-growth candidate differs')
        problem = stdlib_provenance.check(lowered.stdlib_provenance, c_lowering.locate(), source,
                    models=tuple(sorted(set((*lowered.models, *lowered.std_models)))),
                    substitutions=lowered.stdlib_substitutions)
        if problem:
            raise ValueError('fresh original-TU provenance differs: '+problem)
        (out/'original.cc').write_bytes(source.read_bytes())
        (out/'lowering.original.c').write_bytes(lowered.text.encode())
        (out/'anchors.fresh.json').write_bytes(lowered.anchors_json.encode())
        write(out/'anchors.cached-lineage.json', {
            'lineage': expected['cached_anchor_lineage'],
            'complete_cached_anchor_reference': expected['cached_inputs']['anchors'],
            'scope': 'Exact lineage projection; complete historical Mac certificate remains in the local authoring packet, not a Linux runtime certificate.'})
        block = '/*@ '+ '\n    '.join(expected['contract_clauses'])+' */'
        merged = hint_check.wp_base(lowered.text, lowered.anchors,
                                   {expected['function']+'.contract': [block]})
        if hashlib.sha256(merged.encode()).hexdigest() != expected['wp_input_sha256']:
            raise ValueError('ordinary contract-anchor insertion differs from frozen input')
        reader_dir = out/'reader'; reader_dir.mkdir()
        reader = proof_setup.compile_report_module(reader_dir, timeout=min(90, remaining()))
        tool = [expected['tools']['frama-c']['path']]
        foundation = heap_model_view.foundations(tool, out/'foundation', deadline)
        if foundation['ocaml_package_paths']['wp_core'] != expected['linux_prefix']+'/lib/frama-c-wp/core':
            raise ValueError('selected native reader/foundation package differs')
        write(out/'foundation.json', foundation)
        directory = out/'generation'; directory.mkdir(); (directory/'tmp').mkdir()
        (directory/'wp_input.c').write_text(merged)
        flags = expected['generation_flags']
        command = [*tool, '-machdep', 'x86_64', 'wp_input.c', '-print', '-ocode', 'wp-normalized.c',
                   '-then', *flags, '-wp-report-json', 'wp-goals.json', '-then',
                   '-load-module', str(reader), '-report', '-report-untried', '-report-csv', 'wp-properties.csv']
        if any(flag.startswith('-wp-prop') for flag in command) or flags.count('-wp-gen') != 1 or \
                '-wp-no-why3-detect' not in flags:
            raise ValueError('generation-only complete root flags differ')
        runtime_check(); remaining(); budget()
        if (directory/'wp_input.c').read_bytes() != merged.encode():
            raise ValueError('original merged source changed before generation')
        environment = {**os.environ, 'TMPDIR': str(directory/'tmp'),
                       'SWDB_PROOF_REPORT_OUT': str(directory/'wp-inventory.json')}
        timeout = min(policy['frama_seconds'], remaining())
        write(directory/'command.json', {'argv': command, 'cwd': str(directory), 'timeout_seconds': timeout,
            'input': pin(directory/'wp_input.c'), 'source': pin(source),
            'policy': 'Generation-only; source/model contracts remain unproved hypotheses. No body/caller proof record.'})
        observed = guarded_generation(command, directory, environment, policy, timeout, rss_watchdog, out.parent)
        write(directory/'resources.json', observed); result['generation_resources'] = observed
        if observed['exit_code'] or observed['timed_out'] or observed['out_of_memory'] or observed['output_limit']:
            raise ValueError('generation stopped; retain partial artifacts and exact failure')
        result['task_census'] = task_census(directory, expected['function'])
        source_check(); runtime_check(); remaining()
        if lowered.sha256 != sha(out/'lowering.original.c') or sha(directory/'wp_input.c') != expected['wp_input_sha256']:
            raise ValueError('original retained lowering/input changed after generation')
        result.update(generation_complete=True, source_after_clean=True, raw_bytes=budget(),
            classification='Complete ORIGINAL root task-generation observation; common task/import/hypothesis review pending. No proof or source-runtime correspondence acceptance.')
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
    finally:
        result.update(elapsed_seconds=time.monotonic()-started,
                      within_profile_budget=time.monotonic() <= deadline)
        write(out/'result.json', result)
        write(out/'artifact-manifest.json', [{'relative': str(path.relative_to(out)), **pin(path)}
            for path in sorted(out.rglob('*')) if path.is_file() and path != out/'artifact-manifest.json'])
    return 0 if result['generation_complete'] and result['within_profile_budget'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""2026-10-16 ET. Authorized passive in-place V3 metadata/source audit.

Run via isolated system Python on mbit10. Stdlib and read-only Git only. No
project imports, raw transfers, writes, compilation, generation or solver calls.
"""
import collections
import csv
import hashlib
import json
import re
import resource
import signal
import subprocess
import time
from pathlib import Path

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-c978393b-t25-original-no-growth-gen-v3')
PROFILE = RAW/'original-no-growth-generation-v3-profile'
PROJECT = Path('/data1/yanruj/probata-resume-20261016-c978393b/swdb-project')
SOURCE = 'c978393b119a3614229a37f0f2c8ca2a097c750b'
ROOT = 'vector_realloc_v3_no_growth'
errors = []
checks = 0
hashed = {}


def require(value, description):
    global checks
    checks += 1
    if not value:
        errors.append(description)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    result = digest.hexdigest()
    hashed[str(path)] = result
    return result


def snapshot(directory):
    rows = []
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), 'redirected raw path '+str(path))
        if path.is_file():
            rows.append({'path': str(path.relative_to(directory)),
                         'bytes': path.stat().st_size, 'sha256': sha(path)})
    return rows


def git(*arguments):
    return subprocess.check_output(['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
        '-C', str(PROJECT.parent), *arguments], text=True, timeout=120).strip()


def main():
    started = time.monotonic()
    signal.alarm(180)
    resource.setrlimit(resource.RLIMIT_AS, (256*1024**2, 256*1024**2))
    before = snapshot(PROFILE)
    expected_path = PROFILE/'expected.json'
    require(sha(expected_path) == '25f044c1b0c12ac2122efe0c5b4e17409b842c11dd1024d6f19ea2d666b0dd27', 'actual expected V3 hash')
    require(sha(PROFILE/'entry.py') == '2311dea162593dbaf064a84e1ffb233ffa3dde1a90ccc27708c9a599df2f415b', 'actual entry V3 hash')
    expected = json.loads(expected_path.read_bytes())
    result = json.loads((PROFILE/'result.json').read_bytes())
    require(result['generation_complete'] is False and result['error'] == 'generated obligation escaped the sole original root function', 'preserved actual V3 observer refusal')
    require(git('rev-parse', 'HEAD') == SOURCE and git('rev-parse', '--abbrev-ref', 'HEAD') == 'HEAD', 'exact detached source after actual V3')
    require(not git('status', '--porcelain', '--untracked-files=all'), 'source clean after actual V3')
    for row in expected['source_blobs']:
        require(sha(PROJECT/row['relative']) == row['sha256'], 'source package '+row['relative'])
    consumers = json.loads((PROFILE/'source-consumers-0.json').read_bytes())
    for relative, row in consumers['trees'].items():
        require(git('rev-parse', SOURCE+':swdb-project/'+relative) == row['oid'], 'consumer source Git tree '+relative)
    for row in consumers['files']:
        path = Path(row['path'])
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'source consumer '+row['relative'])
    for name, row in expected['tools'].items():
        require(sha(Path(row['path'])) == row['sha256'], 'selected tool physical bytes '+name)
    for row in expected['wp_artifacts']:
        require(sha(Path(row['path'])) == row['sha256'], 'WP artifact '+row['path'])
    prefix = Path(expected['linux_prefix'])
    runtime_pins = []
    for row in expected['runtime_sources']:
        path = prefix/'lib/frama-c-wp/core'/row['name']
        digest = sha(path)
        require(digest == row['sha256'], 'selected runtime source '+row['name'])
        runtime_pins.append({'name': row['name'], 'sha256': digest})
    for key, path in [('why3_stdlib', prefix/'share/why3/stdlib'),
                      ('wp_why3_support', prefix/'share/frama-c/share/wp/why3'),
                      ('why3_drivers', prefix/'share/why3/drivers')]:
        rows = [{'relative': str(p.relative_to(path)), 'sha256': sha(p)}
                for p in sorted(path.rglob('*')) if p.is_file()]
        require(rows == expected['portable_import_surfaces'][key], 'complete selected support membership '+key)
    require(sha(Path(expected['why3_config']['path'])) == expected['why3_config']['sha256'], 'selected Why3 configuration')
    compiler = json.loads((PROFILE/'compiler-runtime.json').read_bytes())
    require(compiler == {'runtime': expected['linux_project_identity_derivation']['runtime'],
                         'identity': expected['linux_project_identity_derivation']['predicted_identity']}, 'recorded compiler/source/runtime composite')
    for name in ('command_executable', 'driver', 'parser'):
        row = compiler['runtime'].get(name, {})
        if row.get('path') and row.get('sha256'):
            require(sha(Path(row['path'])) == row['sha256'], 'fresh physical compiler component '+name)
    foundation = json.loads((PROFILE/'foundation.json').read_bytes())
    for row in foundation['sources']:
        require(sha(Path(row['path'])) == row['sha256'], 'selected foundation '+row['path'])
    require(sha(Path(foundation['metadata_executable'])) == foundation['metadata_executable_sha256'], 'retained foundation helper bytes')
    require(sha(PROFILE/'foundation/heap_model_environment.ml') == foundation['metadata_source_sha256'], 'retained foundation helper source')
    manifest = json.loads((PROFILE/'artifact-manifest.json').read_bytes())
    require({r['relative'] for r in manifest} == {r['path'] for r in before if r['path'] != 'artifact-manifest.json'}, 'complete original raw-manifest membership')
    for row in manifest:
        path = PROFILE/row['relative']
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'actual raw pin '+row['relative'])

    require(sha(PROFILE/'original.cc') == expected['source_sha256'] == sha(PROJECT/expected['source_relative']), 'original C++ source lineage')
    require(sha(PROFILE/'lowering.original.c') == expected['lowered_sha256'], 'unchanged original lowering lineage')
    input_path = PROFILE/'generation/wp_input.c'
    require(sha(input_path) == expected['wp_input_sha256'], 'unchanged exact three-clause merged input')
    source_lines = input_path.read_text().splitlines()
    lowered = (PROFILE/'lowering.original.c').read_bytes()
    anchors = json.loads((PROFILE/'anchors.fresh.json').read_bytes())
    candidate = anchors['vector_reallocation_candidate']
    require(candidate['source_sha256'] == expected['source_sha256'] and candidate['lowered_sha256'] == expected['lowered_sha256'], 'fresh candidate source/lowering identities')
    require(candidate['reserve_request'] == 'count' and candidate['observation'] == 'captured alias', 'original no-growth alias observation')
    require(candidate['known_origins_granted'] == [] and candidate['original_caller_premises_added'] == [], 'no candidate ownership or caller-premise admission')

    directory = PROFILE/'generation'
    command = json.loads((directory/'command.json').read_bytes())
    actual = command['argv']; flags = expected['generation_flags']
    require(actual[actual.index('-then')+1:actual.index('-wp-report-json')] == flags, 'exact generation flags and no property filtering')
    require(not any(x.startswith('-wp-prop') for x in actual), 'no WP property suppression')
    require(actual[actual.index('-wp-fct')+1] == ROOT, 'exact selected original source root')
    require('-wp-gen' in actual and '-wp-no-why3-detect' in actual, 'generation-only and no solver autodetection')
    require(sha(Path(actual[actual.index('-load-module')+1])) == sha(PROFILE/'reader/proof_report.cmxs'), 'exact retained native reader selected')
    require(sha(PROFILE/'reader/proof_report.ml') == sha(PROJECT/'swdb/proof_report.ml'), 'unchanged selected native reader source')

    inventory = json.loads((directory/'wp-inventory.json').read_bytes())
    wp = json.loads((directory/'wp-goals.json').read_bytes())
    goals = inventory['goals']; properties = inventory['properties']
    require(len(goals) == 33 and len(properties) == 84, 'retain complete actual 33-goal/84-property census')
    native = {row['goal']: row for row in goals}; standard = {row['goal']: row for row in wp}
    by_property = {row['property']: row for row in properties}
    require(inventory['complete'] is True and len(native) == len(goals) and len(standard) == len(wp), 'complete unique native/standard goal census')
    require(set(native) == set(standard), 'native/WP JSON complete goal ID equality')
    require(all(row['function'] == ROOT for row in wp), 'standard WP JSON all goal owners equal selected root')
    for ident, row in native.items():
        peer = standard[ident]
        require(all(row.get(k) == peer.get(k) for k in ('property', 'line', 'smoke', 'passed')), 'native/WP common goal fields '+ident)
        require(row['property'] in by_property, 'native goal property exists '+ident)
    families = collections.Counter()
    for row in goals:
        ident = row['goal']
        family = 'smoke' if row['smoke'] else 'call_precondition' if '_call_' in ident else 'frame' if '_assigns_' in ident else 'initialization' if '_assert_rte_initialization' in ident else 'access' if '_assert_rte_mem_access' in ident else 'postcondition' if ident.endswith('_ensures') else 'other_ordinary'
        families[family] += 1
    require(families == {'smoke': 9, 'frame': 13, 'initialization': 3, 'access': 1,
                        'postcondition': 1, 'call_precondition': 4, 'other_ordinary': 2}, 'complete expected root ordinary/RTE/init/frame/smoke families')
    bindings = {'constructor': 'std_vector_int_ctor_count_value', 'data capture': 'std_vector_int_data',
                'reserve': 'std_vector_int_reserve', 'destructor': 'std_vector_int_dtor'}
    events = {row['event']: row for row in candidate['lowered_lifetime']['events'] if row['reachable_on_normal_return']}
    insertion_lines = len(source_lines)-len(lowered.decode().splitlines())
    require(insertion_lines == 3, 'exact ordinary contract insertion line shift')
    mismatches = [row for row in goals if row['function'] != ROOT]
    require(len(mismatches) == 4 and all(row['smoke'] for row in mismatches), 'only four native callee-labelled smoke owner mismatches')
    lineage = []
    for event, callee in bindings.items():
        span = events[event]['lowered_source']
        fragment = lowered[span['begin']:span['end']]
        require(hashlib.sha256(fragment).hexdigest() == span['sha256'], 'fresh exact lowered call span '+event)
        line = lowered[:span['begin']].count(b'\n')+1+insertion_lines
        require(re.search(r'\b'+re.escape(callee)+r'\s*\(', source_lines[line-1]) is not None, 'same source call at merged physical line '+event)
        smoke = [row for row in mismatches if row['function'] == callee and row['line'] == line]
        require(len(smoke) == 1, 'one exact call smoke '+callee)
        if len(smoke) != 1:
            continue
        row = smoke[0]; prop = by_property[row['property']]
        match = re.fullmatch(re.escape(callee)+r'_wp_smoke_dead_call_s(\d+)', row['property'])
        require(match is not None and prop['property_variant'] == 'IPOther' and
                prop['property_export_origin'] == 'wp-smoke-reference' and prop['status_registered'] is False and
                prop['description'] == 'wp_smoke_dead_call' and prop['source_file'] == str(input_path) and
                prop['extern'] is False and prop['dependencies'] == [] and prop['origin'] is None,
                'exact synthetic call smoke property family '+callee)
        call_instances = [p for p in properties if isinstance(p.get('call_context'), dict) and
                          p['call_context']['caller'] == ROOT and p['call_context']['callee'] == callee and p['line'] == line]
        require(len(call_instances) == 1, 'one native source-root call instance '+callee)
        if call_instances and match:
            require(call_instances[0]['call_context']['statement_id'] == int(match.group(1)) and
                    call_instances[0]['call_context']['source_file'] == str(input_path), 'exact source call statement/lineage '+callee)
        ordinary = [g for g in goals if not g['smoke'] and g['property'] == call_instances[0]['property']] if call_instances else []
        require(len(ordinary) == 1 and ordinary[0]['function'] == ROOT, 'root ordinary precondition retained '+callee)
        lineage.append({'event': event, 'callee': callee, 'merged_line': line,
                        'statement_id': int(match.group(1)) if match else None,
                        'native_smoke_goal': row['goal'], 'native_property_owner': row['function'],
                        'standard_wp_owner': standard[row['goal']]['function'],
                        'ordinary_precondition_goal': ordinary[0]['goal'] if ordinary else None,
                        'lowered_span_sha256': span['sha256']})

    missing_dependencies = sorted({name for p in properties for name in p['dependencies'] if name not in by_property})
    missing_origins = sorted({p['origin'] for p in properties if p['origin'] is not None and p['origin'] not in by_property})
    require(not missing_dependencies and not missing_origins, 'native property origin/dependency closure')
    log_path = directory/'frama-c.log'
    require(sha(log_path) == 'ce3ef3ba970c16e3d35622ad1a03a44906432dc76c52da31843e4a5b25d75fc6' and
            log_path.stat().st_size == 414051, 'unchanged exact actual common-task/import log')
    log = log_path.read_bytes()
    markers = list(re.finditer(rb'(?m)^\s*(?:\[wp(?::[^\]]+)?\]\s*)?EXPORT GOAL\s+(\S+)\s*$', log))
    common_tasks = []
    for index, marker in enumerate(markers):
        stop = markers[index+1].start() if index+1 < len(markers) else len(log)
        fragment = log[marker.start():stop]
        ident = marker.group(1).decode()
        owners = [g for g in goals if g['goal'].endswith('_'+ident)]
        require(len(owners) == 1, 'unique native owner of actual common export '+ident)
        require(re.search(rb'(?m)^\s*(?:\[wp:print-generated\]\s*)?theory\s+\w+', fragment) is not None and
                re.search(rb'(?m)^\s*goal\s+', fragment) is not None and
                re.search(rb'(?m)^\s*end\s*$', fragment) is not None,
                'complete retained common-theory log fragment '+ident)
        common_tasks.append({'export_id': ident, 'goal': owners[0]['goal'] if owners else None,
            'log_byte_range': [marker.start(), stop], 'bytes': len(fragment),
            'sha256': hashlib.sha256(fragment).hexdigest()})
    exported = {row['goal'] for row in common_tasks}
    require(len(common_tasks) == len(exported) == 16, 'all sixteen actual common exports retained uniquely')
    inventory_only = [g for g in goals if g['goal'] not in exported]
    require(len(inventory_only) == 17 and all(g['results'] == ['valid'] and
            any(p['prover'] == 'qed' and p.get('success') == 1 for p in standard[g['goal']]['provers'])
            for g in inventory_only), 'seventeen other goals have only recorded internal Qed simplification')
    with (directory/'wp-properties.csv').open() as stream:
        reader = csv.DictReader(stream, delimiter='\t'); csv_rows = list(reader); csv_fields = reader.fieldnames
    csv_missing = sorted({row['property'] for row in csv_rows if row.get('property') and row['property'] not in by_property})
    require(not csv_missing, 'CSV property names in native complete closure')
    after = snapshot(PROFILE)
    require(before == after, 'raw profile byte-for-byte unchanged through passive inspection')
    require(git('rev-parse', 'HEAD') == SOURCE and not git('status', '--porcelain', '--untracked-files=all'), 'source remains clean after passive inspection')
    report = {'created': '2026-10-16 ET', 'scope': __doc__,
        'decision': 'PASS_CONDITIONAL_GENERATION_OBSERVATION_SOURCE_RUNTIME_AND_CALL_SMOKE_LINEAGE' if not errors else 'REFUSED_PASSIVE_CLOSURE',
        'checks': checks, 'errors': errors, 'source_commit': SOURCE,
        'source_package_files_checked': len(expected['source_blobs']),
        'source_consumer_files_checked': len(consumers['files']),
        'source_consumer_bytes_checked': sum(row['bytes'] for row in consumers['files']),
        'runtime_source_pins': runtime_pins, 'unique_physical_paths_hashed': len(hashed),
        'raw_files_unchanged': len(before), 'raw_bytes_unchanged': sum(row['bytes'] for row in before),
        'native_goal_count': len(goals), 'native_property_count': len(properties),
        'goal_families': dict(families), 'native_standard_goal_ids_equal': set(native) == set(standard),
        'common_tasks_in_place': common_tasks, 'internal_qed_inventory_only_goals': [g['goal'] for g in inventory_only],
        'call_smoke_source_lineage': lineage, 'csv_rows': len(csv_rows), 'csv_fields': csv_fields,
        'native_extern_properties': [p['property'] for p in properties if p['extern']],
        'missing_dependencies': missing_dependencies, 'missing_origins': missing_origins,
        'retained_actual_result': {'sha256': sha(PROFILE/'result.json'), 'generation_complete': result['generation_complete'],
            'error_type': result['error_type'], 'error': result['error'], 'generation_resources': result['generation_resources']},
        'retained_input_pins': {name: sha(PROFILE/name) for name in ('entry.py','expected.json','original.cc','lowering.original.c','generation/wp_input.c','generation/wp-goals.json','generation/wp-inventory.json','generation/wp-properties.csv','generation/wp-normalized.c','generation/frama-c.log')},
        'proof_acceptance': False, 'source_typed_bridge_established': False, 'caller_acceptance': False,
        'actual_refusal_unchanged': True, 'compiler_or_native_or_verifier_reruns': 0,
        'raw_content_transferred': False,
        'passive_limits': {'alarm_seconds': 180, 'address_space_cap_bytes': 256*1024**2},
        'passive_elapsed_seconds': time.monotonic()-started,
        'boundary': 'Physical metadata/source/runtime and selected-root generation lineage only. All original33/84 rows retained; four callee-labelled synthetic smokes are cross-bound to actual source-root call sites, never renamed or filtered. Common-task term/import/hypothesis interpretation is coordinated separately; original callee contracts remain unproved. Original entry refusal remains preserved.'}
    signal.alarm(0)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())

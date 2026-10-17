"""2026-10-16 ET. INERT mixed V8 available-evidence cold capture.

Root source review/admission required. No project import/compiler/native helper/
verifier/solver/version query. Missing original proof-term bytes remain missing;
normal record success cannot create a complete hypothesis/import certificate.
"""
import ast
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import time
import types
import xml.etree.ElementTree as ET

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-36266e10-mixed-pair-public-v8')
SOURCE = Path('/data1/yanruj/probata-resume-20261016-36266e10')
COMMIT = '36266e101e0484f3c2cf5f3fae4322d5de648d85'
PROFILE = RAW / 'mixed-pair-profile'
MAX_JSON = 4 * 1024**2
MAX_FILE = 128 * 1024**2
CHECKS = 0
GIT_ACTIVE = False

# __REVIEWED_READ_ONLY_HELPERS__


def strict_yaml(data):
    # Normal safe YAML construction plus duplicate mapping-key refusal. Selected
    # physical PyYAML is package TCB; no project import or libyaml/tool invocation.
    import yaml
    class UniqueSafeLoader(yaml.SafeLoader):
        def construct_mapping(self, node, deep=False):
            self.flatten_mapping(node)
            pairs = [(self.construct_object(k, deep=deep), self.construct_object(v, deep=deep))
                     for k, v in node.value]
            need(len({k for k, _ in pairs}) == len(pairs), 'unique physical YAML mapping keys')
            return dict(pairs)
    return yaml.load(data, Loader=UniqueSafeLoader)


def record_order(records):
    by_subject = {(r['job']['adapter'], r['subject']['kind'], r['subject']['id']): r for r in records}
    keys = [('wp', 'c_model', name) for name in CONTEXT['model_names']]
    keys += [(adapter, 'library_summary', name) for adapter in ('wp', 'cbmc')
             for name in ('contract.fixture_pair_pointer_values', 'contract.fixture_pair_pointer_wrong_identity')]
    need(len(records) == len(by_subject) == len(keys) == 8 and set(by_subject) == set(keys),
         'exact eight physical source/adapter subjects')
    return [by_subject[key] for key in keys]


def raw_membership():
    rows, pending = [], [RAW]
    while pending:
        root = pending.pop()
        need(stat.S_ISDIR(root.lstat().st_mode), 'physical raw traversal')
        with os.scandir(root) as stream:
            children = sorted(stream, key=lambda entry: entry.name)
        for entry in children:
            path = root / entry.name
            st = path.lstat()
            if stat.S_ISDIR(st.st_mode):
                kind = 'directory'
                pending.append(path)
            elif stat.S_ISREG(st.st_mode):
                kind = 'regular'
            else:
                relative = str(path.relative_to(RAW))
                need(stat.S_ISLNK(st.st_mode) and relative in CONTEXT['aliases'] and
                     os.readlink(path) == CONTEXT['aliases'][relative], 'closed pytest alias only')
                target = Path(os.readlink(path))
                need(target == PROFILE / 'pytest/test_actual_mixed_pair_bodies_0' and
                     stat.S_ISDIR(target.lstat().st_mode) and target.resolve(strict=True) == target,
                     'alias remains in sole physical selected test directory')
                kind = 'symlink'
            rows.append({'relative': str(path.relative_to(RAW)), 'kind': kind})
            need(len(rows) <= 1000, 'finite exact mixed raw membership')
    rows.sort(key=lambda row: Path(row['relative']).parts)
    need(rows == CONTEXT['raw_membership'], 'complete exact raw member/type census')
    return rows


def wp_context(directory, record):
    inventory = read(directory / 'wp-inventory.json')
    standard = read(directory / 'wp-goals.json')
    need(inventory['complete'] is True and inventory['version'] == '1', 'complete native WP report')
    native = inventory['goals']
    need(len({g['goal'] for g in native}) == len(native) and
         {g['goal'] for g in native} == {g['goal'] for g in standard}, 'complete native/standard WP goal identity')
    peers = {g['goal']: g for g in standard}
    for goal in native:
        need(all(goal.get(k) == peers[goal['goal']].get(k) for k in
                 ('goal', 'property', 'function', 'line', 'smoke', 'passed')), 'native/standard property owner')
    props = inventory['properties']
    names = {p['property'] for p in props}
    need(len(names) == len(props), 'unique complete native property inventory')
    missing = sorted({d for p in props for d in p.get('dependencies', []) if d not in names})
    origins = sorted({p['origin'] for p in props if p.get('origin') is not None and p['origin'] not in names})
    csv_rows = list(csv.DictReader(io.StringIO(read_bytes(directory / 'wp-properties.csv').decode()), delimiter='\t'))
    log = read_bytes(directory / 'frama-c.log').decode()
    exports = re.findall(r'(?m)^\s*(?:\[wp[^\]]*\]\s*)?EXPORT GOAL\s+(\S+)', log)
    imports = sorted(set(re.findall(r'\(\* use ([\w.]+) \*\)|\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)', log)))
    raw_input = directory / 'wp_input.c'
    need(raw_input.is_file(), 'retained full WP query input')
    compact_properties = [{**{key: value for key, value in prop.items() if key not in ('description', 'call_context')},
                           'description_sha256': sha(prop.get('description', '').encode()),
                           'call_context_sha256': digest(prop.get('call_context'))}
                          for prop in props]
    return {'record': record['id'], 'query': pin(raw_input), 'native': pin(directory / 'wp-inventory.json'),
            'standard': pin(directory / 'wp-goals.json'), 'CSV': pin(directory / 'wp-properties.csv'),
            'log': pin(directory / 'frama-c.log'), 'native_goals': native, 'ordinary_goals': standard,
            'property_closure': inventory['property_closure'], 'properties': compact_properties, 'CSV_rows': csv_rows,
            'missing_dependency_ids': missing, 'unbound_origin_ids': origins,
            'Extern_properties': [p['property'] for p in props if p.get('extern')],
            'common_export_ids': exports, 'printed_import_names': imports,
            'retained_standalone_task_files': [],
            'complete_hypothesis_import_semantics_admitted': False,
            'boundary': 'Native/CSV/query/context census only. No original materialized solver task is retained in the fixed raw namespace. Printed log fragments, properties, model record dependencies and current translators do not replace complete task/import/hypothesis byte closure.'}


def cbmc_context(directory, record):
    document = read(directory / 'cbmc.json')
    need(isinstance(document, list), 'complete CBMC structured output array')
    results = [row for message in document for row in message.get('result', [])]
    need(results and len({row['property'] for row in results}) == len(results), 'complete unique CBMC property IDs')
    goals = {goal['goal']: goal for goal in record['goals']}
    need(set(goals) == {row['property'] for row in results}, 'every actual CBMC property is retained in the normal record')
    for row in results:
        need(row['status'].lower() == goals[row['property']]['status'], 'actual CBMC status/record agreement')
    failed = [goals[row['property']]['property'] for row in results if row['status'] == 'FAILURE']
    wrong = record['subject']['id'] == 'contract.fixture_pair_pointer_wrong_identity'
    wanted = {'swdb_reach.end'} | ({'contract.fixture_pair_pointer_wrong_identity#post.ensures1'} if wrong else set())
    need(set(failed) == wanted, 'exact reachability plus intended negative postcondition failures')
    need(not any('unwind' in row['property'].lower() or 'unwind' in row.get('description', '').lower()
                 for row in results if row['status'] == 'FAILURE'), 'no failed unwind property hidden by result')
    agreement = record['settings']['agreement']
    need(agreement['verdict'] == 'agree' and agreement['runs'] == 49 and agreement['sampled'] is False,
         'exact bounded49 independent C/C++ draws')
    c_output = directory / 'differential_c.out'
    cxx_output = directory / 'differential_cxx.out'
    need(pin(c_output)['sha256'] == agreement['c_output_sha256'] and
         pin(cxx_output)['sha256'] == agreement['cxx_output_sha256'], 'physical bounded native output pins')
    sources = []
    for name in ('job.c', 'differential_c.c', 'differential_cxx.cc', 'replay_cxx.cc'):
        path = directory / name
        if path.is_file():
            value = read_bytes(path).decode()
            includes = re.findall(r'^\s*#\s*include\s*[<"]([^>"\n]+)[>"]', value, re.M)
            sources.append({'name': name, **pin(path), 'direct_include_spellings': includes,
                            'source_text_exported': False})
    replay = record.get('counterexample', {}).get('replay', {})
    if wrong:
        need(replay.get('replayed') is True and (directory / 'replay_cxx.cc').is_file() and
             record['settings']['forms']['cxx'] == 'refuted (counterexample replayed)', 'original C++ counterexample replay artifact')
    return {'record': record['id'], 'structured_output': pin(directory / 'cbmc.json'),
            'all_properties': [{**{key: row[key] for key in ('property', 'status', 'sourceLocation') if key in row},
                                'description_sha256': sha(row.get('description', '').encode())}
                               for row in results], 'failed_property_labels': failed,
            'normal_forms': record['settings']['forms'], 'bounded_agreement': agreement,
            'physical_outputs': [pin(c_output), pin(cxx_output)], 'source_artifacts': sources,
            'original_cpp_replayed_reported': replay.get('replayed', False),
            'counterexample_trace_transfer': False,
            'trace_to_original_source_reconstruction_independently_admitted': False,
            'boundary': 'All structured result IDs/statuses and physical record/replay/native output pins reconciled. Independent trace-to-original-expression/source, undefined-behavior, ABI and native runtime interpretation remains pending; no universal C++ result from49draws.'}


def main():
    started = time.monotonic()
    signal.alarm(180)
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    # Imports of fixed stdlib/PyYAML are passive reader TCB. No other external
    # process except exact read-only Git is permitted after this point.
    sys.addaudithook(audit)
    raw_before = raw_membership()
    expected = read(RAW / 'control/policy.json')
    need(pin(RAW / 'control/policy.json')['sha256'] == CONTEXT['policy_sha256'], 'exact original policy')
    lane = read(RAW / 'lane.json')['socket_lane']
    need(lane['lease_generation'] == 622 and lane['node'] == 0 and lane['exit_code'] == 0 and
         lane['numa_memory_policy'] == 'bind:0' and lane['ended_utc'] == '2026-10-16T22:12:07Z',
         'exact settled original lane guard context')
    launch = read(RAW / 'launch.json')
    need(launch['source_commit'] == COMMIT and launch['source'] == str(SOURCE) and
         launch['rss_cap_bytes'] == 8589934592 and launch['workers'] == 1 and launch['timeout_seconds'] == 1200,
         'exact original launch/source/resource role')
    for name in ('resources.json', 'outer-resources.json'):
        value = read(RAW / name)
        need(value['exit_code'] == 0 and not value['out_of_memory'] and not value['timed_out'] and
             value['peak_rss_bytes'] <= 8589934592, 'healthy settled original whole guard')
    for relative, wanted in CONTEXT['raw_regular_pins'].items():
        got = pin(RAW / relative)
        need(got['sha256'] == wanted['sha256'] and got['bytes'] == wanted['bytes'], 'entire fixed raw physical content')
    aliases = CONTEXT['aliases']
    for relative, wanted in aliases.items():
        path = RAW / relative
        need(stat.S_ISLNK(path.lstat().st_mode) and os.readlink(path) == wanted, 'exact closed pytest-current alias')
    need(git('rev-parse', 'HEAD').decode().strip() == COMMIT and
         not git('status', '--porcelain', '--untracked-files=all'), 'evaluated source remains exact clean')
    for relative, wanted in expected['source_files'].items():
        need(pin(SOURCE / 'swdb-project' / relative)['sha256'] == wanted, 'current selected source pin')
    before = read(RAW / 'mixed-source-before.json')
    after = read(RAW / 'mixed-source-after.json')
    need(before == after, 'exact producer source-consumer receipts')
    for relative, row in before['trees'].items():
        need(git('rev-parse', COMMIT + ':swdb-project/' + relative).decode().strip() == row['oid'], 'opaque consumer Git root')
    for row in before['files']:
        got = pin(row['path'])
        need(got['sha256'] == row['sha256'] and got['bytes'] == row['bytes'], 'opaque current consumer physical content')
    for left, right in CONTEXT['equal_retained_before_after']:
        need(read(RAW / left) == read(RAW / right), 'retained producer runtime/source pre/post equality')
    for path, value in expected['runtime_files'].items():
        need(pin(path)['sha256'] == value, 'declared current physical runtime file')
    root = PROFILE / 'pytest/test_actual_mixed_pair_bodies_0'
    progress = read(root / 'actual-mixed-pair-progress.json')
    files = sorted((root / 'records/proofs').glob('*.yaml'))
    records = record_order([strict_yaml(read_bytes(path)) for path in files])
    need(len(progress) == 8 and {r['id']: r for r in progress} == {r['id']: r for r in records}, 'all8 physical YAML/progress equality')
    namespace = {'need': need, 'RSS_BYTES': 8589934592, 'MEMBERS': tuple(CONTEXT['model_names'])}
    exec(compile(CONTEXT['eight_record_gate_source'], '<exact-reviewed-eight-record-gate>', 'exec'), namespace)
    projected = namespace['check_eight_records'](records, read(RAW / 'mixed-project-runtime.json')['model_hashes'])
    junit = ET.fromstring(read_bytes(PROFILE / 'junit.xml'))
    need(len(list(junit.iter('testcase'))) == 1 and not any(list(junit.iter(kind)) for kind in
         ('skipped', 'error', 'failure')), 'exact one zero-skip successful actual testcase')
    wp = [wp_context(root / 'runs' / record['id'] / 'wp', record) for record in records[:6]]
    cbmc = [cbmc_context(root / 'runs' / record['id'] / 'cbmc', record) for record in records[6:]]
    for relative, wanted in CONTEXT['raw_regular_pins'].items():
        need(pin(RAW / relative)['sha256'] == wanted['sha256'], 'fixed raw unchanged after passive interpretation')
    need(raw_membership() == raw_before, 'settled full raw membership unchanged')
    for relative, wanted in expected['source_files'].items():
        need(pin(SOURCE / 'swdb-project' / relative)['sha256'] == wanted, 'current source posthash')
    for path, value in expected['runtime_files'].items():
        need(pin(path)['sha256'] == value, 'declared current runtime posthash')
    output = {'schema': 'mixed-v8-available-cold-evidence-1', 'date': '2026-10-16 ET',
        'classification': 'AVAILABLE_RECORD_CONTEXT_RECONCILED_FULL_TASK_CLOSURE_UNAVAILABLE',
        'source_commit': COMMIT, 'raw_root': str(RAW), 'checks': CHECKS,
        'elapsed_seconds': time.monotonic() - started, 'producer_record_gate': projected,
        'WP_contexts': wp, 'CBMC_contexts': cbmc, 'physical_records': [pin(path) for path in files],
        'full_original_solver_task_files_retained': 0,
        'complete_task_hypothesis_import_semantics_admitted': False,
        'scientific_cold_acceptance': False, 'source_caller_default_or_ticket_acceptance': False,
        'runtime_boundary': 'Declared current physical runtime pins and producer-retained pre/post snapshots only. No historical continuous identity, complete dynamic-loader/dlopen/source-to-binary closure or retroactive old Why3server identity.',
        'scope': 'Eight contract-fixture observations and available native/CSV/CBMC/replay metadata only. No original task bytes are invented and no compiler/prover/native program is rerun.'}
    encoded = compact(output) + b'\n'
    need(len(encoded) <= 2 * 1024**2, 'compact passive result cap')
    sys.stdout.buffer.write(encoded)
    return 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        sys.stdout.buffer.write(compact({'classification': 'REFUSED_MIXED_V8_PASSIVE_COLD',
            'error_type': type(error).__name__, 'error': str(error)[:2048], 'checks': CHECKS,
            'scientific_cold_acceptance': False}) + b'\n')
        raise SystemExit(1)

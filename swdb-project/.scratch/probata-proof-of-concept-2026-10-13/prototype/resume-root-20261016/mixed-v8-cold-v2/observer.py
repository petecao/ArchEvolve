"""2026-10-16 ET. INERT mixed V8 available-evidence cold capture V2.

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


"""2026-10-16 ET. Closed observed mixed-WP report convention reconciliation.

No proof or hypothesis is accepted. Full original proof-task bytes remain absent.
This helper only attributes two exact inventory-only goals and four exact dual
caller/callee smoke labels, preserving complete native and normal record census.
"""


def query_callsites(query, caller):
    """Check actual original query caller scope/token/line, export metadata only."""
    need(caller in ('swdb_pair_pointer_values', 'swdb_pair_pointer_wrong_identity'),
         'exact two source caller functions required')
    # Erase comments/string/character payloads while retaining every newline;
    # tokens from comments/quotes can never stand in for a real direct call.
    stripped = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                      lambda m: ''.join('\n' if c == '\n' else ' ' for c in m.group()), query, flags=re.S)
    matches = list(re.finditer(r'\b'+re.escape(caller)+r'\s*\([^;{}]*\)\s*\{', stripped))
    need(len(matches) == 1, 'unique original query caller definition required')
    start = matches[0].end(); depth = 1; end = None
    for offset in range(start, len(stripped)):
        depth += (stripped[offset] == '{')-(stripped[offset] == '}')
        if depth == 0:
            end = offset; break
    need(end is not None, 'complete original query caller body required')
    calls = []
    for callee, sid, line in zip(CONTEXT['model_names'], (18,19,20,21), (45,49,53,56)):
        sites = list(re.finditer(r'\b'+re.escape(callee)+r'\s*\(', stripped[start:end]))
        need(len(sites) == 1, 'one exact callee call inside original caller required')
        offset = start+sites[0].start()
        need(stripped.count('\n',0,offset)+1 == line, 'exact source query call line differs')
        calls.append({'caller':caller,'callee':callee,'statement_id':sid,'line':line})
    return calls


def reconcile_wp_reports(native, standard, properties, record, query):
    """Closed exact-record projection of source-defined report conventions."""
    generated = {g['goal']:g for g in native}
    peers = {g['goal']:g for g in standard}
    rows = {g['goal']:g for g in record['goals']}
    props = {p['property']:p for p in properties}
    need(len(generated) == len(native) and len(peers) == len(standard) and
         len(rows) == len(record['goals']) and len(props) == len(properties),
         'unique complete native/standard/normal-record/property IDs required')
    need(set(generated) == set(rows) and set(peers) <= set(generated),
         'complete native inventory equals normal record; standard cannot add goals')
    model = record['subject']['kind'] == 'c_model'
    ident = record['subject']['id']
    if model:
        need(ident in CONTEXT['model_names'], 'exact four model subjects required')
        extras = {f'typed_real_{ident}_{suffix}' for suffix in ('terminates','exits')}
        need(set(generated)-set(peers) == extras, 'only exact two observed CFG inventory goals may lack standard rows')
        callsites = []
    else:
        need(record['subject']['kind'] == 'library_summary' and ident in
             ('contract.fixture_pair_pointer_values','contract.fixture_pair_pointer_wrong_identity'),
             'exact two caller subjects required')
        need(set(generated) == set(peers), 'caller inventory cannot omit any standard goal')
        extras = set()
        caller = 'swdb_pair_pointer_values' if ident.endswith('_values') else 'swdb_pair_pointer_wrong_identity'
        callsites = query_callsites(query, caller)
    special = {f"typed_real_{r['callee']}_wp_smoke_dead_call_s{r['statement_id']}":r for r in callsites}
    seen = set(); inventory_only = []; dual_owner = []
    for gid, goal in generated.items():
        normal = rows[gid]
        need(normal.get('property') == goal.get('property') and
             normal.get('smoke') is goal.get('smoke'), 'every normal record binds native property/smoke role')
        if gid in extras:
            suffix = gid.rsplit('_',1)[1]
            prop = props.get(goal.get('property'))
            need(goal.get('property') == ident+'_'+suffix and goal.get('function') == ident and
                 goal.get('line') == (13 if ident.endswith('_assign') else 11) and
                 goal.get('smoke') is False and goal.get('passed') is True and
                 isinstance(goal.get('results'),list) and 'valid' in goal['results'] and
                 normal.get('function') == ident and normal.get('status') == 'valid' and
                 normal.get('solver') is None and normal.get('seconds') is None and
                 normal.get('source') == 'wp_inventory', 'exact observed inventory-only CFG status/owner required')
            need(prop is not None and prop.get('function') == ident and
                 prop.get('line') == goal['line'] and prop.get('dependencies') == [] and
                 prop.get('extern') is False and prop.get('origin') is None and prop.get('call_context') is None,
                 'inventory-only CFG property graph must remain explicit and closed')
            inventory_only.append({'goal':gid,'property':goal['property'],'function':ident,
                                   'normal_status':'valid','source':'wp_inventory'})
            continue
        peer = peers[gid]
        need(all(goal.get(k) == peer.get(k) for k in ('goal','property','line','smoke','passed')),
             'all shared native/standard nonowner fields exact')
        need(normal.get('function') == peer.get('function') and normal.get('source') == 'wp_json',
             'normal shared goal retains exact standard-report owner/provenance')
        if gid in special:
            site = special[gid]; prop = props.get(goal.get('property'))
            need(goal.get('function') == site['callee'] and peer.get('function') == site['caller'] and
                 goal.get('line') == site['line'] and goal.get('smoke') is True and
                 goal.get('passed') is True and normal.get('status') == 'valid' and
                 goal.get('property') == gid.removeprefix('typed_real_') and
                 prop is not None and prop.get('function') == site['callee'] and
                 prop.get('line') == site['line'] and prop.get('dependencies') == [] and
                 prop.get('extern') is False and prop.get('origin') is None and
                 prop.get('call_context') is None, 'exact source-callsite/caller/callee smoke ownership required')
            seen.add(gid); dual_owner.append({'goal':gid,**site})
        else:
            need(goal.get('function') == peer.get('function'), 'unlisted native/standard owner difference refused')
    need(seen == set(special), 'all four exact callee-owned caller smokes required')
    return {'complete_native_normal_record_IDs_exact':True,
            'standard_is_exact_expected_subset':True,
            'inventory_only_CFG_goals':sorted(inventory_only,key=lambda r:r['goal']),
            'exact_source_bound_dual_owner_smokes':sorted(dual_owner,key=lambda r:r['goal']),
            'scientific_or_full_task_closure_accepted':False}


def wp_context(directory, record):
    inventory = read(directory / 'wp-inventory.json')
    standard = read(directory / 'wp-goals.json')
    need(inventory['complete'] is True and inventory['version'] == '1', 'complete native WP report')
    native = inventory['goals']
    props = inventory['properties']
    raw_input = directory / 'wp_input.c'
    reconciliation = reconcile_wp_reports(native, standard, props, record, read_bytes(raw_input).decode())
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
            'closed_report_reconciliation': reconciliation,
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
    output = {'schema': 'mixed-v8-available-cold-evidence-2', 'date': '2026-10-16 ET',
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

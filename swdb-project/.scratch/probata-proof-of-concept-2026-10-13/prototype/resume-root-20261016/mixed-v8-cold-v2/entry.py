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

def need(value, label):
    global CHECKS
    if not value:
        raise ValueError(label)
    CHECKS += 1


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return sha(compact(value))


def identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_uid, st.st_gid,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def physical(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'absolute canonical input path')
    for parent in reversed(path.parents):
        need(stat.S_ISDIR(parent.lstat().st_mode), 'physical input ancestor ' + str(parent))
    return path


def read_bytes(path, cap=MAX_JSON):
    path = physical(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'bounded regular input ' + str(path))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(identity(os.fstat(descriptor)) == identity(before), 'opened original physical input')
        chunks = []
        remaining = cap + 1
        while remaining:
            block = os.read(descriptor, min(1048576, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        value = b''.join(chunks)
        need(len(value) == before.st_size and len(value) <= cap, 'bounded complete input read')
        need(identity(before) == identity(os.fstat(descriptor)) == identity(path.lstat()), 'stable input bytes')
        return value
    finally:
        os.close(descriptor)


def pin(path, cap=None):
    path = physical(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and (cap is None or before.st_size <= cap), 'physical bounded hash input')
    h = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(identity(os.fstat(descriptor)) == identity(before), 'physical hash descriptor')
        count = 0
        while True:
            block = os.read(descriptor, 1048576)
            if not block:
                break
            h.update(block)
            count += len(block)
        need(count == before.st_size and identity(before) == identity(os.fstat(descriptor)) == identity(path.lstat()),
             'stable complete hash input')
        return {'path': str(path), 'bytes': count, 'sha256': h.hexdigest()}
    finally:
        os.close(descriptor)


def read(path):
    def pairs(items):
        result = {}
        for name, value in items:
            need(name not in result, 'unique JSON field')
            result[name] = value
        return result
    return json.loads(read_bytes(path), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('finite JSON required')))


def git(*arguments):
    global GIT_ACTIVE
    need(arguments in [('rev-parse', 'HEAD'), ('status', '--porcelain', '--untracked-files=all')]
         or len(arguments) == 2 and arguments[0] == 'rev-parse' and arguments[1].startswith(COMMIT + ':swdb-project/'),
         'closed read-only Git operation')
    GIT_ACTIVE = True
    try:
        return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '--no-optional-locks',
                                       '-c', 'core.fsmonitor=false', '-c', 'core.preloadIndex=false',
                                       '-c', 'index.threads=1', '-C', str(SOURCE), *arguments], timeout=20,
                                       env={'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent',
                                            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
                                            'GIT_OPTIONAL_LOCKS': '0', 'LC_ALL': 'C'})
    finally:
        GIT_ACTIVE = False


def audit(event, args):
    if event == 'subprocess.Popen':
        need(GIT_ACTIVE and args[0] == '/usr/bin/git', 'only closed read-only Git child')
    elif event.startswith('socket.') or event in {'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen'}:
        raise RuntimeError('native/network/project/tool execution forbidden')
    elif event == 'open':
        filename, mode, flags = args
        writable = isinstance(mode, str) and any(char in mode for char in 'wax+')
        writable = writable or flags & os.O_ACCMODE != os.O_RDONLY or flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        if writable:
            need(isinstance(filename, int) and GIT_ACTIVE and stat.S_ISFIFO(os.fstat(filename).st_mode),
                 'read-only observer forbids filesystem writes')


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


CONTEXT = json.loads('{"aliases": {"mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_current": "/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-36266e10-mixed-pair-public-v8/mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0"}, "date": "2026-10-16 ET", "eight_record_gate_source": "def check_eight_records(records, model_hashes):\\n    need(isinstance(records, list) and len(records) == 8\\n         and len({row[\\"id\\"] for row in records}) == 8, \\"exact eight distinct records required\\")\\n    for row in records:\\n        need(row[\\"evidence_kind\\"] == \\"contract_fixture\\"\\n             and row[\\"settings\\"][\\"rss_cap_bytes\\"] == RSS_BYTES\\n             and row[\\"pins\\"][\\"method_version\\"][\\"id\\"] == \\"method.pair-workflow-fixture\\"\\n             and \\"skip_reason\\" not in row,\\n             \\"record fixture scope/RSS differs\\")\\n    need([row[\\"job\\"][\\"adapter\\"] for row in records] == [\\"wp\\"] * 6 + [\\"cbmc\\"] * 2,\\n         \\"original four-model/two-WP/two-CBMC adapter order differs\\")\\n    models = dict(zip(MEMBERS, records[:4]))\\n    for name, row in models.items():\\n        need(row[\\"subject\\"] == {\\"kind\\": \\"c_model\\", \\"id\\": name}\\n             and row[\\"verdict\\"] == \\"proven\\" and row.get(\\"unproven_properties\\", []) == [],\\n             \\"original mixed-pair model was not completely proven\\")\\n        need(row[\\"pins\\"][\\"code\\"][\\"sha256\\"] == model_hashes[name], \\"original model code pin differs\\")\\n    safe, wrong, cbmc_safe, cbmc_wrong = records[4:]\\n    need([row[\\"subject\\"] for row in records[4:]] == [\\n        {\\"kind\\": \\"library_summary\\", \\"id\\": name} for name in\\n        (\\"contract.fixture_pair_pointer_values\\", \\"contract.fixture_pair_pointer_wrong_identity\\") * 2],\\n        \\"original safe/wrong contract identity differs\\")\\n    for row in records[:6]:\\n        need(row[\\"goals\\"] and any(not goal.get(\\"smoke\\") for goal in row[\\"goals\\"])\\n             and any(goal.get(\\"smoke\\") for goal in row[\\"goals\\"]),\\n             \\"complete ordinary and smoke WP observation required\\")\\n        if row is not wrong:\\n            need(all(goal[\\"status\\"] == \\"valid\\" for goal in row[\\"goals\\"]),\\n                 \\"positive ordinary/smoke WP goal was not valid\\")\\n    need(safe[\\"verdict\\"] == \\"proven\\", \\"original WP caller not proven\\")\\n    pins = {row[\\"id\\"]: row for row in safe[\\"pins\\"][\\"models\\"]}\\n    need(len(safe[\\"pins\\"][\\"models\\"]) == len(MEMBERS) and set(pins) == set(MEMBERS),\\n         \\"caller model dependency set differs\\")\\n    for name, row in models.items():\\n        need(pins[name][\\"proof_record\\"] == row[\\"id\\"]\\n             and pins[name][\\"sha256\\"] == model_hashes[name], \\"caller uses another model proof/code\\")\\n    need(wrong[\\"verdict\\"] == \\"not_proven\\" and wrong[\\"failure_class\\"] in (\\"unknown\\", \\"timeout\\")\\n         and any(not goal.get(\\"smoke\\") and goal[\\"status\\"] != \\"valid\\" for goal in wrong[\\"goals\\"])\\n         and all(goal[\\"status\\"] == \\"valid\\" for goal in wrong[\\"goals\\"] if goal.get(\\"smoke\\")),\\n         \\"original wrong-identity WP duties or smoke health differ\\")\\n    need(cbmc_safe[\\"verdict\\"] == \\"proven\\"\\n         and cbmc_safe[\\"settings\\"][\\"agreement\\"][\\"verdict\\"] == \\"agree\\", \\"CBMC safe C/C++ agreement differs\\")\\n    need(cbmc_wrong[\\"verdict\\"] == \\"refuted\\"\\n         and cbmc_wrong[\\"counterexample\\"][\\"replay\\"][\\"replayed\\"] is True\\n         and cbmc_wrong[\\"settings\\"][\\"forms\\"][\\"cxx\\"] == \\"refuted (counterexample replayed)\\",\\n         \\"original C++ wrong-identity counterexample was not replayed\\")\\n    return {\\"records\\": 8, \\"models\\": 4, \\"WP_callers\\": 2, \\"CBMC_callers\\": 2,\\n            \\"verdicts\\": [row[\\"verdict\\"] for row in records], \\"independent_cold_acceptance\\": False}", "equal_retained_before_after": [["mixed-source-before.json", "mixed-source-after.json"], ["initialized-runtime-before.json", "initialized-runtime-after.json"], ["mixed-why3-runtime-before.json", "mixed-why3-runtime-after.json"], ["mixed-native-runtime-before.json", "mixed-native-runtime-after.json"], ["mixed-native-C-wrapper-before.json", "mixed-native-C-wrapper-after.json"]], "model_names": ["std_pair_int_int_ptr_ctor_default", "std_pair_int_int_ptr_ctor", "std_pair_int_int_ptr_copy_ctor", "std_pair_int_int_ptr_operator_assign"], "policy_sha256": "0e7df71c422e83137d9fc18737233c756dab772cd3aca5b495008dc1f5a20f97", "raw_membership": [{"kind": "regular", "relative": "acceptance.log"}, {"kind": "directory", "relative": "cache"}, {"kind": "directory", "relative": "control"}, {"kind": "regular", "relative": "control/cbmc_release_gate.py"}, {"kind": "regular", "relative": "control/clang-sibling-passive.json"}, {"kind": "regular", "relative": "control/closed_python_surface.py"}, {"kind": "regular", "relative": "control/entry.py"}, {"kind": "regular", "relative": "control/job-lifecycle-source-attribution.json"}, {"kind": "regular", "relative": "control/policy.json"}, {"kind": "regular", "relative": "control/prior19-pytest-aliases.json"}, {"kind": "regular", "relative": "control/pytest-tmpdir-source-observation.json"}, {"kind": "regular", "relative": "control/python_role_observer_v2.py"}, {"kind": "regular", "relative": "control/python_startup_roles_v2.py"}, {"kind": "regular", "relative": "control/reviewed-function-lineage.json"}, {"kind": "regular", "relative": "control/reviewed_native_gates.py"}, {"kind": "regular", "relative": "control/reviewed_wp_gates.py"}, {"kind": "regular", "relative": "control/root30-control-admission.json"}, {"kind": "regular", "relative": "control/t25-why3-dependencies-passive-20261016.json"}, {"kind": "regular", "relative": "control/t25-why3-primary-socket-source-20261016.json"}, {"kind": "regular", "relative": "control/t25-why3-runtime-extension-passive-20261016.json"}, {"kind": "regular", "relative": "control/t28-linux-runtime-observer-v2-actual-20261016.json"}, {"kind": "regular", "relative": "control/why3-extension-ELF-candidates-passive.json"}, {"kind": "regular", "relative": "dispatch-argv.json"}, {"kind": "regular", "relative": "dispatch-environment.json"}, {"kind": "regular", "relative": "dispatch.log"}, {"kind": "regular", "relative": "execute.py"}, {"kind": "regular", "relative": "initialized-python-entry-isolated-accepted.json"}, {"kind": "regular", "relative": "initialized-python-entry-isolated.json"}, {"kind": "regular", "relative": "initialized-python-pytest-child-accepted.json"}, {"kind": "regular", "relative": "initialized-python-pytest-child.json"}, {"kind": "regular", "relative": "initialized-runtime-after-startup.json"}, {"kind": "regular", "relative": "initialized-runtime-after.json"}, {"kind": "regular", "relative": "initialized-runtime-before.json"}, {"kind": "regular", "relative": "lane.json"}, {"kind": "regular", "relative": "launch.json"}, {"kind": "regular", "relative": "mixed-cbmc-release.json"}, {"kind": "regular", "relative": "mixed-command.json"}, {"kind": "regular", "relative": "mixed-final-aliases.json"}, {"kind": "regular", "relative": "mixed-linux-admission.json"}, {"kind": "regular", "relative": "mixed-native-C-wrapper-after.json"}, {"kind": "regular", "relative": "mixed-native-C-wrapper-before.json"}, {"kind": "regular", "relative": "mixed-native-runtime-after.json"}, {"kind": "regular", "relative": "mixed-native-runtime-before.json"}, {"kind": "directory", "relative": "mixed-pair-profile"}, {"kind": "directory", "relative": "mixed-pair-profile/cache"}, {"kind": "regular", "relative": "mixed-pair-profile/junit.xml"}, {"kind": "regular", "relative": "mixed-pair-profile/progress-observer.jsonl"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/actual-mixed-pair-progress.json"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/methods"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/methods/pair-workflow-fixture.yaml"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/proof_units"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/proof_units/pair_only.cc"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/rewrite_contracts"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/rewrite_contracts/fixture_pair_values.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/rewrite_contracts/fixture_pair_wrong_field.yaml"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/.swdb.lock"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640.yaml"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56.yaml"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/frama-c.log"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/stdlib_provenance_unit.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/swdb_pair_pointer_values.anchors.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/swdb_pair_pointer_values.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-goals.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-inventory.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-normalized.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-properties.csv"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp_input.c"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/cbmc.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_c.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_c.out"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_cxx.cc"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_cxx.out"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/job.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/stdlib_provenance_unit.json"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/frama-c.log"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/handler.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/stdlib_provenance_unit.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/swdb_pair_pointer_wrong_identity.anchors.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/swdb_pair_pointer_wrong_identity.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-goals.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-inventory.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-normalized.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-properties.csv"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp_input.c"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/cbmc.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_c.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_c.out"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_cxx.cc"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_cxx.out"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/job.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/replay_cxx.cc"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/stdlib_provenance_unit.json"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/frama-c.log"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-goals.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-inventory.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-normalized.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-properties.csv"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp_input.c"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/frama-c.log"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-goals.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-inventory.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-normalized.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-properties.csv"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp_input.c"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/frama-c.log"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-goals.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-inventory.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-normalized.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-properties.csv"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp_input.c"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/adapter.log"}, {"kind": "directory", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/frama-c.log"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-goals.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-inventory.json"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-normalized.c"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-properties.csv"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp_input.c"}, {"kind": "symlink", "relative": "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_current"}, {"kind": "regular", "relative": "mixed-pair-profile/pytest.log"}, {"kind": "directory", "relative": "mixed-pair-profile/tmp"}, {"kind": "directory", "relative": "mixed-pair-profile/verifier.queue"}, {"kind": "regular", "relative": "mixed-project-runtime.json"}, {"kind": "regular", "relative": "mixed-pytest-alias-policy-after.json"}, {"kind": "regular", "relative": "mixed-pytest-alias-policy-before.json"}, {"kind": "regular", "relative": "mixed-record-census.json"}, {"kind": "regular", "relative": "mixed-result.json"}, {"kind": "regular", "relative": "mixed-root30-admission.json"}, {"kind": "regular", "relative": "mixed-source-after.json"}, {"kind": "regular", "relative": "mixed-source-before.json"}, {"kind": "regular", "relative": "mixed-why3-runtime-after.json"}, {"kind": "regular", "relative": "mixed-why3-runtime-before.json"}, {"kind": "regular", "relative": "mixed-why3-stdlib.json"}, {"kind": "regular", "relative": "outer-resources.json"}, {"kind": "regular", "relative": "preflight.json"}, {"kind": "regular", "relative": "resources.json"}, {"kind": "regular", "relative": "run.sh"}, {"kind": "regular", "relative": "runtime-provenance.json"}, {"kind": "regular", "relative": "source-after.json"}, {"kind": "regular", "relative": "source-manifest.json"}, {"kind": "directory", "relative": "tmp"}, {"kind": "regular", "relative": "watch.py"}, {"kind": "regular", "relative": "worker.log"}], "raw_regular_pins": {"acceptance.log": {"bytes": 1036, "sha256": "d0653114466f550a570ce34c868604330180d4f97c0ad0825274aed8e426d798"}, "control/cbmc_release_gate.py": {"bytes": 1905, "sha256": "681ad7be43312e224529a03d42b939305010795becd2fc203724a59c63db3dfc"}, "control/clang-sibling-passive.json": {"bytes": 1492, "sha256": "8dfe61c967652da23db53548286078356c100d896ba55bffb892596c77914f40"}, "control/closed_python_surface.py": {"bytes": 18385, "sha256": "748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af"}, "control/entry.py": {"bytes": 46357, "sha256": "bd5b1ebadd7db245660499d03a9d99395f645316db548ca752e8e8fae6b0ae34"}, "control/job-lifecycle-source-attribution.json": {"bytes": 13774, "sha256": "b14f5d2db65dbf2ca189c048986b842a2ebe7935ed9a2d1f30f71c34c869a818"}, "control/policy.json": {"bytes": 718063, "sha256": "0e7df71c422e83137d9fc18737233c756dab772cd3aca5b495008dc1f5a20f97"}, "control/prior19-pytest-aliases.json": {"bytes": 4976, "sha256": "69b6494d01946e34aeee72ff351ce3ec25d46296f52a416e175e0ee29e7dd0d3"}, "control/pytest-tmpdir-source-observation.json": {"bytes": 1649, "sha256": "24709dcf0212c84770bf60826a5472072e94862ad3d8a630b335e66c11c0777d"}, "control/python_role_observer_v2.py": {"bytes": 2709, "sha256": "9b100cbe2fdef3e7d429ccdf05d6489d44855a84328e2dd8532eb547beeaf43b"}, "control/python_startup_roles_v2.py": {"bytes": 9610, "sha256": "5e9d2e6dfa2aaa7999f4670a979d3cc32736b852a612f77d4e2f7c71bc229618"}, "control/reviewed-function-lineage.json": {"bytes": 9100, "sha256": "81534a7de64403203b758a008f7557941927eedafad35517141503539b028ec0"}, "control/reviewed_native_gates.py": {"bytes": 3637, "sha256": "c13376db78d81e351486b3e0d44c295b6f679ee9863f21023639a9893b25d283"}, "control/reviewed_wp_gates.py": {"bytes": 19781, "sha256": "76a0dc85050e70de0fbbc29099fa6cc50afa9e9edb085d991127c92f7f059151"}, "control/root30-control-admission.json": {"bytes": 2798, "sha256": "3ba333bebdd77c6117f4bfeb6981cafda249248a3323d6ab48b02f55ef12a9ae"}, "control/t25-why3-dependencies-passive-20261016.json": {"bytes": 20593, "sha256": "993074816c01d1ce45aefc82894df8d3e7e31080386cb19d1a9af6c151a08776"}, "control/t25-why3-primary-socket-source-20261016.json": {"bytes": 1579, "sha256": "ba8fc6a14d628028cd9c412d5c527a475ff138480d11fd02aafa9c6784c5d36b"}, "control/t25-why3-runtime-extension-passive-20261016.json": {"bytes": 9571, "sha256": "304b7907b78c71048b93e647b2690c07fb099e28b11466038a6105549bc2b800"}, "control/t28-linux-runtime-observer-v2-actual-20261016.json": {"bytes": 116503, "sha256": "092397608fe3a08c42d85e9c8e121ed139f0d94e345a12ae3aaa57ad6e93a5f0"}, "control/why3-extension-ELF-candidates-passive.json": {"bytes": 16856, "sha256": "f2c8b25e5d1445d69d27db28d58a84fc1eacdf19e1a3b653cc3c8e4b75627a7a"}, "dispatch-argv.json": {"bytes": 452, "sha256": "ce256f1ae098ed11681e46dd358557ea65521e14019f495f22eb84365c072f6a"}, "dispatch-environment.json": {"bytes": 171, "sha256": "4a440cb713ebc7bfac4d2fb6d2036eab733130f2eb330c9f283854f1c2bc4bb0"}, "dispatch.log": {"bytes": 1984, "sha256": "d1c6a793fe449f3cc6590fd5768cbd1a7f04c3c1d3b128ad0195f9e72d2386ae"}, "execute.py": {"bytes": 1603, "sha256": "ea774376014605a6ad31356a35abccef729f42e327ce07f4075853743dbcb612"}, "initialized-python-entry-isolated-accepted.json": {"bytes": 861, "sha256": "79f3fc294fe95e888b9dbe8cbe5060a8bfcc67876c539a7eda1a81f4984efab0"}, "initialized-python-entry-isolated.json": {"bytes": 9094, "sha256": "c31c08f31c8fdcb3a5df4c639b32c886d344dd278649cf58fb62cb465e8bd4a0"}, "initialized-python-pytest-child-accepted.json": {"bytes": 993, "sha256": "d4a1903070b94a94a06873674eb7fb3eeb49f4190a7ccb54a35b15cbf19cc607"}, "initialized-python-pytest-child.json": {"bytes": 9475, "sha256": "bf4e04642e1fb0d8a24fd28ea5f773acf1d4d49faea95f6977422e85939aa678"}, "initialized-runtime-after-startup.json": {"bytes": 861898, "sha256": "65b00322ec1aa97394b675cb519378e4189dd4b85ad5b768f69ed5004abc966c"}, "initialized-runtime-after.json": {"bytes": 861898, "sha256": "65b00322ec1aa97394b675cb519378e4189dd4b85ad5b768f69ed5004abc966c"}, "initialized-runtime-before.json": {"bytes": 861898, "sha256": "65b00322ec1aa97394b675cb519378e4189dd4b85ad5b768f69ed5004abc966c"}, "lane.json": {"bytes": 828, "sha256": "49a30d192c5b8ea831d8d92f28ec5921220300481a8b5872341caf0896a50723"}, "launch.json": {"bytes": 1484, "sha256": "564df0a47909c336a5d0f59e11af9306e163c3e37a09c7206eaedb30e1d3fea1"}, "mixed-cbmc-release.json": {"bytes": 365, "sha256": "d40d4c2dbb8db63ba2fa6994dfaad6b9ef17c5325f988d2d8694870664109fe6"}, "mixed-command.json": {"bytes": 847, "sha256": "07a99a4ccc2baee8e950bad5fae4b49fbe1428bca360fff6595581cddef9dcab"}, "mixed-final-aliases.json": {"bytes": 418, "sha256": "5304510dee3078fc87c664dabd38c17ad805f03955c518da961647defbcac1d3"}, "mixed-linux-admission.json": {"bytes": 1101, "sha256": "baf17ea7bc287f849eff3cde9a0ea75a90b7ca1b26aa707e7f8e7c431309eac0"}, "mixed-native-C-wrapper-after.json": {"bytes": 613, "sha256": "13a9da4a7e752568b901f05bcbcf4c2a32c8f73fed7bdca361d92d2c1978c03a"}, "mixed-native-C-wrapper-before.json": {"bytes": 613, "sha256": "13a9da4a7e752568b901f05bcbcf4c2a32c8f73fed7bdca361d92d2c1978c03a"}, "mixed-native-runtime-after.json": {"bytes": 9035, "sha256": "c1de993d778ff01b19f2d1dc9b803d164dbff698eeadf0d42852227fd5922f86"}, "mixed-native-runtime-before.json": {"bytes": 9035, "sha256": "c1de993d778ff01b19f2d1dc9b803d164dbff698eeadf0d42852227fd5922f86"}, "mixed-pair-profile/junit.xml": {"bytes": 384, "sha256": "5a91a56c524889c9b8358e403146816ff4bac736c4148d09f4d3c4cf620dca07"}, "mixed-pair-profile/progress-observer.jsonl": {"bytes": 6034, "sha256": "efd1428db2b28f2d13a916d658d6eae323880f862f334bacd4e8e67e6231fdd4"}, "mixed-pair-profile/pytest.log": {"bytes": 110, "sha256": "b410088862afe2225cd7a00cac914daa31fe9e2fc5405656e7a1592a72f44788"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/actual-mixed-pair-progress.json": {"bytes": 1330947, "sha256": "ae24cd5f39e1596794cc60ce963dfd4e2bc4313671841d478b4d4faf8e52701a"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/methods/pair-workflow-fixture.yaml": {"bytes": 3444, "sha256": "96b2b4584c08a8c1ab87f84d73db7826da1ec077b80904898596c2dbed648dd2"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/proof_units/pair_only.cc": {"bytes": 1165, "sha256": "bf835eab316a9266e5733c1c1a2c1277ae983e83d496a1068a17490ac31c7fe1"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/rewrite_contracts/fixture_pair_values.yaml": {"bytes": 1482, "sha256": "83503c1be1bf20007e8dcb77b0991e3eb456e0c9882062a760f8b6f5e4341710"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/library/rewrite_contracts/fixture_pair_wrong_field.yaml": {"bytes": 1498, "sha256": "18a46bdb63a30b4c62c15da9dca03c8fa93b87e44ad5f13d16c29da866f281bd"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/.swdb.lock": {"bytes": 0, "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81.yaml": {"bytes": 240302, "sha256": "83cf778a129ce2edf212a449c70778a0181c1330a9bc37b24976e96c8922f4bc"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2.yaml": {"bytes": 245527, "sha256": "bfa837ea9148a1b1b218ad6c6a61ccd6dda569797432a4726136bfbb86f9de76"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5.yaml": {"bytes": 241943, "sha256": "e0ec27bc97e8249532f79b4878186d2f4a48e55db279a642c3f2990abc0eb80f"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168.yaml": {"bytes": 246447, "sha256": "64fb9baf3ba13b322d21a1bfb5b4ce04b22293b8fe8f1de42ae662019ff4ea4d"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec.yaml": {"bytes": 13872, "sha256": "282cbf3bb673fe75db4ac1194722053daf8e79d0a6f8127973b91aa28a83b6b5"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981.yaml": {"bytes": 13915, "sha256": "c61e49a7747c5f731400bdfc8cebefe9fdf2aadf5a87564814bfe0c6e17c4321"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640.yaml": {"bytes": 14247, "sha256": "28bcb1f2a8fb3ee1e21787fb5861d2ce689f59db54ab747c9d4b4935da5a7a50"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/records/proofs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56.yaml": {"bytes": 14344, "sha256": "4999d4919a90e6ba0d9edb38bbfe50b25b9eb627971373f4abd9f89d80a7abb8"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/adapter.log": {"bytes": 1099, "sha256": "49467d6ce7f7f6fe483047b0ed7a56b180f14f52ffc16b4f16aadaa61f8b0d61"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/frama-c.log": {"bytes": 6923, "sha256": "0c884beba028d6e0fac446e319bff3472a77036513999c95c100c56a72ad1630"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/stdlib_provenance_unit.json": {"bytes": 237037, "sha256": "2f9db70a017c47869bc0717830d072228624be7b27c8ccaee9e5b2a97697cc36"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/swdb_pair_pointer_values.anchors.json": {"bytes": 237774, "sha256": "c2cce7e247527c616149834f120a6862460a562b0563b1f0d99eaf0c22bc8817"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/swdb_pair_pointer_values.c": {"bytes": 3530, "sha256": "436bea97f5bf8f6220f4252fff6cd18402d49a37b24ee8faf6f43bf34234b81c"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-goals.json": {"bytes": 20905, "sha256": "451ee2a0d6ff166681db5d587f900cffe962d9dd2df23be71fcb3e89dbb223f4"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-inventory.json": {"bytes": 49005, "sha256": "e0aa054a25ed1caddb120887db6e6ddacdb75e0c775ffc8420e1c6b239b367b3"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-normalized.c": {"bytes": 9719, "sha256": "ae8a2b2306039a22efe3b1d9b3b3ddd5bff85fe722979189398ea617fcf3b4f0"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp-properties.csv": {"bytes": 4265, "sha256": "f39e1e20bab1125ba8bafdcf9a6ead3578b233ec3e403f2bafee6d064c5c12c0"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t220647z.7ab10e81/wp/wp_input.c": {"bytes": 3634, "sha256": "820ee4aeb9cd55b8ef5d4112aa9d85cc94f27d02bcfe6c66e64ee5df74005ef6"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/adapter.log": {"bytes": 625, "sha256": "ba0fb04d183462782497c7686ea68c100552d38a3f52e572a96faa5bf8f9f859"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/cbmc.json": {"bytes": 587430, "sha256": "d235beb20f4e41e59e471a9c53ddfc1223a838e0b30d9b8437073ceae3b20db4"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_c.c": {"bytes": 9392, "sha256": "21aa02eec9ba668ca09f4593a92246df0bc86e8c81248b9e21a19bf32053f4ad"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_c.out": {"bytes": 1192, "sha256": "d0820b9d60246c9abb7e6988eab8d617f8a757345cb425e848fd4c2e395f8b97"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_cxx.cc": {"bytes": 6396, "sha256": "84cf8eedc393abf47a00c0c85a0bc65b7fded3019c5fc354e6496ba984e12ee7"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/differential_cxx.out": {"bytes": 1192, "sha256": "d0820b9d60246c9abb7e6988eab8d617f8a757345cb425e848fd4c2e395f8b97"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/job.c": {"bytes": 9392, "sha256": "21aa02eec9ba668ca09f4593a92246df0bc86e8c81248b9e21a19bf32053f4ad"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_values.20261016t221103z.bb5ec3b2/cbmc/stdlib_provenance_unit.json": {"bytes": 237037, "sha256": "2f9db70a017c47869bc0717830d072228624be7b27c8ccaee9e5b2a97697cc36"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/adapter.log": {"bytes": 1226, "sha256": "868fb23fe0db53d98e640363a634bb175cc5529e9b914010bbf19b1c4cec8199"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/frama-c.log": {"bytes": 7066, "sha256": "fb8ad4adeea85af98198bcc750d5ce02012571df037a2a63684fad20251791a4"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/handler.json": {"bytes": 272, "sha256": "a24495825881bb5ea3818262b40c42009579d1c2a73bb7107d3046eb3725eba2"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/stdlib_provenance_unit.json": {"bytes": 237037, "sha256": "2f9db70a017c47869bc0717830d072228624be7b27c8ccaee9e5b2a97697cc36"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/swdb_pair_pointer_wrong_identity.anchors.json": {"bytes": 238186, "sha256": "5b2788acfb450a7de96b90ad3d8988dbcb6a8957acc2644c1abb3a1d25154655"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/swdb_pair_pointer_wrong_identity.c": {"bytes": 3699, "sha256": "104ab39be6017bec37e2cdd4b762c1225362c34a5ea4d310abcf68c34de4564c"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-goals.json": {"bytes": 21812, "sha256": "fb084f8ca992f1ce00c119987543c8fcea7d4a8e2ae37eecf21a7345aecd77af"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-inventory.json": {"bytes": 50420, "sha256": "e43c97bf4bd4db217fc40cf05882d96f3519cb1c8d93b21e76fff840bc68790b"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-normalized.c": {"bytes": 9778, "sha256": "bce59e1066441367ccb080273cd06b7da0848196312c6def2aa32e732f6c2cb1"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp-properties.csv": {"bytes": 4399, "sha256": "1f474494eb9f1056c313881cc70c8b88a4510c7a7d85984e225348598f3c899b"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t220809z.820de8b5/wp/wp_input.c": {"bytes": 3803, "sha256": "8cba72b8ff707a4da2b1bbbdfda4e9f2485496fb1b0e19637105ad37f5969c74"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/adapter.log": {"bytes": 824, "sha256": "02382ead027d56c127ad3f4597fa211da14a8b37c1e6b8fb4bceb90a2fc27246"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/cbmc.json": {"bytes": 1087119, "sha256": "331444ff10962bb774197393b6862e836a74863da892756d9b8cb786e6f094ca"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_c.c": {"bytes": 9601, "sha256": "c64bbe3ad5aec8d0d62ce10f5ecc0749ac51aadacfe746925cc1fa4c2eda13a3"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_c.out": {"bytes": 2802, "sha256": "7f41213d492b8a9c61b5019d0998dab0f05175a1e0088be23b75ce9cd155a3a0"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_cxx.cc": {"bytes": 6461, "sha256": "db5e218ac5aed4bce287e274c523da4b91375e86555f8fb7856886330c080b68"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/differential_cxx.out": {"bytes": 2802, "sha256": "7f41213d492b8a9c61b5019d0998dab0f05175a1e0088be23b75ce9cd155a3a0"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/job.c": {"bytes": 9601, "sha256": "c64bbe3ad5aec8d0d62ce10f5ecc0749ac51aadacfe746925cc1fa4c2eda13a3"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/replay_cxx.cc": {"bytes": 6461, "sha256": "db5e218ac5aed4bce287e274c523da4b91375e86555f8fb7856886330c080b68"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.contract.fixture_pair_pointer_wrong_identity.20261016t221128z.bb05f168/cbmc/stdlib_provenance_unit.json": {"bytes": 237037, "sha256": "2f9db70a017c47869bc0717830d072228624be7b27c8ccaee9e5b2a97697cc36"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/adapter.log": {"bytes": 1091, "sha256": "58fa0dd56b4f0abda68ee31b5d0b07e9193b56fc5aff3ff0a0d55a80643a9818"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/frama-c.log": {"bytes": 2019, "sha256": "341f03b8043829599e673985f7a0022e50cd6dda82e9a53c79cc5c07f1a9015f"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-goals.json": {"bytes": 3793, "sha256": "5de3f36be525f2a72a67a392e06263e6a4a6242b5569e85d98d85245499a5e6b"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-inventory.json": {"bytes": 9299, "sha256": "ea383b47b729292bd952078f0f1b3e14e0df4ec4419354b905cfa61357c5eb51"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-normalized.c": {"bytes": 2110, "sha256": "d8d57f10e3307bf16aa5987577afb8e293f4dad865cfd0801fd6b8bd08599594"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp-properties.csv": {"bytes": 826, "sha256": "53afd59b85c845f089480bbacccd09ce92b5bc76840aace742559a7cc6f9210b"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_copy_ctor.20261016t220611z.3ba534ec/wp/wp_input.c": {"bytes": 592, "sha256": "1ec8c54c65a50a2ade9b7105a4fc56ea74863cf066786a3948f6e66b696ceb79"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/adapter.log": {"bytes": 1072, "sha256": "61b162eea5856ff426808daa66b9f8a9b92b36b27b96e64ab8bda99748f26e6c"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/frama-c.log": {"bytes": 2009, "sha256": "e7c2ec39163e993e62582d15605403fbd1b9aca9c901931ed2946f059a1ab1e5"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-goals.json": {"bytes": 4323, "sha256": "70e0821a38ccd7f0242ec3580552c150a54ba60918acf012b75b6c26dda69e45"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-inventory.json": {"bytes": 9131, "sha256": "b6f18c48262473da6a9308a2f1c0dd8f318cbc121f35cd934eeaee82a642c5de"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-normalized.c": {"bytes": 1859, "sha256": "c1f65b197a8b99a74442fc8c64b6380042d3cd853689a9058884982115d3e891"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp-properties.csv": {"bytes": 727, "sha256": "cb22f329488eda43964fcef0d6e7e0b2b9b0b874969f43199369785cc410861c"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor.20261016t220550z.3d1e3981/wp/wp_input.c": {"bytes": 511, "sha256": "89fb167980c9d5a5998e0058c9ccb7173b316042e668b1fec4b6aa1f9796cdb4"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/adapter.log": {"bytes": 1104, "sha256": "bbe598034ebc808acaf6f912bc5f8c25d27c4a508f2f149f31b9e69e2ccd9a69"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/frama-c.log": {"bytes": 2028, "sha256": "8d913e6343bd9471745778584fcf02b656ba00862aa166030028f29bfbbebe15"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-goals.json": {"bytes": 4549, "sha256": "2482ed39a0b78ae3b89cf708f9a84199aa05e9b02985631f1d76623978f4e30e"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-inventory.json": {"bytes": 9676, "sha256": "e3f52ab20885fc10f90ff144efcec7002088d78c406a95a2e839e4ca05baa6d0"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-normalized.c": {"bytes": 1730, "sha256": "55d04875d72dac2c799c2ed45b670adc5fc0f788b332da47f66b95ffc0058ff2"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp-properties.csv": {"bytes": 786, "sha256": "06b04deb9b18d3a81f2d67bccc3d33619e347aa194d0fa6e69827752a710c93a"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_ctor_default.20261016t220530z.47341640/wp/wp_input.c": {"bytes": 503, "sha256": "720762600742e15743c74aab15602f34f13b3ac1b8374ea428bf32f914eca364"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/adapter.log": {"bytes": 1116, "sha256": "8652062dcb85701b6d4f9c79107383816235858b9907da60b8be971b1e9c0885"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/frama-c.log": {"bytes": 2330, "sha256": "f3c2c159b31923c1be5f09d9281c134df2103c0a3e4339e5f984740af00cb3f0"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-goals.json": {"bytes": 4530, "sha256": "aae7d02dbf790d7bc94481b78c6bae6ce3c3b2c714d84e07f21c79481064f3ab"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-inventory.json": {"bytes": 10764, "sha256": "9b61072f886ed80b5531d26442212c953b3de640b31bfed70f1dabc394b303ae"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-normalized.c": {"bytes": 2371, "sha256": "08fc09ba9811e33209a1e4283504aa9947aebe964bcbf6189a414eec245b7e40"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp-properties.csv": {"bytes": 971, "sha256": "e0d79a45859a96fe65c38f5402e1223e77480c7e4c22f219832e09180fcd7b25"}, "mixed-pair-profile/pytest/test_actual_mixed_pair_bodies_0/runs/proof.model.std_pair_int_int_ptr_operator_assign.20261016t220629z.d0aadf56/wp/wp_input.c": {"bytes": 699, "sha256": "b2f88dcc5ebeb64c8ab36a514f02f682a19920b4762c60f96d28ad958985d990"}, "mixed-project-runtime.json": {"bytes": 4946, "sha256": "cadb280027a804460e9395950012e79b87a46ce144c0f544fc1a3014443bec49"}, "mixed-pytest-alias-policy-after.json": {"bytes": 1736, "sha256": "50cba480bb49f51d140350dd314e572d45af6b1412b1b15770bcff3a729f1d5b"}, "mixed-pytest-alias-policy-before.json": {"bytes": 1736, "sha256": "50cba480bb49f51d140350dd314e572d45af6b1412b1b15770bcff3a729f1d5b"}, "mixed-record-census.json": {"bytes": 2466, "sha256": "b96aa653ef7c80eb0062192622b2c7f78f37b97b8e764db748b496e414011c82"}, "mixed-result.json": {"bytes": 1178, "sha256": "758503b0f15d275db5fad1b236d6424c42dfeed98a88e2bc142e793e1e86b40d"}, "mixed-root30-admission.json": {"bytes": 2798, "sha256": "7851e0234d503611eed4c019c5fd0f44c003106d42b1de7453ac3304d6c637d9"}, "mixed-source-after.json": {"bytes": 671310, "sha256": "4ced840b3cc2e1e8d27539804d98c8eebcd1a1c030204aa92d5e01bfc46bedc4"}, "mixed-source-before.json": {"bytes": 671310, "sha256": "4ced840b3cc2e1e8d27539804d98c8eebcd1a1c030204aa92d5e01bfc46bedc4"}, "mixed-why3-runtime-after.json": {"bytes": 1618, "sha256": "4578c1aea2708aca3cef416729f95431047668a626a325e7fe9b3a1b6fb1f285"}, "mixed-why3-runtime-before.json": {"bytes": 1618, "sha256": "4578c1aea2708aca3cef416729f95431047668a626a325e7fe9b3a1b6fb1f285"}, "mixed-why3-stdlib.json": {"bytes": 176, "sha256": "acbe6ef8dbf5051a20a606f780e1675e9033e7f86c07bbe54b4b6b4792ba024f"}, "outer-resources.json": {"bytes": 174, "sha256": "4b169b91a7234a9d0433be6143270299a384bafb953ab41f6e6732be3d614672"}, "preflight.json": {"bytes": 25716, "sha256": "b5aea53dbe72f3c3609cf64058e6fc4866b6be58d641427f1342ac294dc8744c"}, "resources.json": {"bytes": 168, "sha256": "5a186de4f07836d15accc5f0394730ec306781b6a37c635a02b0997f1dbadce9"}, "run.sh": {"bytes": 1112, "sha256": "bfa7d95c82c2cf74c10e034543418b7e28a8ccb5631a5ea7c2b2b12e324a80d2"}, "runtime-provenance.json": {"bytes": 3368, "sha256": "a881fa51ac867fab17fa225c10a089473bba557adce22a57183778f85475c26e"}, "source-after.json": {"bytes": 112, "sha256": "fb5c0e28d46126eec462901f6418b4901f82233bd4d422db98a147b14050b5ea"}, "source-manifest.json": {"bytes": 25586, "sha256": "0e020985ca58f7ee0ab5f36ede5162b8db5af68891612bebab606264e4018c6b"}, "watch.py": {"bytes": 470, "sha256": "4485ae66aa50c65f2b579f84836576aa67b54431978da71cac6eea6a68ecd07c"}, "worker.log": {"bytes": 0, "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}}}')

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        sys.stdout.buffer.write(compact({'classification': 'REFUSED_MIXED_V8_PASSIVE_COLD',
            'error_type': type(error).__name__, 'error': str(error)[:2048], 'checks': CHECKS,
            'scientific_cold_acceptance': False}) + b'\n')
        raise SystemExit(1)

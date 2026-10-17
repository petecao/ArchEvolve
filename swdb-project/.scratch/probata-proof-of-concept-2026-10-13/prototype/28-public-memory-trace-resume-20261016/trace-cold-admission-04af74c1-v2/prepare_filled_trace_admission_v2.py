"""2026-10-16 ET. Mechanical filled policy/staging manifest; never run reader."""
import ast
import hashlib
import json
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
V1 = TRACE / 'trace-cold-audit-v1'
SHAPE = TRACE / 'trace-cold-actual-shape-controls-v2'
INIT = TRACE.parent / '28-initialized-u32-resume-20261016'
POC = TRACE.parent.parent
OLD_COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v1'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v2'
CONTROL = COLD + '/control'
PINNED = {
    V1 / 'trace_cold_audit_v1.py': '3cefa1c4eb7c05371afcdaf8b43d6f46927dfe80aed0be90e652bac0cf0157ee',
    V1 / 'trace-cold-policy-template-04af74c1-v1.json': 'f292d4e3158859869ef59697bcf9d777a4e8859923e949b3d396a35c2b58b6fb',
    V1 / 'trace-cold-source-packet-v1.json': '3d3ec111c5efe462ff1cb0298f8c54464d2cab1392280a96c4025645d7e29aa8',
    SHAPE / 'trace-cold-actual-shape-source-packet-v2.json': 'e7b1463d39037d31974372ccfc9501578393bc9bbcdb49386b8ed865eba96491',
    SHAPE / 'frozen-source-overlay-receipt-20261016.json': 'd794cec793cfa63600eaff5c64996f34e8ce3b0672918150a159b7a2bbc70f98',
    POC / 'evidence/t28-trace-v4-root-execution-20261016.json': 'c94420bdb85074be52aa2044158c9ee77cace37f4dbb0fac2274e64973a5e7ff',
}


def sha(data): return hashlib.sha256(data).hexdigest()


def read(path):
    before = path.lstat(); assert stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path
    data = path.read_bytes(); after = path.lstat()
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    if path in PINNED: assert sha(data) == PINNED[path]
    return data


def pin(path, remote=None):
    data = read(path)
    return {'path': remote or str(path), 'bytes': len(data), 'sha256': sha(data)}


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def rebind(value, reverse=False):
    if isinstance(value, dict): return {key: rebind(item, reverse) for key, item in value.items()}
    if isinstance(value, list): return [rebind(item, reverse) for item in value]
    if isinstance(value, str): return value.replace(COLD, OLD_COLD) if reverse else value.replace(OLD_COLD, COLD)
    return value


def build():
    for path in PINNED: read(path)
    review_path = V1 / 'independent-trace-cold-v1-source-review-20261016.json'
    review = json.loads(read(review_path))
    assert review['findings'] == [] and review['status'] == 'PASS_INDEPENDENT_TRACE_COLD_V1_READER_SOURCE_AND_UNADMITTED_TEMPLATE_REVIEW'
    assert review['reader']['sha256'] == PINNED[V1 / 'trace_cold_audit_v1.py']
    shape_packet = json.loads(read(SHAPE / 'trace-cold-actual-shape-source-packet-v2.json'))
    assert shape_packet['v1_reader_or_policy_changes'] is False
    for name, row in shape_packet['files'].items():
        assert pin(SHAPE / name) == row
    controls_result = json.loads(read(SHAPE / 'pure-controls-result-v2.json'))
    assert controls_result['tests'] == 6 and controls_result['exit_code'] == controls_result['failures'] == controls_result['errors'] == controls_result['skips'] == 0
    template = json.loads(read(V1 / 'trace-cold-policy-template-04af74c1-v1.json'))
    assert template['admitted'] is template['reader_admission']['admitted'] is False
    policy = rebind(template)
    policy['admitted'] = policy['reader_admission']['admitted'] = True
    staged = {}
    def stage(name, path, purpose):
        assert Path(name).name == name and name not in staged
        staged[name] = {**pin(path, CONTROL + '/' + name), 'source': str(path), 'purpose': purpose}
        return {key: staged[name][key] for key in ('path', 'bytes', 'sha256')}
    for name, row in policy['reader_files'].items():
        path = V1 / name if (V1 / name).is_file() else TRACE / name if (TRACE / name).is_file() else INIT / name
        assert stage(name, path, 'reviewed passive reader primitive') == row
    stage('trace_cold_audit_v1.py', V1 / 'trace_cold_audit_v1.py', 'byte-identical independently reviewed passive reader')
    root_name = 't28-trace-v4-root-execution-20261016.json'
    assert stage(root_name, POC / 'evidence' / root_name, 'exact original root observation provenance') == policy['root_execution_receipt']
    provenance = {
        'independent_reader_source_review': stage(review_path.name, review_path, 'independent source review; not execution'),
        'actual_shape_controls': stage('trace-cold-actual-shape-source-packet-v2.json', SHAPE / 'trace-cold-actual-shape-source-packet-v2.json', 'actual metadata controls source packet'),
        'actual_shape_test_source': stage('test_actual_metadata_shapes_v2.py', SHAPE / 'test_actual_metadata_shapes_v2.py', 'inert actual-metadata controls; never executed remotely'),
        'actual_shape_result': stage('trace-actual-shape-pure-controls-result-v2.json', SHAPE / 'pure-controls-result-v2.json', 'six author pure controls passed; not actual reader evidence'),
        'immutable_overlay_receipt': stage('frozen-source-overlay-receipt-20261016.json', SHAPE / 'frozen-source-overlay-receipt-20261016.json', 'root-staged immutable source provenance; shared edits preserved'),
        'immutable_overlay_files': [],
    }
    for filename in ('bounded_std_initialization.py', 'proof_setup.py', 'wp_adapter.py'):
        provenance['immutable_overlay_files'].append(stage('provenance-04af-' + filename, SHAPE / 'frozen-source/swdb' / filename,
            'inert immutable04af control evidence only; not imported by reader'))
    policy['provenance']['filled_admission'] = provenance
    policy['scope'] = ('Filled exact original abstract25 policy request, awaiting independent filled-policy and root launch admission. '
        'No actual reader execution, hardware counterexamples, source-call refinement, whole-interface, current0.2 or full28 claim.')
    # Complete mechanical policy inverse: no record, method, scope premise or
    # scientific criterion changes are permitted.
    inverse = rebind(policy, reverse=True)
    inverse['admitted'] = inverse['reader_admission']['admitted'] = False
    inverse['provenance'].pop('filled_admission')
    inverse['scope'] = template['scope']
    assert inverse == template
    policy_name = 'trace-cold-policy-04af74c1-v2.json'
    dump(policy_name, policy)
    stage(policy_name, HERE / policy_name, 'filled policy; execution still requires root admission')
    manifest_name = 'trace-cold-control-manifest-v2.json'
    dump(manifest_name, {'date': '2026-10-16 ET', 'fresh_raw': COLD, 'source_commit': policy['source_commit'],
        'payload_files': staged, 'payload_file_count': len(staged), 'payload_bytes': sum(row['bytes'] for row in staged.values()),
        'manifest_self_listed': False, 'reader_executed': False,
        'expected_control_basenames': sorted([*staged, manifest_name])})
    stage(manifest_name, HERE / manifest_name, 'complete control membership/pins excluding its own recursive pin')
    total = sum(row['bytes'] for row in staged.values()); assert total <= 1048576
    argv = [policy['reader_admission']['sys_path'][3].split('/lib/python3.12/')[0] + '/bin/python', '-I', '-B', '-X',
        'pycache_prefix=' + policy['reader_admission']['pycache_prefix'], CONTROL + '/trace_cold_audit_v1.py',
        CONTROL + '/' + policy_name, sha(read(HERE / policy_name))]
    assert argv[0] == '/data1/yanruj/venvs/swdb-test/bin/python'
    environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C'}
    environment.update({name: value for name, value in policy['reader_admission']['environment'].items() if value is not None})
    dump('trace-cold-command-04af74c1-v2.json', {'date': '2026-10-16 ET',
        'status': 'FILLED_STAGING_REQUEST_AWAITING_INDEPENDENT_POLICY_REVIEW_AND_ROOT_EXECUTION_ADMISSION',
        'fresh_raw': COLD, 'source_commit': policy['source_commit'], 'command': argv,
        'process_environment_mode': 'replace', 'process_environment': environment,
        'required_absent': [name for name, value in policy['reader_admission']['environment'].items() if value is None],
        'control_files': staged, 'control_file_count': len(staged), 'control_total_bytes': total,
        'reader_executed': False, 'scientific_execution': False,
        'root_conditions': ['Independently review/admit exact final invocation, replacement environment and root guard',
            'reader-source-cache absent before and after; root may create distinct outer cache',
            'Reconfirm immutable original raw/source/runtime and finite original process/lease settlement',
            'Output only in fresh cold raw; no scientific rerun or mutation of original trace raw'],
    })
    dump('filled-policy-inverse-v2.json', {'date': '2026-10-16 ET', 'old_template': pin(V1 / 'trace-cold-policy-template-04af74c1-v1.json'),
        'filled_policy': pin(HERE / policy_name), 'allowed_delta': ['two admission Booleans', 'fresh cold namespace',
            'explicit execution-pending scope sentence', 'closed staged review/actual-shape/immutable-overlay provenance'],
        'complete_inverse_equality': True, 'reader_and_scientific_logic_changed': False, 'reader_executed': False})


if __name__ == '__main__': build()

"""2026-10-16 ET. Passive physical reuse audit; no project/tool/proof execution.

Policy contains hashes/paths/IDs only. Raw source/task text is never returned.
"""
import base64
import hashlib
import json
import resource
import signal
import sys
import time
import zlib
from pathlib import Path

POLICY_SHA256 = '__POLICY_SHA256__'
POLICY_BASE64 = '__POLICY_BASE64__'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def snapshot(root):
    rows = {}
    for path in sorted(root.rglob('*')):
        assert not path.is_symlink() and (path.is_file() or path.is_dir())
        if path.is_file():
            rows[str(path.relative_to(root))] = {'bytes':path.stat().st_size, 'sha256':sha(path)}
    return rows


def main():
    started = time.monotonic()
    signal.alarm(180)
    resource.setrlimit(resource.RLIMIT_AS, (256*1024**2, 256*1024**2))
    def audit(event, args):
        if event in {'subprocess.Popen','os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:
            raise RuntimeError('external/native execution forbidden')
        if event == 'open' and len(args)>1 and isinstance(args[1],str) and any(x in args[1] for x in 'wax+'):
            raise RuntimeError('remote writes forbidden')
    sys.addaudithook(audit)
    raw = zlib.decompress(base64.b64decode(POLICY_BASE64, validate=True))
    assert hashlib.sha256(raw).hexdigest() == POLICY_SHA256
    policy = json.loads(raw)
    errors = []
    cases = []
    for case in policy['cases']:
        root = Path(case['raw']); profile = root/case['profile']
        before = snapshot(root)
        expected = case['raw_files']
        missing = sorted(set(expected)-set(before)); added = sorted(set(before)-set(expected))
        changed = sorted(p for p in set(expected)&set(before) if expected[p] != before[p])
        if missing or added or changed:
            errors.append({'case':case['name'], 'missing':missing,'added':added,'changed':changed})
        canonical = profile/'canonical-inputs'
        manifest_path = canonical/'manifest.json'
        manifest = json.loads(manifest_path.read_bytes())
        targets = []
        for row in case['targets']:
            source = canonical/row['path']
            assert sha(source) == row['sha256']
            actuals = [root/p for p in expected if p.endswith('/heap-job-'+row['id']+'/wp_input.c')]
            assert len(actuals) == 1 and sha(actuals[0]) == row['sha256']
            targets.append({'id':row['id'],'sha256':row['sha256'],'canonical_and_actual_input_equal':True})
        assert sha(manifest_path) == case['canonical_manifest_sha256']
        assert sha(canonical/'original.c') == case['original_sha256']
        assert sha(canonical/'qualified.c') == case['qualified_sha256']
        theory_paths = [root/p for p in expected if p.endswith('/theory/heap_reallocation.mlw')]
        assert theory_paths and all(sha(p) == case['theory']['sha256'] for p in theory_paths)
        refs = [p for p in expected if '/canonical-inputs/references/' in p]
        common_log_paths = [p for p in expected if p.endswith('/frama-c.log') and '/heap-job-' in p]
        task_paths = [p for p in expected if '/prover-files/' in p and p.endswith(('.smt2','.why','.mlw'))]
        report_paths = [p for p in expected if p.endswith(('/wp-goals.json','/wp-inventory.json','/wp-properties.csv'))]
        normalized_paths = [p for p in expected if p.endswith('/wp-normalized.c')]
        after = snapshot(root)
        assert before == after
        cases.append({'name':case['name'],'source_commit':case['source_commit'],'raw':str(root),
            'raw_unchanged':True,'raw_expected_membership_and_hashes_equal':not(missing or added or changed),
            'raw_files':len(before),'raw_bytes':sum(r['bytes'] for r in before.values()),
            'canonical_manifest_sha256':sha(manifest_path),'targets':targets,
            'canonical_reference_files':[{'relative':p,**before[p]} for p in refs],
            'original_sha256':sha(canonical/'original.c'),'qualified_sha256':sha(canonical/'qualified.c'),
            'theory_copies':len(theory_paths),'theory_sha256':case['theory']['sha256'],
            'common_task_logs':len(common_log_paths),'materialized_task_files':len(task_paths),
            'native_JSON_CSV_reports':len(report_paths),'normalized_C_files':len(normalized_paths),
            'complete_retained_raw_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
    current = policy['cases'][0]['expected']
    physical = []
    for kind, rows in [('tool',list(current['tools'].values())),('WP_artifact',current['wp_artifacts']),
                       ('Clang_component',[current['linux_clang_components'][key] for key in ('command_executable','driver')])]:
        for row in rows:
            path = Path(row['path']); digest = sha(path)
            assert digest == row['sha256']
            physical.append({'kind':kind,'path':str(path),'sha256':digest})
    config = current['why3_config']; assert sha(Path(config['path'])) == config['sha256']
    prefix = Path(current['linux_prefix']); surfaces = []
    for key, relative in [('why3_stdlib','share/why3/stdlib'),('wp_why3_support','share/frama-c/share/wp/why3'),
                          ('why3_drivers','share/why3/drivers')]:
        root = prefix/relative; actual = []
        for path in sorted(root.rglob('*')):
            assert not path.is_symlink() and (path.is_file() or path.is_dir())
            if path.is_file():actual.append({'relative':str(path.relative_to(root)),'sha256':sha(path)})
        assert actual == current['portable_import_surfaces'][key]
        surfaces.append({'key':key,'root':str(root),'files':len(actual),
                         'membership_sha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
    runtime = []
    for row in policy['current_runtime_sources']:
        path = prefix/'lib/frama-c-wp/core'/row['name']; assert sha(path) == row['sha256']
        runtime.append({'name':row['name'],'sha256':row['sha256']})
    report = {'created':'2026-10-16 ET','scope':__doc__,'current_source':policy['current_source'],
        'decision':'PHYSICAL_CONTENT_REUSE_MATCH' if not errors else 'REFUSED_PHYSICAL_REUSE_MATCH',
        'policy_sha256':POLICY_SHA256,'errors':errors,'cases':cases,'physical_tools_and_artifacts':physical,
        'why3_config_sha256':config['sha256'],'complete_support_surfaces':surfaces,'current_runtime_sources':runtime,
        'elapsed_seconds':time.monotonic()-started,'actual_evaluations':0,'compiler_native_verifier_solver_calls':0,
        'raw_C_AST_SMT_transferred':False,'old_current_record_adoption':False,'caller_acceptance':False,
        'boundary':'Physical equality with accepted retained conditional model math only; old root decisions and their TCB/scope stay unchanged. No fresh record/source/Typed/body/caller admission or actual submitted-byte attestation.'}
    output=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode(); assert len(output)<1024**2
    signal.alarm(0);sys.stdout.buffer.write(output)


if __name__ == '__main__':
    main()

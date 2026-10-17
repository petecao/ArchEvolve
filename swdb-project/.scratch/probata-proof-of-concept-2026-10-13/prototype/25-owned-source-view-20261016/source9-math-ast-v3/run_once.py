"""2026-10-16 ET. Root once-admitted exact complete26 metadata execution."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
EVIDENCE = POC / 'evidence'
PREFIX = 't25-owned-source9-math-ast-v3-'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, raw):
    path = EVIDENCE / (PREFIX + name)
    with path.open('xb') as stream:
        stream.write(raw)
    return pin(path)


def run(label, argv, data, stdout_cap, seconds):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    result = subprocess.run(argv, input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=seconds)
    return {'argv': argv, 'started_utc': started,
        'elapsed_seconds': time.monotonic() - clock, 'exit_code': result.returncode,
        'stdin_sha256': hashlib.sha256(data).hexdigest(),
        'stdout': save(label + '-stdout-20261016.json', result.stdout),
        'stderr': save(label + '-stderr-20261016.txt', result.stderr),
        'within_output_cap': len(result.stdout) <= stdout_cap and len(result.stderr) <= 32768}


def main():
    admission = EVIDENCE / 't25-owned-source9-math-ast-root-once-admission-v3-20261016.json'
    assert pin(admission)['sha256'] == '5c9427d17162d6847ae734c34df8ff46d99a24021029dac933afa16f3a322167'
    command = json.loads((HERE / 'command.json').read_bytes())
    assert pin(HERE / 'command.json')['sha256'] == '575432a695cda77d42fd6c5435e315e71e92e783cd803f2b175363666d2440d1'
    assert pin(HERE / 'entry.py') == command['stdin']
    assert command['stdin']['sha256'] == 'cb1b46356ff9331f2b543d82ac86c3706c18fb68396da2794627cef99f9d29d0'
    preflight = HERE.parent / 'source9-cold/root-admitted-scoped-preflight-source9-v1.py'
    assert pin(preflight)['sha256'] == '45256d3d124bde5d76f9b1df136e34f97cd456d977a245c52b7ad71c1528dbd9'
    ssh = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'mbit10']
    preflight_argv = [*ssh, '/usr/bin/env', '-i', 'HOME=/nonexistent',
        'PATH=/usr/bin:/bin', 'LANG=C', 'LC_ALL=C', '/usr/bin/timeout',
        '--signal=TERM', '--kill-after=5s', '35s', '/usr/bin/python3', '-I', '-B', '-']
    result = {'date': '2026-10-16 ET', 'admission': pin(admission),
        'entry': pin(HERE / 'entry.py'), 'command': pin(HERE / 'command.json'),
        'preflight_script': pin(preflight), 'proof_native_compiler_verifier_solver_rerun': False,
        'remote_raw_mutation': False, 'all_scientific_source_Heap_Typed_caller_acceptance': False}
    result['preflight'] = run('preflight', preflight_argv, preflight.read_bytes(), 65536, 45)
    pre = json.loads(Path(result['preflight']['stdout']['path']).read_bytes())
    assert result['preflight']['exit_code'] == 0 and result['preflight']['within_output_cap']
    assert pre['scoped_preflight_pass'] and pre['source_clean']
    save('once-marker-20261016.json', (json.dumps({'date': '2026-10-16 ET',
        'entry': command['stdin'], 'admission': pin(admission),
        'exact_query_attempt_reserved': True}, sort_keys=True) + '\n').encode())
    result['actual'] = run('actual', [*ssh, *command['argv_after_fresh_scoped_root_preflight']],
        (HERE / 'entry.py').read_bytes(), command['stdout_cap_bytes'], command['local_timeout_seconds'])
    result['postflight'] = run('postflight', preflight_argv, preflight.read_bytes(), 65536, 45)
    post = json.loads(Path(result['postflight']['stdout']['path']).read_bytes())
    actual = json.loads(Path(result['actual']['stdout']['path']).read_bytes())
    result['postflight_passed'] = (result['postflight']['exit_code'] == 0
        and result['postflight']['within_output_cap'] and post['scoped_preflight_pass'])
    result['classification'] = actual.get('classification')
    result['expected_metadata_exit2'] = result['actual']['exit_code'] == 2
    result['all29_content_and_nine_stat_pre_post_equal'] = actual.get('all29_content_and_nine_stat_pre_post_equal', False)
    result['task_count'] = actual.get('task_count')
    result['unique_math_commands'] = actual.get('unique_math_commands')
    result['complete'] = (result['expected_metadata_exit2'] and result['actual']['within_output_cap']
        and result['all29_content_and_nine_stat_pre_post_equal'] and result['postflight_passed']
        and actual.get('classification') == 'COMPLETE26_PARSED_MATHEMATICAL_METADATA_ONLY'
        and actual.get('task_count') == 26 and actual.get('scientific_acceptance') is False
        and actual.get('mathematical_acceptance') is False)
    output = save('actual-execution-20261016.json',
        (json.dumps(result, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({'execution': output, 'complete': result['complete'],
        'actual_exit': result['actual']['exit_code'], 'classification': result['classification'],
        'stdout_bytes': result['actual']['stdout']['bytes'], 'tasks': result['task_count'],
        'unique_math_commands': result['unique_math_commands'],
        'postflight_passed': result['postflight_passed']}))
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

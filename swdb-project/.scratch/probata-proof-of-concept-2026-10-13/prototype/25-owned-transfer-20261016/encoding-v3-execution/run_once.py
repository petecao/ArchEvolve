"""2026-10-16 ET. Root once-admitted exact passive G621 encoding V3 only."""
import datetime
import hashlib
import json
import subprocess
import time
from pathlib import Path

POC = Path(__file__).resolve().parents[3]
DIRECTORY = POC/'prototype/25-owned-transfer-20261016/cold-g621-encoding-v3'
EVIDENCE = POC/'evidence'
PREFIX = 't25-owned-transfer10-encoding-v3-'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
    return pin(path)


def run(label, argv, data, stdout_cap, seconds):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    result = subprocess.run(argv, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=seconds)
    stdout = save(EVIDENCE/(PREFIX+label+'-stdout-20261016.json'), result.stdout)
    stderr = save(EVIDENCE/(PREFIX+label+'-stderr-20261016.txt'), result.stderr)
    return {'argv': argv, 'started_utc': started, 'elapsed_seconds': time.monotonic()-clock,
            'exit_code': result.returncode, 'stdin_sha256': hashlib.sha256(data).hexdigest(),
            'stdout': stdout, 'stderr': stderr,
            'within_output_cap': len(result.stdout) <= stdout_cap and len(result.stderr) <= 32768}


def main():
    admission = EVIDENCE/'t25-owned-transfer10-encoding-v3-root-admission-20261016.json'
    assert pin(admission)['sha256'] == '30ab6bd1866a9cc57eac3bd69f1bc8d92a3286bac21e20607ebdc486c0b4e806'
    command = json.loads((DIRECTORY/'command.json').read_bytes())
    assert pin(DIRECTORY/'entry.py') == command['stdin']
    assert command['stdin']['sha256'] == 'cd85933706b161b4611dbb6e04cf04a2018127f525bcf8f1da73751b4deee7c6'
    assert pin(DIRECTORY/'command.json')['sha256'] == '91623c301d14f635c55ea40ab6b44e064c860aa211a643ed629e860b1b7df19f'
    preflight = DIRECTORY.parent/'cold-g621-encoding-v1/root-admitted-scoped-preflight-v3.py'
    assert pin(preflight)['sha256'] == 'c19d0da21c83059505d9a8097bf7f4f3b61145580bd7fdbc43dabaeca34bc69e'
    ssh = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'mbit10']
    environment = ['/usr/bin/env', '-i', 'HOME=/nonexistent', 'PATH=/usr/bin:/bin', 'LANG=C', 'LC_ALL=C']
    preflight_argv = [*ssh, *environment, '/usr/bin/timeout', '--signal=TERM', '--kill-after=5s',
                      '35s', '/usr/bin/python3', '-I', '-B', '-']
    result = {'date': '2026-10-16 ET', 'admission': pin(admission), 'entry': pin(DIRECTORY/'entry.py'),
              'command': pin(DIRECTORY/'command.json'), 'preflight_script': pin(preflight),
              'proof_native_compiler_verifier_solver_rerun': False, 'remote_raw_mutation': False,
              'all_scientific_source_body_Typed_caller_acceptance': False}
    result['preflight'] = run('preflight-v3', preflight_argv, preflight.read_bytes(), 65536, 45)
    pre = json.loads(Path(result['preflight']['stdout']['path']).read_bytes())
    assert result['preflight']['exit_code'] == 0 and result['preflight']['within_output_cap']
    assert pre['scoped_preflight_pass'] and pre['source_clean']
    save(EVIDENCE/(PREFIX+'once-marker-20261016.json'),
         (json.dumps({'date': '2026-10-16 ET', 'entry': command['stdin'],
                      'admission': pin(admission), 'exact_query_attempt_reserved': True}, sort_keys=True)+'\n').encode())
    query_argv = [*ssh, '/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '90s',
                  *environment, *command['argv_after_root_read_only_preflight']]
    result['actual'] = run('actual', query_argv, (DIRECTORY/'entry.py').read_bytes(), command['stdout_cap_bytes'], 105)
    result['postflight'] = run('postflight-v3', preflight_argv, preflight.read_bytes(), 65536, 45)
    post = json.loads(Path(result['postflight']['stdout']['path']).read_bytes())
    result['postflight_passed'] = result['postflight']['exit_code'] == 0 and result['postflight']['within_output_cap'] and post['scoped_preflight_pass']
    actual = json.loads(Path(result['actual']['stdout']['path']).read_bytes())
    result['classification'] = actual.get('classification')
    result['expected_metadata_exit2'] = result['actual']['exit_code'] == 2
    result['all22_selected_inputs_pre_post_equal'] = actual.get('all22_selected_inputs_pre_post_equal', False)
    result['status'] = 'ACTUAL_ONCE_METADATA_CAPTURED_POSTFLIGHT_PASSED' if result['postflight_passed'] else 'REFUSED_POSTFLIGHT'
    output = save(EVIDENCE/(PREFIX+'actual-execution-20261016.json'),
                  (json.dumps(result, sort_keys=True, indent=2)+'\n').encode())
    print(json.dumps({'execution': output, 'actual_exit': result['actual']['exit_code'],
                      'classification': result['classification'],
                      'stdout_bytes': result['actual']['stdout']['bytes'],
                      'postflight_passed': result['postflight_passed']}))


if __name__ == '__main__':
    main()

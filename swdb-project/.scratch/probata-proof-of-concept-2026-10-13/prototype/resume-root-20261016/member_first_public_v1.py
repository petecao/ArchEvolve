"""2026-10-16 ET. One real public member proof before scaling to 32 bodies.

Uses the committed adapter and ordinary shared verifier lock/RSS watchdog.
No native replay or caller adoption. Original generated evidence stays in /tmp.
"""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    project = Path(__file__).resolve().parents[4]
    output = Path('/private/tmp/probata-vector-member-first-public-20261016-v1')
    assert not output.exists() and shutil.disk_usage(output.parent).free > 20 * 1024**3
    commit = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    assert commit == '1c45737f6cff9b43731d8da530be869a7e5d745e'
    relatives = ('swdb/standard_vector_member_view.py', 'swdb/wp_adapter.py',
        'swdb/wp_pointer_bounds.py', 'swdb/proof_setup.py', 'schemas/proof.schema.json',
        'tests/testkit/standard_library.py')
    pins = []
    for relative in relatives:
        raw = (project / relative).read_bytes()
        original = subprocess.check_output(['git', '-C', str(project), 'show', commit + ':swdb-project/' + relative])
        assert raw == original
        pins.append({'relative': relative, 'sha256': hashlib.sha256(raw).hexdigest()})
    sys.path[:0] = [str(project), str(project / 'tests')]
    import yaml
    from swdb import c_lowering, rss_watchdog, standard_vector_member_view as view, std_models
    from testkit.standard_library import method_version
    output.mkdir()
    records = output / 'records'
    records.mkdir()
    methods = output / 'library/methods'
    methods.mkdir(parents=True)
    shutil.copyfile(project / 'tests/fixtures/proof/methods/contract-fixture-1.yaml',
                    methods / 'contract-fixture-1.yaml')
    method = method_version(c_lowering.identity())
    method.update(id=view.METHOD, sequence=3)
    method['models']['std_vector'] = std_models.identity()
    method['c_lowering']['translators'].append(view.identity())
    (methods / 'wp-vector-member-source-v1.yaml').write_text(yaml.safe_dump(method, sort_keys=False))
    command = [sys.executable, '-B', '-m', 'swdb', 'prove', '--records', str(records),
        '--adapter', 'wp', '--model', 'std_vector_int_end', '--method-version', view.METHOD,
        '--budget-minutes', '3', '--runs-dir', str(output / 'runs'), '--format', 'json']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
        SWDB_VERIFIER_RSS_CAP_BYTES=str(8 * 1024**3))
    selectors = [key for key in environment if key.startswith(('FRAMAC_WP', 'WP_'))
                 or key in ('SWDB_FRAMA_C', 'SWDB_VERIFIER_LOCK', 'SWDB_PROOF_REPORT_OUT')]
    assert not selectors, selectors
    plan = {'date': '2026-10-16 ET', 'source_commit': commit, 'source_pins': pins,
        'command': command, 'cwd': str(project), 'RSS_cap_bytes': 8 * 1024**3,
        'outer_seconds': 240, 'job_seconds': 180, 'workers': 1,
        'expected': 'proven qualified original int end body; no caller admission',
        'preflight': {'Mac_memory_free_percent': 58, 'disk_free_bytes': shutil.disk_usage(output).free},
        'output_budget_bytes': 128 * 1024**2, 'raw_destination': str(output)}
    (output / 'plan.json').write_text(json.dumps(plan, sort_keys=True, indent=2) + '\n')
    result = rss_watchdog.run(command, log=output / 'public.log', cwd=project,
        env=environment, cap_bytes=8 * 1024**3, timeout=240)
    (output / 'resources.json').write_text(json.dumps(dataclasses.asdict(result), sort_keys=True, indent=2) + '\n')
    total = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
    assert total <= 128 * 1024**2
    print(json.dumps({'output': str(output), 'resources': dataclasses.asdict(result),
                      'retained_bytes': total, 'caller_admission': False}, sort_keys=True))
    return result.exit_code


if __name__ == '__main__':
    raise SystemExit(main())

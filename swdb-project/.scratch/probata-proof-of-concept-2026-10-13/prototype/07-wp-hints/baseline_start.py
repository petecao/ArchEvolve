"""METHOD23 fresh-own-baseline diagnostic initialization, 2026-10-15 ET.

No round or cross-mode formula equivalence is claimed. Final acceptance still
replays every obligation. This module supplies no hint or historical result.
"""
import json
from pathlib import Path

import hints as H
import loop as L
import staged_search as S

METHOD = 'codex-only-machine-tasks-fresh-baseline-v1'
ARTIFACTS = ('goals.json', 'baseline-smoke10.log', 'baseline-smoke10.log.summary.json')


def observed(directory):
    directory = Path(directory)
    source = (L.STANDIN_DIR / L.UNIT).read_text()
    if H.check(source, []) or H.erase(H.merge(source, [])) != source:
        raise ValueError('initial baseline source/empty-hint erasure guard refused')
    if (directory / L.UNIT).read_text() != source:
        raise ValueError('initial baseline source is not the empty canonical source')
    headers = {h: L.sha(L.STANDIN_DIR / h) for h in L.HEADERS}
    if any(L.sha(directory / h) != digest for h, digest in headers.items()):
        raise ValueError('initial baseline headers changed')
    log = directory / 'baseline-smoke10.log'
    checked = S.check_run(directory, log, round_mode=False)
    summary = json.loads(Path(str(log) + '.summary.json').read_text())
    if summary['cmd'] != [str(L.HERE / 'wp_run.sh'), 'baseline-smoke10', str(directory), L.UNIT]:
        raise ValueError('initial baseline invocation differs from the frozen full baseline')
    goals = json.loads((directory / 'goals.json').read_text())
    smoke = [g for g in goals if g['smoke']]
    if not smoke or H.smoke_failures(goals):
        raise ValueError('initial full baseline smoke inventory missing or failed')
    selected = [g for g in goals if not g['smoke'] and
                (g.get('function') == 'TDStep' or g['goal'].startswith('typed_lemma_'))]
    if not any(g.get('function') == 'TDStep' for g in selected):
        raise ValueError('initial diagnostic TDStep subset missing')
    failures = H.goal_positions(selected, source, L.UNIT, L.headers_text())
    observation = {'source_sha256': L.sha(directory / L.UNIT), 'headers_sha256': headers,
                   'artifacts_sha256': {name: L.sha(directory / name) for name in ARTIFACTS},
                   'full_baseline_inventory': len(goals), 'diagnostic_subset_inventory': len(selected),
                   'diagnostic_goal_ids': [g['goal'] for g in selected], 'checked_baseline': checked}
    return observation, failures


def initialize(out):
    out = Path(out)
    directory = out / 'round-0'
    observation, failures = observed(directory)
    meta = json.loads((out / 'meta.json').read_text())
    receipt = {'method': METHOD, 'source_mode': 'baseline-smoke10', 'hints': [],
               'run_root': str(out.resolve()), 'run_started': meta['started'],
               'cross_mode_formula_equivalence_claimed': False,
               'diagnostic_only': True, 'all_final_obligations_mandatory': True, **observation}
    artifact = out / 'baseline-initial.json'
    if artifact.exists():
        raise ValueError('initial baseline receipt already exists')
    artifact.write_text(json.dumps(receipt, indent=1))
    return {'hints': [], 'failing_goals': failures, 'n_open': len(failures),
            'n_goals': receipt['diagnostic_subset_inventory'], 'dir': str(directory),
            'from': 'fresh-baseline', 'history': ['fresh-baseline'],
            'baseline_initial_sha256': L.sha(artifact)}, receipt


def verify(best, *, expected_out):
    """Retained-report seam for the genuinely empty initial incumbent only."""
    try:
        if expected_out is None:
            raise ValueError('current run identity is required')
        out = Path(expected_out).resolve()
        directory = Path(best['dir']).resolve()
        if directory != out / 'round-0':
            raise ValueError('initial baseline is outside the current run')
        artifact = out / 'baseline-initial.json'
        if directory.name != 'round-0' or best['hints'] != [] or best.get('from') != 'fresh-baseline':
            raise ValueError('only the empty fresh baseline incumbent is admissible')
        if L.sha(artifact) != best['baseline_initial_sha256']:
            raise ValueError('initial baseline receipt changed')
        receipt = json.loads(artifact.read_text())
        meta = json.loads((out / 'meta.json').read_text())
        if (receipt.get('method') != METHOD or meta.get('method23', {}).get('id') != METHOD
                or receipt.get('run_root') != str(out.resolve()) or receipt.get('run_started') != meta['started']
                or receipt.get('hints') != [] or receipt.get('source_mode') != 'baseline-smoke10'
                or receipt.get('cross_mode_formula_equivalence_claimed') is not False):
            raise ValueError('initial baseline run/protocol identity differs')
        observation, failures = observed(directory)
        if any(receipt.get(key) != value for key, value in observation.items()):
            raise ValueError('initial baseline retained observation changed')
        if (best['failing_goals'] != failures or best['n_open'] != len(failures)
                or best['n_goals'] != observation['diagnostic_subset_inventory']):
            raise ValueError('initial baseline diagnostic projection changed')
        return {**observation['checked_baseline'], 'initial_kind': 'fresh-full-baseline-subset'}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('fresh baseline incumbent refused: ' + str(exc)) from None

"""Method22 terminal acceptance protocol, created2026-10-15 ET.

Zero generated hints; natural provider receipts; positive and wait-removal
control share the original60minute clock. This module supplies no proof hint.
"""
import hashlib
import json
from pathlib import Path
import re

import hints as H
import loop as L
import staged_search as S

METHOD = 'codex-only-paged-terminal30-v1'
PROOF_STOP_MIN = 33
HARD_STOP_MIN = 36
NEGATIVE_RESERVE_MIN = 8


def prompt(template):
    start = template.index('- The loop keeps ONE checked incumbent;')
    end = template.index('- You change the best set only by EDITS:', start)
    template = template[:start] + ("- The loop begins with a genuinely EMPTY hint set. All annotations must come from your own\n"
        "  scoped operations; independently author loop_assigns from source/contracts when needed;\n"
        "  no generated/historical frames or concrete hints are supplied. No hint is exempt from proof.\n") + template[end:]
    template = template.replace('merged with the seed into one annotation right before that loop',
                                'merged deterministically into one annotation right before that loop')
    template = template.replace('Strategy names must be new (the seeds use names starting with "Seed").',
                                'Strategy names must be new.')
    start = template.index('- Round mode:')
    end = template.index('\nIn-call tools', start)
    template = template[:start] + ("- Round mode: {round_timeout}s per prover, TDStep and your lemmas only. This is diagnostic.\n"
        "  At search end ONE fresh full30s all-function/cache-none/smoke replay checks the authoritative\n"
        "  incumbent even if diagnostic goals remain open. Every obligation must pass, then the same\n"
        "  hints must pass the covering-wait negative control, all within the original60minute clock.\n"
        "- Proof tools stop at counted minute33. Return your final JSON immediately then; minutes33–36\n"
        "  are a natural-return window, not extra proof time. A forced interruption lacks complete usage\n"
        "  and cannot qualify acceptance. Do not wait for the hard36minute deadline.\n"
        "- show_goal supports bounded offset pages of the exact active WP task. Inspect omitted premises\n"
        "  by repeating its task_sha256 with offset; task/source identities and truncation are explicit.\n") + template[end:]
    return template


def usage(history):
    calls = [h['codex'] for h in history if h.get('codex') is not None]
    complete = all(c.get('usage_status') == 'complete' for c in calls)
    return {'status': 'complete' if complete else 'partial', 'provider_calls': len(calls),
            'completed_receipts': sum(c.get('usage_status') == 'complete' for c in calls),
            'admissible': complete and all(c.get('completion_deadline_met') is True and c.get('error') is None for c in calls),
            'late_provider_calls': sum(c.get('completion_deadline_met') is not True for c in calls),
            'criterion': 'every scoped call naturally exits0 with valid completed-turn usage; no interrupted-tail imputation'}



def verify_incumbent(best):
    source = (L.STANDIN_DIR / L.UNIT).read_text()
    directory = Path(best['dir'])
    merged = H.merge(source, best['hints'])
    if H.check(source, best['hints']) or H.erase(merged) != source or (directory / L.UNIT).read_text() != merged:
        raise RuntimeError('terminal incumbent source/erasure check refused')
    if any((directory / h).read_bytes() != (L.STANDIN_DIR / h).read_bytes() for h in L.HEADERS):
        raise RuntimeError('terminal incumbent header guard refused')
    log = next((directory / mode for mode in ('round-s.log', 'round.log') if (directory / mode).exists()), None)
    if log is None:
        raise RuntimeError('terminal incumbent has no checked round')
    return S.check_run(directory, log, round_mode=True)


def negative_replay(out, best, *, remaining_s, mode):
    source = (L.STANDIN_DIR / L.UNIT).read_text()
    target = '          __dxc_wait(c.tile[5]);\n'
    if source.count(target) != 1 or remaining_s() <= 0:
        return {'negative_control_passed': False, 'refusal': 'exact covering wait or total budget missing'}
    negative = source.replace(target, '', 1)
    rec = {'same_hints_sha256': hashlib.sha256(json.dumps(best['hints'], sort_keys=True).encode()).hexdigest(),
           'negative_base_sha256': hashlib.sha256(negative.encode()).hexdigest(),
           'mutation': 'remove exactly one covering __dxc_wait(c.tile[5]); statement'}
    d = L.precheck(out, 'negative-same-hints', negative, best['hints'], rec, remaining_s=remaining_s)
    if d is None or remaining_s() <= 0:
        return {**rec, 'negative_control_passed': False, 'refusal': 'negative precheck/budget'}
    L.wp_round(out, 'negative-same-hints', negative, best['hints'], rec, mode=mode, d=d,
               timeout=max(1, remaining_s()), remaining_s=remaining_s)
    if not rec.get('wp') or not rec['wp'].get('log'):
        return {**rec, 'negative_control_passed': False, 'refusal': rec.get('outcome', 'negative report unavailable')}
    log = Path(rec['wp']['log'])
    try:
        checked = S.check_run(d, log, round_mode=False)
    except RuntimeError as exc:
        return {**rec, 'negative_control_passed': False, 'refusal': str(exc)}
    goals = json.loads((d / 'goals.json').read_text())
    hazard = [g for g in goals if not g['smoke'] and g.get('function') == 'TDStep'
              and g.get('property') == 'TDStep_check_hazard_hints_read'
              and re.fullmatch(r'typed_TDStep_check_hazard_hints_read(?:_part\d+)?', g['goal'])]
    unproven = [g for g in hazard if not g['passed']]
    passed = bool(hazard and unproven and not H.smoke_failures(goals) and remaining_s() >= 0
                  and all(g['verdict'] in {'unknown', 'timeout', 'stepout'} for g in unproven))
    return {**rec, 'checked_run': checked, 'hazard_hints_read': hazard,
            'negative_control_passed': passed, 'negative_answer': 'not proven' if passed else 'not established',
            'refuted': False if passed else None, 'dir': str(d)}

"""Public retained-artifact counters for the throwaway spike, 2026-10-15 ET.

These counts describe recorded requests and guarded process reports. They never
score/promote a candidate or imply proof acceptance. Baseline/seeds/final replay
are deliberately separate from candidate edit attempts.
"""
import json
from pathlib import Path

import staged_search as S


def attempt_counts(out, history):
    """Read complete checks independently of request count or process exit alone."""
    counts = {'recorded_proposal_requests': sum((h.get('tool') or {}).get('propose_calls', 0) +
              bool(h.get('final_answer_edit')) for h in history),
              'candidate_wp_attempts_with_report': 0, 'candidate_wp_completed_checks': 0,
              'candidate_wp_deadline_censored': 0, 'candidate_wp_other_incomplete': 0}
    for path in sorted(Path(out).glob('attempt-*/*.log.summary.json')):
        report = json.loads(path.read_text())
        argv = report.get('cmd') or []
        if len(argv) < 2 or argv[1] not in ('round', 'round-s'):
            continue
        counts['candidate_wp_attempts_with_report'] += 1
        log = Path(str(path).removesuffix('.summary.json'))
        try:
            S.check_run(path.parent, log, round_mode=True)
        except RuntimeError:
            field = 'candidate_wp_deadline_censored' if report.get('timed_out') else 'candidate_wp_other_incomplete'
            counts[field] += 1
        else:
            counts['candidate_wp_completed_checks'] += 1
    turns = [h['codex'] for h in history if h.get('codex') is not None]
    known = sum(bool(turn.get('usage')) for turn in turns)
    counts.update(provider_turns_with_usage=known, provider_turns_without_usage=len(turns)-known,
                  token_totals_are_lower_bounds=known < len(turns))
    return counts

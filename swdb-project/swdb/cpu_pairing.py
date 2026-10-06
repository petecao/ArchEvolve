"""Add analytic state beside native CPU output; timing still decides. Created: 2026-10-06 ET."""
from swdb import artifacts
from swdb.cli import Failure


def paired_estimate(store, evaluation, request):
    result = {'format': 'swdb.cpu-paired-estimate.v1', 'basis': 'estimated',
        'state': 'unavailable', 'seconds': None, 'estimate': None,
        'native_timing_decides': True, 'missing': ['matched_counted_evaluator_scope'],
        'reason': 'No counted source/input/runtime/protocol binding for this established native evaluator scope.'}
    # Decide this boundary before inspecting timing or following an estimate.
    if evaluation.get('mode') == 'extensa':
        result.update(state='excluded', missing=['ArchEvolve_mode'],
            reason='Extensa timing is excluded from the team CPU error check.')
        return result
    rid = request.get('analytic_estimate') if isinstance(request, dict) else None
    if rid is None:
        return result
    try:
        if not isinstance(rid, str):
            raise Failure('analytic_estimate must name a persisted estimate record')
        estimate = store.get(rid, 'estimate')
        if estimate is None:
            raise Failure('requested analytic estimate record is unavailable')
        from swdb.archevolve import require_team_safe
        require_team_safe(store, estimate, command='CPU paired estimate')
        result['estimate'] = {'id': rid, 'sha256': artifacts.digest(estimate)}
        # Registered original-driver counts preserve advancing five-call heap
        # state. The established CPU evaluator uses independent protected-driver
        # processes/source slots. There is no protected-evaluator adapter yet.
        # Retain a reference for inspection without admitting a numeric pair.
        result.update(state='excluded', missing=['matched_counted_evaluator_scope'],
            reason='The requested estimate lacks a verified binding to this evaluator process/source/ROI/runtime scope.')
    except Failure as exc:
        result.update(state='excluded', missing=['requested_estimate_admission'], reason=str(exc))
    return result

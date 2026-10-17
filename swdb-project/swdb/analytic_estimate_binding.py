"""Fresh count-to-model admission before CPU outcomes. Updated: 2026-10-09 ET.

Hash equality binds saved bytes, not their numerical derivation. Replay only a
current frozen protocol; historical validation continues checking saved pins.
This establishes model consistency, never the truth of a target premise or an
elapsed-time boundary, DX100 bridge, error band or agreement claim.
"""
from swdb import artifacts
from swdb.cli import Failure


def admit(store, estimate, characterization, target):
    """Bind the frozen inputs, then require their exact count-only composition."""
    from swdb import analytic, estimate_protocol
    try:
        protocol = estimate_protocol.bind(store, estimate['protocol'], characterization, target)
        expected = analytic.compose_estimate(characterization, target, store, protocol)
        expected_proofs = expected.pop('extensions', {}).get('legacy_trial_scope_reconciliations')
        for field, value in expected.items():
            if field not in estimate or artifacts.digest(estimate[field]) != artifacts.digest(value):
                raise Failure('paired count-to-model composition differs: ' + field)
        for field in ('trials', 'summary', 'count_reuse'):
            if field in estimate and field not in expected:
                raise Failure('paired count-to-model composition has an unexpected field: ' + field)
        recorded_proofs = estimate.get('extensions', {}).get('legacy_trial_scope_reconciliations')
        if artifacts.digest(recorded_proofs) != artifacts.digest(expected_proofs):
            raise Failure('paired count-to-model composition differs: legacy trial scope')
        return protocol
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        raise Failure('malformed paired count-to-model composition: ' + str(exc)) from None

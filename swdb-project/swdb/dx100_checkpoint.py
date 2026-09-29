"""Strict checkpoint compatibility and explicit legacy evidence. Updated: 2026-09-25."""

from swdb import artifacts
from swdb.bfs_native import StageFailure

FORMAT = 'swdb.dx100.checkpoint.v2'


def compatibility(manifest, reference, binding, request, store):
    """Validate exact modeled settings; legacy manifests need their source record."""
    if not isinstance(manifest, dict):
        raise StageFailure('incompatible', 'checkpoint manifest must be an object')
    if manifest.get('format') == FORMAT:
        if manifest.get('binding') != binding:
            raise StageFailure('incompatible', 'checkpoint binding differs from exact binary/workload/source/model/configuration/options')
        identifier = request.get('checkpoint_evaluation')
        if identifier is not None:
            prior = store.get(identifier, 'evaluation') if isinstance(identifier, str) else None
            if not prior or prior.get('context', {}).get('checkpoint_manifest') != reference:
                raise StageFailure('incompatible', 'checkpoint source evaluation differs from the supplied manifest')
        return None
    if manifest.get('format') != 'swdb.dx100.checkpoint.v1':
        raise StageFailure('incompatible', 'unsupported checkpoint manifest format')
    identifier = request.get('checkpoint_evaluation')
    if not isinstance(identifier, str) or not identifier:
        raise StageFailure('incompatible', 'legacy checkpoint requires its identified source evaluation for configuration proof')
    prior = store.get(identifier, 'evaluation')
    context = prior.get('context', {}) if prior else {}
    legacy_binding = {key: value for key, value in binding.items()
                      if key not in {'modeled_configuration', 'hardware_target'}}
    if (not prior or prior.get('evidence_kind') != manifest.get('evidence_kind')
            or context.get('checkpoint_manifest') != reference
            or context.get('execution_binding') != legacy_binding
            or context.get('execution_binding_sha256') != artifacts.digest(legacy_binding)
            or manifest.get('binding') != legacy_binding
            or context.get('configuration') != binding['modeled_configuration']
            or context.get('target') != binding['hardware_target']
            or not any(stage.get('stage') in {'checkpoint', 'checkpoint_resolution'}
                       and stage.get('state') == 'complete' for stage in prior.get('stages', []))):
        raise StageFailure('incompatible', 'legacy checkpoint source evidence or exact modeled configuration differs')
    proof = {'source_evaluation': identifier, 'manifest': reference,
             'configuration': context['configuration'], 'target': context['target'],
             'source_execution_binding': context['execution_binding']}
    return {**proof, 'proof_sha256': artifacts.digest(proof),
            'rule': 'legacy v1 reuse only with exact retained source-evaluation configuration and binding'}

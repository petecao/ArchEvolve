"""Outcome-free, immutable campaign estimates and an append-only timing-access ledger.

Created 2026-10-06 ET (ticket16). A structural unknown is a recorded estimate,
never an agreement sample. Functional trial-lambda observations do not prove a
complete-call MMIO or native-driver bridge. Timing remains the selection input.
"""
import copy
import json
import os
from pathlib import Path

from swdb import artifacts, workflow, writer
from swdb.cli import Failure
from swdb.problems import Problem
from swdb.store import Store

FORMAT = 'swdb.extensa-paired-estimate.v1'
LEDGER = 'swdb.extensa-pairing-ledger.v1'
VERSION = 'swdb.extensa-pairing.v1'
PAYLOAD = ('format', 'mode', 'campaign', 'basis', 'estimator_variant', 'estimator_version',
           'estimator_sha256', 'policy_sha256', 'timing_context', 'context_sha256',
           'estimated_at', 'seconds', 'state', 'structural_missing', 'evidence_kind',
           'eligible_for_agreement')


def identity(data):
    return artifacts.digest({key: data[key] for key in PAYLOAD})


def validate_record(record, ctx):
    data = record.data
    if identity(data) != data['identity_sha256'] or not data['id'].endswith('.' + identity(data)[:16]):
        yield Problem(record.rel, 'identity_sha256', 'paired estimate immutable payload/hash differs')
    if artifacts.digest(data['timing_context']) != data['context_sha256']:
        yield Problem(record.rel, 'context_sha256', 'paired estimate timing context/hash differs')
    if data['state'] == 'unknown' and (data['seconds'] is not None or not data['structural_missing']):
        yield Problem(record.rel, 'seconds', 'unknown estimate requires null seconds and a structural reason')
    if data['seconds'] is not None and data['evidence_kind'] != 'contract_fixture':
        yield Problem(record.rel, 'seconds', 'no verified complete-call application timing adapter is registered')
    if data['state'] == 'fixture_estimate' and data['seconds'] is None:
        yield Problem(record.rel, 'seconds', 'fixture estimate requires its synthetic estimated seconds')


class PairingLedger:
    """Persist estimates before opening any outcome-bearing evaluator route.

    Every context contains only source/input/configuration facts supplied before
    execution. No evaluation, profile, comparison or timing value enters a model.
    The portable implementation digest and configuration are frozen across resume.
    """
    def __init__(self, campaign, store_dir, folder, *, fixture_model=None):
        self.campaign, self.store_dir = campaign, Path(store_dir)
        self.folder = Path(folder) / 'pairing'
        self.fixture_model = copy.deepcopy(fixture_model)
        self.enabled = campaign.get('paired_estimates', {}).get('enabled', True)

    def _policy(self):
        from swdb.estimate_protocol import estimator_identity
        value = {'format': LEDGER, 'campaign': self.campaign['id'], 'version': VERSION,
                 'estimator_sha256': estimator_identity(), 'enabled': self.enabled,
                 'configuration': copy.deepcopy(self.campaign.get('paired_estimates', {})),
                 'fixture_model': self.fixture_model}
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / 'policy.json'
        if path.exists():
            if json.loads(path.read_text()) != value:
                raise Failure('paired estimate implementation/configuration changed after freeze; start a fresh campaign')
        else:
            with path.open('x') as stream:
                json.dump(value, stream, sort_keys=True, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
        return value

    def _context(self, store, request):
        candidate = store.get(request['candidate'], 'candidate')
        workload = store.get(request['workload']['id'], 'workload')
        if candidate is None or workload is None:
            raise Failure('paired estimate requires its actual candidate and registered workload')
        definition = workload['definition']
        # Preserve exact representation hashes and canonical graph identity, never
        # substitute equal vertex/edge totals for the registered graph.
        input_facts = {key: copy.deepcopy(definition[key]) for key in
                       ('canonical_sha256', 'canonical_format', 'normalization', 'sources', 'source_policy')
                       if key in definition}
        input_facts['representations'] = [{key: row[key] for key in
            ('id', 'sha256', 'format', 'application', 'canonical_sha256', 'adjacency_verified') if key in row}
            for row in definition.get('representations', [])]
        execution = {key: copy.deepcopy(value) for key, value in request.items()
                     if key not in {'id', 'message_version', 'candidate', 'workload', 'budget', 'build_directory'}}
        execution['target'] = self.campaign['target']
        execution.setdefault('roi', self.campaign['protocol']['roi'])
        execution.setdefault('threads', self.campaign['protocol']['threads'])
        execution.setdefault('sources', list(self.campaign['protocol']['sources']))
        execution.setdefault('repetitions', self.campaign['protocol']['repetitions'])
        return {'subject': {'id': candidate['id'], 'artifact_sha256': candidate['artifact']['sha256']},
                'input': {'id': workload['id'], 'identity_sha256': workload['identity_sha256'], **input_facts},
                'execution': execution}

    def freeze(self, requests):
        if not self.enabled:
            return []
        policy = self._policy()
        store, result = Store(self.store_dir), []
        for request in requests:
            context = self._context(store, request)
            digest = artifacts.digest(context)
            existing = [r.data for r in store.of_kind('paired_estimate')
                        if r.data['context_sha256'] == digest and r.data['campaign'] == self.campaign['id']]
            if existing:
                if len(existing) != 1 or existing[0]['policy_sha256'] != artifacts.digest(policy):
                    raise Failure('paired estimate context has ambiguous or changed frozen policy')
                result.append(existing[0]['id'])
                continue
            seconds, state, missing = None, 'unknown', [
                'exact_registered_graph_complete_call_count_binding',
                'counted_backend_build_runtime_correspondence',
                'complete_required_mechanisms_and_composition',
                'prospective_artifact_input_configuration_freshness']
            evidence = 'contract_fixture' if request.get('fixture') else 'execution'
            if evidence == 'contract_fixture' and self.fixture_model is not None:
                # Explicit synthetic work/rate premise, separate from fixture timings.
                role = 'baseline' if request['candidate'] in {b['candidate'] for b in self.campaign['baselines']} else 'candidate'
                seconds = self.fixture_model['work_units'][role] / self.fixture_model['units_per_second']
                state, missing = 'fixture_estimate', ['contract_fixture_never_application_agreement']
            if self.campaign['target'] == 'dx100_gem5':
                missing.append('functional_trial_lambda_to_mmio_complete_call_bridge')
            data = workflow.record('paired_estimate', self.campaign['id'] + '.paired', format=FORMAT,
                mode='extensa', campaign=self.campaign['id'], basis='estimated', estimator_variant='research',
                estimator_version=VERSION, estimator_sha256=policy['estimator_sha256'],
                policy_sha256=artifacts.digest(policy), timing_context=context, context_sha256=digest,
                estimated_at=writer.now(), seconds=seconds, state=state, structural_missing=missing,
                evidence_kind=evidence, eligible_for_agreement=False)
            data['identity_sha256'] = identity(data)
            data['id'] += '.' + data['identity_sha256'][:16]
            workflow.persist(self.store_dir, data, create=True)
            store = Store(self.store_dir)
            result.append(data['id'])
        return result

    def before(self, stage, requests):
        """Durably retain the boundary before the caller reads or starts timing."""
        if not self.enabled:
            return []
        refs = self.freeze(requests)
        event = {'stage': stage, 'paired_estimates': refs, 'outcome_access_started_at': writer.now()}
        with (self.folder / 'outcome-accesses.jsonl').open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        return refs

    def summary(self):
        records = [r.data for r in Store(self.store_dir).of_kind('paired_estimate')
                   if r.data['campaign'] == self.campaign['id']]
        path = self.folder / 'outcome-accesses.jsonl'
        events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        by_id = {row['id']: row for row in records}
        for event in events:
            if not event['paired_estimates'] or any(rid not in by_id or
                    by_id[rid]['estimated_at'] >= event['outcome_access_started_at'] for rid in event['paired_estimates']):
                raise Failure('campaign outcome access lacks a preceding immutable paired estimate')
        return {'format': LEDGER, 'enabled': self.enabled, 'records': records, 'outcome_accesses': events,
                'eligible_application_estimates': 0,
                'selection_policy': 'unchanged_timing_only'}

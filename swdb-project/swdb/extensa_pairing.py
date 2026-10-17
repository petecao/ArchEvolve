"""Outcome-free, immutable campaign estimates and an append-only timing-access ledger.

Created 2026-10-06 ET (ticket16). A structural unknown is a recorded estimate,
never an agreement sample. Functional trial-lambda observations do not prove a
complete-call MMIO or native-driver bridge. Timing remains the selection input.
Updated: 2026-10-09 23:20 ET (review F6/F7): optional `paired_range` label (D29);
an enabled ledger must show a preceding outcome access for every timed candidate
comparison and every per-class baseline evaluation in its summary.
"""
import copy
from datetime import datetime
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
# Prospective metadata coverage only. Never an executable/timed forecast.
ARTIFACT_SCOPE = 'artifact_before_certification'
ARTIFACT_SETTINGS = ('target', 'roi', 'threads', 'repetitions', 'sources', 'workloads')
ARTIFACT_EXECUTION = frozenset({'observation_scope', 'backend', 'protocol',
    'protocol_identity_sha256', 'protocol_settings_sha256', 'protocol_context',
    'selected_input', 'target', 'roi', 'threads', 'sources', 'repetitions'})
ARTIFACT_MISSING = ('artifact_metadata_not_complete_timing_request',
    'functional_certification_not_admitted_for_artifact_forecast')
PAYLOAD = ('format', 'mode', 'campaign', 'basis', 'estimator_variant', 'estimator_version',
           'estimator_sha256', 'policy_sha256', 'timing_context', 'context_sha256',
           'estimated_at', 'seconds', 'state', 'structural_missing', 'evidence_kind',
           'eligible_for_agreement')
# 2026-10-09 ET (review F6, D29): optional and hashed only when present, so earlier
# receipts keep their identity. The campaign loop never sets it: a paired estimate's
# input is the graph its own campaign times. `beyond_paired_range` marks an estimate
# for a graph beyond gem5's sizes; agreement reports never count it.
OPTIONAL_PAYLOAD = ('paired_range',)


def identity(data):
    return artifacts.digest({key: data[key] for key in PAYLOAD + OPTIONAL_PAYLOAD
                             if key in PAYLOAD or key in data})


def request_identity(context):
    """Match record aliases of the same outcome-free observation request.

    Keep the actual context in the receipt/event. Only subject record names and
    a guest build's output name/path may differ; guest executable bytes and every
    compiler/backend/input/configuration fact must remain equal. This reuses an
    unknown forecast, never functional/MMIO counts or an application estimate.
    """
    facts = copy.deepcopy(context)
    facts.pop('prior_outcome_exposure', None)
    facts['subject'].pop('id', None)
    execution = facts['execution']
    binary, build = execution.get('binary', {}), execution.get('timing_policy', {}).get('build', {})
    if (binary.get('sha256') and binary.get('sha256') == build.get('binary_sha256') and
            all(key in build for key in ('compiler', 'compiler_version', 'flags', 'adapter'))):
        execution.pop('candidate_build', None)
        binary.pop('path', None)
    return artifacts.digest(facts)


def artifact_only(row):
    return row['timing_context']['execution'].get('observation_scope') == ARTIFACT_SCOPE


def artifact_problems(data):
    """Closed metadata projection; an original request/build is still unresolved."""
    execution = data['timing_context']['execution']
    if 'observation_scope' not in execution:
        return  # Historical complete timing-request receipts remain unchanged.
    if (execution.get('observation_scope') != ARTIFACT_SCOPE or set(execution) != ARTIFACT_EXECUTION
            or execution.get('backend') != 'source_metadata_only' or execution.get('selected_input') != {}):
        yield 'artifact forecast has an invalid closed observation scope'
        return
    projection = execution.get('protocol_context')
    if not isinstance(projection, dict) or set(projection) != set(ARTIFACT_SETTINGS):
        yield 'artifact forecast has an invalid closed campaign metadata projection'
        return
    if any(projection[key] != execution[key] for key in ('target', 'roi', 'threads', 'sources', 'repetitions')):
        yield 'artifact forecast scope differs from its campaign metadata projection'
    if data['timing_context']['input']['id'] not in projection['workloads'].values():
        yield 'artifact forecast input is outside its campaign metadata projection'
    if (data['state'] != 'unknown' or data['seconds'] is not None
            or data['eligible_for_agreement'] is not False
            or not set(ARTIFACT_MISSING) <= set(data['structural_missing'])):
        yield 'artifact forecast must remain unknown, null and ineligible with its missing proof'


def validate_record(record, ctx):
    data = record.data
    for issue in artifact_problems(data):
        yield Problem(record.rel, 'timing_context', issue)
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
    try:
        _time(data['estimated_at'])
    except (ValueError, TypeError):
        yield Problem(record.rel, 'estimated_at', 'paired estimate timestamp must declare UTC')


def _time(value):
    value = datetime.fromisoformat(value)
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ValueError('pairing timestamps must declare UTC')
    return value


def ledger_problems(ledger, campaign):
    """Validate a self-contained copied ledger, without reopening raw timing files."""
    rows = ledger['records']
    by_id = {row['id']: row for row in rows}
    if len(by_id) != len(rows):
        yield 'records contain duplicate paired estimate IDs'
    if not ledger['enabled'] and (rows or ledger['outcome_accesses']):
        yield 'disabled legacy pairing cannot carry paired evidence'
    for row in rows:
        if row['campaign'] != campaign or row['mode'] != 'extensa':
            yield 'record belongs to a different campaign/mode'
        if identity(row) != row['identity_sha256'] or not row['id'].endswith('.' + identity(row)[:16]):
            yield 'embedded paired estimate immutable payload/hash differs'
        if artifacts.digest(row['timing_context']) != row['context_sha256']:
            yield 'embedded paired estimate context/hash differs'
        try:
            _time(row['estimated_at'])
        except (ValueError, TypeError):
            yield 'embedded estimate timestamp is not UTC'
    for event in ledger['outcome_accesses']:
        if any(rid in by_id and artifact_only(by_id[rid]) for rid in event['paired_estimates']):
            yield 'artifact-only forecast cannot authorize an outcome access'
        contexts = event.get('timing_contexts')
        if contexts is not None and (len(contexts) != len(event['paired_estimates']) or any(
                rid not in by_id or request_identity(context) != request_identity(by_id[rid]['timing_context'])
                for context, rid in zip(contexts, event['paired_estimates']))):
            yield 'outcome request differs from the preceding immutable artifact/input/build/policy estimate'
        try:
            started = _time(event['outcome_access_started_at'])
            if not event['paired_estimates'] or any(rid not in by_id or
                    _time(by_id[rid]['estimated_at']) >= started for rid in event['paired_estimates']):
                yield 'outcome access lacks a preceding immutable paired estimate'
        except (ValueError, TypeError):
            yield 'outcome access timestamp is not UTC'


def validate_summary(record, ctx):
    if 'paired_estimates' not in record.data:
        return  # Historical campaign summaries remain valid.
    ledger = record.data['paired_estimates']
    from swdb.schemas import SchemaSet
    from swdb import paths
    validator = SchemaSet(paths.SCHEMAS, ctx.vocabs).for_kind('paired_estimate')
    malformed = False
    for i, row in enumerate(ledger['records']):
        errors = list(validator.iter_errors(row))
        for error in errors:
            malformed = True
            yield Problem(record.rel, f'paired_estimates.records[{i}]', error.message)
        if not errors:
            from swdb.store import Record
            yield from validate_record(Record(record.rel, row), ctx)
    if not malformed:
        protocol = record.data.get('protocol') or {}
        for row in ledger['records']:
            if not artifact_only(row):
                continue
            execution = row['timing_context']['execution']
            settings = protocol.get('settings') or {}
            projection = {key: settings[key] for key in ARTIFACT_SETTINGS if key in settings}
            if (execution['protocol'] != protocol.get('id')
                    or execution['protocol_identity_sha256'] != protocol.get('identity_sha256')
                    or execution['protocol_settings_sha256'] != artifacts.digest(settings)
                    or execution['protocol_context'] != projection):
                yield Problem(record.rel, 'paired_estimates',
                              'artifact forecast differs from the original frozen campaign metadata')
        for problem in ledger_problems(ledger, record.data['campaign']):
            yield Problem(record.rel, 'paired_estimates', problem)
        for problem in coverage_problems(record.data):
            yield Problem(record.rel, 'paired_estimates', problem)


def coverage_problems(summary):
    """Every timing in an enabled ledger's summary needs a recorded preceding access.

    Review F7 (2026-10-09 ET): ledger_problems checks only the events that exist,
    so deleting an event used to leave a valid summary with an unestimated timing.
    An access names its timing contexts and the preceding estimates; either binds
    the subject and input. Disabled legacy ledgers carry no paired evidence.
    """
    ledger = summary['paired_estimates']
    if not ledger.get('enabled', True):
        return
    rows = {row['id']: row for row in ledger.get('records', [])}
    contexts = [context for event in ledger.get('outcome_accesses', [])
                for context in (event.get('timing_contexts') or [])]
    contexts += [rows[rid]['timing_context'] for event in ledger.get('outcome_accesses', [])
                 for rid in event.get('paired_estimates', []) if rid in rows]
    artifacts_seen = {(c['subject']['artifact_sha256'], c['input']['id']) for c in contexts}
    subjects_seen = {(c['subject']['id'], c['input']['id']) for c in contexts}
    workloads = {row['class']: row['workload'] for row in summary.get('workload_classes', [])}
    for iteration in summary.get('iterations', []):
        for candidate in iteration.get('candidates', []):
            if candidate.get('comparisons') and (candidate.get('artifact_sha256'),
                                                 workloads.get(candidate.get('class'))) not in artifacts_seen:
                yield (f"timed candidate {candidate.get('id')} has no recorded outcome access preceded "
                       "by its paired estimate")
    for baseline in summary.get('baselines', []):
        for cls, evaluation in (baseline.get('evaluation_ids_by_class') or {}).items():
            if evaluation and (baseline.get('candidate'), workloads.get(cls)) not in subjects_seen:
                yield (f"baseline {baseline.get('candidate')} evaluation {evaluation} has no recorded "
                       "outcome access preceded by its paired estimate")


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

    def verify_resume(self, state):
        if not self.enabled:
            return
        had_outcomes = bool(state.get('pilot') or state.get('baselines') or
            any(candidate.get('comparisons') for iteration in state.get('iterations', [])
                for candidate in iteration.get('candidates', [])))
        if had_outcomes and (not (self.folder / 'policy.json').is_file() or
                             not (self.folder / 'outcome-accesses.jsonl').is_file()):
            raise Failure('paired estimate history is missing for prior pilot/shared-baseline outcomes; start a fresh campaign')
        self._policy()  # Refuse implementation/configuration drift before any provider/outcome access.
        if had_outcomes:
            value = self.summary()
            if not value['records'] or not value['outcome_accesses']:
                raise Failure('paired estimate history is empty for prior outcomes; start a fresh campaign')

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
        selected = {key: copy.deepcopy(value) for key, value in request['workload'].items() if key != 'id'}
        if isinstance(selected.get('representation'), dict):
            selected['representation'].pop('path', None)
        if request.get('observation_scope') == ARTIFACT_SCOPE:
            execution.pop('fixture', None)
        execution['selected_input'] = selected
        execution['target'] = self.campaign['target']
        execution.setdefault('roi', self.campaign['protocol']['roi'])
        execution.setdefault('threads', self.campaign['protocol']['threads'])
        execution.setdefault('sources', list(self.campaign['protocol']['sources']))
        execution.setdefault('repetitions', self.campaign['protocol']['repetitions'])
        return {'subject': {'id': candidate['id'], 'artifact_sha256': candidate['artifact']['sha256']},
                'input': {'id': workload['id'], 'identity_sha256': workload['identity_sha256'], **input_facts},
                'execution': execution}

    def freeze_artifacts(self, candidates, protocol, *, fixture=False):
        """Cover immutable artifacts before admission, without running their code.

        The protocol identity is the original freeze result, and the closed six
        fields are campaign metadata, not a binary/build/runtime correspondence.
        Actual before() requests retain their own later exact-context forecasts.
        """
        if not self.enabled:
            return []
        settings = protocol['settings']
        projection = {key: copy.deepcopy(settings[key]) for key in ARTIFACT_SETTINGS}
        from swdb.campaign import protocol_settings
        expected = protocol_settings(self.campaign)
        if projection != {key: expected[key] for key in ARTIFACT_SETTINGS}:
            raise Failure('artifact forecast requires original frozen campaign metadata')
        requests = [{'candidate': candidate, 'workload': {'id': row['workload']},
            'fixture': fixture, 'observation_scope': ARTIFACT_SCOPE,
            'backend': 'source_metadata_only', 'protocol': protocol['id'],
            'protocol_identity_sha256': protocol['identity_sha256'],
            'protocol_settings_sha256': artifacts.digest(settings),
            'protocol_context': copy.deepcopy(projection)}
            for candidate in candidates for row in self.campaign['workload_classes']]
        # fixture is record evidence classification, never part of execution scope.
        return self.freeze(requests)

    def freeze(self, requests):
        if not self.enabled:
            return []
        policy = self._policy()
        store, result, pending = Store(self.store_dir), [], []
        frozen = {request_identity(r.data['timing_context']): r.data for r in store.of_kind('paired_estimate')
                  if r.data['campaign'] == self.campaign['id']}
        for request in requests:
            context = self._context(store, request)
            key = request_identity(context)
            existing = frozen.get(key)
            if existing:
                if existing['policy_sha256'] != artifacts.digest(policy):
                    raise Failure('paired estimate context has ambiguous or changed frozen policy')
                result.append(existing['id'])
                continue
            seconds, state, missing = None, 'unknown', [
                'exact_registered_graph_complete_call_count_binding',
                'counted_backend_build_runtime_correspondence',
                'complete_required_mechanisms_and_composition',
                'prospective_artifact_input_configuration_freshness']
            evidence = 'contract_fixture' if request.get('fixture') else 'execution'
            is_artifact = request.get('observation_scope') == ARTIFACT_SCOPE
            if is_artifact:
                missing.extend(ARTIFACT_MISSING)
            if not is_artifact and evidence == 'contract_fixture' and self.fixture_model is not None:
                # Explicit synthetic work/rate premise, separate from fixture timings.
                role = 'baseline' if request['candidate'] in {b['candidate'] for b in self.campaign['baselines']} else 'candidate'
                seconds = self.fixture_model['work_units'][role] / self.fixture_model['units_per_second']
                state, missing = 'fixture_estimate', ['contract_fixture_never_application_agreement']
            if self.campaign['target'] == 'dx100_gem5':
                missing.append('functional_trial_lambda_to_mmio_complete_call_bridge')
            exposure = self._prior_exposure(store, context['subject']['artifact_sha256'])
            if exposure:
                context['prior_outcome_exposure'] = exposure
                missing.append('prior_artifact_outcome_access_not_fresh_by_record_name')
            digest = artifacts.digest(context)
            data = workflow.record('paired_estimate', self.campaign['id'] + '.paired', format=FORMAT,
                mode='extensa', campaign=self.campaign['id'], basis='estimated', estimator_variant='research',
                estimator_version=VERSION, estimator_sha256=policy['estimator_sha256'],
                policy_sha256=artifacts.digest(policy), timing_context=context, context_sha256=digest,
                estimated_at=writer.now(), seconds=seconds, state=state, structural_missing=missing,
                evidence_kind=evidence, eligible_for_agreement=False)
            data['identity_sha256'] = identity(data)
            data['id'] += '.' + data['identity_sha256'][:16]
            pending.append(data)
            frozen[key] = data
            result.append(data['id'])
        if pending:
            # One transaction validates all contexts before the first outcome,
            # avoiding repeated catalog validation while pre-freezing a population.
            from swdb import db
            writer.commit(self.store_dir, new=pending)
            db.build(self.store_dir, db.default_path(self.store_dir))
        return result

    def _prior_exposure(self, store, artifact_sha256):
        """Read retained identity/access metadata only, never any duration/ratio.

        Prior artifact access is a conservative disclosure, not proof that a new
        artifact+input+configuration tuple is fresh. Unindexed raw history remains
        unverified; every real estimate is still structurally unknown/ineligible.
        """
        result = []
        for record in store.of_kind('evaluation'):
            data = record.data
            if not data.get('timing'):
                continue  # Compile-only records have no timing observations.
            candidate = store.get(data.get('candidate'), 'candidate')
            sha = data.get('context', {}).get('candidate_sha256')
            if sha is None and candidate is not None:
                sha = candidate['artifact']['sha256']
            if sha == artifact_sha256:
                result.append({'record': data['id'], 'scope': 'prior_artifact_timing_record_metadata'})
        path = self.folder / 'outcome-accesses.jsonl'
        if path.exists():
            rows = {r.id: r.data for r in store.of_kind('paired_estimate')}
            for event in (json.loads(line) for line in path.read_text().splitlines()):
                for rid in event['paired_estimates']:
                    row = rows.get(rid)
                    if row and row['timing_context']['subject']['artifact_sha256'] == artifact_sha256:
                        result.append({'record': rid, 'stage': event['stage'],
                                       'scope': 'prior_artifact_outcome_access_boundary'})
        return sorted({json.dumps(row, sort_keys=True): row for row in result}.values(),
                      key=lambda row: json.dumps(row, sort_keys=True))

    def before(self, stage, requests):
        """Durably retain the boundary before the caller reads or starts timing."""
        if not self.enabled:
            return []
        if any('observation_scope' in request for request in requests):
            raise Failure('artifact-only forecast cannot authorize an outcome access')
        refs = self.freeze(requests)
        store = Store(self.store_dir)
        event = {'stage': stage, 'paired_estimates': refs,
                 'timing_contexts': [self._context(store, request) for request in requests],
                 'outcome_access_started_at': writer.now()}
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
        value = {'format': LEDGER, 'enabled': self.enabled, 'records': records, 'outcome_accesses': events,
                 'eligible_application_estimates': 0, 'selection_policy': 'unchanged_timing_only'}
        problems = list(ledger_problems(value, self.campaign['id']))
        if problems:
            raise Failure('paired estimate ledger refuses continuation: ' + '; '.join(problems))
        return value

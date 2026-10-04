"""Typed library validation and evidence-derived state. Updated: 2026-10-03 ET.

Normative YAML and code pins never carry review or certification state. Since
ticket 46 (BC reuses the BFS contract), entries have a JSON schema
(``schemas/library/library_entry.schema.json``) and SQLite tables built by
``swdb.db``; the YAML stays authoritative.
"""
import yaml
import re

from jsonschema import Draft202012Validator
from pathlib import Path

from swdb import artifacts, paths, yamlio
from swdb.problems import Problem

KINDS = {'intrinsic': 'intrinsics', 'lowering': 'lowerings',
         'library_operation': 'library_operations', 'rewrite_contract': 'rewrite_contracts'}
PREFIXES = {'intrinsic': 'intrinsic.', 'lowering': 'lowering.',
            'library_operation': 'operation.', 'rewrite_contract': 'contract.'}
TEST_MODES = {'runtime_guard', 'static_assertion', 'structural', 'differential_test'}
DISCHARGE_MODES = TEST_MODES | {'observed_on_target', 'assumed', 'not_applicable', 'open'}
ROLES = {'precondition', 'postcondition', 'frame', 'legality', 'preservation'}
PROMOTION_REVIEWER = 'Yan-Ru Jhou'


def authorized_reviewer(name):
    """ADR 0007 assigns shared-library review to the project maintainer."""
    return isinstance(name, str) and name.strip().casefold() in {'yan-ru jhou', 'yanrujhou'}


SCHEMA = paths.HOME / 'schemas' / 'library' / 'library_entry.schema.json'
_VALIDATOR = []


def entry_validator():
    """The JSON-schema validator of one normative library entry (ticket 46)."""
    if not _VALIDATOR:
        import json
        schema = json.loads(SCHEMA.read_text())
        Draft202012Validator.check_schema(schema)
        _VALIDATOR.append(Draft202012Validator(schema))
    return _VALIDATOR[0]


def derived_from(data):
    """The contract ID a derived rewrite contract cites, or None (ticket 42, 2026-10-03 ET)."""
    citation = (data.get('provenance') or {}).get('derived_from') if isinstance(data.get('provenance'), dict) else None
    return citation.get('id') if isinstance(citation, dict) else None


def default_root(records=None):
    if records is None or Path(records).resolve() == paths.RECORDS.resolve():
        return paths.HOME / 'library'
    return Path(records).parent / 'library'


class Library:
    def __init__(self, root=None, store=None):
        self.root = Path(root or paths.HOME / 'library').resolve()
        self.store = store
        self.entries = {}
        self.files = {}
        self.problems = []
        for folder in KINDS.values():
            for path in sorted((self.root / folder).rglob('*.yaml')):
                try:
                    data = yamlio.load(path)
                    if not isinstance(data, dict) or not isinstance(data.get('id'), str):
                        raise ValueError('entry needs a mapping and text ID')
                    if data['id'] in self.entries:
                        raise ValueError(f"duplicate entry ID {data['id']}")
                    self.entries[data['id']] = data
                    self.files[data['id']] = path
                except (OSError, ValueError, yaml.YAMLError) as exc:
                    self.problems.append(Problem(str(path), '-', str(exc)))

    def get(self, entry_id):
        return self.entries.get(entry_id)

    def content_sha256(self, entry_id):
        data = self.get(entry_id)
        if data is None:
            raise ValueError(f'unknown library entry {entry_id}')
        return artifacts.digest(data)

    def dependency_pins(self, entry_id):
        """Bind every referenced normative entry, including nested dependencies.

        Intrinsic/lowering links form intentional cycles. Visit each entry once
        and omit the subject itself, whose hash is already in the receipt.
        """
        if self.get(entry_id) is None:
            raise ValueError(f'unknown library entry {entry_id}')
        seen = {entry_id}
        pending = [entry_id]
        while pending:
            data = self.get(pending.pop())
            kind = data['kind']
            if kind == 'lowering':
                references = [data['intrinsic']]
            elif kind == 'intrinsic':
                references = data.get('lowerings', [])
            else:
                references = data.get('uses_intrinsics', []) + data.get('uses_library_operations', [])
                # Ticket 42: a derived contract depends on the contract it cites.
                parent = derived_from(data)
                if parent:
                    references = references + [parent]
            for dependency in references:
                if self.get(dependency) is None:
                    raise ValueError(f'unknown library dependency {dependency}')
                if dependency not in seen:
                    seen.add(dependency)
                    pending.append(dependency)
        return [{'id': dependency, 'content_sha256': self.content_sha256(dependency)}
                for dependency in sorted(seen - {entry_id})]

    def current_certification(self, receipt):
        """Historical evidence cannot certify changed semantics or dependencies."""
        if not receipt or receipt.get('evidence_kind') != 'execution':
            return False
        try:
            entry_id = receipt['entry']['id']
            return (receipt['entry'] == {'id': entry_id, 'content_sha256': self.content_sha256(entry_id)}
                    and sorted(receipt.get('dependencies', []), key=lambda pin: pin['id'])
                    == self.dependency_pins(entry_id))
        except (KeyError, TypeError, ValueError):
            return False

    def resolve(self, location):
        """No symlinks or parent traversal may escape a declared reference root."""
        roots = {'library':self.root, 'project':paths.HOME, 'repository':paths.HOME.parent}
        base = roots.get(location.get('root','library'), self.root)
        if location.get('root', 'library') not in {'library', 'project', 'repository'}:
            raise ValueError('reference root must be library, project or repository')
        relative = Path(location['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('reference path must stay inside its declared root')
        target = (base / relative).resolve()
        if not target.is_relative_to(base.resolve()) or not target.is_file():
            raise ValueError(f'reference is missing or escapes root: {relative}')
        return target

    def _pin(self, pin):
        if not isinstance(pin, dict) or not re.fullmatch('[0-9a-f]{64}', str(pin.get('sha256', ''))):
            raise ValueError('pinned reference needs path and sha256')
        target = self.resolve(pin)
        if artifacts.file_hash(target) != pin['sha256']:
            raise ValueError(f"pinned reference sha256 differs: {pin.get('path')}")
        if pin.get('symbol') and pin['symbol'] not in target.read_text():
            raise ValueError(f"pinned symbol is absent: {pin['symbol']}")

    def validate(self):
        found = list(self.problems)
        for entry_id, data in self.entries.items():
            path = self.files[entry_id]
            def error(field, reason):
                found.append(Problem(str(path), field, reason))
            kind = data.get('kind')
            if not isinstance(kind,str) or kind not in KINDS:
                error('kind', 'unknown library entry kind')
                continue
            if not re.fullmatch('[a-z0-9][a-z0-9._-]*', entry_id) or not entry_id.startswith(PREFIXES[kind]):
                error('id', f'entry ID requires prefix {PREFIXES[kind]}')
            if not path.is_relative_to(self.root / KINDS[kind]):
                error('kind', 'entry is in the wrong kind folder')
            if self.store and entry_id in self.store.by_id:
                error('id', 'entry ID collides with a record ID')
            for prohibited in ('tier', 'status', 'certification_results', 'applications', 'content_sha256'):
                if prohibited in data:
                    error(prohibited, 'evidence state is derived from records, never normative entry content')
            required = {
                'intrinsic': ('intrinsic_record','signature','intent','reference_semantics','hardware_operations','memory_footprint','completion','lowerings'),
                'lowering': ('intrinsic','interface','location','code_sha256','build_defines','differential_test'),
                'library_operation': ('signature','intent','location','code_sha256','reference_semantics','uses_intrinsics','differential_test'),
                'rewrite_contract': ('pattern_key','strategies','uses_intrinsics','uses_library_operations','runtime_guards','knobs','preservation_obligations','correctness_check','execution_witness','negative_controls','requirement_map'),
            }[kind]
            for field in ('id','kind','provenance','clauses', *required):
                if field not in data:
                    error(field, 'required field is missing')
            # Ticket 46 (2026-10-03 ET): the entry shape is schemas/library/library_entry.schema.json.
            # Missing fields are reported above with their names, so 'required' errors are not repeated.
            type_errors = [problem for problem in entry_validator().iter_errors(data) if problem.validator != 'required']
            if type_errors:
                for problem in type_errors:
                    error('.'.join(map(str,problem.path)),problem.message)
                continue
            if not isinstance(data.get('provenance'), dict) or not data['provenance'].get('origin'):
                error('provenance', 'experimental origin is required')
            def check_pins(value, field):
                if isinstance(value, dict):
                    if 'path' in value and 'sha256' in value:
                        try:
                            self._pin(value)
                        except (KeyError, TypeError, ValueError, OSError) as exc:
                            error(field, str(exc))
                    for name, child in value.items():
                        check_pins(child, field+'.'+name)
                elif isinstance(value, list):
                    for index, child in enumerate(value):
                        check_pins(child, f'{field}[{index}]')
            check_pins(data.get('provenance', {}), 'provenance')
            clauses = data.get('clauses', [])
            if not isinstance(clauses, list):
                error('clauses', 'clauses must be a list')
                clauses = []
            ids = set()
            for i, clause in enumerate(clauses):
                where = f'clauses[{i}]'
                if not isinstance(clause, dict):
                    error(where, 'clause must be a mapping')
                    continue
                cid = clause.get('id')
                if not isinstance(cid, str) or not cid or cid in ids:
                    error(where+'.id', 'clause ID is required and unique')
                if isinstance(cid, str):
                    ids.add(cid)
                if clause.get('role') not in ROLES or not clause.get('statement'):
                    error(where, 'clause requires a valid role and natural-language statement')
                mode = clause.get('discharge_mode')
                if mode not in DISCHARGE_MODES:
                    error(where+'.discharge_mode', 'unknown discharge mode')
                control = clause.get('negative_control')
                if mode in TEST_MODES:
                    if not isinstance(control, dict) or not control.get('id') or not control.get('check'):
                        error(where+'.negative_control', 'test-discharged clauses require a named control and check')
                elif not isinstance(control, dict) or control.get('id') != 'none' or not control.get('reason'):
                    error(where+'.negative_control', 'non-test modes require none and a reason')
                if mode == 'assumed' and (not clause.get('owner') or not clause.get('evidence')):
                    error(where, 'assumed clauses require owner and evidence')
                formal = clause.get('formal')
                if formal is None:
                    if not clause.get('natural_language_only'):
                        error(where+'.formal', 'a clause without a formal half states why')
                    if 'formal_label' in clause:
                        error(where+'.formal_label', 'formal labels require a formal half')
                else:
                    if clause.get('formal_label') != 'stated':
                        error(where+'.formal_label', 'proven labels require a formal verifier; only stated is supported')
                    try:
                        if formal.get('language') == 'reference':
                            self._pin(formal['reference'])
                        elif formal.get('language') == 'extensa_predicate':
                            from swdb.predicate_grammar import parse
                            parse(formal['predicate'])
                        else:
                            raise ValueError('unknown formal language')
                    except (KeyError, TypeError, ValueError, OSError) as exc:
                        error(where+'.formal', str(exc))
            for key in ('reference_semantics',):
                if key in data:
                    try:
                        self._pin(data[key])
                    except (KeyError, TypeError, ValueError, OSError) as exc:
                        error(key, str(exc))
            if kind == 'library_operation':
                from swdb.library_operations import body_problems
                for field, reason in body_problems(self, data):
                    error(field, reason)
            if kind in {'lowering','library_operation'}:
                try:
                    self._pin({**data['location'], 'sha256': data['code_sha256']})
                    self._pin(data['differential_test'])
                except (KeyError, TypeError, ValueError, OSError) as exc:
                    error('location', str(exc))
            if kind == 'lowering':
                interface = data.get('interface')
                if not isinstance(interface, dict) or set(interface) != {'id','version'} or not all(isinstance(v,str) and v for v in interface.values()):
                    error('interface', 'hardware interface needs id and version')
                elif not path.is_relative_to(self.root / 'lowerings' / interface['id'] / interface['version']):
                    error('interface', 'lowering must be grouped under interface/version')
                if self.get(data.get('intrinsic')) is None:
                    error('intrinsic', 'unknown library intrinsic')
            if kind == 'intrinsic':
                if self.store and not self.store.get(data.get('intrinsic_record'),'intrinsic'):
                    error('intrinsic_record','unknown intrinsic record')
                for operation in data.get('hardware_operations',[]):
                    if self.store and not self.store.get(operation,'operation'):
                        error('hardware_operations','unknown hardware-operation record')
                for lower in data.get('lowerings', []):
                    if not self.get(lower) or self.get(lower).get('kind') != 'lowering' or self.get(lower).get('intrinsic') != entry_id:
                        error('lowerings', 'lowering must point back to this intrinsic')
            for field, expected_kind in (('uses_intrinsics','intrinsic'),('uses_library_operations','library_operation')):
                for dependency in data.get(field,[]):
                    if not self.get(dependency) or self.get(dependency).get('kind') != expected_kind:
                        error(field,f'unknown {expected_kind} dependency')
            for strategy in data.get('strategies',[]):
                if self.store and not self.store.get(strategy,'strategy'):
                    error('strategies','unknown strategy record')
            if kind == 'rewrite_contract':
                keys = data.get('pattern_key')
                if not isinstance(keys, list) or not keys:
                    error('pattern_key', 'requires one role-named pattern per matched access')
                else:
                    for pattern in keys:
                        if not isinstance(pattern, dict) or not pattern.get('roles') or not pattern.get('address_shapes') or not pattern.get('update_kind'):
                            error('pattern_key', 'patterns require roles, address_shapes and update_kind')
                        elif any(role not in {'index','offsets','target'} for role in pattern['roles']):
                            error('pattern_key', 'array roles must come from the array-role vocabulary')
                citation = data.get('provenance', {}).get('derived_from')
                if citation is not None:
                    parent = self.get(citation.get('id')) if isinstance(citation, dict) else None
                    if (not isinstance(citation, dict) or citation.get('id') == entry_id or parent is None
                            or parent.get('kind') != 'rewrite_contract'):
                        error('provenance.derived_from', 'a derived contract cites another existing rewrite contract')
                    elif citation.get('content_sha256') != self.content_sha256(citation['id']):
                        error('provenance.derived_from', 'cited contract content changed; re-derive and re-pin')
                    else:
                        parent_clauses = {c.get('id') for c in parent.get('clauses', []) if isinstance(c, dict)}
                        missing = parent_clauses - ids
                        if missing:
                            error('clauses', 'a derived contract keeps every cited clause ID: ' + ', '.join(sorted(missing)))
                controls = data.get('negative_controls', [])
                kinds = {c.get('kind') for c in controls if isinstance(c,dict)} if isinstance(controls,list) else set()
                if not {'overlapping_pointer','double_claim','dropped_operand'} <= kinds:
                    error('negative_controls', 'all three mandatory control kinds are required')
                legality_ids = {c.get('id') for c in clauses if c.get('role') == 'legality'}
                for knob in data.get('knobs', []):
                    if not isinstance(knob, dict) or knob.get('legality_clause') not in legality_ids or 'default' not in knob or not knob.get('origin'):
                        error('knobs', 'knob requires default, origin and a legality-clause binding')
                        continue
                    default, bounds = knob['default'], knob.get('range')
                    choices = bounds.get('choices') if isinstance(bounds,dict) else None
                    numeric = isinstance(bounds,dict) and all(type(bounds.get(key)) in (int,float) for key in ('min','max')) and type(default) in (int,float)
                    allowed = isinstance(choices,list) and default in choices
                    allowed = allowed or (numeric and bounds['min'] <= default <= bounds['max'])
                    allowed = allowed or (isinstance(bounds,dict) and default == 'build.tile_size' and bounds.get('upper_bound') == 'build.tile_size')
                    if not allowed:
                        error('knobs', 'default is outside its allowed range')
        return found

    def state(self, entry_id, store=None):
        store = store or self.store
        data = self.get(entry_id)
        if data is None:
            raise ValueError(f'unknown library entry {entry_id}')
        sha = self.content_sha256(entry_id)
        records = [r.data for r in store.records] if store else []
        relevant = [r for r in records if r.get('kind') == 'certification'
                    and r.get('entry', {}).get('id') == entry_id
                    and self.current_certification(r)]
        status = 'draft'
        if any(r.get('verdict') == 'failed' and any(c.get('status') == 'failed' for c in r.get('matrix',[])) for r in relevant):
            status = 'refuted'
        elif any(r.get('verdict') == 'certified' for r in relevant):
            status = 'certified'
        elif any(r.get('verdict') == 'inconclusive' for r in relevant):
            status = 'inconclusive'
        if data['kind'] == 'intrinsic':
            status = 'draft'
        if data['kind'] == 'intrinsic' and data.get('lowerings'):
            lower_states = [self.state(i,store)['status'] for i in data['lowerings']]
            if all(s in {'certified','evaluated_on_target'} for s in lower_states):
                status = 'certified'
            elif 'refuted' in lower_states:
                status = 'refuted'
        dependencies = data.get('lowerings',[]) if data['kind'] == 'intrinsic' else [entry_id]
        def current_review(review):
            if (review.get('kind') != 'review' or not authorized_reviewer(review.get('reviewer'))
                    or review.get('target') != {'id':entry_id,'content_sha256':sha}):
                return False
            evidence = [store.get(rid,'certification') for rid in review.get('evidence',[])] if store else []
            covered = {c['entry']['id'] for c in evidence if c and c.get('verdict') == 'certified'
                       and c['entry']['id'] in dependencies and self.current_certification(c)}
            return set(dependencies) <= covered
        tier = 'shared' if any(current_review(r) for r in records) else 'experimental'
        target_states = []
        for evaluation in records:
            if evaluation.get('kind') != 'evaluation' or not store:
                continue
            candidate = store.get(evaluation.get('candidate'),'candidate')
            proposal = store.get((candidate or {}).get('proposal'),'proposal')
            library = (proposal or {}).get('request',{}).get('library',{})
            cited = [library.get('contract',{})] + library.get('entries',[])
            if {'id':entry_id,'content_sha256':sha} not in cited:
                continue
            # Target executions also describe a fixed dependency closure. An
            # old proposal cannot establish target status for revised semantics.
            if any(pin not in cited for pin in self.dependency_pins(entry_id)):
                continue
            contract = self.get(library.get('contract',{}).get('id'))
            if (not contract or library.get('contract') != {
                    'id': contract['id'], 'content_sha256': self.content_sha256(contract['id'])}
                    or any(pin not in cited for pin in self.dependency_pins(contract['id']))):
                continue
            target_state = self._target_state(evaluation, candidate, contract, store)
            if target_state:
                target_states.append(target_state)
        if 'refuted' in target_states:
            status = 'refuted'
        elif status != 'refuted' and 'evaluated_on_target' in target_states:
            status = 'evaluated_on_target'
        elif status != 'refuted' and 'inconclusive' in target_states:
            status = 'inconclusive'
        return {'tier':tier,'status':status}

    def _target_state(self, evaluation, candidate, contract, store):
        """Only an entered target run can derive state. Updated: 2026-10-03 ET."""
        if contract is None or evaluation.get('component_evaluations'):
            # Aggregation copies its components' stages and checks; it does not
            # execute another guest. state() considers the actual component
            # records individually, using their own identities and custody.
            return None
        # Execution evidence also labels real compiler and collector processes.
        # A checkpoint starts a guest before its timed simulation; its history
        # must distinguish an incomplete attempt from compilation or collection.
        stages = {stage.get('stage') for stage in evaluation.get('stages', [])}
        entered_run = bool(stages & {'simulation', 'execution'})
        if not entered_run and 'checkpoint' not in stages:
            return None
        context = evaluation.get('context',{})
        target = store.get(context.get('target'), 'hardware_target')
        if not target or context.get('backend') != target.get('backend',{}).get('id') or evaluation.get('evidence_kind') != 'execution':
            return None
        if context.get('candidate_sha256') != (candidate or {}).get('artifact',{}).get('sha256'):
            return None
        for intrinsic_id in (contract or {}).get('uses_intrinsics',[]):
            intrinsic = self.get(intrinsic_id)
            if not intrinsic or not any(self.get(lower_id).get('interface') == target.get('interface') for lower_id in intrinsic.get('lowerings',[]) if self.get(lower_id)):
                return None
        if not entered_run:
            # A checkpoint alone cannot satisfy or refute the timed witness,
            # even when guest startup finishes; the target run is still pending.
            return 'inconclusive'
        correctness = evaluation.get('correctness',{})
        checks = correctness.get('checks',[])
        if correctness.get('state') == 'failed' or any(c.get('parent_gather_race',{}).get('outcome') == 'refuted' for c in checks):
            return 'refuted'
        if evaluation.get('outcome',{}).get('state') != 'complete':
            return 'inconclusive'
        witness = (contract or {}).get('execution_witness',{}).get('gem5',{}).get('case')
        completed = checks and all(c.get('passed') is True and c.get('continuation',{}).get('normal_exit_observed') is True for c in checks)
        # Ticket 39 (2026-10-03 ET): every kernel plug-in's witness checker is v2.
        from swdb import kernels
        WITNESSED = kernels.witness_checkers()
        v2 = (context.get('verifier') in WITNESSED
              or context.get('adapter') == 'dx100.complete_call.v2'
              or evaluation.get('request', {}).get('verification', {}).get('checker') in WITNESSED
              or evaluation.get('build', {}).get('adapter') == 'dx100.complete_call.v2'
              or any(c.get('checker') in WITNESSED or c.get('verifier') in WITNESSED
                     or c.get('continuation', {}).get('checker') in WITNESSED
                     or 'exit_witness' in c.get('continuation', {}) for c in checks))
        if v2:
            from swdb.cli import Failure
            # A bounded simulator continuation can prove guest exit. Require
            # its authoritative v2 validation, never an unbound completion flag
            # or a fallback to legacy normal-exit metadata after rejection.
            try:
                plugin = kernels.by_gem5_checker(context.get('verifier')) or kernels.BFS
                plugin.validate_record_witness(evaluation, store=store)
                completed = True
            except Failure:
                completed = False
        witnessed = witness and all(c.get('coverage',{}).get(witness,{}).get('state') == 'observed' for c in checks)
        if correctness.get('state') == 'passed' and completed and witnessed:
            return 'evaluated_on_target'
        # A completed run has had its opportunity to satisfy the required
        # witness. Missing or failed checks refute that execution; only an
        # unfinished run remains inconclusive. state() preserves this result
        # even when another execution supplies a positive witness.
        return 'refuted'


def promote(args):
    """Record review without rewriting normative entries. Created: 2026-10-03."""
    import datetime
    import uuid
    from swdb import writer
    from swdb.store import Store
    from swdb.cli import Failure
    if not authorized_reviewer(args.reviewer):
        raise Failure(f'promotion requires the designated reviewer {PROMOTION_REVIEWER}')
    store = Store(args.records)
    library = Library(args.library or paths.HOME / 'library', store)
    issues = library.validate()
    if issues:
        raise Failure('library validation failed: ' + '; '.join(str(p) for p in issues[:5]))
    if library.get(args.id) is None:
        raise Failure(f'unknown library entry {args.id}')
    state = library.state(args.id)
    if state['status'] not in {'certified','evaluated_on_target'}:
        raise Failure(f"promotion requires certification for current content; status is {state['status']}")
    sha = library.content_sha256(args.id)
    entry_ids = [args.id]
    if library.get(args.id)['kind'] == 'intrinsic':
        entry_ids = library.get(args.id)['lowerings']
    evidence = [r.id for r in store.of_kind('certification')
                if r.data.get('entry',{}).get('id') in entry_ids
                and r.data.get('verdict') == 'certified'
                and library.current_certification(r.data)]
    if not evidence:
        raise Failure('no current passing certification receipt')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {'kind':'review','schema_version':'0.4','id':f'review.{args.id}.{uuid.uuid4().hex[:12]}',
              'status':'reviewed','created':writer.today(),'updated':writer.today(),
              'provenance':[{'id':'review','kind':'human_report','description':f'Review recorded by {args.reviewer} through swdb promote.','uri':None}],
              'target':{'id':args.id,'content_sha256':sha},'reviewer':PROMOTION_REVIEWER,'reviewed_at':now,'evidence':evidence}
    writer.commit(args.records,new=[record])
    return record


def proposal_gate(request, store):
    """Require current shared evidence for every normative proposal pin."""
    from swdb.cli import Failure
    section = request.get('library')
    if section is None:
        return None
    library = Library(default_root(store.dir), store)
    issues = library.validate()
    if issues:
        raise Failure('library validation failed: ' + '; '.join(str(p) for p in issues[:5]))
    pins = [section['contract']] + section['entries']
    ids = [pin['id'] for pin in pins]
    if len(ids) != len(set(ids)):
        raise Failure('library section repeats an entry ID')
    for pin in pins:
        entry = library.get(pin['id'])
        if entry is None or library.content_sha256(pin['id']) != pin['content_sha256']:
            raise Failure(f"stale or missing library entry {pin['id']}")
        state = library.state(pin['id'])
        if state['tier'] != 'shared' or state['status'] not in {'certified','evaluated_on_target'}:
            raise Failure(f"ArchEvolve submit requires shared certified library entry {pin['id']}; found {state}")
    contract = library.get(section['contract']['id'])
    if contract['kind'] != 'rewrite_contract':
        raise Failure('library contract pin must identify a rewrite contract')
    required = {pin['id'] for pin in library.dependency_pins(contract['id'])}
    if not required <= set(ids):
        raise Failure('library section omits a contract dependency: '+', '.join(sorted(required-set(ids))))
    editable = set(request['constraints']['editable_files'])
    shipped = section['shipped_files']
    names = [row['path'] for row in shipped]
    if len(names) != len(set(names)):
        raise Failure('shipped library files repeat a path')
    for row in shipped:
        if row['path'] not in editable or not row['lowerings']:
            raise Failure('shipped file requires an exact editable path and lowering IDs')
        for lower_id in row['lowerings']:
            lower = library.get(lower_id)
            if lower_id not in ids or lower is None or lower['kind'] != 'lowering':
                raise Failure('shipped file names an uncited lowering')
            if lower['code_sha256'] != row['sha256']:
                raise Failure('shipped header sha256 differs from certified lowering')
    return library


def check_shipped_files(request, store, source, candidate):
    from swdb.cli import Failure
    if 'library' not in request:
        return
    library = proposal_gate(request, store)
    before = {row['path']:row for row in source['files']}
    after = {row['path']:row for row in candidate['files']}
    shipped = {row['path']:row for row in request['library']['shipped_files']}
    if set(after)-set(before) != set(shipped):
        raise Failure('library patch may add only its declared lowering files')
    for path,row in shipped.items():
        if path not in after or after[path]['sha256'] != row['sha256']:
            raise Failure(f'shipped header bytes differ from certified content: {path}')
        for lower_id in row['lowerings']:
            if artifacts.file_hash(library.resolve(library.get(lower_id)['location'])) != after[path]['sha256']:
                raise Failure('canonical lowering header differs from shipped bytes')


def validate_record(record, ctx):
    """Prevent contradictory receipts from granting certification or promotion."""
    data = record.data
    if record.kind == 'certification' and data['verdict'] == 'certified':
        if not data['matrix'] or not all(cell.get('status') == 'passed' for cell in data['matrix']):
            yield Problem(record.rel,'verdict','certified requires every positive matrix cell to pass')
        if not data['negative_controls'] or not all(control.get('status') == 'rejected' for control in data['negative_controls']):
            yield Problem(record.rel,'verdict','certified requires every negative control to build and fail a named check')
        candidate = data.get('candidate')
        if candidate and (candidate.get('contract') != data['entry']['id'] or candidate.get('contract_sha256') != data['entry']['content_sha256'] or not re.fullmatch('[0-9a-f]{64}', str(candidate.get('tree_sha256','')))):
            yield Problem(record.rel,'candidate','candidate certification requires exact contract and tree pins')
    elif record.kind == 'review':
        for index, rid in enumerate(data['evidence']):
            certification = ctx.store.get(rid, 'certification')
            if not certification or certification.get('verdict') != 'certified' or certification.get('evidence_kind') != 'execution':
                yield Problem(record.rel,f'evidence[{index}]','review evidence requires passing execution certification')
        library = Library(default_root(ctx.store.dir), ctx.store)
        target = library.get(data['target']['id'])
        if target:
            if not authorized_reviewer(data.get('reviewer')):
                yield Problem(record.rel,'reviewer',f'shared library review requires {PROMOTION_REVIEWER}')
            if library.content_sha256(target['id']) != data['target']['content_sha256']:
                # Historical review records remain valid when normative content changes.
                return
            candidates = [ctx.store.get(rid,'certification') for rid in data['evidence']]
            dependencies = target.get('lowerings',[]) if target['kind'] == 'intrinsic' else [target['id']]
            # A lowering may change while its intrinsic's normative content stays
            # unchanged. Keep that old review valid as history; state checks its
            # dependency hashes before granting the current shared tier.
            covered = {c['entry']['id'] for c in candidates if c and c['entry']['id'] in dependencies}
            if not set(dependencies) <= covered:
                yield Problem(record.rel,'evidence','review does not identify entry certification dependencies')

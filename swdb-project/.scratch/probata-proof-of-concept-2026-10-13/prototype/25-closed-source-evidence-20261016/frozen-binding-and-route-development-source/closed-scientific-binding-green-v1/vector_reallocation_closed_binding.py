"""2026-10-16 ET. Exact retained mathematical evidence for the closed source rule.

The reviewed registry names immutable historical evidence, not current model
records. Every use also reconstructs the complete current source observation
rule and all mathematical inputs. Native projected-C observations remain
supplemental, and public/framework admission is deliberately separate.
"""
import hashlib
import json
from pathlib import Path

from swdb import vector_reallocation_closed_evidence as source_rule
from swdb import vector_reallocation_closed_lifetime as glue
from swdb import vector_reallocation_closed_lifetime_parts as parts
from swdb import vector_reallocation_private_frame as private
from swdb import vector_reallocation_vcs as constructor


class Refused(ValueError):
    pass


# Extending this registry requires review of the actual complete source/task/
# support/import/runtime evidence, not a new user-supplied verdict assertion.
REVIEWED_CATALOG_SHA256 = '42100d4ecb63de8718f6d16071f179ba3fb173cd94511730b195106426a1cb60'
HISTORICAL_SOURCES = {
    'constructor': '6216fc9440897bebc16a09eeb124ce76f202f185',
    'destructor': '2e01d27d0aea7f3c2056d3abb06600b4cefa29be',
    'private_frame': 'f918f5d52035fd99499280a0a8058efd0ed4ef55',
    'gluing': 'fb197c5ddd173065ca781766886c6a797684a838',
    'positive': '04af74c121a733589fbe1a2087ad602deaef598b',
}
COUNTS = {'constructor': 35, 'destructor': 11, 'private_frame': 9,
          'gluing': 4, 'positive': 23}
PROOF_BASIS = 'checked closed source observation rule and exact conditional mathematical evidence'
MAX_DOCUMENT_BYTES = 4*1024*1024
MAX_BUNDLE_BYTES = 16*1024*1024


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def _pairs(rows):
    output = {}
    for key, value in rows:
        if key in output:
            raise Refused('duplicate evidence JSON key')
        output[key] = value
    return output


def _decode(raw):
    try:
        return json.loads(raw, object_pairs_hook=_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(Refused('nonfinite evidence number')))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Refused('invalid bounded evidence JSON: '+str(error)) from None


def _hex(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= set('0123456789abcdef')


def _bundle(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise Refused('scientific bundle must be a physical directory')
    paths = list(directory.rglob('*'))
    if len(paths) > 256 or any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths):
        raise Refused('scientific bundle has linked, special or excessive entries')
    if sum(path.stat().st_size for path in paths if path.is_file()) > MAX_BUNDLE_BYTES:
        raise Refused('scientific bundle exceeds its compact bound')
    catalog_path = directory/'catalog.json'
    if not catalog_path.is_file() or catalog_path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise Refused('one bounded scientific catalog is required')
    raw = catalog_path.read_bytes()
    catalog = _decode(raw)
    if _sha(raw) != REVIEWED_CATALOG_SHA256:
        raise Refused('scientific catalog is outside the independently reviewed evidence registry')
    if catalog['schema_version'] != 1 or catalog['kind'] != 'vector-closed-scientific-bundle' or \
            catalog['required_target_count'] != 82 or catalog['gaps'] or \
            any(catalog[name] is not False for name in ('source_admission', 'caller_acceptance', 'proof_record_created')):
        raise Refused('scientific catalog scope or complete dependency count changed')
    documents = {}
    for row in catalog['documents']:
        digest = row['sha256']
        if not _hex(digest) or row['path'] != 'objects/'+digest+'.json' or \
                type(row['bytes']) is not int or not 0 < row['bytes'] <= MAX_DOCUMENT_BYTES:
            raise Refused('invalid content-addressed scientific document')
        if row['path'] in documents:
            raise Refused('duplicate scientific document')
        path = directory/row['path']
        if not path.is_file() or path.stat().st_size != row['bytes']:
            raise Refused('scientific document is missing or has changed extent')
        data = path.read_bytes()
        if _sha(data) != digest:
            raise Refused('scientific document differs from its retained identity')
        documents[row['path']] = (row, _decode(data))
    expected = {'catalog.json', *documents}
    if {str(path.relative_to(directory)) for path in paths if path.is_file()} != expected or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != {'objects'}:
        raise Refused('scientific bundle contains unbound or missing material')

    def resolve(location):
        try:
            document = location['document']
            registered, value = documents[document['path']]
            if document != registered or set(location) != {'document', 'pointer'}:
                raise Refused('scientific location has a changed document descriptor')
            pointer = location['pointer']
            if not isinstance(pointer, str) or (pointer and not pointer.startswith('/')):
                raise Refused('scientific location has an invalid JSON pointer')
            for encoded in pointer.split('/')[1:]:
                if '~' in encoded.replace('~0', '').replace('~1', ''):
                    raise Refused('scientific location has an invalid pointer escape')
                key = encoded.replace('~1', '/').replace('~0', '~')
                if isinstance(value, list):
                    if not key.isdecimal() or str(int(key)) != key:
                        raise Refused('scientific array pointer is noncanonical')
                    value = value[int(key)]
                else:
                    value = value[key]
            return value
        except (KeyError, TypeError, IndexError, ValueError):
            raise Refused('scientific location does not resolve exactly') from None

    # Resolve only explicit content-addressed locations. Historical filesystem
    # pins inside the evidence are values; they are never opened or followed.
    def visit(value):
        if isinstance(value, dict):
            if set(value) == {'document', 'pointer'}:
                resolve(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(catalog)
    return catalog, documents, resolve


def _current(lowering, source, formal_texts):
    try:
        rule, rule_files = source_rule.declaration(lowering, source, formal_texts)
        targets = {
            'constructor': constructor.declaration(glue.CTOR),
            'destructor': constructor.declaration(glue.DTOR),
            'private_frame': private.declaration(),
            'gluing': glue.declaration(lowering, source, formal_texts),
            'positive': parts.declaration(lowering, source, formal_texts),
        }
    except ValueError as error:
        raise Refused(str(error)) from None
    return rule, rule_files, targets


def _source_context(value):
    """Compare the full source rule except its observed compiler certificate.

    The sole removed leaf names the complete compiler use-time certificate,
    which is retained in both the fresh rule and historical evidence. This
    permits the already reviewed macOS/Linux provenance distinction without
    deleting ABI, model, executable source, ownership or allocator conditions.
    """
    result = json.loads(json.dumps(value))
    try:
        result['source_view']['library_allocator_binding'].pop('certificate_sha256')
    except (KeyError, TypeError):
        raise Refused('complete source compiler binding is missing') from None
    return result


def _observed(target, historical, resolve):
    observation = target['observation']
    primary = resolve(observation['evidence'])
    if observation['reader_check'] != historical['reader_check'] or \
            observation.get('normal_verdict', observation.get('reconstructed_normal_verdict')) != 'proven':
        raise Refused('normal historical reader outcome or identity changed')
    if 'record_run_metadata' in primary:
        run = primary['record_run_metadata']
        census = primary['goal_reconciliation']
        if run['verdict'] != 'proven' or run['reading']['check'] != historical['reader_check']:
            raise Refused('constructor normal reader observation changed')
        for output, field in [('ordinary', 'normalized_ordinary'), ('smoke', 'normalized_smoke'),
                              ('inventory_only_ordinary', 'inventory_only_ordinary'),
                              ('native_report_rows', 'native_report_rows'),
                              ('native_report_verdicts', 'native_report_verdicts')]:
            if observation[output] != census[field]:
                raise Refused('complete constructor ordinary/smoke/inventory census changed')
        native = [status for row in census['goals'] for status in row['inventory_results']]
    elif 'cold_census' in observation:
        census = resolve(observation['cold_census'])
        if primary['verdict'] != 'proven' or primary['reading']['check'] != historical['reader_check']:
            raise Refused('destructor normal reader observation changed')
        for output, field in [('ordinary', 'ordinary'), ('smoke', 'smokes'),
                              ('properties', 'properties'), ('CSV_rows', 'CSV_rows')]:
            if observation[output] != census[field]:
                raise Refused('complete destructor ordinary/smoke/property census changed')
        native = census['portfolio_results']
    else:
        for field in ('ordinary', 'smoke', 'properties', 'CSV_rows'):
            if observation[field] != primary[field]:
                raise Refused('complete standalone ordinary/smoke/property census changed')
        if 'normal_verdict' in primary:
            if primary['normal_verdict'] != 'proven' or not primary['passed']:
                raise Refused('standalone normal reader observation changed')
        else:
            basis = observation['normal_verdict_basis']
            if basis['kind'] != 'reviewed-passive-observer-assertion' or \
                    basis['auditor_sha256'] != '12cd78dcbdda5d7d8a1c7a2a60ef99992a6214ea1d22426b382a663771133250' or \
                    not _hex(observation['outcome_artifact']['sha256']) or \
                    not _hex(basis['result_artifact']['sha256']):
                raise Refused('private-frame retained normal-verdict assertion basis changed')
        native = primary['native_results']
    if observation['native_results'] != native:
        raise Refused('actual native result sequence changed')
    observed_input = primary.get('input_sha256', primary.get('input', {}).get('sha256'))
    if primary['id'] != target['id'] or observed_input != target['input_sha256']:
        raise Refused('retained actual outcome has a foreign mathematical input')
    return observation


def _component(component, current, rule, resolve):
    name = component['id']
    plan, files = current
    required = plan['obligations'][:4] if name == 'gluing' else plan['obligations']
    if len(required) != COUNTS[name] or len(component['targets']) != COUNTS[name] or \
            component['historical_identity']['source_commit'] != HISTORICAL_SOURCES[name] or \
            not component['cold_evidence']:
        raise Refused('scientific target or historical component scope changed')
    old = resolve(component['context']['canonical_manifest'])
    if old['semantics'] != plan['semantics'] or \
            _sha(files[plan['semantics']['path']]) != old['semantics']['sha256']:
        raise Refused('scientific heap theory changed')
    if name in {'constructor', 'destructor'}:
        for field in ('member', 'sources', 'source_sha256', 'source_inventory',
                      'typed_source_image', 'source_parameter_semantics',
                      'incoming_heap', 'allocation_identities', 'logical_obligations'):
            if old[field] != plan[field]:
                raise Refused('scientific source/domain/translation condition changed: '+field)
        for path, descriptor in old['sources'].items():
            if _sha(files[path]) != descriptor['sha256']:
                raise Refused('scientific original/qualified source inverse changed')
    elif name in {'gluing', 'positive'}:
        for descriptor in old['source_files']:
            if _sha(files[descriptor['path']]) != descriptor['sha256']:
                raise Refused('closed source or original/qualified body changed')
        # Keep the full source-derived allocator and body dependencies, including
        # all inverse/model/domain fields. The compiler certificate is recorded
        # at its historical use; matching source does not relabel its compiler.
        for field in ('constructor_dependency', 'destructor_dependency',
                      'private_frame_dependency', 'explicit_allocator_library_TCB',
                      'original_contract', 'caller_premises_added'):
            if old[field] != plan[field]:
                raise Refused('scientific source dependency or allocator TCB changed: '+field)
        if name == 'positive' and old['conjunctions'] != plan['conjunctions']:
            raise Refused('positive conjunction or existential witness reconstruction changed')
    expected_requirements = {
        'constructor': 'constructor', 'destructor': 'destructor',
        'private_frame': 'private_frame', 'gluing': 'unchanged_gluing',
        'positive': 'positive_conjunctions'}[name]
    if resolve(component['context']['source_rule_requirements']) != rule['scientific_dependencies'][expected_requirements]:
        raise Refused('complete scientific source-rule dependency changed')
    accepted_ids = component['accepted_subset']['target_ids']
    if accepted_ids != [row['id'] for row in required]:
        raise Refused('accepted scientific target subset changed')
    decision = resolve(component['accepted_decision'])
    if decision['source_commit'] != HISTORICAL_SOURCES[name]:
        raise Refused('accepted decision historical source changed')
    targets = []
    for target, requirement in zip(component['targets'], required, strict=True):
        previous = resolve(target['canonical_obligation'])
        for field in ('id', 'goal', 'kind', 'statement'):
            if target[field] != requirement[field] or previous[field] != requirement[field]:
                raise Refused('exact mathematical goal, kind or complete statement changed')
        digest = _sha(files[requirement['path']])
        if digest != requirement['sha256'] or digest != previous['sha256'] or digest != target['input_sha256']:
            raise Refused('complete mathematical input byte identity changed')
        observation = _observed(target, component['historical_identity'], resolve)
        targets.append({'id': requirement['id'], 'goal': requirement['goal'],
            'kind': requirement['kind'], 'statement': requirement['statement'],
            'input_sha256': digest, 'observation': observation})
    if name == 'gluing':
        original = component['accepted_subset']['preserved_unaccepted_historical_outcomes']
        if [row['id'] for row in original] != ['positive.exit_image', 'positive.cleanup'] or \
                any(row['normal_verdict'] != 'not_proven' or row['failure_class'] != 'timeout' or
                    row['native_results'] != ['timeout', 'unknown', 'timeout'] for row in original):
            raise Refused('the two original compound timeouts were promoted or omitted')
    return {'id': name, 'targets': targets,
        'historical_identity': component['historical_identity'],
        'historical_source_commit': HISTORICAL_SOURCES[name],
        'historical_identity_preserved': True, 'accepted_decision': component['accepted_decision'],
        'complete_cold_context': component['context'], 'cold_evidence': component['cold_evidence'],
        'accepted_subset': component['accepted_subset']}


def declaration(lowering, source, formal_texts, scientific_directory):
    catalog, documents, resolve = _bundle(scientific_directory)
    rule, rule_files, current = _current(lowering, source, formal_texts)
    if _source_context(resolve(catalog['requirements'])) != _source_context(rule) or \
            [row['id'] for row in catalog['components']] != list(COUNTS):
        raise Refused('complete reviewed source rule or component membership changed')
    components = [_component(row, current[row['id']], rule, resolve) for row in catalog['components']]
    result = {'created': '2026-10-16 ET', 'checker': identity(), 'proof_basis': PROOF_BASIS,
        'scientific_dependencies_bound': True, 'complete_source_target_count': 82,
        'source_rule': rule, 'components': components,
        'scientific_catalog_sha256': REVIEWED_CATALOG_SHA256,
        'evidence_object_count': len(documents),
        'historical_records_rewritten': False, 'current_model_records_created': [],
        'original_two_timeout_results_preserved': True,
        'original_native_reader_not_proven_preserved': True,
        'source_typed_bridge_established': False, 'source_admission': False,
        'public_proof_record_created': False, 'caller_acceptance': False,
        'proof_admission': 'unsupported: exact scientific dependencies are bound; reviewed public framework integration remains required'}
    files = {'source-rule/'+name: raw for name, raw in rule_files.items()}
    files['manifest.json'] = _json(result)
    return result, files


def identity():
    return {'id': 'vector-closed-scientific-binding-1',
            'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
                                  'source_rule': source_rule.identity(),
                                  'reviewed_catalog': REVIEWED_CATALOG_SHA256}))}


def prepare(lowering, source, formal_texts, scientific_directory, directory):
    result, files = declaration(lowering, source, formal_texts, scientific_directory)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return result


def check(lowering, source, formal_texts, scientific_directory, directory):
    result, files = declaration(lowering, source, formal_texts, scientific_directory)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if directory.is_symlink() or any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths) or \
            {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != parents:
        raise Refused('closed scientific binding canonical membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise Refused('closed scientific binding or source derivation differs: '+name)
    return result


def check_launch(lowering, source, formal_texts, scientific_directory, directory):
    check(lowering, source, formal_texts, scientific_directory, directory)
    raise Refused('public framework integration of the checked source proof basis remains required')

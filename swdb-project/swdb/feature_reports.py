"""Additional reported workload inputs; preserve counted facts. Created: 2026-10-06 ET.
Updated: 2026-10-09 ET (wider timing/PMU names; internal width conflicts; generic footprint units)."""
import copy
import hashlib
import re
from pathlib import Path

from yaml import YAMLError

from swdb import access, analytic, artifacts, paths, writer
from swdb.cli import Failure
from swdb.store import Store


def register_cli(commands):
    sub = commands.add_parser('import-feature-report', help='attach a sanitized reported input to a new characterization; counted facts stay unchanged')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--report', type=Path, required=True)
    sub.add_argument('--characterization', required=True, help='existing characterization ID or YAML/JSON file')
    sub.add_argument('--methodology', type=Path, help='reported structured methodology; never inferred from the filename')
    sub.add_argument('--methodology-text', type=Path, help='optional original methodology text for explicit internal conflicts')
    sub.add_argument('--manifest', type=Path, help='optional received-report manifest')
    sub.add_argument('--array-alias', action='append', default=[], metavar='REPORTED=SWDB', help='explicit comparison alias; does not establish source/access equivalence')
    sub.add_argument('--id', required=True, help='new immutable characterization ID')
    sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    sub.set_defaults(analytic_handler=import_report)


def _read(path):
    try:
        before = access.record_hash(path)
        data = access.read_record(path)
        after = access.record_hash(path)
    except (OSError, UnicodeError, ValueError, YAMLError) as exc:
        raise Failure(f'cannot read feature input {path}: {exc}') from None
    if before != after:
        raise Failure('feature input changed while it was read; retry with stable source bytes')
    if not isinstance(data, dict):
        raise Failure('feature input must be an object')
    try:
        artifacts.digest(data)
    except (ValueError, TypeError):
        raise Failure('feature input must contain finite JSON-compatible values') from None
    return data, after


SANITIZER_VERSION = 'swdb.feature-report-sanitizer.v2'
# Unit-suffixed durations (trial_sec, kernel_ms, wall_clock_s), latencies, cache
# hit/miss rates, MPKI and bandwidth/FLOP rates are outcomes too.
_OUTCOME_KEY = re.compile(r'(?:^|_)(?:times?|timings?|runtime|elapsed|duration|latency|latencies|seconds?|secs?|milliseconds?|microseconds?|nanoseconds?|ms|us|ns|s|cycles?|ipc|cpi|mpki|pmu|speedup|throughput|bandwidth|gbps|mbps|gflops|flops|performance|(?:hit|miss)_(?:rates?|ratios?))(?:_|$)|instructions_per_cycle|frequency_ghz', re.I)
# Methodology flags (measures_cache_hit_rate: false) say what was measured, not a value.
_FLAG_KEY = re.compile(r'measures_[a-z0-9_]+|runtime_thread_interleaving_observed')


def _sanitize(value, redactions, path=''):
    """Keep index/count statistics; withhold named timing/PMU outcomes recursively.

    Original values stay in the source report, never in redaction descriptions.
    Percent locality and operation execution-frequency descriptions are not PMU
    timings. Free text with a duration or performance verdict is withheld too.
    """
    from swdb.extensa.leakage import find_outcome_claims
    if isinstance(value, dict):
        kept = {}
        for key, item in value.items():
            child = path + '/' + str(key).replace('~', '~0').replace('/', '~1')
            normalized = re.sub(r'([a-z])([A-Z])', r'\1_\2', str(key)).lower()
            if _OUTCOME_KEY.search(normalized) and not (_FLAG_KEY.fullmatch(normalized) and isinstance(item, bool)):
                redactions.append({'path': child, 'reason': 'Timing/PMU/performance outcomes are withheld from estimation inputs'})
            else:
                sanitized, allowed = _sanitize(item, redactions, child)
                if allowed:
                    kept[key] = sanitized
        return kept, True
    if isinstance(value, list):
        kept = []
        for index, item in enumerate(value):
            sanitized, allowed = _sanitize(item, redactions, path + '/' + str(index))
            if allowed:
                kept.append(sanitized)
        return kept, True
    if isinstance(value, str) and any(c.pattern in {'duration_magnitude', 'outcome_vocabulary'} for c in find_outcome_claims(value)):
        redactions.append({'path': path, 'reason': 'Free-text timing/performance outcome is withheld from estimation inputs'})
        return None, False
    return value, True


def _conflict(kind, path, reason, **facts):
    return {'kind': kind, 'path': path, 'reason': reason, **facts}


def _aliases(arguments):
    result = {}
    for argument in arguments:
        old, separator, new = argument.partition('=')
        if not separator or not old or not new or old in result:
            raise Failure('array aliases require unique REPORTED=SWDB names')
        result[old] = new
    return result


def _document(path):
    redactions = []
    original, source_sha = _read(path)
    features, _ = _sanitize(original, redactions)
    return {'path': str(path.resolve()), 'sha256': source_sha,
        'sanitized_sha256': artifacts.digest(features), 'sanitizer_version': SANITIZER_VERSION,
        'features': features, 'redactions': redactions, 'basis': 'reported'}


def _methodology(path):
    document = _document(path)
    features = document['features']
    if not isinstance(features.get('footprints', {}), dict):
        raise Failure('methodology footprints must be an object')
    if not isinstance(features.get('footprints', {}).get('element_bytes', {}), dict):
        raise Failure('methodology footprints.element_bytes must be an object')
    identities = features.get('applies_to_input_sha256', [])
    if not isinstance(identities, list) or any(not isinstance(value, str) for value in identities):
        raise Failure('methodology applies_to_input_sha256 must list source identities')
    return document


def _source_scope(original, report, conflicts):
    kernel = report['kernel']
    provenance = report.get('profiling_provenance', {})
    reported_scope = {'function': kernel.get('function'), 'source_revision': kernel.get('source_revision'),
        'source_file': kernel.get('source_file'), 'graph': provenance.get('profiled_graph', kernel.get('graph_topology')),
        'command_line': provenance.get('command_line'), 'compiler_toolchain': provenance.get('compiler_toolchain'),
        'host': provenance.get('execution_environment', report.get('hardware_performance_profile', {}).get('measurement_platform'))}
    identity = original['binding']['subject_source_identity']
    counted_scope = {'function': original['coverage'].get('function', identity.get('registered_function')),
        'source_revision': identity.get('source_commit', identity.get('registered_source', {}).get('commit')),
        'input': original['input'], 'roi': original['binding']['roi'], 'threads': original['binding']['threads'],
        'source_sha256': original['source']['sha256'], 'host': original['host']}
    # A mismatch needs a fact known on both sides that differs; otherwise the scope is only unbound.
    differs = any(reported_scope[key] is not None and counted_scope[key] is not None and reported_scope[key] != counted_scope[key]
                  for key in ('function', 'source_revision'))
    conflicts.append(_conflict('source_scope_mismatch' if differs else 'source_scope_unbound', '/kernel',
        'Reported function/source/input/host scope is not bound to these native counts. A TDStep report is not automatically the complete counted call.',
        reported=reported_scope, swdb=counted_scope, comparison_scope='unresolved_source_and_access_binding'))
    return reported_scope


def _array_conflicts(report, subject, aliases, conflicts):
    catalog = {}
    for pattern in subject.get('access_patterns', []):
        for step in pattern['steps']:
            array = step['array']
            catalog.setdefault(array['name'], set()).add(array['element_bytes'])
    # Every reported width for an array, from every section. A repeated row or a
    # disagreement between sections is listed, never resolved by keeping one.
    reported = {}
    for index, row in enumerate(report.get('data_structures', [])):
        reported.setdefault(row['name'], []).append(('/data_structures/' + str(index), row.get('element_size_bytes')))
    for index, row in enumerate(report.get('indirect_access_distances', [])):
        reported.setdefault(row['array_name'], []).append(('/indirect_access_distances/' + str(index), row.get('element_size_bytes')))
    for name, rows in reported.items():
        path = '/data_structures/' + name
        repeated = [(where, width) for where, width in rows if where.startswith('/data_structures/')]
        if len(repeated) > 1:
            conflicts.append(_conflict('reported_internal_conflict', path,
                'The report lists this array more than once; every row is retained and none is selected.',
                reported=[{'path': where, 'element_size_bytes': width} for where, width in repeated]))
        values = []
        for _, width in rows:
            if width not in values:
                values.append(width)
        if len([value for value in values if value is not None]) > 1:
            conflicts.append(_conflict('reported_internal_conflict', path + '/element_size_bytes',
                'Report sections give different element widths for this array; every width is retained and none is selected.',
                reported=[{'path': where, 'element_size_bytes': width} for where, width in rows]))
        for value in values:
            if type(value) is not int:
                conflicts.append(_conflict('non_numeric_reported_value', path + '/element_size_bytes',
                    'Element width is not an explicit integer byte value; no conversion is guessed.', reported=value, swdb=None))
        if name not in aliases:
            conflicts.append(_conflict('array_unmapped', path,
                'No explicit array alias was supplied; names and numeric statistics are retained without matching a native access site.', reported=name, swdb=None))
            continue
        widths = catalog.get(aliases[name])
        if not widths:
            conflicts.append(_conflict('array_alias_unresolved', path,
                'The explicit destination array has no registered access-pattern definition.', reported=name, swdb=aliases[name]))
            continue
        for value in values:
            if type(value) is int and (len(widths) != 1 or value not in widths):
                conflicts.append(_conflict('element_size_mismatch', path + '/element_size_bytes',
                    'Explicitly aliased reported/catalog widths differ. Source revisions and concrete access bindings remain unresolved; neither width is repaired.',
                    reported={'value': value, 'unit': 'bytes', 'basis': 'reported'},
                    swdb={'value': next(iter(widths)) if len(widths) == 1 else sorted(widths), 'unit': 'bytes', 'basis': 'code_reading'},
                    comparison_scope='unresolved_source_and_access_binding'))
    for name in set(aliases) - set(reported):
        conflicts.append(_conflict('array_alias_unresolved', '/array_aliases/' + name,
            'Explicit source name is absent from the report.', reported=name, swdb=aliases[name]))


def _unit_conflicts(report, methodology, conflicts):
    structures = {row['name']: row for row in report.get('data_structures', [])}
    field_arrays = {'parent': 'parent', 'offsets': 'VertexOffsets', 'neighbors': 'g.out_neighbors_', 'queue': 'queue.shared'}
    def visit(value, path):
        if not isinstance(value, dict):
            return
        for field, number in value.items():
            match = re.fullmatch(r'(parent|offsets|neighbors|queue)_footprint_(mb|kb)', field)
            if match:
                prefix, unit = match.groups()
                array = structures.get(field_arrays[prefix], {})
                width = array.get('element_size_bytes')
                symbol = array.get('capacity')
                capacity = value.get('num_directed_edges') if symbol == 'num_directed_edges' else value.get('num_nodes') if symbol in ('num_nodes', 'num_nodes + 1') else None
                known = type(width) is int and type(capacity) is int
                if known and symbol == 'num_nodes + 1':
                    capacity += 1
                conflicts.append(_conflict('unit_ambiguity', path + '/' + field,
                    'KB/MB labels do not establish decimal versus binary units. Logical capacity is not active working set; no unit is selected or value converted.',
                    reported={'value': number, 'unit': unit.upper(), 'basis': 'reported'},
                    expected_logical_capacity_bytes=capacity * width if known else None,
                    reported_unit_claim=(methodology or {}).get('features', {}).get('footprints', {}).get('reported_unit_claim'),
                    resolved_unit=None))
            elif not isinstance(number, dict) and re.fullmatch(r'.+_(kb|mb|gb)', field):
                # Other size fields (total_working_set_mb) carry the same unit ambiguity;
                # no array/capacity binding is known for them.
                conflicts.append(_conflict('unit_ambiguity', path + '/' + field,
                    'KB/MB/GB labels do not establish decimal versus binary units. No unit is selected or value converted.',
                    reported={'value': number, 'unit': field.rsplit('_', 1)[1].upper(), 'basis': 'reported'},
                    expected_logical_capacity_bytes=None,
                    reported_unit_claim=(methodology or {}).get('features', {}).get('footprints', {}).get('reported_unit_claim'),
                    resolved_unit=None))
            else:
                visit(number, path + '/' + field)
    visit(report.get('working_set', {}), '/working_set')


def _methodology_text(path, methodology, conflicts):
    try:
        raw = access.read_record_bytes(path)
        text = raw.decode('utf-8')
    except (OSError, UnicodeError) as exc:
        raise Failure(f'cannot read methodology text: {exc}') from None
    source = (methodology or {}).get('features', {})
    widths = source.get('footprints', {}).get('element_bytes', {})
    kept = []; redactions = []
    for number, line in enumerate(text.splitlines(), 1):
        # Only concrete array/type table rows enter the input; full prose remains
        # evaluator-owned source evidence. It can contain performance outcomes.
        if line.lstrip().startswith('|') and 'VertexOffsets' in line:
            candidate, allowed = _sanitize(line, redactions, '/lines/' + str(number))
            if allowed:
                kept.append({'line': number, 'text': candidate})
                found = [int(n) for match in re.findall(r'(?:\\times|×)\s*([0-9]+)\s*\\?text\{?\s*B|\|\s*([0-9]+) bytes', line) for n in match if n]
                expected = widths.get('VertexOffsets')
                if expected is not None and any(width != expected for width in found):
                    conflicts.append(_conflict('methodology_internal_conflict', '/methodology_text/lines/' + str(number),
                        'The methodology table declares an offset width different from its structured/type declaration. Both statements remain reported.',
                        reported={'element_size_bytes': found, 'basis': 'reported'}, structured={'element_size_bytes': expected, 'basis': 'reported'}))
                continue
        redactions.append({'path': '/lines/' + str(number), 'reason': 'Full narrative remains in evaluator source; only concrete array/type rows enter this input'})
    features = {'retained_rows': kept}
    result = {'path': str(path.resolve()), 'sha256': hashlib.sha256(raw).hexdigest(), 'sanitized_sha256': artifacts.digest(features),
        'sanitizer_version': SANITIZER_VERSION, 'basis': 'reported', 'features': features, 'redactions': redactions}
    if source.get('source_sha256') is not None and source['source_sha256'] != result['sha256']:
        conflicts.append(_conflict('methodology_identity_mismatch', '/methodology/source_sha256',
            'Declared methodology text identity differs from supplied bytes; neither source is silently substituted.',
            reported=source['source_sha256'], other=result['sha256']))
    return result


def _manifest(path, report_path, report, report_sha, conflicts):
    document = _document(path)
    manifest = document['features']
    if not isinstance(manifest.get('records', []), list) or any(not isinstance(row, dict) for row in manifest.get('records', [])):
        raise Failure('manifest records must list objects')
    if not isinstance(manifest.get('handling_notes', []), list) or any(not isinstance(note, str) for note in manifest.get('handling_notes', [])):
        raise Failure('manifest handling_notes must list strings')
    matches = [entry for entry in manifest.get('records', []) if entry.get('file') == report_path.name]
    selected = matches[0] if len(matches) == 1 else None
    if selected is None or selected.get('sha256') != report_sha:
        conflicts.append(_conflict('manifest_identity_mismatch', '/manifest/records',
            'Manifest does not uniquely identify these report bytes.', reported=report_sha, other=selected))
    for index, note in enumerate(manifest.get('handling_notes', [])):
        if (report['kernel'].get('source_revision') and 'Neither file supplies the exact profiled source revision' in note
                or '64-bit VertexOffsets' in note and any(row.get('name') == 'VertexOffsets' and row.get('element_size_bytes') == 4 for row in report.get('data_structures', []))):
            conflicts.append(_conflict('manifest_scope_conflict', '/manifest/handling_notes/' + str(index),
                'Historical handling note conflicts with the selected updated report; it is retained but not applied as a repair.', reported=note))
    document['features'] = {'received_on': manifest.get('received_on'), 'selected_record': selected, 'handling_notes': manifest.get('handling_notes', [])}
    document['sanitized_sha256'] = artifacts.digest(document['features'])
    return document


def _report_shape(report):
    if not isinstance(report.get('schema_version'), str) or not isinstance(report.get('kernel'), dict):
        raise Failure('feature report needs explicit schema_version and kernel scope')
    for key in ('profiling_provenance', 'hardware_performance_profile', 'working_set'):
        if key in report and not isinstance(report[key], dict):
            raise Failure(f'feature report {key} must be an object')
    for key, name in (('data_structures', 'name'), ('indirect_access_distances', 'array_name')):
        rows = report.get(key, [])
        if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get(name), str) or not row[name] for row in rows):
            raise Failure(f'feature report {key} must list objects with explicit {name}')


def import_report(args):
    store = Store(args.records)
    original = analytic._load(store, args.characterization, 'workload_characterization')
    report, report_sha = _read(args.report)
    _report_shape(report)
    redactions = []
    features, _ = _sanitize(report, redactions)
    match = re.search(r'\.v([0-9]+\.[0-9]+)\.', args.report.name)
    filename_version = match.group(1) if match else None
    conflicts = []
    if filename_version and filename_version != report['schema_version']:
        conflicts.append({'kind': 'version_mismatch', 'path': '/schema_version',
            'reported': report['schema_version'], 'other': filename_version,
            'reason': 'Report content and filename declare different versions; neither is rewritten.'})
    aliases = _aliases(args.array_alias)
    scope = _source_scope(original, features, conflicts)
    # Dense report host context is separate from its withheld PMU outcome block.
    if scope['host'] is None:
        host, allowed = _sanitize(report.get('hardware_performance_profile', {}).get('measurement_platform'), redactions, '/hardware_performance_profile/measurement_platform')
        scope['host'] = host if allowed else None
    _array_conflicts(features, store.get(original['subject']['id'], original['subject']['kind']) or {}, aliases, conflicts)
    methodology = _methodology(args.methodology) if args.methodology else None
    if methodology and report_sha not in methodology['features'].get('applies_to_input_sha256', []):
        conflicts.append(_conflict('methodology_identity_mismatch', '/methodology/applies_to_input_sha256', 'Methodology does not explicitly apply to these report bytes.', reported=report_sha))
    _unit_conflicts(features, methodology, conflicts)
    methodology_text = _methodology_text(args.methodology_text, methodology, conflicts) if args.methodology_text else None
    manifest = _manifest(args.manifest, args.report, features, report_sha, conflicts) if args.manifest else None
    supplied = {'basis': 'reported',
        'source_report': {'path': str(args.report.resolve()), 'sha256': report_sha,
            'filename_version': filename_version, 'schema_version': report['schema_version'],
            'sanitized_sha256': artifacts.digest(features), 'sanitizer_version': SANITIZER_VERSION},
        'base_characterization': {'id': original['id'], 'sha256': artifacts.digest(original)},
        'features': features, 'scope': scope, 'array_aliases': aliases, 'conflicts': conflicts, 'redactions': redactions}
    if methodology:
        supplied['methodology'] = methodology
    if methodology_text:
        supplied['methodology_text'] = methodology_text
    if manifest:
        supplied['manifest'] = manifest
    record = copy.deepcopy(original)
    record['id'] = args.id
    record['created'] = record['updated'] = writer.today()
    record.setdefault('reported_inputs', []).append(supplied)
    record['provenance'].append({'id': 'feature-report.' + str(len(record['reported_inputs'])),
        'kind': 'human_report', 'description': 'Additional reported feature input; counted evidence retained unchanged.', 'uri': None})
    record.pop('identity_sha256', None)
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record


def payload_problems(data):
    """Optional reported-input seals and outcome-free contract, even for file inputs."""
    for index, supplied in enumerate(data.get('reported_inputs', [])):
        prefix = f'reported_inputs[{index}]'
        try:
            artifacts.digest(supplied)
        except (ValueError, TypeError):
            yield prefix, 'reported input must contain finite JSON-compatible values'
            continue
        documents = [('features', supplied['features'], supplied['source_report']['sanitized_sha256'])]
        for key in ('methodology', 'methodology_text', 'manifest'):
            if key in supplied:
                document = supplied[key]
                documents.append((key + '.features', document['features'], document['sanitized_sha256']))
        for key, features, digest in documents:
            if artifacts.digest(features) != digest:
                yield prefix + '.' + key, 'sanitized reported input content hash differs'
            removed = []
            sanitized, _ = _sanitize(features, removed)
            if sanitized != features:
                yield prefix + '.' + key, 'timing/PMU outcomes are forbidden in reported estimation inputs'
        for key in ('scope', 'conflicts'):
            removed = []
            sanitized, _ = _sanitize(supplied[key], removed)
            if sanitized != supplied[key]:
                yield prefix + '.' + key, 'timing/PMU outcomes are forbidden in reported metadata'


def validate_record(record, ctx):
    """Keep the pinned parent and all of its native facts unchanged."""
    from swdb.problems import Problem
    metadata = {'id', 'created', 'updated', 'provenance', 'identity_sha256', 'reported_inputs'}
    for index, supplied in enumerate(record.data.get('reported_inputs', [])):
        parent = ctx.passed(supplied['base_characterization']['id'], 'workload_characterization')
        if parent is None:
            # File inputs can be imported without storing their original bytes;
            # the original canonical identity remains explicit for reproduction.
            continue
        field = f'reported_inputs[{index}].base_characterization'
        if artifacts.digest(parent) != supplied['base_characterization']['sha256']:
            yield Problem(record.rel, field, 'pinned parent characterization content differs')
        if {k:v for k,v in parent.items() if k not in metadata} != {k:v for k,v in record.data.items() if k not in metadata}:
            yield Problem(record.rel, field, 'imported reported input must preserve every native characterization fact')

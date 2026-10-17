"""Source-only P3 public-summary metadata query. NOT RUN in preparation.

Parse only the fixed original public YAML summary and original stop receipt.
Return bounded identities, all-nine-stat/file pins and pairing counts/digests.
No raw summary, candidate/provider body, original state, log or command returns.
"""
import datetime, hashlib, json, os, pwd, re, signal, socket, stat, sys, time
from pathlib import Path

UID = 114316761
CID = 'extensa-gem5-bfs-20261006-p3'
R = '5e12a9796432654d88def24ecea617d16ca605b2'
CONFIG = 'ddb21f8165f98297a38e430ded016b4d072d9e29d42ca63ca742085229f5cad1'
STOP_SHA = 'e030cba330a1bba1beae016e8f19422b8d1a2bb131d1d214ed47c4d1e461cf25'
STOP_ID = 'ce67fe2143deba2889f9674e174f562b114cbfd53c41b56c76d5ab0e00fc2d64'
RAW = Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
SUMMARY = RAW / 'campaign-runs/extensa' / CID / 'records/campaign_summaries' / (CID + '.summary.yaml')
STOP = RAW / 'attempts' / CID / 'attempt-1/stopped-receipt.json'
FIELDS = ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'mtime_ns', 'ctime_ns')
FORMAT = 'swdb.lanl17-p3-public-summary-pairing-metadata-readonly.v1'
END = time.monotonic() + 45

class Refused(ValueError):
    pass

def need(ok, code):
    if not ok:
        raise Refused(code)

def tick():
    need(time.monotonic() < END, 'query_deadline')

def interrupted(number, frame):
    raise Refused('query_deadline_or_signal')

for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(number, interrupted)
signal.alarm(45)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=True, allow_nan=False).encode())

def stamp(value):
    return {key: getattr(value, 'st_' + key) for key in FIELDS}

def canonical(path):
    need(path.is_absolute() and path.resolve(strict=True) == path and
         not any(p.is_symlink() for p in (path, *path.parents)), 'canonical_nonsymlink_route')

def read_original(path, maximum):
    tick()
    canonical(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_uid == UID and before.st_nlink == 1
         and not before.st_mode & 0o7000 and 0 <= before.st_size <= maximum,
         'original_identity_or_cap')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(before), 'original_open_changed')
        raw = stream.read(maximum + 1)
        need(len(raw) == before.st_size <= maximum and
             stamp(before) == stamp(os.fstat(stream.fileno())) == stamp(path.lstat()),
             'returned_original_bytes_or_stat_changed')
    return raw, {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw), 'stat': stamp(before)}

def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result
    def bad(value):
        raise Refused('nonfinite_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def read():
    need(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10' and
         os.getuid() == os.geteuid() == UID and pwd.getpwuid(UID).pw_name == 'yanruj', 'actual_account')
    need(Path('/proc/self/exe').resolve() == Path('/usr/bin/python3.12') and
         sys.flags.dont_write_bytecode and not sys.flags.optimize, 'native_Python_flags')
    # Match the existing working monitor's native Python -B public dependency environment.
    # No SWDB or Store import; no local parser execution during source preparation.
    import yaml
    parser_path = Path(yaml.__file__).resolve(strict=True)
    need(parser_path.name == '__init__.py' and parser_path.parent.name == 'yaml', 'public_yaml_parser_route')
    parser_stat = parser_path.stat()
    need(stat.S_ISREG(parser_stat.st_mode) and parser_stat.st_uid in (0, UID)
         and parser_stat.st_nlink == 1 and parser_stat.st_size <= 1024 * 1024,
         'bounded_public_yaml_parser_identity')

    class Loader(yaml.SafeLoader):
        nodes = 0
        depth = 0
        def compose_node(self, parent, index):
            tick()
            need(not self.check_event(yaml.events.AliasEvent), 'summary_alias_refused')
            self.nodes += 1
            self.depth += 1
            need(self.nodes <= 100000 and self.depth <= 40, 'bounded_summary_structure')
            try:
                return super().compose_node(parent, index)
            finally:
                self.depth -= 1
    Loader.yaml_implicit_resolvers = {
        first: [(tag, expression) for tag, expression in resolvers
                if tag != 'tag:yaml.org,2002:timestamp']
        for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()}
    def unique_mapping(loader, node, deep=False):
        seen = set()
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            need(key not in seen, 'duplicate_YAML_key')
            seen.add(key)
        return loader.construct_mapping(node, deep=deep)
    Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)

    raw, summary_pin = read_original(SUMMARY, 32 * 1024 * 1024)
    stop_raw, stop_pin = read_original(STOP, 65536)
    need(stop_pin['bytes'] == 1355 and stop_pin['sha256'] == STOP_SHA, 'original_stop_file_pin')
    stopped = strict_json(stop_raw)
    need(type(stopped) is dict and stopped.get('identity_sha256') == STOP_ID and
         digest({key: value for key, value in stopped.items() if key != 'identity_sha256'}) == STOP_ID,
         'original_stop_seal')
    need(stopped.get('campaign') == CID and stopped.get('source_commit') == R and
         stopped.get('runner_exit_code') == stopped.get('public_exit_code') == 0 and
         stopped.get('infrastructure_error') is None, 'original_stop_binding')
    value = yaml.load(raw, Loader=Loader)
    need(type(value) is dict and value.get('kind') == 'campaign_summary' and
         value.get('id') == CID + '.summary' and value.get('campaign') == CID and
         value.get('mode') == 'extensa' and value.get('target') == 'dx100_gem5' and
         value.get('swdb_commit') == R and value.get('evidence_kind') == 'execution' and
         value.get('stop_reason') == 'plateau' and type(value.get('campaign_file')) is dict and
         value['campaign_file'].get('sha256') == CONFIG, 'original_public_summary_binding')
    pairing = value.get('paired_estimates')
    known_keys = {'format', 'enabled', 'records', 'outcome_accesses',
                  'eligible_application_estimates', 'selection_policy'}
    need(type(pairing) is dict and set(pairing) == known_keys and
         type(pairing['enabled']) is bool and pairing['enabled'] is True and
         pairing['format'] == 'swdb.extensa-pairing-ledger.v1' and
         pairing['selection_policy'] == 'unchanged_timing_only' and
         type(pairing['eligible_application_estimates']) is int and
         pairing['eligible_application_estimates'] >= 0, 'closed_public_pairing_mapping')
    records, events = pairing['records'], pairing['outcome_accesses']
    need(type(records) is list and type(events) is list and
         len(records) <= 10000 and len(events) <= 10000, 'bounded_public_pairing_lists')
    flags = []
    for record in records:
        need(type(record) is dict and record.get('kind') == 'paired_estimate' and
             record.get('campaign') == CID, 'public_paired_record_identity')
        flag = record.get('eligible_for_agreement')
        need(type(flag) is bool, 'public_paired_eligible_flag_type')
        flags.append(flag)
    for event in events:
        need(type(event) is dict, 'public_outcome_event_mapping')
    for path, maximum, initial_raw, initial_pin in (
            (SUMMARY, 32 * 1024 * 1024, raw, summary_pin), (STOP, 65536, stop_raw, stop_pin)):
        repeated_raw, repeated_pin = read_original(path, maximum)
        need(repeated_raw == initial_raw and repeated_pin == initial_pin, 'original_snapshot_changed')
    need(stamp(parser_path.stat()) == stamp(parser_stat), 'public_yaml_parser_stat_changed')
    tick()
    return {'format': FORMAT, 'sealed': False, 'scientific_admission': False,
            'query_ready': True, 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'campaign': CID, 'source_commit': R, 'summary_kind': 'campaign_summary',
            'summary_id': CID + '.summary', 'stop_reason': 'plateau',
            'summary_file': summary_pin, 'summary_record_sha256': digest(value),
            'original_stop_file': stop_pin, 'original_stop_identity_sha256': STOP_ID,
            'paired_estimates': {'top_keys': sorted(pairing), 'enabled': True,
                'format': pairing['format'], 'records': len(records), 'outcome_accesses': len(events),
                'eligible_flags_true': sum(flags), 'eligible_flags_false': len(flags) - sum(flags),
                'eligible_application_estimates': pairing['eligible_application_estimates'],
                'records_sha256': digest(records), 'outcome_accesses_sha256': digest(events)},
            'yaml_parser': {'path': str(parser_path), 'bytes': parser_stat.st_size,
                            'stat': stamp(parser_stat)},
            'raw_summary_state_candidate_provider_bodies_returned': False,
            'state_provider_prompt_auth_log_command_files_opened': 0,
            'blind_order_and_trajectory_admission_inferred': False}

try:
    result = read()
    encoded = (json.dumps(result, sort_keys=True, allow_nan=False) + '\n').encode()
    need(len(encoded) <= 16 * 1024, 'metadata_output_cap')
    sys.stdout.buffer.write(encoded)
except Exception as exc:
    sys.stdout.write(json.dumps({'format': FORMAT, 'sealed': False, 'scientific_admission': False,
        'query_ready': False, 'error_class': type(exc).__name__, 'reason_sha256': sha(str(exc).encode()),
        'raw_context_transferred': False,
        'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}, sort_keys=True) + '\n')
    sys.exit(3)

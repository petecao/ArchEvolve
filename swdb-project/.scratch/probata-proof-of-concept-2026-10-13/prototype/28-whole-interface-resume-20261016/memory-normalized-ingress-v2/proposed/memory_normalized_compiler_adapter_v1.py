"""Exact G642/source55b9 normalized stream into the unchanged TU consumer.

The generic semantic preparation schema stays intact for the strict reviewed
three-root helper. A separate mandatory transport field distinguishes every
original/derived memory identity. No first-source transport is accepted here.
"""
import hashlib
from pathlib import Path
from swdb._dx100_whole import compiler_unit_adapter_v3 as legacy
from swdb._dx100_whole import abi_role_transport_v1 as abi_transport

KIND = 'complete-memory-original-tu-paired-type-gzip-1'
EFFECTIVE_LIMIT = 201326592
LEGACY_CEILING = 536870912
EXPANDED_BYTES = 177082275
EXPANDED_SHA = '5895fc09a89f41b352368a16fb32b3c5065e8add0672a06fcb29a6be0afa8319'
COMPRESSED_BYTES = 12666345
SOURCE_SHA = '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
SOURCE_BYTES = 3258
SOURCE_PATH = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1/control/same_thread_memory_v1.cpp'
CAPTURE_SHA = 'b8f7e85a358e5670bb63bec658cbdf2f16ecc79d1400a1d97e9e0b76e91489c8'
ORIGINAL_WIRE_SHA = 'c89c00e8b03717a6ab3c9733d7fbb14aeb46c0d7f2ea4c6d7e87097ad0e9ba67'
ORIGINAL_TOKEN_SHA = '5ddd90248ab0e6bbe298feb5c8ec48e6af28bd3fd9a7a3581cf4330e4f52d08a'
LEGACY_SHA = '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
CASES = (('whole_same_thread_read_during_store', 12), ('whole_same_thread_write_during_gather', 14),
         ('whole_same_thread_read_during_gather', 14))


def need(value, message):
    if not value: raise ValueError(message)


def check_cases(prepared):
    calls = prepared.get('calls')
    need(type(calls) is list and len(calls) == sum(count for _, count in CASES)
         and all(type(row) is dict for row in calls), 'complete memory call census required')
    callers = {'_Z' + str(len(name)) + name + 'v': count for name, count in CASES}
    need({row.get('caller_mangled') for row in calls} == set(callers), 'exact three original memory callers required')
    for caller, count in callers.items():
        rows = [row for row in calls if row['caller_mangled'] == caller]
        need(len(rows) == count and len({tuple(row['call_range']) for row in rows}) == count,
             'complete distinct per-caller original API calls required')


def prepare_unit(api, *, transport_kind, full_tu_raw, abi_raw, source_path, source_bytes, probe_path, probe_bytes,
                 declarations, compiler_capture_pin, full_tu_compressed_bytes, full_tu_expanded_limit):
    need(type(transport_kind) is str and transport_kind == KIND, 'exact memory normalized transport required')
    need(type(full_tu_expanded_limit) is int and full_tu_expanded_limit == EFFECTIVE_LIMIT
         and type(full_tu_raw) is bytes and len(full_tu_raw) == EXPANDED_BYTES <= EFFECTIVE_LIMIT
         and hashlib.sha256(full_tu_raw).hexdigest() == EXPANDED_SHA
         and type(full_tu_compressed_bytes) is int and full_tu_compressed_bytes == COMPRESSED_BYTES,
         'exact bounded memory normalized stream required')
    need(str(source_path) == SOURCE_PATH and type(source_bytes) is bytes and len(source_bytes) == SOURCE_BYTES
         and hashlib.sha256(source_bytes).hexdigest() == SOURCE_SHA and compiler_capture_pin == CAPTURE_SHA,
         'exact original G642 source and compiler observation required')
    path = Path(legacy.__file__)
    need(hashlib.sha256(path.read_bytes()).hexdigest() == LEGACY_SHA, 'unchanged generic compiler consumer required')
    derived_abi, abi_receipt = abi_transport.normalize_abi(abi_raw)
    need(abi_receipt['selected_family'] == 'three-memory-g642', 'exact genuine G642 original ABI family required')
    prepared = legacy.prepare_unit(api, full_tu_raw=full_tu_raw, abi_raw=derived_abi, source_path=source_path,
        source_bytes=source_bytes, probe_path=probe_path, probe_bytes=probe_bytes, declarations=declarations,
        compiler_capture_pin=compiler_capture_pin, full_tu_compressed_bytes=full_tu_compressed_bytes,
        full_tu_expanded_limit=LEGACY_CEILING)
    need(hashlib.sha256(path.read_bytes()).hexdigest() == LEGACY_SHA, 'generic compiler consumer changed')
    need(prepared.get('schema') == 'whole-interface-original-tu-preparation-1'
         and prepared.get('raw_full_tu_sha256') == EXPANDED_SHA and prepared.get('original_source_sha256') == SOURCE_SHA
         and prepared.get('public_admission') is False, 'complete memory preparation identity differs')
    check_cases(prepared)
    need(prepared['abi_observation']['raw_probe_sha256'] == abi_receipt['derived_strict_sha256'],
         'unchanged legacy ABI reader must identify its actual derived strict memory input')
    return {**prepared, 'abi_observation': {**prepared['abi_observation'],
        'original_raw_probe_sha256': abi_receipt['original_sha256'],
        'paired_type_role_transport': abi_receipt}, 'normalized_transport': {'kind': KIND, 'source_family': 'three-same-thread-memory-1',
        'source_sha256': SOURCE_SHA, 'effective_expanded_limit_bytes': EFFECTIVE_LIMIT,
        'legacy_consumer_implementation_ceiling_bytes': LEGACY_CEILING,
        'normalized_expanded_bytes': EXPANDED_BYTES, 'normalized_expanded_sha256': EXPANDED_SHA,
        'compressed_bytes': COMPRESSED_BYTES, 'original_wire_expanded_sha256': ORIGINAL_WIRE_SHA,
        'original_minified_token_sha256': ORIGINAL_TOKEN_SHA,
        'original_wire_identity_is_normalized_identity': False, 'compiler_run_or_public_admission_inferred': False}}

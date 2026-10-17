"""2026-10-16 ET. Closed normalized transport into the selected semantic TU consumer.

This is the exact first V10-derived stream only. It establishes no compiler run,
transport provenance, ABI theorem or public admission. The enclosing ingress
must already have checked the complete original/derived/runtime/root closure.
"""
import hashlib
from pathlib import Path

from swdb._dx100_whole import compiler_unit_adapter_v4 as consumer
from swdb._dx100_whole import abi_role_transport_v1 as abi_transport

KIND='complete-original-tu-paired-type-gzip-2'
EFFECTIVE_LIMIT=201326592
LEGACY_CEILING=536870912
EXPANDED_BYTES=178924116
EXPANDED_SHA='1f0616302273d146fc88e1c676d25c41230432ee8ec259a92ae65f8fbb5755a3'
COMPRESSED_BYTES=12787585
ORIGINAL_WIRE_SHA='cd7f4fa566146b9b061c2084b52b1143efc054d4c4d75cbe4f7911c81e326622'
ORIGINAL_TOKEN_SHA='fa44d97fbaff20b5b16300d39128bb29e41d9600ba7db57202b50be09368f366'
CONSUMER_SHA='b5bd7293259f69ffe4e5d6094cb6bd46c2d5527ef95cd28d0aaa95d88529e6c6'


def need(condition,message):
    if not condition:raise ValueError(message)


def prepare_unit(api, *, transport_kind, full_tu_raw, abi_raw, source_path, source_bytes, probe_path, probe_bytes,
                 declarations, compiler_capture_pin, full_tu_compressed_bytes, full_tu_expanded_limit):
    """Apply the stricter transport contract before reaching legacy parsing.

    The legacy function has a fixed 512 MiB implementation parameter. Passing
    that unchanged sentinel below does not enlarge this wrapper's 192 MiB bound:
    the exact bytes/type/count/hash are checked first, and all parser input bytes
    are the same already checked full-TU object. The ABI inlet separately retains
    its original identity and passes an explicitly derived strict stream. The semantic reader is a separately pinned module; its full-TU
    consumer function is byte-identical to the original v3 function.
    """
    need(type(transport_kind) is str and transport_kind==KIND,'exact normalized transport discriminator required')
    need(type(full_tu_expanded_limit) is int and full_tu_expanded_limit==EFFECTIVE_LIMIT
        and type(full_tu_raw) is bytes and len(full_tu_raw)==EXPANDED_BYTES<=EFFECTIVE_LIMIT
        and hashlib.sha256(full_tu_raw).hexdigest()==EXPANDED_SHA
        and type(full_tu_compressed_bytes) is int and full_tu_compressed_bytes==COMPRESSED_BYTES,
        'exact bounded first normalized stream identity required')
    legacy_path=Path(consumer.__file__)
    need(hashlib.sha256(legacy_path.read_bytes()).hexdigest()==CONSUMER_SHA,'selected physical semantic compiler consumer required')
    derived_abi, abi_receipt=abi_transport.normalize_abi(abi_raw)
    need(abi_receipt['selected_family']=='first-source-v10','exact first-source original ABI family required')
    prepared=consumer.prepare_unit(api,full_tu_raw=full_tu_raw,abi_raw=derived_abi,source_path=source_path,source_bytes=source_bytes,
        probe_path=probe_path,probe_bytes=probe_bytes,declarations=declarations,compiler_capture_pin=compiler_capture_pin,
        full_tu_compressed_bytes=full_tu_compressed_bytes,full_tu_expanded_limit=LEGACY_CEILING)
    need(hashlib.sha256(legacy_path.read_bytes()).hexdigest()==CONSUMER_SHA,'semantic compiler consumer changed during preparation')
    need(prepared.get('schema')=='whole-interface-original-tu-preparation-1' and prepared.get('raw_full_tu_sha256')==EXPANDED_SHA
        and prepared.get('public_admission') is False,'legacy complete-TU preparation identity differs')
    need(prepared['abi_observation']['raw_probe_sha256']==abi_receipt['derived_strict_sha256'],
        'selected semantic ABI reader must identify its actual derived strict input')
    return {**prepared,'schema':'whole-interface-normalized-original-tu-preparation-1',
        'abi_observation':{**prepared['abi_observation'],
            'original_raw_probe_sha256':abi_receipt['original_sha256'],
            'paired_type_role_transport':abi_receipt},
        'normalized_transport':{'kind':KIND,'effective_expanded_limit_bytes':EFFECTIVE_LIMIT,
            'legacy_consumer_implementation_ceiling_bytes':LEGACY_CEILING,'normalized_expanded_bytes':EXPANDED_BYTES,
            'normalized_expanded_sha256':EXPANDED_SHA,'compressed_bytes':COMPRESSED_BYTES,
            'original_wire_expanded_sha256':ORIGINAL_WIRE_SHA,'original_minified_token_sha256':ORIGINAL_TOKEN_SHA,
            'original_wire_identity_is_normalized_identity':False,'compiler_run_or_public_admission_inferred':False}}

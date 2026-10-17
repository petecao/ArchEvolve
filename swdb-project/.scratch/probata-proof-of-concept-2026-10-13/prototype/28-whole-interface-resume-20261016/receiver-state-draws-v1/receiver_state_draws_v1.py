"""2026-10-16 ET. Inert, typed receiver/draw preparation; no source admission.

The launch owner must select the exact policy pin through its independent
admission mechanism. A matching hash binds bytes; it cannot attest the external
fresh/exclusive/quiescent premises. This module imports no project code, runs no
tools, and emits no replacement source function or arbitrary user callback.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat


SOURCE_KIND = 'dx100-whole-interface-source-v1'
MODEL_KIND = 'dx100-whole-interface-checked-body-1'
PROFILE = 'fresh-program-exclusive-quiescent-modeled-trace-v1'
SOURCE_SHA = '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
SOURCE_BYTES = 4524
HEADER_SHAS = {'MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',
    'MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174'}
INPUT_NAMES = frozenset({'source', 'full_tu', 'abi_observation', 'capture_receipt',
    'model_assembly', 'source_atlas', 'source_globals', 'statement_preparation',
    'runtime_receipt', 'assertion_header'})
PHYSICAL_ROLES = frozenset({'compiler_driver', 'compiler_wrapper',
    'device_configuration', 'address_projection', 'numeric_runtime'})
FLAGS = {
    'signed_shift_cpp17_arithmetic': 'C++17 signed-left-shift and arithmetic negative-right-shift implementation profile',
    'ieee_binary_rn': 'binary32/binary64 round-to-nearest, no fast-math, and the backend floating environment guards',
    'alu_minmax_unordered_first': 'pinned ALU unordered comparison selects the first operand',
}
PREMISES = {
    'fresh-host': 'A fresh C++ program supplies the twelve observed static globals, with no intervening mutation before source entry.',
    'exclusive-model-instance': 'This modeled trace exclusively controls the selected DX100 instance; all CPU/device interference is represented by the complete admitted trace.',
    'quiescent-entry': 'The modeled trace starts quiescent, with no prior pending command, construction, history, software tile/register owner, or registered region; no device payload value is asserted.',
    'valid-entry-metadata': 'Initial tile size/status metadata is in the selected valid/quiescent domain: Finished with an unknown size in 0..16384. No particular size, payload value, or payload initializedness is asserted.',
    'ordinary-allocation': 'Ordinary local storage comes from the exact checked original automatic declaration and live scope; allocation origin is not exclusive ordinary-memory access ownership.',
    'physical-runtime': 'The selected physical mapping, device configuration, compiler ABI, and numeric runtime policies apply to this trace under their exact pinned inputs.',
}
GLOBALS = {
    'REG_count': ('MAA.hpp', 'int', 'dxg_next'),
    'SPD_count': ('MAA.hpp', 'int', 'dxs_tile_next'),
    'SPD_data_cacheable': ('MAA.hpp', 'void *', 'dxs_mmio[0]'),
    'SPD_data_noncacheable': ('MAA.hpp', 'volatile void *', 'dxs_mmio[1]'),
    'SPD_size_noncacheable': ('MAA.hpp', 'volatile uint16_t *', 'dxs_mmio[2]'),
    'SPD_ready_noncacheable': ('MAA.hpp', 'volatile uint16_t *', 'dxs_mmio[3]'),
    'REG_noncacheable': ('MAA.hpp', 'volatile void *', 'dxs_mmio[4]'),
    'INSTR_opcode_datatype_optype_tdst1_tdst2': ('MAA_gem5.hpp', 'volatile uint64_t *', 'dxs_mmio[5]'),
    'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc': ('MAA_gem5.hpp', 'volatile uint64_t *', 'dxs_mmio[5]+8'),
    'INSTR_baseaddr': ('MAA_gem5.hpp', 'volatile uint64_t *', 'dxs_mmio[5]+16'),
    'MAA_end_addr': ('MAA_gem5.hpp', 'uint64_t', 'dxs_mmio[6]'),
    'region_count': ('MAA_gem5.hpp', 'int8_t', 'dxs_region_next'),
}
FROZEN = {
    'whole_value_backend_v1.h': 'c37481e56517d29729ffc83f2eb538cc5b5cb8ce5ab831babae3287cb332956f',
    'whole_adapters.h': 'e8efe60182d7fbd0d7c9f54c8fc6f70c235a91bd613cabd3be6ac893105c4a1a',
    'whole_value_builders_v1.h': '88f6bd0d310e8a2a6ad522ae15fec32b9f32b4ed6d792a314e8a365e0118824e',
    'whole_closed_routes_v1.h': '0168b2f78e0d5a6a6d42c8955ba45304533b8a0c63b92bebcabd50fd730969c7',
    'model-entry-v2/whole_model_v2.py': '7ddff742ec78573dec9ee53c071f57d88ed8fd4d4f819a05118456f72acafe61',
    'model-entry-v1/whole_model_v1.py': '75c99c39664fc9b7b40838622b8fa03835977c7afbf35c5aab2a5704c4f538f4',
    'source-integration-schema-v2.json': '433e3e6149b0cc3be9f4f7e16db6bfdc3b1dc912115dee88783f5bed1052f792',
    'source_program_globals_v1.py': '17bc9b0aefc7cadd5762f630b28c3ab97496f3cac17eb40bbd89deda1fe8cc77',
    'whole_interface_v4.py': '217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8',
    'source_dispatch_v3.py': 'd05d3ba716af2d88703636ffbf57bf0834acd5e59ee7ce3aebe0a72648a8b703',
    'compiler_unit_adapter_v2.py': '1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317',
    'source_argument_staging_v2.py': '79bdae72fd7b4de05771776684b5c6af275afb736313ece1df8790ae57ae6178',
    'source_statements_v1.py': '333148951b8e1c634600a7a0deb2abf312c4d708b1ca69fdd04429959518c0d1',
    'harness/cbmc_translator.py': '61a25090b66a5bd86a332a600973a048d3f38936dea2c6a088c8456d53d2e4d3',
}


class Refused(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Refused(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def object_sha(value):
    return sha(canonical(value))


def exact(value, keys, name):
    need(type(value) is dict and set(value) == set(keys), name + ' exact fields required')


def digest(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'lowercase SHA-256 required')
    return value


@dataclass(frozen=True)
class Pin:
    path: str
    bytes: int
    sha256: str

    def __post_init__(self):
        need(type(self.path) is str and Path(self.path).is_absolute(), 'absolute input path required')
        need(type(self.bytes) is int and self.bytes >= 0, 'exact nonnegative byte count required')
        digest(self.sha256)

    @classmethod
    def parse(cls, row):
        exact(row, {'path', 'bytes', 'sha256'}, 'physical pin')
        need(type(row['path']) is str and Path(row['path']).is_absolute(), 'absolute input path required')
        need(type(row['bytes']) is int and row['bytes'] >= 0, 'exact nonnegative byte count required')
        return cls(row['path'], row['bytes'], digest(row['sha256']))

    def row(self):
        return {'path': self.path, 'bytes': self.bytes, 'sha256': self.sha256}


@dataclass(frozen=True)
class OwnedSelection:
    """An externally selected pin, not an authority token or self-attestation."""
    policy: Pin


@dataclass(frozen=True)
class PreparedReceiver:
    c_text: str
    binding_json: bytes
    draw_plan_json: bytes
    integration_plan_json: bytes


def check_file(pin, *, retain=False, limit=8 * 1024 * 1024):
    need(type(pin) is Pin, 'typed physical pin required')
    path = Path(pin.path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path,
         'canonical physical regular input required')
    need(before.st_size == pin.bytes and (not retain or pin.bytes <= limit), 'input size or bounded document limit differs')
    hasher = hashlib.sha256()
    chunks = []
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
            if retain:
                chunks.append(chunk)
    need(path.lstat() == before and hasher.hexdigest() == pin.sha256,
         'physical input changed or hash differs')
    return b''.join(chunks) if retain else None


def document(pin):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'duplicate JSON key refused')
            result[key] = value
        return result
    try:
        return json.loads(check_file(pin, retain=True), object_pairs_hook=unique,
            parse_constant=lambda _value: (_ for _ in ()).throw(Refused('nonfinite JSON refused')))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Refused('bounded UTF-8 JSON input required') from error


def global_relation(name):
    if name in {'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc', 'INSTR_baseaddr'}:
        return {'kind': 'instruction-pointer-derived-only-after-allocation', 'model_base': 'dxs_mmio[5]',
            'offset_after_alloc': 16 if name == 'INSTR_baseaddr' else 8,
            'unallocated_source_value': 'null pointer', 'preallocation_use': 'setup-domain refusal'}
    return {'kind': 'source host field', 'model_field': GLOBALS[name][2]}


def check_globals(observation, context_sha, tu_sha):
    true_fields = {'fresh_program_interpretation_requires_root_admission',
        'pointer_null_is_source_semantic_value_not_raw_bit_claim', 'model_host_mapping_requires_derived_setup_state',
        'instruction_pointer_offsets_apply_only_after_alloc_not_to_null_initial_values'}
    false_fields = {'model_reset_called', 'alloc_MAA_called', 'init_MAA_called',
        'device_payload_initializedness_granted', 'device_ownership_granted',
        'preexisting_command_history_cleared', 'device_receiver_state_bound', 'public_admission'}
    exact(observation, {'schema', 'execution_mode', 'program_context_receipt_sha256', 'globals', 'full_tu_sha256'} | true_fields | false_fields, 'global observation')
    need(observation['schema'] == 'whole-interface-source-program-globals-1'
         and observation['execution_mode'] == 'fresh-cxx-program-globals'
         and observation['program_context_receipt_sha256'] == context_sha
         and observation['full_tu_sha256'] == tu_sha, 'same context/TU global observation required')
    need(all(observation[key] is True for key in true_fields)
         and all(observation[key] is False for key in false_fields), 'global observation boundary differs')
    rows = observation['globals']
    need(type(rows) is list and [row.get('name') for row in rows if type(row) is dict] == sorted(GLOBALS),
         'exact sorted twelve-global census required')
    for row in rows:
        exact(row, {'name', 'declaration_id', 'actual_type', 'source_type', 'source_range', 'header_path',
            'header_sha256', 'declaration_sha256', 'CXX_static_initialization', 'source_initial_value',
            'model_host_receiver_relation'}, 'source global')
        name = row['name']
        header, typ, _receiver = GLOBALS[name]
        pointer = '*' in typ
        need(type(row['declaration_id']) is str and row['declaration_id']
             and row['source_type'] == typ and type(row['actual_type']) is dict
             and re.findall(r'[A-Za-z_]\w*|\*', row['actual_type'].get('qualType', '')) == re.findall(r'[A-Za-z_]\w*|\*', typ), 'observed source declaration/type differs')
        need(type(row['source_range']) is list and len(row['source_range']) == 2
             and all(type(x) is int for x in row['source_range'])
             and 0 <= row['source_range'][0] < row['source_range'][1], 'direct global source span required')
        need(Path(row['header_path']).name == header and Path(row['header_path']).is_absolute(), 'global header path differs')
        need(row['header_sha256'] == HEADER_SHAS[header], 'frozen original source header differs')
        digest(row['declaration_sha256'])
        need(row['CXX_static_initialization'] == ('null pointer' if pointer else 'zero scalar')
             and (row['source_initial_value'] is None if pointer else type(row['source_initial_value']) is int and row['source_initial_value'] == 0)
             and row['model_host_receiver_relation'] == global_relation(name), 'source null/zero receiver mapping differs')


def check_allocations(rows, atlas, source_sha, modeled_threads):
    need(type(rows) is list and type(atlas) is dict and atlas.get('schema') == 'source-ordinary-cell-atlas-1'
         and type(atlas.get('objects')) is list and atlas['objects'], 'nonempty actual source atlas required')
    exact(atlas, {'schema', 'objects', 'cells', 'mmio_excluded_span', 'initialization_granted',
        'history_events_added', 'owned_premises', 'public_admission'}, 'ordinary atlas')
    mmio = (17179869184, 17179869184 + 8 * 32 * 16384 + 4 * 32 + 4 * 32 + 24)
    need(atlas['initialization_granted'] is False and type(atlas['history_events_added']) is int
         and atlas['history_events_added'] == 0 and atlas['public_admission'] is False
         and atlas['mmio_excluded_span'] == list(mmio)
         and atlas['owned_premises'] == ['source object identity/lifetime', 'guest→physical projection', 'complete CPU-access instrumentation'],
         'ordinary atlas cannot grant initializedness/history/admission')
    need(len(rows) == len(atlas['objects']) <= 64, 'one bounded original local allocation per atlas object required')
    spans, guest_spans, cells = [], [], []
    for index, (row, obj) in enumerate(zip(rows, atlas['objects'])):
        exact(obj, {'object_id', 'guest_base', 'physical_base', 'extent', 'dtype', 'source_pin', 'base_cell', 'cell_ids'}, 'ordinary atlas object')
        exact(row, {'object_index', 'object_id', 'caller', 'local_id', 'declaration_sha256', 'declaration_range',
            'scope_end_offset', 'allocation_thread', 'allocation_origin'}, 'ordinary allocation')
        need(row['object_index'] == index and type(row['object_index']) is int
             and row['object_id'] == obj['object_id'] and row['allocation_origin'] == 'checked-original-automatic-declaration',
             'allocation origin/index differs')
        need(type(row['allocation_thread']) is int and 0 <= row['allocation_thread'] < modeled_threads,
             'allocation producer thread outside admitted trace')
        need(all(type(row[key]) is str and row[key] for key in ('caller', 'local_id')), 'source allocation identities required')
        digest(row['declaration_sha256'])
        need(object_sha({'source_sha256': source_sha, 'caller': row['caller'], 'local_id': row['local_id'],
            'declaration_sha256': row['declaration_sha256']}) == obj['source_pin'], 'source local/atlas certificate differs')
        span = row['declaration_range']
        need(type(span) is list and len(span) == 2 and all(type(x) is int for x in span)
             and type(row['scope_end_offset']) is int and 0 <= span[0] < span[1] < row['scope_end_offset'] <= SOURCE_BYTES,
             'exact original declaration/scope bounds required')
        need(type(obj['dtype']) is int and 0 <= obj['dtype'] < 6 and type(obj['extent']) is int and obj['extent'] > 0
             and type(obj['base_cell']) is int and obj['base_cell'] >= 0
             and obj['base_cell'] + obj['extent'] <= 64, 'fixed backend ordinary cell capacity differs')
        width = 4 if obj['dtype'] < 3 else 8
        for key in ('guest_base', 'physical_base'):
            address = obj[key]
            need(type(address) is int and 0 <= address <= 2**64 - 1 - obj['extent'] * width and address % width == 0,
                 'aligned nonwrapping source/physical object address required')
            need(address + obj['extent'] * width <= mmio[0] or mmio[1] <= address, 'ordinary/MMIO alias refused')
        span = (obj['physical_base'], obj['physical_base'] + obj['extent'] * width)
        guest = (obj['guest_base'], obj['guest_base'] + obj['extent'] * width)
        need(all(span[1] <= old[0] or old[1] <= span[0] for old in spans), 'local alias/reuse requires a successor profile')
        need(all(guest[1] <= old[0] or old[1] <= guest[0] for old in guest_spans), 'local guest alias/reuse requires a successor profile')
        need(obj['cell_ids'] == list(range(obj['base_cell'], obj['base_cell'] + obj['extent']))
             and all(type(cell) is int for cell in obj['cell_ids']), 'complete contiguous object cell mapping required')
        cells += [{'cell': obj['base_cell'] + lane, 'physical_begin': obj['physical_base'] + lane * width,
            'physical_end': obj['physical_base'] + (lane + 1) * width, 'dtype': obj['dtype']} for lane in range(obj['extent'])]
        spans.append(span)
        guest_spans.append(guest)
    need(len({row['local_id'] for row in rows}) == len(rows), 'duplicate local allocation identity refused')
    need(len({obj['object_id'] for obj in atlas['objects']}) == len(rows), 'duplicate source object identity refused')
    cells.sort(key=lambda row: (row['physical_begin'], row['physical_end'], row['dtype']))
    need(type(atlas['cells']) is list and all(type(row) is dict and set(row) == {'cell', 'physical_begin', 'physical_end', 'dtype'}
         and all(type(value) is int for value in row.values()) for row in atlas['cells']), 'exact typed cell rows required')
    need(all(row['cell'] == index for index, row in enumerate(cells)) and atlas['cells'] == cells,
         'complete canonical physical cell census required')


def choice_hook_prefix(budget):
    """Exact reviewed V2 hook text; answer domain and draw budget stay separate."""
    return '''/* Checked-body hooks: preserve every ordinary property. */
#include <stdint.h>
#include <stddef.h>
#ifndef SWDB_CHECK
#error "public checked-property hooks must precede model assembly"
#endif
static uint32_t dws_choice_table[%d];
static unsigned dws_choice_used;
static unsigned dws_model_choose(unsigned alternatives) {
  SWDB_CHECK(alternatives>0,"whole-choice-domain");
  SWDB_CHECK(dws_choice_used<%du,"whole-choice-capacity");
  return dws_choice_table[dws_choice_used++] %% alternatives;
}
#define DXM_CHECK(condition,rule) SWDB_CHECK((condition),rule)
#define DXM_CHOOSE(alternatives) dws_model_choose(alternatives)
''' % (budget, budget)


def receiver_text(flags, budget, allocations, threads):
    """Fixed code only. These one-shot checks cannot authorize a context."""
    lines = ['/*2026-10-16 ET. Inert fixed receiver/draw proposal; external owned premises required. */',
        'static void dws_source_object_leave(unsigned object);',
        'static unsigned dws_receiver_entered_v1;',
        'static unsigned dws_local_live_v1[%d];' % len(allocations),
        'static unsigned dws_local_seen_v1[%d];' % len(allocations),
        'static int dws_local_origin_v1[%d];' % len(allocations),
        'static void dws_prepare_receiver_v1(void) {',
        '  SWDB_CHECK(dws_receiver_entered_v1==0,"receiver-single-entry");',
        '  SWDB_CHECK(DXM_CELLS==64 && DXM_TILES==32 && DXG_REGS==32 && DXC_REGIONS==256 && DXP_VALUE_BOUND==2 && DXP_TILE_WORDS==16384,"receiver-fixed-model-domain");',
        '  SWDB_CHECK(dxm_count==0 && dxm_event_count==0 && dxc_count==0 && dxc_constructing==0 && dxa_count==0 && dxp_count==0,"receiver-untouched-bookkeeping");',
        '  SWDB_CHECK(dxg_next==0 && dxs_tile_next==0 && dxs_region_next==0 && dxs_allocated==0 && dws_print_count==0 && dws_choice_used==0,"receiver-untouched-host-state");',
        '  SWDB_CHECK(dxt_runtime.signed_shift_cpp17_arithmetic==0 && dxt_runtime.ieee_binary_rn==0 && dxt_runtime.alu_minmax_unordered_first==0,"receiver-untouched-runtime-flags");',
        '  for(unsigned i=0;i<DXM_CELLS;++i) SWDB_CHECK(dxm_initialized[i]==0,"receiver-ordinary-uninitialized");',
        '  for(unsigned i=0;i<DXG_REGS*4;++i) SWDB_CHECK(dxg_image[i].initialized==0,"receiver-register-uninitialized");',
        '  for(unsigned i=0;i<DXC_COMMANDS;++i) SWDB_CHECK(dxg_roles[i].bound==0,"receiver-unbound-roles");',
        '  for(unsigned i=0;i<DXM_TILES;++i) SWDB_CHECK(dxm_tile_owner[i]==0 && dxz_sizes[i]==0,"receiver-untouched-tile-ghosts");',
        '  for(unsigned i=0;i<DXG_REGS;++i) SWDB_CHECK(dxg_owner[i]==0,"receiver-untouched-register-ghosts");',
        '  for(unsigned i=0;i<DXC_REGIONS;++i) SWDB_CHECK(dxr_regions[i].begin==0 && dxr_regions[i].end==0,"receiver-empty-regions");',
        '  for(unsigned i=0;i<7;++i) SWDB_CHECK(dxs_mmio[i]==0,"receiver-null-source-setup");',
        '  dws_receiver_entered_v1=1;',
        '  for(unsigned i=0;i<DXM_TILES;++i) { dxm_tile_owner[i]=-1; dxz_sizes[i]=UINT_MAX; }',
        '  for(unsigned i=0;i<DXG_REGS;++i) dxg_owner[i]=-1;',
        '  for(unsigned i=0;i<%du;++i) {' % len(allocations),
        '    SWDB_CHECK(dws_local_live_v1[i]==0 && dws_local_seen_v1[i]==0 && dws_local_origin_v1[i]==0,"receiver-untouched-local-ghosts");',
        '    dws_local_origin_v1[i]=-1;', '  }']
    lines += ['  dxt_runtime.%s=%du;' % (name, flags[name]) for name in FLAGS]
    lines += ['  for(unsigned i=0;i<%du;++i) dws_choice_table[i]=(uint32_t)swdb_next();' % budget, '}',
        'static void dws_local_require_v1(unsigned object,unsigned accessing_thread) {',
        '  SWDB_CHECK(dws_receiver_entered_v1==1,"receiver-before-source");',
        '  SWDB_CHECK(object<%du && accessing_thread<%du,"ordinary-live-domain");' % (len(allocations), threads),
        '  SWDB_CHECK(dws_local_live_v1[object]==1 && dws_local_origin_v1[object]>=0,"ordinary-live-allocation");',
        '  /* Allocation origin is not exclusive access: another admitted thread may read/CAS. */', '}']
    for index, row in enumerate(allocations):
        lines += ['static void dws_local_enter_%d_v1(void) {' % index,
            '  SWDB_CHECK(dws_receiver_entered_v1==1 && dws_local_live_v1[%d]==0 && dws_local_seen_v1[%d]==0,"ordinary-fresh-local-lifetime");' % (index, index),
            '  dws_local_seen_v1[%d]=1; dws_local_live_v1[%d]=1; dws_local_origin_v1[%d]=%d;' % (index, index, index, row['allocation_thread']), '}',
            'static void dws_local_leave_%d_v1(void) {' % index,
            '  dws_local_require_v1(%du,%du);' % (index, row['allocation_thread']),
            '  dws_source_object_leave(%du);' % index,
            '  dws_local_live_v1[%d]=0; dws_local_origin_v1[%d]=-1;' % (index, index), '}']
    return '\n'.join(lines) + '\n'


def _prepare(selection: OwnedSelection) -> PreparedReceiver:
    need(type(selection) is OwnedSelection and type(selection.policy) is Pin, 'externally selected typed policy pin required')
    policy = document(selection.policy)
    exact(policy, {'schema', 'selection_owner', 'source_kind', 'model_kind', 'profile', 'inputs',
        'context_receipt', 'physical_inputs', 'frozen_inputs', 'choice_budget', 'modeled_threads',
        'full_tu_canonical_sha256'}, 'receiver selection policy')
    need(policy['schema'] == 'whole-interface-receiver-selection-1' and type(policy['selection_owner']) is str
         and policy['selection_owner'] and policy['source_kind'] == SOURCE_KIND and policy['model_kind'] == MODEL_KIND
         and policy['profile'] == PROFILE, 'closed source/model/profile/owner required')
    budget, threads = policy['choice_budget'], policy['modeled_threads']
    need(type(budget) is int and 1 <= budget <= 256 and type(threads) is int and threads in (1, 2), 'exact choice budget/thread domain required')
    digest(policy['full_tu_canonical_sha256'])
    exact(policy['inputs'], INPUT_NAMES, 'selected input census')
    inputs = {name: Pin.parse(row) for name, row in policy['inputs'].items()}
    context_pin = Pin.parse(policy['context_receipt'])
    need(inputs['source'].sha256 == SOURCE_SHA and inputs['source'].bytes == SOURCE_BYTES, 'first source fixture scope differs')
    exact(policy['physical_inputs'], PHYSICAL_ROLES, 'physical role census')
    physical = {name: Pin.parse(row) for name, row in policy['physical_inputs'].items()}
    exact(policy['frozen_inputs'], FROZEN, 'frozen implementation census')
    frozen = {name: Pin.parse(row) for name, row in policy['frozen_inputs'].items()}
    for name, expected in FROZEN.items():
        need(expected is not None and frozen[name].sha256 == expected, 'frozen implementation differs')
    all_pins = [selection.policy, context_pin, *inputs.values(), *physical.values(), *frozen.values()]
    for pin in all_pins:
        check_file(pin)
    context = document(context_pin)
    exact(context, {'schema', 'owner', 'source_kind', 'model_kind', 'profile', 'execution_mode', 'bindings',
        'physical_inputs_sha256', 'modeled_threads', 'numeric_flags', 'premises', 'ordinary_allocations'}, 'owned context receipt')
    need(context['schema'] == 'whole-interface-program-context-1' and context['owner'] == policy['selection_owner']
         and context['source_kind'] == SOURCE_KIND and context['model_kind'] == MODEL_KIND
         and context['profile'] == PROFILE and context['execution_mode'] == 'fresh-cxx-program-globals'
         and context['modeled_threads'] == threads and type(context['modeled_threads']) is int,
         'exact owned fresh/exclusive/quiescent context required')
    need(context['bindings'] == {name: pin.sha256 for name, pin in inputs.items() if name != 'source_globals'}
         and context['physical_inputs_sha256'] == object_sha(policy['physical_inputs']), 'context source/physical/runtime binding differs')
    need(type(context['premises']) is list and len(context['premises']) == len(PREMISES), 'complete owned premise census required')
    for row, name in zip(context['premises'], sorted(PREMISES)):
        exact(row, {'rule', 'statement', 'owner', 'record_assumption'}, 'owned premise')
        need(row == {'rule': name, 'statement': PREMISES[name], 'owner': context['owner'], 'record_assumption': True},
             'exact owned recorded premise required')
    runtime = document(inputs['runtime_receipt'])
    exact(runtime, {'schema', 'evidence_kind', 'owner', 'physical_inputs_sha256', 'numeric_flags'}, 'numeric/runtime selection receipt')
    need(runtime['schema'] == 'whole-interface-runtime-selection-1'
         and runtime['evidence_kind'] == 'selected-configuration-and-owned-numeric-policies'
         and runtime['owner'] == context['owner'] and runtime['physical_inputs_sha256'] == context['physical_inputs_sha256'],
         'exact runtime receipt and context numeric flags required')
    exact(context['numeric_flags'], FLAGS, 'numeric flags')
    exact(runtime['numeric_flags'], FLAGS, 'runtime numeric flags')
    flag_values = {}
    for name, row in context['numeric_flags'].items():
        exact(row, {'value', 'policy', 'runtime_receipt_sha256'}, 'numeric flag binding')
        # The runtime receipt cannot contain its own hash. That linkage is made
        # by the externally selected context, after runtime bytes are finalized.
        need(type(row['value']) is int and row['value'] in (0, 1) and row['policy'] == FLAGS[name]
             and row['runtime_receipt_sha256'] == inputs['runtime_receipt'].sha256, 'owned numeric flag policy differs')
        need(runtime['numeric_flags'][name] == {key: row[key] for key in ('value', 'policy')},
             'runtime flag value/policy differs from selected context')
        flag_values[name] = row['value']
    observation = document(inputs['source_globals'])
    check_globals(observation, context_pin.sha256, policy['full_tu_canonical_sha256'])
    header_pins = {}
    for row in observation['globals']:
        path = row['header_path']
        need(path not in header_pins or header_pins[path] == row['header_sha256'], 'global header pin collision')
        header_pins[path] = row['header_sha256']
    for path, expected in header_pins.items():
        pin = Pin(path, Path(path).lstat().st_size, expected)
        check_file(pin)
        all_pins.append(pin)
    atlas, assembly, statements = (document(inputs[name]) for name in ('source_atlas', 'model_assembly', 'statement_preparation'))
    check_allocations(context['ordinary_allocations'], atlas, inputs['source'].sha256, threads)
    need(type(assembly) is dict and set(assembly) == {'entry', 'c_text', 'instances', 'atlas'}
         and assembly['atlas'] == atlas and type(assembly['c_text']) is str, 'exact checked-body assembly envelope required')
    entry = assembly['entry']
    need(entry.get('kind') == 'proof_semantics' and entry.get('target') == 'dx100-mmio'
         and entry.get('contract_form') == MODEL_KIND and entry.get('public_admission') is False
         and entry.get('source_preconditions_assumed') is False
         and entry.get('model', {}).get('sha256') == sha(assembly['c_text'].encode())
         and entry['model'].get('source_atlas_sha256') == object_sha(atlas)
         and entry.get('harness_draws') == {'object': 'dws_choice_table', 'scalar_type': 'uint32_t',
            'count': budget, 'independent': True, 'draw_before_source_unit': True}, 'bound concrete model/draw table identity differs')
    need(assembly['c_text'].startswith(choice_hook_prefix(budget)), 'fatal V2 choice hooks differ')
    for name in ('whole_value_backend_v1.h', 'whole_adapters.h', 'whole_value_builders_v1.h', 'whole_closed_routes_v1.h'):
        body = check_file(frozen[name], retain=True).decode('utf-8')
        need(assembly['c_text'].count(body) == 1 and frozen[name].row() in entry['model']['source_inputs'],
             'concrete checked backend bytes/provenance missing or duplicated')
    need(type(statements) is dict and statements.get('schema') == 'whole-interface-source-statements-1'
         and statements.get('original_full_tu_sha256') == policy['full_tu_canonical_sha256']
         and statements.get('original_source_sha256') == SOURCE_SHA
         and statements.get('assertion_header_pin') == inputs['assertion_header'].row()
         and type(statements.get('text')) is str and statements.get('generated_c_sha256') == sha(statements['text'].encode()),
         'actual source/TU/assertion/statement identity differs')
    code = receiver_text(flag_values, budget, context['ordinary_allocations'], threads)
    draw_plan = {'schema': 'whole-interface-harness-draw-plan-1', 'model_kind': MODEL_KIND,
        'model_assembly_sha256': inputs['model_assembly'].sha256, 'count': budget, 'scalar_type': 'uint32_t',
        'domain': [0, 2**32 - 1], 'independent_calls': budget, 'draw_symbol': 'swdb_next',
        'draw_semantics': 'independent full signed-64 oracle slots cast to uint32; native/differential/replay consume the same ordered recorded slots; no assume, range filter, seed or desired-value restriction',
        'producer_plan_rows': [{'name': 'whole_choice_' + str(index), 'role': 'whole-model-choice', 'ctype': 'uint32_t'}
            for index in range(budget)],
        'producer_capacity': 'count every added Plan draw before fixing capacity; retain swdb.oracle_capacity fatal guard',
        'order': ['one-shot receiver checks', 'all independent scalar draws', 'original source function'],
        'choice_zero_and_exhaustion': 'unchanged fatal whole-choice-domain and whole-choice-capacity checks',
        'budget_failure': 'checked property failure, never assume/truncate'}
    integration = {'schema': 'whole-interface-receiver-integration-plan-1',
        'statement_preparation_sha256': inputs['statement_preparation'].sha256,
        'original_source_text_unchanged': True, 'before_source': 'dws_prepare_receiver_v1();',
        'translation_unit_order': ['pinned harness prelude', 'pinned checked-body assembly',
            'fixed receiver/lifetime hooks with forward declaration', 'source lifetime helper and instrumented original lowered function',
            'Plan-bound harness invokes one-shot preparation then source once'],
        'allocation_hooks': context['ordinary_allocations'],
        'enter': 'insert fixed object-specific enter hook before original array descriptor/initializer stores at its checked declaration',
        'ordinary_access': 'insert live-allocation/admitted-thread require at every original CPU access and ordinary device memory footprint; no origin-thread equality',
        'leave': 'replace each existing pending-command lifetime leave with the corresponding fixed leave hook at every checked exit',
        'draw_consumer': 'public harness must register all independent oracle slots in Plan in the exact draw order for CBMC/native/differential/replay; retain the pinned swdb_next implementation and fatal oracle capacity',
        'public_source_consumer': 'must independently enforce complete source/CPU/lifetime/RTE/unwinding/assumption/method closure; these snippets do not install that consumer'}
    binding = {'schema': 'whole-interface-receiver-state-binding-1', 'source_kind': SOURCE_KIND, 'model_kind': MODEL_KIND,
        'policy_sha256': selection.policy.sha256, 'program_context_receipt_sha256': context_pin.sha256,
        'source_globals_observation_sha256': inputs['source_globals'].sha256, 'host_globals': observation['globals'],
        'receiver_c_sha256': sha(code.encode()), 'harness_draw_plan_sha256': object_sha(draw_plan),
        'integration_plan_sha256': object_sha(integration), 'record_assumptions': context['premises'],
        'initial_receiver': {'ordinary_initialized': 0, 'register_initialized': 0, 'tile_image_entries': 0,
            'tile_register_owner': -1, 'tile_size': 'UINT_MAX unknown sentinel', 'payload_values': 'not assigned or granted',
            'prior_model_histories': 'absent by explicit owned entry premise; no count/history is reset',
            'ordinary_lifetimes': 'inactive until checked original local allocation hook; origin does not restrict other admitted threads'},
        'numeric_flags': context['numeric_flags'], 'input_pins': policy['inputs'], 'physical_inputs': policy['physical_inputs'],
        'scope': 'inert first-source-fixture modeled trace preparation; external owned premises, not a hardware refinement theorem',
        'remaining_admission': 'root-selected actual context and complete public producer/consumer integration required'}
    for pin in all_pins:
        check_file(pin)
    return PreparedReceiver(code, canonical(binding), canonical(draw_plan), canonical(integration))


def prepare(selection: OwnedSelection) -> PreparedReceiver:
    """Validate selected physical receipts and return immutable preparation.

    Missing/malformed metadata refuses; a typed selection still requires its
    independent launch-owner admission. No actual observation is inferred here.
    """
    try:
        return _prepare(selection)
    except Refused:
        raise
    except (OSError, TypeError, KeyError, AttributeError, ValueError, OverflowError) as error:
        raise Refused('malformed, unavailable, or inconsistent receiver input') from error

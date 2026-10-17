"""2026-10-16 ET. Synthetic scalar trace fixture; no source/hardware refinement.

Preparation uses the standard library only. Nothing here launches a child or
imports project code. The root supplies a separate public-prove execution test.
"""
import hashlib
import json
from pathlib import Path


ENTRY = 'semantics.dx100_memory_trace_fixture_0_2'
POLICY_ID = 'dx100-synthetic-scalar-memory-trace-1'
CONSTANTS = {'DX_K': 2, 'DX_NT': 4, 'DX_NR': 1, 'DX_NM': 2, 'DX_TS': 1}
QUERY_PROTOTYPES = {
    'swdb_t28_claim': 'int swdb_t28_claim(int thread, int tile, int bytes)',
    'swdb_t28_cpu_write': 'int swdb_t28_cpu_write(int thread, int cell, int value)',
    'swdb_t28_cpu_read': 'int swdb_t28_cpu_read(int thread, int cell)',
    'swdb_t28_cpu_cas': 'int swdb_t28_cpu_cas(int thread, int cell, int expected, int desired)',
    'swdb_t28_issue': 'int swdb_t28_issue(int thread, int access, int region, int cell, int tile, int bytes, int value)',
    'swdb_t28_wait': 'int swdb_t28_wait(int tile)',
    'swdb_t28_tile_read': 'int swdb_t28_tile_read(int thread, int tile, int bytes)',
    'swdb_t28_pending': 'int swdb_t28_pending(int command)',
    'swdb_t28_result': 'int swdb_t28_result(int command)',
    'swdb_t28_ready': 'int swdb_t28_ready(int tile)',
}
WP_REFUSAL = r'requires \false; assigns \nothing;'
SCOPE = ('Synthetic scalar event traces use abstract cells and tile masks only, with four independently '
         'drawn initialized scalar choice cells and a fatal checked choice budget; all real DX100 calls are '
         'unsupported. This fixture supplies no header-body, CPU-access, address-translation, typed-value, '
         'hardware-counterexample, interleaving-completeness or current-version refinement certificate.')
TRUST = {
    'mmio_ordering': 'The pinned MMIO implements call semantics including ordering; its wait fence lacks a memory clobber, a portability note independent of candidate artifacts.',
    'cross_core_filter': 'A DX100 store remains visible if the snoop filter drops its line before the write reaches L3.',
    'cross_core_write_buffer': 'A DX100 store remains visible when L3 passes a write below it because no block can be allocated.',
    'no_stale_cpu_copy': 'No stale CPU copy survives a DX100 store (owner Eric).',
    'one_instance': 'All commands belong to one DX100 instance.',
}
SOURCE_PINS = {
    'tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json': 'd48a3971f2e9421e736d72ff160074f22e9cbbb7c9c756ef52457a5c4314b3b6',
    'apps/dx100/benchmarks/API/MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',
    'apps/dx100/benchmarks/API/MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174',
    'tests/fixtures/proof/dx100/gem5-e4fc4af/IF.cc': 'fd7dd67f35f63ff6ed9ef0b8ce36cb60cc6d63b20fe9c0796e648bff82da6561',
    'tests/fixtures/proof/dx100/gem5-e4fc4af/SPD.cc': '9e6bb3672be95954e8816c054b4032f95811a3085ca6df418aed90ad1e852b4a',
}


class Refused(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_inventory(project):
    """Read closed source inventory only; no kernel/offload source is opened."""
    project = Path(project)
    for name, sha in SOURCE_PINS.items():
        if digest((project / name).read_bytes()) != sha:
            raise Refused('immutable source differs: ' + name)
    return json.loads((project / next(iter(SOURCE_PINS))).read_text())


def ghost_text():
    # The existing proof-semantics reader requires one ghost declaration. This
    # compatibility marker is never read by the scalar trace implementation.
    return '/* 2026-10-16 ET. Compatibility ghost, never observed. */\nghost int swdb_t28_marker[1];\n'


def state_text():
    lines = ['/* 2026-10-16 ET. Closed scalar event state; no caller pointers. */',
             '/* Canonical independent harness draws supply four fresh choice cells. */',
             'int dx_tile_data[DX_NT][DX_TS];', 'static int tr_count = 0;', 'static int tr_picks = 0;']
    lines += [f'static int tr_owner{i} = -1;' for i in range(4)]
    lines += [f'static int tr_mem{i} = 0;' for i in range(2)]
    for slot in range(2):
        for name in ('pending', 'thread', 'access', 'region', 'cell', 'tile', 'mask', 'value', 'issue', 'later', 'writes', 'result'):
            lines.append(f'static int tr_c{slot}_{name} = 0;')
    return '\n'.join(lines) + '\n'


def model_text():
    """Generate scalar slots; four initialized choice cells are the only array reads."""
    out = [r'''/* 2026-10-16 ET. CBMC synthetic trace model, deliberately no real API body.
 * Abstract cells 0/1 are disjoint physical lines; their registered region IDs
 * are respectively 0/1. A trace is one fixed sequential event order over two
 * thread IDs, four physical tiles, at most two commands and one later CPU
 * write per unfinished gather. Four independent initialized harness cells supply
 * at most four fresh nondeterministic choices. Values are int in 0..31, never FP
 * or bit images. The choice budget is checked, never silently recycled.
 * No completion is inferred from a known value. Ready is a LOGICAL ghost query:
 * the pinned header's wait_ready blocks, and has no get_tile_ready operation.
 * All domains/capacities use checked obligations; only choice-bit selection is
 * nondeterministic. No source entry precondition or desired result is assumed.
 */
#define TR_CHECK(c, r) SWDB_CHECK((c), DX_RULE(r))
static void tr_thread(int thread) { TR_CHECK(thread == 0 || thread == 1,"thread_domain"); }
static void tr_cell(int cell) { TR_CHECK(cell == 0 || cell == 1,"cell_domain"); }
static void tr_value(int value) { TR_CHECK(0 <= value && value <= 31,"value_domain"); }
static int tr_mask(int tile, int bytes) {
  TR_CHECK(0 <= tile && tile < 4,"tile_domain");
  TR_CHECK(bytes == 4 || bytes == 8,"width_domain");
  TR_CHECK(bytes == 4 || tile < 3,"pair_domain");
  return (bytes == 4 ? 1 : 3) << tile;
}
static int tr_owner(int tile) {
  return tile == 0 ? tr_owner0 : tile == 1 ? tr_owner1 : tile == 2 ? tr_owner2 : tr_owner3;
}
static void tr_owned(int thread, int mask) {
  tr_thread(thread);
''']
    for tile in range(4):
        out.append(f'  if (mask & {1 << tile}) TR_CHECK(tr_owner{tile} == thread,"tile_ownership");')
    out += ['}', 'static int tr_pick(void) {',
            '  SWDB_CHECK(0 <= tr_picks && tr_picks < 4,"swdb.ghost_capacity");',
            '  int draw = tr_picks == 0 ? dx_tile_data[0][0] : tr_picks == 1 ? dx_tile_data[1][0] :',
            '             tr_picks == 2 ? dx_tile_data[2][0] : dx_tile_data[3][0];',
            '  tr_picks = tr_picks + 1; return (int)((unsigned int)draw % 2u);', '}',
            'static int tr_memory(int cell) { return cell == 0 ? tr_mem0 : tr_mem1; }',
            'static void tr_set_memory(int cell, int value) { if (cell == 0) tr_mem0 = value; else tr_mem1 = value; }']
    for slot in range(2):
        p = f'tr_c{slot}_'
        out += [f'static void tr_cover{slot}(void) {{', f'  if ({p}pending) {{',
                f'    if ({p}access == 1) {{',
                # Each actual later write supplies one additional history value.
                f'      int pick = {p}writes ? tr_pick() : 0;',
                f'      {p}result = pick ? {p}later : {p}issue;',
                '    } else {', f'      tr_set_memory({p}cell, {p}value);', '    }',
                f'    {p}pending = 0;', '  }', '}']
    out += ['static void swdb_dx_init(void) {', '  tr_count = 0; tr_picks = 0; tr_mem0 = 0; tr_mem1 = 0;']
    for tile in range(4):
        out.append(f'  tr_owner{tile} = -1;')
    for slot in range(2):
        for name in ('pending', 'thread', 'access', 'region', 'cell', 'tile', 'mask', 'value', 'issue', 'later', 'writes', 'result'):
            out.append(f'  tr_c{slot}_{name} = 0;')
    out += ['}', 'static void swdb_dx_check_exit(void) {',
            '  SWDB_CHECK(!tr_c0_pending && !tr_c1_pending,"swdb.dx100_memory_domain");', '}',
            QUERY_PROTOTYPES['swdb_t28_claim'] + ' {', '  tr_thread(thread);', '  int mask = tr_mask(tile, bytes);']
    for tile in range(4):
        out.append(f'  if (mask & {1 << tile}) TR_CHECK(tr_owner{tile} == -1,"tile_already_owned");')
    for tile in range(4):
        out.append(f'  if (mask & {1 << tile}) tr_owner{tile} = thread;')
    out += ['  return 0;', '}', 'static void tr_cpu_access(int thread, int cell, int write) {',
            '  tr_thread(thread); tr_cell(cell);']
    for slot in range(2):
        p = f'tr_c{slot}_'
        out += [f'  if ({p}pending && {p}cell == cell) {{',
                f'    TR_CHECK({p}access != 2,"store_footprint_cpu_access");',
                f'    if (write) TR_CHECK({p}thread != thread,"same_thread_read_footprint_write");', '  }']
    out += ['}', QUERY_PROTOTYPES['swdb_t28_cpu_read'] + ' {',
            '  tr_cpu_access(thread, cell, 0); return tr_memory(cell);', '}',
            QUERY_PROTOTYPES['swdb_t28_cpu_write'] + ' {',
            '  tr_cpu_access(thread, cell, 1); tr_value(value);']
    for slot in range(2):
        p = f'tr_c{slot}_'
        out += [f'  if ({p}pending && {p}access == 1 && {p}cell == cell) {{',
                f'    SWDB_CHECK({p}writes == 0,"swdb.ghost_capacity");',
                f'    {p}later = value; {p}writes = 1;', '  }']
    out += ['  tr_set_memory(cell, value); return 0;', '}',
            QUERY_PROTOTYPES['swdb_t28_cpu_cas'] + ' {',
            '  tr_value(expected); tr_value(desired);',
            '  int actual = swdb_t28_cpu_read(thread, cell);',
            '  if (actual == expected) { swdb_t28_cpu_write(thread, cell, desired); return 1; }',
            '  return 0;', '}', QUERY_PROTOTYPES['swdb_t28_issue'] + ' {',
            '  tr_thread(thread); tr_cell(cell); tr_value(value);',
            '  TR_CHECK(access == 1 || access == 2,"access_domain");',
            '  TR_CHECK(region == cell,"region_footprint_correspondence");',
            '  int mask = tr_mask(tile, bytes); tr_owned(thread, mask);',
            '  SWDB_CHECK(tr_count < 2,"swdb.ghost_capacity");']
    for slot in range(2):
        p = f'tr_c{slot}_'
        out += [f'  if ({p}pending && ((access == 1 && tile == {p}tile) ||',
                f'      ({p}region == region && (access == 2 || {p}access == 2)))) tr_cover{slot}();']
    for slot in range(2):
        p = f'tr_c{slot}_'
        out += [f'  if ({p}pending) {{',
                f'    TR_CHECK(!(mask & {p}mask) || (access == 2 && {p}access == 2),"pending_tile_write");',
                f'    TR_CHECK(cell != {p}cell || (access == 1 && {p}access == 1),"device_memory_conflict");', '  }']
    out += ['  int command = tr_count;', '  if (command == 0) {']
    for slot in range(2):
        if slot:
            out.append('  } else {')
        p = f'tr_c{slot}_'
        for name, expr in {'pending': '1', 'thread': 'thread', 'access': 'access', 'region': 'region',
                           'cell': 'cell', 'tile': 'tile', 'mask': 'mask', 'value': 'value',
                           'issue': 'tr_memory(cell)', 'later': '0', 'writes': '0', 'result': '0'}.items():
            out.append(f'    {p}{name} = {expr};')
    out += ['  }', '  tr_count = tr_count + 1; return command;', '}',
            QUERY_PROTOTYPES['swdb_t28_wait'] + ' {', '  int mask = tr_mask(tile, 4);']
    for slot in range(2):
        out.append(f'  if (tr_c{slot}_pending && (tr_c{slot}_mask & mask)) tr_cover{slot}();')
    out += ['  return 0;', '}', QUERY_PROTOTYPES['swdb_t28_tile_read'] + ' {',
            '  int mask = tr_mask(tile, bytes); tr_owned(thread, mask);']
    for slot in range(2):
        out.append(f'  TR_CHECK(!tr_c{slot}_pending || tr_c{slot}_access != 1 || !(tr_c{slot}_mask & mask),"pending_tile_write");')
    out += ['  return 0;', '}', QUERY_PROTOTYPES['swdb_t28_pending'] + ' {',
            '  TR_CHECK(0 <= command && command < tr_count,"command_domain");',
            '  return command == 0 ? tr_c0_pending : tr_c1_pending;', '}',
            QUERY_PROTOTYPES['swdb_t28_result'] + ' {',
            '  TR_CHECK(0 <= command && command < tr_count,"command_domain");',
            '  TR_CHECK(!swdb_t28_pending(command),"pending_tile_write");',
            '  TR_CHECK((command == 0 ? tr_c0_access : tr_c1_access) == 1,"result_domain");',
            '  return command == 0 ? tr_c0_result : tr_c1_result;', '}',
            QUERY_PROTOTYPES['swdb_t28_ready'] + ' {',
            '  int mask = tr_mask(tile, 4);',
            '  int pending = (tr_c0_pending && (tr_c0_mask & mask)) || (tr_c1_pending && (tr_c1_mask & mask));',
            '  int ready = pending ? tr_pick() : 1;',
            '  if (ready) swdb_t28_wait(tile);', '  return ready;', '}', '']
    return '\n'.join(out)


def components():
    return {'ghost': ghost_text(), 'state': state_text(), 'c': model_text(),
            # A definition avoids an empty/nested ACSL annotation in the old
            # reader. It introduces no axiom and is unused by all contracts.
            'logic': 'logic integer swdb_t28_identity_20261016(integer value) = value;\n'}


def policy_document():
    return {'date': '2026-10-16 ET', 'id': POLICY_ID, 'entry': ENTRY,
            'components': {k: digest(v.encode()) for k, v in components().items()},
            'constants': CONSTANTS, 'queries': QUERY_PROTOTYPES, 'query_contract': WP_REFUSAL,
            'calls_supported': [], 'pointer_calls': [], 'scope': SCOPE,
            'source_pins': SOURCE_PINS, 'requires_fresh_model_equality': True,
            'requires_fresh_entry_sha256': True, 'requires_exact_complete_inventory': True}


def transform(data, library, *, project=None):
    """testkit.dx100_trust semantics_transform; writes fixture library only.

    This builder is inert until its parent explicitly invokes it during an
    admitted public test. It does not modify the installed source library.
    """
    library = Path(library)
    project = Path(project) if project else Path(__file__).resolve().parents[4]
    installed = (project / 'library').resolve()
    if library.resolve() == installed or installed in library.resolve().parents:
        raise Refused('synthetic fixture builder cannot edit the installed library')
    manifest = source_inventory(project)
    # The legacy YAML's inventory references kernel source. Remove only its
    # disposable fixture copy before validation, so this synthetic suite never
    # validates or hashes that kernel. The installed readable 0.1 stays intact.
    (library / 'proof_semantics/dx100_bfs_0_1.yaml').unlink(missing_ok=True)
    data.clear()
    data.update(id=ENTRY, kind='proof_semantics', formal_frame=1, target='dx100-mmio', clauses=[],
                hardware_interface={'id': 'dx100-mmio', 'version': '1.0-e4fc4af', 'gem5_commit': manifest['upstream_commit']},
                version='0.2', sequence=2, constants=dict(CONSTANTS), wp={},
                provenance={'origin': {'probata_ticket': '28', 'created': '2026-10-16 ET', 'scope': 'synthetic abstract trace only'}},
                description=SCOPE, declaration_inventory={k: manifest[k] for k in ('sources', 'declarations')})
    data['inventory'] = {'sources': manifest['sources'], 'calls': sorted({r['name'] for r in manifest['declarations']})}
    owner = 'Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
    data['rules'] = [{'id': 'synthetic_trace_scope', 'statement': SCOPE,
                      'assumed': {'owner': owner}, 'record_assumption': True},
                     {'id': 'region_stall', 'statement': 'The abstract region conflict follows the pinned global IF stall.',
                      'cites': {'gem5_commit': manifest['upstream_commit'], 'path': 'src/mem/MAA/IF.cc', 'lines': '193-218'}},
                     {'id': 'pair_width', 'statement': 'An eight-byte abstract role covers both physical four-byte halves.',
                      'cites': {'gem5_commit': manifest['upstream_commit'], 'path': 'src/mem/MAA/SPD.cc', 'lines': '120-137'}},
                     {'id': 'trace_domain', 'statement': 'Two initialized abstract cells are distinct physical lines with region IDs equal to their cell IDs by construction; four owned physical tiles, at most two commands and one later CPU write per unfinished gather; four independent initialized harness cells supply a checked budget of four fresh choice bits for history settlement and logical ready queries; fixed event order and no typed pointer or source refinement.',
                      'assumed': {'owner': owner}, 'record_assumption': True},
                     {'id': 'history_visibility', 'statement': 'Each gather observes its issue value or a real successful later CPU write before covering; stores before issue are visible and results are immutable after cover.',
                      'assumed': {'owner': owner}, 'record_assumption': True}]
    data['rules'] += [{'id': name, 'statement': text + ' Retained unused boundary entry: the abstract trace does not use this physical premise and establishes no source or hardware refinement.', 'record_assumption': True,
                       'assumed': {'owner': 'Eric' if name == 'no_stale_cpu_copy' else owner}}
                      for name, text in TRUST.items()]
    calls = []
    for name in data['inventory']['calls']:
        row = {'call': name, 'prototype': 'int ' + name + '(void)', 'contract': WP_REFUSAL,
               'supported': False, 'rules': ['synthetic_trace_scope']}
        signatures = [r['declaration'] for r in manifest['declarations'] if r['name'] == name]
        if len(signatures) > 1:
            row['overloads'] = [{'declaration': signature,
                                 'prototype': 'int swdb_refused_' + name + '_' + str(i) + '(void)',
                                 'contract': WP_REFUSAL} for i, signature in enumerate(signatures)]
        calls.append(row)
    data['calls'] = calls
    data['queries'] = [{'query': name, 'prototype': prototype, 'contract': WP_REFUSAL}
                       for name, prototype in QUERY_PROTOTYPES.items()]
    folder = library / 'proof_semantics/synthetic-memory-trace'
    folder.mkdir()
    refs = {}
    for key, text in components().items():
        filename = {'ghost': 'ghost.acsl', 'state': 'state.h', 'c': 'model.h', 'logic': 'logic.acsl'}[key]
        path = folder / filename
        path.write_text(text)
        refs[key] = {'root': 'library', 'path': str(path.relative_to(library)), 'sha256': digest(path.read_bytes())}
    data['ghost'] = {'acsl': refs['ghost'], 'capacity': {'commands': 2}}
    data['model'] = {key: refs[key] for key in ('state', 'c', 'logic')}


def prepare(output=None):
    """Write only this owned preparation directory; no command or compiler use."""
    expected = Path(__file__).resolve().parent
    output = Path(output).resolve() if output else expected
    if output != expected:
        raise Refused('preparation output must be the exact owned prototype directory')
    for key, text in components().items():
        (output / {'ghost': 'ghost.acsl', 'state': 'state.h', 'c': 'model.h', 'logic': 'logic.acsl'}[key]).write_text(text)
    (output / 'integration-policy.json').write_text(json.dumps(policy_document(), indent=2, sort_keys=True) + '\n')
    return policy_document()


if __name__ == '__main__':
    prepare()

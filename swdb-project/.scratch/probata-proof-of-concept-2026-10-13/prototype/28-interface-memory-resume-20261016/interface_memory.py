"""2026-10-16 ET. Pinned-source tile/memory preparation, never public call support.

Only standard-library source parsing and C/JSON preparation occur here. The
result is not imported by SWDB. Register/value/history binding and source-site
instrumentation remain mandatory before a command can become a public model.
"""
import hashlib
import json
from pathlib import Path
import re


COMMIT = 'e4fc4afdf894f295442cef3604667a469fab8e62'
PINS = {
    'apps/dx100/benchmarks/API/MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',
    'apps/dx100/benchmarks/API/MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174',
    'tests/fixtures/proof/dx100/gem5-e4fc4af/IF.cc': 'fd7dd67f35f63ff6ed9ef0b8ce36cb60cc6d63b20fe9c0796e648bff82da6561',
    'tests/fixtures/proof/dx100/gem5-e4fc4af/MAA.cc': '058395cbd171ccf3746fb524967d2d205cb8d622d4aa06e8eef530b00dc21299',
    'tests/fixtures/proof/dx100/gem5-e4fc4af/SPD.cc': '9e6bb3672be95954e8816c054b4032f95811a3085ca6df418aed90ad1e852b4a',
}
MEMORY_OPCODES = {'STREAM_LD': 1, 'STREAM_ST': 2, 'INDIR_LD': 1,
                  'INDIR_ST_SCALAR': 2, 'INDIR_ST_VECTOR': 2,
                  'INDIR_RMW_SCALAR': 2, 'INDIR_RMW_VECTOR': 2}
ROLE_FIELDS = {56: 'src1', 48: 'src2', 40: 'rdst1', 32: 'rdst2',
               24: 'rsrc1', 16: 'rsrc2', 8: 'rsrc3', 0: 'condition'}
COMMENT = re.compile(r'//[^\n]*|/\*.*?\*/', re.S)
DECLARATION = re.compile(r'(?m)^inline void (maa_\w+)\(([^{};]*)\)\s*\{')


class Refused(ValueError):
    """Source/preparation domain refusal, not a hardware counterexample."""


def _trim_parentheses(text):
    text = text.strip()
    while text.startswith('(') and text.endswith(')'):
        depth = 0
        enclosed = True
        for char in text[:-1]:
            depth += (char == '(') - (char == ')')
            if depth == 0:
                enclosed = False
                break
        if not enclosed:
            break
        text = text[1:-1].strip()
    return text


def _packet(expression):
    """Parse the fixed pinned cast/shift/OR syntax, not arbitrary C++."""
    parts, start, depth = [], 0, 0
    for index, char in enumerate(expression):
        depth += (char == '(') - (char == ')')
        if char == '|' and depth == 0:
            parts.append(expression[start:index].strip())
            start = index + 1
    parts.append(expression[start:].strip())
    result = {}
    for part in parts:
        part = _trim_parentheses(part)
        match = re.fullmatch(r'\(uint64_t\)(.*?)(?:\s*<<\s*(\d+))?', part, re.S)
        if match is None:
            raise Refused('unrecognized pinned packet term: ' + part)
        expression = _trim_parentheses(match[1])
        shift = int(match[2] or 0)
        if shift in result:
            raise Refused('duplicate packet shift')
        result[shift] = ' '.join(expression.split())
    return result


def _operand(expression):
    if expression == 'NA_UINT8':
        return None
    optional = re.fullmatch(r'(\w+) == -1 \? NA_UINT8 : (\w+)', expression)
    if optional:
        if optional[1] != optional[2]:
            raise Refused('optional source operand disagrees with itself')
        return {'parameter': optional[1], 'optional': True}
    if re.fullmatch(r'[A-Za-z_]\w*', expression):
        return {'parameter': expression, 'optional': False}
    raise Refused('unsupported source operand expression: ' + expression)


def _definitions(text):
    clean = COMMENT.sub(lambda match: re.sub(r'[^\n]', ' ', match[0]), text)
    for declaration in DECLARATION.finditer(clean):
        end, depth = declaration.end(), 1
        while depth and end < len(clean):
            depth += (clean[end] == '{') - (clean[end] == '}')
            end += 1
        if depth:
            raise Refused('unbalanced pinned function body')
        yield declaration, clean[declaration.end():end - 1], end


def inventory(project):
    """Read exact source bytes and derive seven memory packet role projections."""
    project = Path(project).resolve()
    texts, sources = {}, []
    for relative, digest in PINS.items():
        data = (project / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise Refused('immutable source differs: ' + relative)
        sources.append({'relative': relative, 'bytes': len(data), 'sha256': digest})
        texts[Path(relative).name] = data.decode('utf-8')
    calls = []
    for declaration, body, end in _definitions(texts['MAA_gem5.hpp']):
        assignments = dict(re.findall(r'\*(INSTR_\w+)\s*=\s*([^;]+);', body, re.S))
        if 'INSTR_opcode_datatype_optype_tdst1_tdst2' not in assignments:
            continue
        first = _packet(assignments['INSTR_opcode_datatype_optype_tdst1_tdst2'])
        opcode = first[32].removeprefix('OpcodeType::')
        if opcode not in MEMORY_OPCODES:
            continue
        if set(first) != {32, 24, 16, 8, 0} or first[24] != 'data_type' or first[0] != 'NA_UINT8':
            raise Refused('memory instruction first-word shape changed')
        if 'DataType data_type = get_data_type<T1>();' not in body:
            raise Refused('memory template dtype selection changed')
        second = _packet(assignments['INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc'])
        if set(second) != set(ROLE_FIELDS) or assignments['INSTR_baseaddr'].strip() != '(uint64_t)data':
            raise Refused('memory instruction operand/base shape changed')
        roles = {ROLE_FIELDS[shift]: _operand(expression) for shift, expression in second.items()}
        roles['dst1'], roles['dst2'] = _operand(first[8]), _operand(first[0])
        params = re.findall(r'\b(\w+)\s*(?:=\s*-?\d+)?\s*(?:,|$)', declaration[2])
        tile_params = [name for name in params if any(role and role['parameter'] == name
                      for key, role in roles.items() if key in {'src1', 'src2', 'dst1', 'dst2', 'condition'})]
        calls.append({'name': declaration[1], 'opcode': opcode, 'access': MEMORY_OPCODES[opcode],
                      'source': {'relative': 'apps/dx100/benchmarks/API/MAA_gem5.hpp',
                                 'line_start': texts['MAA_gem5.hpp'].count('\n', 0, declaration.start()) + 1,
                                 'line_end': texts['MAA_gem5.hpp'].count('\n', 0, end) + 1},
                      'declaration': ' '.join(declaration[0][:-1].split()),
                      'tile_parameters': tile_params, 'roles': roles,
                      'register_parameters_not_yet_bound': [role['parameter'] for key, role in roles.items()
                                                           if key.startswith('r') and role]})
    if len(calls) != 7 or {call['opcode'] for call in calls} != set(MEMORY_OPCODES):
        raise Refused('complete seven-memory-call preparation inventory required')
    return {'date': '2026-10-16 ET', 'source_commit': COMMIT, 'sources': sources, 'calls': calls,
            'scope': 'private source-derived tile/memory preparation only; no value/history/public proof support',
            'public_support': False, 'current_0_2': False,
            'citations': [
                {'relative': 'tests/fixtures/proof/dx100/gem5-e4fc4af/IF.cc', 'lines': [66, 154], 'rule': 'word widths and explicit-ID priority'},
                {'relative': 'tests/fixtures/proof/dx100/gem5-e4fc4af/IF.cc', 'lines': [193, 218], 'rule': 'explicit destination and region conflict stalls'},
                {'relative': 'tests/fixtures/proof/dx100/gem5-e4fc4af/MAA.cc', 'lines': [200, 241], 'rule': 'registration and first containing region'},
                {'relative': 'tests/fixtures/proof/dx100/gem5-e4fc4af/MAA.cc', 'lines': [563, 580], 'rule': 'src/dst counted roles exclude condition-only role'},
                {'relative': 'tests/fixtures/proof/dx100/gem5-e4fc4af/SPD.cc', 'lines': [120, 137], 'rule': 'eight-byte roles count both physical halves'}]}


def project_roles(call, dtype, arguments, tiles=32):
    """Compiler-free reference of emitted masks, not backend state execution."""
    if type(dtype) is not int or not 0 <= dtype < 6 or type(tiles) is not int or not 1 <= tiles <= 64:
        raise Refused('type/tile-mask domain')
    if set(arguments) != set(call['tile_parameters']):
        raise Refused('exact source tile arguments required')
    explicit_read = explicit_write = physical_read = physical_write = ready = 0
    widths = {}
    for name in ['condition', 'src1', 'src2', 'dst1', 'dst2']:
        role = call['roles'][name]
        if role is None:
            continue
        tile = arguments[role['parameter']]
        if type(tile) is not int:
            raise Refused('integer source tile ID required')
        if role['optional'] and tile == -1:
            continue
        width = 4 if name == 'condition' or (name == 'src1' and call['opcode'].startswith('INDIR')) else (4 if dtype < 3 else 8)
        if not 0 <= tile < tiles or width // 4 > tiles - tile:
            raise Refused('source tile/pair domain')
        if tile in widths and widths[tile] != width:
            raise Refused('source role alias has conflicting getWordSize width')
        widths[tile] = width
        explicit, physical = 1 << tile, ((1 << (width // 4)) - 1) << tile
        if name.startswith('dst'):
            explicit_write |= explicit
            physical_write |= physical
        else:
            explicit_read |= explicit
            physical_read |= physical
        if name != 'condition':
            ready |= physical
    if physical_read & physical_write:
        raise Refused('software physical input/output disjointness domain')
    return {'explicit_read': explicit_read, 'explicit_write': explicit_write,
            'physical_read': physical_read, 'physical_write': physical_write, 'ready_roles': ready}


def render_header(binding):
    """Emit preparers: first-ID/F2 precedes counted-role backend preparation."""
    lines = [r'''/* 2026-10-16 ET. PRIVATE preparation only; not a complete source call model.
 * Include after pinned command_state + region_state. No register/value/history
 * effect is supplied. Source-site admission must generate correspondence inputs;
 * candidate code must not call these helpers or choose its own footprint.
 * No public get_tile_ready is introduced. wait_ready remains a blocking MMIO read.
 */
#ifndef SWDB_DXI_MEMORY_PREPARE_H
#define SWDB_DXI_MEMORY_PREPARE_H
struct dxi_masks { uint64_t er,ew,pr,pw,ready; };
struct dxi_memory_correspondence {
  uint64_t logical_begin,logical_end,physical_begin,physical_end,line_bytes;
};
/* The same ID can occur in several source roles. IF::getWordSize uses condition,
 * src1,src2,dst1,dst2 priority. Different required widths at one ID refuse as a
 * software correspondence obligation rather than inventing independent widths.
 * Odd eight-byte starts remain allowed if both physical halves exist. */
static void dxi_add_role(struct dxi_masks *m,unsigned *widths,int tile,unsigned bytes,
                         unsigned optional,unsigned write,unsigned counted) {
  if (optional && tile == -1) return;
  DXM_CHECK(tile >= 0 && (unsigned)tile < DXM_TILES,"source-tile-domain");
  DXM_CHECK(bytes == 4 || bytes == 8,"source-role-width");
  DXM_CHECK(bytes/4 <= DXM_TILES-(unsigned)tile,"source-pair-domain");
  DXM_CHECK(widths[tile] == 0 || widths[tile] == bytes,"source-role-alias-width");
  widths[tile]=bytes;
  uint64_t explicit_mask=UINT64_C(1) << tile,physical=dxc_tile_mask((unsigned)tile,bytes);
  if (write) { m->ew|=explicit_mask; m->pw|=physical; }
  else { m->er|=explicit_mask; m->pr|=physical; }
  if (counted) m->ready|=physical;
}
static unsigned dxi_prepare_memory(unsigned thread,unsigned access,uint64_t source_base,
    struct dxi_memory_correspondence domain,struct dxi_masks masks) {
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  DXM_CHECK(access == 1 || access == 2,"access-kind-domain");
  DXM_CHECK(domain.logical_begin < domain.logical_end,"logical-footprint-domain");
  DXM_CHECK(domain.physical_begin < domain.physical_end,"physical-footprint-domain");
  /* Actual source addresses and physical addresses are distinct. This checks
     region/F2 in source space; it never assumes their translation is identity. */
  int assigned=dxr_assign(source_base);
  dxr_check_span(assigned,domain.logical_begin,domain.logical_end);
  uint64_t begin=domain.physical_begin,end=domain.physical_end;
  if (access == 2) {
    struct dxc_span line=dxc_store_span(begin,end-begin,domain.line_bytes);
    begin=line.begin; end=line.end;
  }
  return dxc_prepare_counted(thread,assigned,access,masks.er,masks.ew,
                             masks.pr,masks.pw,begin,end,masks.ready);
}
''']
    for call in binding['calls']:
        params = ','.join('int ' + name for name in call['tile_parameters'])
        lines.append('/* MAA_gem5.hpp:%d-%d; %s. Register arguments not bound: %s. */' % (
            call['source']['line_start'], call['source']['line_end'], call['opcode'],
            ','.join(call['register_parameters_not_yet_bound']) or 'none'))
        lines.append('static unsigned dxi_prepare_%s(unsigned thread,unsigned dtype,uint64_t source_base,%s,struct dxi_memory_correspondence domain) {' % (call['name'], params))
        lines += ['  DXM_CHECK(dtype < 6,"numeric-type-domain");',
                  '  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");',
                  '  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};']
        for name in ['condition', 'src1', 'src2', 'dst1', 'dst2']:
            role = call['roles'][name]
            if role is None:
                continue
            width = '4' if name == 'condition' or (name == 'src1' and call['opcode'].startswith('INDIR')) else '(dtype < 3 ? 4 : 8)'
            lines.append('  dxi_add_role(&masks,widths,%s,%s,%d,%d,%d);' % (
                role['parameter'], width, role['optional'], name.startswith('dst'), name != 'condition'))
        lines += ['  return dxi_prepare_memory(thread,%d,source_base,domain,masks);' % call['access'], '}', '']
    lines += ['#endif', '']
    return '\n'.join(lines)


def write_preparation(project, output):
    """Write only the two source-preparation artifacts in an existing directory."""
    output = Path(output).resolve()
    if not output.is_dir() or output.name != '28-interface-memory-resume-20261016':
        raise Refused('exact new prototype output directory required')
    binding = inventory(project)
    (output / 'binding.json').write_text(json.dumps(binding, sort_keys=True, indent=2) + '\n')
    (output / 'interface_memory_prepare.h').write_text(render_header(binding))
    return binding

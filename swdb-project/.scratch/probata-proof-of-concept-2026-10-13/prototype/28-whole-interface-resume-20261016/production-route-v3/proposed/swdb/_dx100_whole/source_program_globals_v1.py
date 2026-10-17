"""2026-10-16 ET. Pure original-TU fresh-program host-global observation.

C++ static zero initialization of actual source globals is separate from device
payload/history/ownership. No model reset, allocation/init call, device value or
fresh-device assumption is emitted. Root binds the fresh-program interpretation
at the public lowering consumer; a hash cannot attest that execution context.
"""
import hashlib
import json
from pathlib import Path
import re

GLOBALS = {
    'REG_count': ('MAA.hpp','int','dxg_next'),
    'SPD_count': ('MAA.hpp','int','dxs_tile_next'),
    'SPD_data_cacheable': ('MAA.hpp','void *','dxs_mmio[0]'),
    'SPD_data_noncacheable': ('MAA.hpp','volatile void *','dxs_mmio[1]'),
    'SPD_size_noncacheable': ('MAA.hpp','volatile uint16_t *','dxs_mmio[2]'),
    'SPD_ready_noncacheable': ('MAA.hpp','volatile uint16_t *','dxs_mmio[3]'),
    'REG_noncacheable': ('MAA.hpp','volatile void *','dxs_mmio[4]'),
    'INSTR_opcode_datatype_optype_tdst1_tdst2': ('MAA_gem5.hpp','volatile uint64_t *','dxs_mmio[5]'),
    'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc': ('MAA_gem5.hpp','volatile uint64_t *','dxs_mmio[5]+8'),
    'INSTR_baseaddr': ('MAA_gem5.hpp','volatile uint64_t *','dxs_mmio[5]+16'),
    'MAA_end_addr': ('MAA_gem5.hpp','uint64_t','dxs_mmio[6]'),
    'region_count': ('MAA_gem5.hpp','int8_t','dxs_region_next'),
}


class Refused(ValueError):
    pass


def need(ok,message):
    if not ok: raise Refused(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def tokens(text):
    return re.findall(r'[A-Za-z_]\w*|\*',text)


def observe_globals(api,tu,declarations,*,execution_mode,program_context_receipt_sha256):
    need(execution_mode == 'fresh-cxx-program-globals', 'reused/preexisting program state requires a separate explicit binding')
    need(isinstance(program_context_receipt_sha256,str) and re.fullmatch('[0-9a-f]{64}',program_context_receipt_sha256),
         'root fresh-program context receipt required; hash alone is not admission')
    need(tu.get('kind') == 'TranslationUnitDecl', 'one complete actual original TU required')
    headers={Path(row['header_path']).name:row for row in declarations}
    need(set(headers) == {'MAA.hpp','MAA_gem5.hpp'}, 'two exact source headers required')
    origin=Path(declarations[0]['header_path']).parents[4]
    need(declarations == api['inventory'](origin), 'fresh exact source inventory required')
    observed={}
    def walk(node,scope=()):
        kind,name=node.get('kind'),node.get('name')
        if kind == 'VarDecl' and name in GLOBALS:
            need(not scope and name not in observed, 'source global must have one original global-scope definition')
            header,source_type,receiver=GLOBALS[name];record=headers[header];path=Path(record['header_path']);raw=path.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == record['header_sha256'], 'physical source header changed')
            loc=node.get('loc',{})
            need(loc.get('_file',loc.get('file')) == str(path), 'global physical source header differs')
            start,end=api['_span'](node)
            expected=re.search(r'^'+re.escape(source_type).replace(r'\ ',r'\s*')+r'\s*'+re.escape(name)+r'\s*;',raw.decode('ascii'),re.M)
            need(expected and raw[start:end].decode('ascii').strip() == expected[0].rstrip(';').strip(), 'global exact uninitialized source declaration required')
            need(not node.get('storageClass') and not node.get('tls') and 'init' not in node and not node.get('inner'),
                 'global initializer/storage/attributes are outside the exact fresh-program binding')
            typ=node.get('type',{});qual=typ.get('qualType')
            need(isinstance(qual,str) and tokens(qual) == tokens(source_type), 'global actual source type spelling differs')
            pointer='*' in source_type
            observed[name]={'name':name,'declaration_id':node.get('id'),'actual_type':typ,'source_type':source_type,
                'source_range':[start,end],'header_path':str(path),'header_sha256':record['header_sha256'],
                'declaration_sha256':digest(node),'CXX_static_initialization':'null pointer' if pointer else 'zero scalar',
                'source_initial_value':None if pointer else 0,
                'model_host_receiver_relation': {'kind':'instruction-pointer-derived-only-after-allocation',
                    'model_base':'dxs_mmio[5]','offset_after_alloc':8 if name == 'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc' else 16,
                    'unallocated_source_value':'null pointer','preallocation_use':'setup-domain refusal'}
                    if name in {'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc','INSTR_baseaddr'}
                    else {'kind':'source host field','model_field':receiver}}
            need(isinstance(node.get('id'),str) and node['id'], 'global actual declaration identity required')
        if kind in {'FunctionDecl','NamespaceDecl','CXXRecordDecl','RecordDecl','LambdaExpr'}:scope=scope+(kind,)
        for child in node.get('inner',[]):
            if isinstance(child,dict):walk(child,scope)
    walk(tu)
    need(set(observed) == set(GLOBALS), 'complete twelve source-global definition census required')
    return {'schema':'whole-interface-source-program-globals-1','execution_mode':execution_mode,
        'program_context_receipt_sha256':program_context_receipt_sha256,'globals':[observed[name] for name in sorted(observed)],
        'full_tu_sha256':digest(tu),'fresh_program_interpretation_requires_root_admission':True,
        'pointer_null_is_source_semantic_value_not_raw_bit_claim':True,
        'model_host_mapping_requires_derived_setup_state':True,
        'instruction_pointer_offsets_apply_only_after_alloc_not_to_null_initial_values':True,
        'model_reset_called':False,'alloc_MAA_called':False,'init_MAA_called':False,
        'device_payload_initializedness_granted':False,'device_ownership_granted':False,
        'preexisting_command_history_cleared':False,'device_receiver_state_bound':False,
        'public_admission':False}

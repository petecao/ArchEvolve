"""2026-10-16 ET. Exact memory-source receiver identity controls, no project/tools."""
import ast
import copy
import hashlib
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise AssertionError('no child/native/network in receiver controls')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':
        raise AssertionError('no project imports in receiver controls')


sys.addaudithook(deny)
M=SimpleNamespace(**runpy.run_path(str(HERE/'receiver_memory_v1.py')))
B=SimpleNamespace(**runpy.run_path(str(WHOLE/'receiver-state-draws-v2/receiver_state_draws_v2.py')))


def source_gate():
    tree=ast.parse((HERE/'receiver_memory_v1.py').read_bytes())
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='_prepare')
    checks=[node for node in ast.walk(function) if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)
        and ast.unparse(node.value.func)=='need' and len(node.value.args)>1
        and isinstance(node.value.args[1],ast.Constant) and node.value.args[1].value=='first source fixture scope differs']
    assert len(checks)==1
    code=compile(ast.fix_missing_locations(ast.Module(body=checks,type_ignores=[])),'<exact receiver source gate>','exec')
    def apply(sha,size):
        exec(code,{'need':M.need,'inputs':{'source':SimpleNamespace(sha256=sha,bytes=size)},'SOURCE_SHA':M.SOURCE_SHA,'SOURCE_BYTES':M.SOURCE_BYTES})
    return apply


class Controls(unittest.TestCase):
    def test_entire_inverse_only_two_source_constants(self):
        old=(WHOLE/'receiver-state-draws-v2/receiver_state_draws_v2.py').read_text()
        new=(HERE/'receiver_memory_v1.py').read_text()
        self.assertEqual(new.replace("SOURCE_SHA = '"+M.SOURCE_SHA+"'","SOURCE_SHA = '"+B.SOURCE_SHA+"'")
            .replace('SOURCE_BYTES = 3258','SOURCE_BYTES = 4524'),old)
        oldtree=ast.parse(old);newtree=ast.parse(new)
        before={node.name:ast.dump(node,include_attributes=False) for node in oldtree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
        after={node.name:ast.dump(node,include_attributes=False) for node in newtree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
        self.assertEqual(before,after)

    def test_exact_actual_source_pin_and_original_prepare_gate(self):
        path=WHOLE/'source-memory-fixtures-v1/same_thread_memory_v1.cpp';raw=path.read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(M.SOURCE_BYTES,M.SOURCE_SHA))
        self.assertEqual(M.check_file(M.Pin(str(path),len(raw),M.SOURCE_SHA),retain=True),raw)
        gate=source_gate();gate(M.SOURCE_SHA,3258)
        for sha,size in ((B.SOURCE_SHA,4524),(M.SOURCE_SHA,4524),(B.SOURCE_SHA,3258),('0'*64,3258),(M.SOURCE_SHA,3257)):
            with self.assertRaises(M.Refused):gate(sha,size)

    def test_one_complete_line_allocation_uses_new_source_identity_and_extent_bound(self):
        source=(WHOLE/'source-memory-fixtures-v1/same_thread_memory_v1.cpp').read_text()
        begin=source.index('std::uint32_t data[16]');end=source.index(';',begin)+1
        row={'object_index':0,'object_id':'owned_data','caller':'_Z35whole_same_thread_read_during_storev',
            'local_id':'0xsource','declaration_sha256':'a'*64,'declaration_range':[begin,end],
            'scope_end_offset':source.index('\n}',end)+2,'allocation_thread':0,
            'allocation_origin':'checked-original-automatic-declaration'}
        source_pin=M.object_sha({'source_sha256':M.SOURCE_SHA,'caller':row['caller'],'local_id':row['local_id'],
            'declaration_sha256':row['declaration_sha256']})
        atlas={'schema':'source-ordinary-cell-atlas-1','objects':[{'object_id':'owned_data','source_pin':source_pin,
            'guest_base':4096,'physical_base':4096,'extent':16,'dtype':0,'base_cell':0,'cell_ids':list(range(16))}],
            'cells':[{'cell':i,'physical_begin':4096+4*i,'physical_end':4100+4*i,'dtype':0} for i in range(16)],
            'mmio_excluded_span':[17179869184,17179869184+8*32*16384+4*32+4*32+24],
            'initialization_granted':False,'history_events_added':0,'public_admission':False,
            'owned_premises':['source object identity/lifetime','guest→physical projection','complete CPU-access instrumentation']}
        M.check_allocations([row],atlas,M.SOURCE_SHA,1)
        with self.assertRaises(M.Refused):M.check_allocations([row],atlas,B.SOURCE_SHA,1)
        for field,value in (('scope_end_offset',3259),('allocation_thread',1),('allocation_origin','caller assertion')):
            candidate=copy.deepcopy(row);candidate[field]=value
            with self.assertRaises(M.Refused):M.check_allocations([candidate],atlas,M.SOURCE_SHA,1)

    def test_receiver_code_draws_premises_and_physical_roles_unchanged(self):
        flags={name:0 for name in M.FLAGS};allocations=[{'allocation_thread':0}]
        self.assertEqual(M.receiver_text(flags,256,allocations,1),B.receiver_text(flags,256,allocations,1))
        self.assertEqual(M.choice_hook_prefix(256),B.choice_hook_prefix(256))
        for name in ('PREMISES','FLAGS','GLOBALS','FROZEN','INPUT_NAMES','PHYSICAL_ROLES','PROFILE','SOURCE_KIND','MODEL_KIND'):
            self.assertEqual(getattr(M,name),getattr(B,name))
        code=M.receiver_text(flags,256,allocations,1)
        self.assertIn('dws_choice_table[i]=(uint32_t)swdb_next()',code)
        self.assertNotIn('memset',code)
        self.assertIn('receiver-untouched-local-ghosts',code)


if __name__=='__main__':unittest.main(verbosity=2)

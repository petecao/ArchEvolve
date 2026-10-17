"""2026-10-16 Eastern. Exact public adapter/ProofUnit source controls; no actual project import."""
import ast
import builtins
from dataclasses import dataclass,replace
import hashlib
import importlib.util
from pathlib import Path
import re
import stat
import sys
import tempfile
from types import SimpleNamespace,ModuleType
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]/'swdb'
def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:raise AssertionError('no child/native/network in attribution controls')
sys.addaudithook(audit)
def extract(path,names,ns):
    nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names);exec(compile(ast.Module(nodes,type_ignores=[]),str(path),'exec'),ns);return ns
module=ModuleType('_actual_summary_ProofUnit_source');module.__dict__.update(dataclass=dataclass);sys.modules[module.__name__]=module
extract(ROOT/'proof.py',{'ProofUnit'},module.__dict__);ProofUnit=module.ProofUnit
class Refused(ValueError):pass
def need(ok,message):
    if not ok:raise Refused(message)
def imported(name,globals=None,locals=None,fromlist=(),level=0):
    if name=='swdb.proof':return SimpleNamespace(ProofUnit=ProofUnit)
    raise AssertionError('no project import: '+name)
source=SimpleNamespace(need=need,FUNCTION='dwe_finite_trace')
ns=dict(source=source,Path=Path,__builtins__=dict(vars(builtins),__import__=imported))
extract(HERE/'proposed/swdb/dx100_finite_trace_adapter.py',{'check_summary_job','prepared_context'},ns)

class Controls(unittest.TestCase):
    def candidate_job(self,candidate='candidate.unrelated'):
        return SimpleNamespace(unit=ProofUnit(candidate,'dwe_finite_trace','/not-used','1'*64,'contract.finite','2'*64))

    def test_all_candidate_shapes_refuse_before_preparation_or_tools(self):
        source.compose=lambda _:(_ for _ in ()).throw(AssertionError('must not compose a candidate'))
        for value in ('candidate.unrelated','',False,0,{},[]):
            job=self.candidate_job(value)
            with self.assertRaisesRegex(Refused,'candidate attribution'):ns['check_summary_job'](job,None)
            with self.assertRaisesRegex(Refused,'candidate attribution'):ns['prepared_context'](None,job,None,{})
        fake=SimpleNamespace(unit=SimpleNamespace(candidate=None))
        with self.assertRaisesRegex(Refused,'normal summary'):ns['check_summary_job'](fake,None)

    def test_real_public_adapter_V3_RED_V4_GREEN_before_tool_discovery(self):
        class ToolsReached(Exception):pass
        class AdapterError(ValueError):pass
        finite=SimpleNamespace(select_baseline=lambda *_:object())
        guard=SimpleNamespace(check_summary_job=ns['check_summary_job'],run=lambda *_:(_ for _ in ()).throw(AssertionError('cannot return an entry proof')))
        def imports(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='swdb':return SimpleNamespace(dx100_finite_trace=finite,dx100_finite_trace_adapter=guard)
            raise AssertionError('no project import: '+name)
        for version in ('finite-trace-public-v3','finite-trace-public-v4'):
            path=HERE.parent/version/'proposed/swdb/cbmc_adapter.py';tree=ast.parse(path.read_bytes())
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CbmcAdapter')
            method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='run')
            scope=dict(Path=Path,AdapterError=AdapterError,_Log=lambda _:SimpleNamespace(line=lambda _:None),__builtins__=dict(vars(builtins),__import__=imports))
            exec(compile(ast.Module([method],type_ignores=[]),str(path),'exec'),scope)
            with tempfile.TemporaryDirectory(dir=HERE,prefix='adapter-attribution-') as directory:
                job=self.candidate_job();job.log=Path(directory)/'adapter.log'
                adapter=SimpleNamespace(library=SimpleNamespace(get=lambda _:{}),contract='contract.finite',_tools=lambda:(_ for _ in ()).throw(ToolsReached('tool lookup must not occur')))
                if version.endswith('v3'):
                    with self.assertRaises(ToolsReached):scope['run'](adapter,job)
                else:
                    with self.assertRaisesRegex(AdapterError,'candidate attribution'):scope['run'](adapter,job)

    def test_normal_summary_all_seven_fields_match_real_cli_shape(self):
        # Actual ProofUnit, Library.resolve and portable-pin source; only the
        # containing library/contract is a named local protocol fixture.
        validator=dict(Path=Path,stat=stat,re=re,hashlib=hashlib,Refused=Refused)
        extract(ROOT/'dx100_whole_checked.py',{'need','stable_metadata','pinned'},validator)
        core=dict(dataclass=dataclass)
        extract(HERE/'proposed/swdb/dx100_finite_trace.py',{'Selection'},core)
        source.Selection=core['Selection'];source.sha=lambda raw:hashlib.sha256(raw).hexdigest()
        source.contracts=SimpleNamespace(pinned=validator['pinned']);source.contract_check=lambda *_:None
        with tempfile.TemporaryDirectory(dir=HERE,prefix='summary-shape-') as directory:
            root=Path(directory).resolve();path=root/'plan.json';path.write_bytes(b'{"synthetic":"shape-control-only"}\n');digest=source.sha(path.read_bytes())
            resolver=dict(Path=Path,paths=SimpleNamespace(HOME=root))
            tree=ast.parse((ROOT/'library.py').read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Library')
            method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='resolve');exec(compile(ast.Module([method],type_ignores=[]),'exact_Library_resolve','exec'),resolver)
            portable=dict(root='library',path='plan.json',sha256=digest);data=dict(id='contract.finite',kind='rewrite_contract',proof_unit=dict(source=portable));library=SimpleNamespace(root=root,get=lambda _:data)
            library.resolve=lambda row:resolver['resolve'](library,row);validator['paths']=SimpleNamespace(HOME=root)
            selection=source.Selection(library,'semantics.fixture','contract.finite','2'*64,'method.fixture')
            unit=ProofUnit(None,source.FUNCTION,str(root),digest,'contract.finite','2'*64,None)
            job=SimpleNamespace(unit=unit);result=ns['check_summary_job'](job,selection)
            self.assertEqual(result['subject'],dict(kind='library_summary',id='contract.finite'));self.assertFalse(result['candidate_attribution'])
            for field,value in [('candidate','candidate.unrelated'),('function','other'),('contract','other'),('contract_sha256','3'*64),('tree',str(root/'other')),('tree_sha256','4'*64),('correctness_policy',{}),('correctness_policy',False)]:
                with self.assertRaises(Refused,msg=field):ns['check_summary_job'](SimpleNamespace(unit=replace(unit,**{field:value})),selection)
            data['kind']='c_model'
            with self.assertRaisesRegex(Refused,'code-model'):ns['check_summary_job'](job,selection)

    def test_preflight_exact_guard_precedes_composition_and_schema_has_no_other_artifact_field(self):
        tree=ast.parse((HERE/'proposed/swdb/proof_setup.py').read_bytes());begin=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='begin')
        branch=next(n for n in begin.body if isinstance(n,ast.If) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='finite_selection' for t in x.targets) for x in ast.walk(n)))
        events=[]
        finite=SimpleNamespace(select_baseline=lambda *_:object(),compose=lambda _:events.append('compose'))
        def imports(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='swdb':return SimpleNamespace(dx100_finite_trace=finite,dx100_finite_trace_adapter=SimpleNamespace(check_summary_job=ns['check_summary_job']))
            raise AssertionError('no project import: '+name)
        def fail(*_):raise Refused('preflight attribution refusal')
        scope=dict(library=SimpleNamespace(get=lambda _:{}),job=self.candidate_job(),_fail=fail,__builtins__=dict(vars(builtins),__import__=imports))
        with self.assertRaisesRegex(Refused,'preflight attribution'):exec(compile(ast.Module([branch],type_ignores=[]),'exact_preflight_branch','exec'),scope)
        self.assertEqual(events,[])
        self.assertEqual(set(ProofUnit.__dataclass_fields__),{'candidate','function','tree','tree_sha256','contract','contract_sha256','correctness_policy'})

if __name__=='__main__':unittest.main(verbosity=2)

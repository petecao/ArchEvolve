"""Preparation: compare source ASTs only. Never execute/import projected code."""
import ast,copy,hashlib,json,pathlib
T=pathlib.Path('/private/tmp');P=pathlib.Path('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def find(tree,name):
    for n in tree.body:
        if getattr(n,'name',None)==name or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):return n
    raise ValueError('Missing projected symbol: '+name)
def sig(n):return ast.dump(n,include_attributes=False)
newpath=T/'lanl17_selected_record_trajectory_auditor_a2_20261007.py';newtree=ast.parse(newpath.read_text())
orig=T/'lanl17_selected_record_trajectory_auditor_20261007.py';originaltree=ast.parse(orig.read_text())
p=T/'lanl17-auditor-a2-source-preparation-20261007.json';proof=json.loads(p.read_text());checked=[]
for item in proof['original_public_projections_retained']:
    name=item['symbol'];fresh=('paired_identity' if item['source'].endswith('extensa_pairing.py') else 'agreement_identity') if name=='identity' else name
    assert sig(find(originaltree,fresh))==sig(find(newtree,fresh))
    checked.append({'symbol':fresh,'basis':'Original already pinned/checked pure projection retained exact'})
for item in proof['new_exact_public_projections']:
    source=ast.parse(pathlib.Path(item['source_path']).read_text());parent=item['parent']
    if parent:source=find(source,parent)
    node=copy.deepcopy(find(source,item['name']))
    # Assignment nodes have no name; do not attach semantic attributes to them.
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)):node.name=item['auditor_name']
    assert sig(node)==sig(find(newtree,item['auditor_name'])),item
    checked.append({'symbol':item['auditor_name'],'basis':item['transformation']})
collector=T/'lanl17_compact_attempt_custody_a2_20261007.py';ct=ast.parse(collector.read_text())
class Rename(ast.NodeTransformer):
    names={'calls':'project_calls','candidate':'project_candidate','iteration':'project_iteration'}
    def visit_Name(self,node):node.id=self.names.get(node.id,node.id);return node
    def visit_FunctionDef(self,node):node.name=self.names.get(node.name,node.name);self.generic_visit(node);return node
for name in ('CALL_KEYS','CANDIDATE_KEYS','ITERATION_KEYS','STATE_KEYS','calls','candidate','iteration','project_state'):
    node=Rename().visit(copy.deepcopy(find(ct,name)));fresh=Rename.names.get(name,name)
    assert sig(node)==sig(find(newtree,fresh)),name
    checked.append({'symbol':fresh,'basis':'Exact collector projection AST; only local function names renamed'})
# Inspect imports/call spellings rather than run help/main/any projected function.
for path in (newpath,collector):
    tree=ast.parse(path.read_text());assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and ((isinstance(n,ast.ImportFrom) and (n.module or '').startswith('swdb')) or (isinstance(n,ast.Import) and any(x.name.startswith('swdb') for x in n.names))) for n in ast.walk(tree))
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('exec','eval','compile','Store') for n in ast.walk(tree))
result={'format':'swdb.lanl17-auditor-a2-exact-AST-preparation.v1','source_preparation_identity':proof['identity_sha256'],'checked_projections':checked,'projection_count':len(checked),'imports_or_code_executed':False,'actual_inputs_tests_Store_native_provider_SSH':False,'source_AST_parse_passed':True,'auditor_sha256':sha(newpath.read_bytes()),'collector_sha256':sha(collector.read_bytes()),'checker_sha256':sha(pathlib.Path(__file__).read_bytes())};result['identity_sha256']=digest(result)
out=T/'lanl17-auditor-a2-exact-AST-preparation-20261007.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'count':len(checked),'proof':str(out),'seal':result['identity_sha256'],'file_sha256':sha(out.read_bytes()),'AST_only':True}))

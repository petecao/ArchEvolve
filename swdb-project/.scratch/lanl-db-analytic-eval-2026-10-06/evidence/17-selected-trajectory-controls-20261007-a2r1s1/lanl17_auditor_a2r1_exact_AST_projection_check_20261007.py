"""Source/AST inspection only; never execute the prepared auditor or collector."""
import ast,copy,difflib,hashlib,json,pathlib
T=pathlib.Path('/private/tmp')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def find(tree,name):
    for n in tree.body:
        if getattr(n,'name',None)==name or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):return n
    raise ValueError('Missing source symbol '+name)
def sig(n):return ast.dump(n,include_attributes=False)
aud=T/'lanl17_selected_record_trajectory_auditor_a2r1_20261007.py';col=T/'lanl17_compact_attempt_custody_a2r1_20261007.py'
at=ast.parse(aud.read_text());ct=ast.parse(col.read_text());checked=[]
proof=json.loads((T/'lanl17-auditor-a2-source-preparation-20261007.json').read_text())
original=T/'lanl17_selected_record_trajectory_auditor_20261007.py';ot=ast.parse(original.read_text())
for p in proof['original_public_projections_retained']:
    name=p['symbol'];name=('paired_identity' if p['source'].endswith('extensa_pairing.py') else 'agreement_identity') if name=='identity' else name
    assert sig(find(ot,name))==sig(find(at,name)),name
    checked.append({'symbol':name,'scope':'Unchanged original exact scientific/public projection'})
for p in proof['new_exact_public_projections']:
    raw=pathlib.Path(p['source_path']).read_bytes();assert sha(raw)==p['source_sha256']
    tree=ast.parse(raw);tree=find(tree,p['parent']) if p['parent'] else tree
    node=copy.deepcopy(find(tree,p['name']))
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)):node.name=p['auditor_name']
    assert sig(node)==sig(find(at,p['auditor_name'])),p
    checked.append({'symbol':p['auditor_name'],'scope':'Unchanged exact source accounting/selection/context; documented method name lifting only'})
class Rename(ast.NodeTransformer):
    names={'calls':'project_calls','candidate':'project_candidate','iteration':'project_iteration'}
    def visit_Name(self,node):node.id=self.names.get(node.id,node.id);return node
    def visit_FunctionDef(self,node):node.name=self.names.get(node.name,node.name);self.generic_visit(node);return node
symbols=('CALL_KEYS','CANDIDATE_KEYS','ITERATION_KEYS','STATE_KEYS','PROJECTION_CONTRACT','public_token','public_scalar','public_fields','excluded_fields','calls','candidate','iteration','project_state')
for name in symbols:
    node=Rename().visit(copy.deepcopy(find(ct,name)));fresh=Rename.names.get(name,name)
    assert sig(node)==sig(find(at,fresh)),name
    checked.append({'symbol':fresh,'scope':'Exact new safe collector projection; only local function names renamed'})
for path in (aud,col):
    tree=ast.parse(path.read_text())
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and ((isinstance(n,ast.ImportFrom) and (n.module or '').startswith('swdb')) or (isinstance(n,ast.Import) and any(x.name.startswith('swdb') for x in n.names))) for n in ast.walk(tree))
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('exec','eval','compile','Store') for n in ast.walk(tree))
oldpaths=[T/'lanl17_selected_record_trajectory_auditor_a2_20261007.py',T/'lanl17_compact_attempt_custody_a2_20261007.py']
expected=['b15e0e433730b1906c937e2248350278c2b6642d8ff1f909ccf749867f043060','edb822dc9b69796321e86ed042ad8debda33d00479d25f10fbc856b4d8e65780']
for p,h in zip(oldpaths,expected):assert sha(p.read_bytes())==h
regex=[]
for tree in (ast.parse(oldpaths[1].read_text()),ct):
    literals=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and '.call[1-9]' in n.value]
    assert literals==[r'\.call[1-9][0-9]*'];regex.append(literals)
assert regex[0]==regex[1] # Exact original single escaped dot, not a regex change.
delta=[]
for old,new in zip(oldpaths,(aud,col)):
    out=T/(new.stem+'-a2-source-diff.txt')
    out.write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old),tofile=str(new))))
    delta.append({'path':str(out),'bytes':out.stat().st_size,'sha256':sha(out.read_bytes())})
files=[aud,col,T/'lanl17_prepare_auditor_a2r1_20261007.py',T/'lanl17_auditor_a2r1_safe_projection_20261007.txt',pathlib.Path(__file__)]
result={'format':'swdb.lanl17-auditor-a2r1-source-AST-preparation.v1','source_C':proof['source_C'],
    'source_AST_parse_passed':True,'checked_projections':checked,'projection_count':len(checked),
    'exact_scientific_public_projections':34,'exact_safe_collector_projections':13,
    'original_a2_file_pins':[{'path':str(p),'sha256':h} for p,h in zip(oldpaths,expected)],
    'single_escaped_dot_regex_preserved':True,'regex_review_correction':'Original a2 already contains one escaped dot; nested JSON rendering was misread. No regex change claimed.',
    'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files],'source_diffs':delta,
    'auditor_or_collector_executed_or_imported':False,'actual_inputs_Store_tests_scientific_commands_native_provider_SSH':False,
    'immutable_controls_and_C_F6_modified':False,'status':'prospective_source_only_parent_review_pending'}
assert len(checked)==47
result['identity_sha256']=digest(result)
out=T/'lanl17-auditor-a2r1-source-AST-preparation-20261007.json';out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'proof':str(out),'seal':result['identity_sha256'],'file_sha256':sha(out.read_bytes()),'projection_count':len(checked),'AST_only':True}))

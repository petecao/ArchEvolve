"""Narrow source-only seal revision. Does not execute/import prepared programs."""
import ast,copy,difflib,hashlib,json,pathlib
T=pathlib.Path('/private/tmp')
def sha(x):return hashlib.sha256(x).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
old=T/'lanl17_selected_record_trajectory_auditor_a2r1_20261007.py';new=T/'lanl17_selected_record_trajectory_auditor_a2r1s1_20261007.py'
assert sha(old.read_bytes())=='5be66dfa7d12feb0230e3e7b11e3571bc6631718ace1c1fe2c5f2cdbc6860d07'
s=old.read_text();assert s.count('exported=self.json(pin)')==1
s=s.replace('self.json(','self.sealed_json(').replace('exported=self.sealed_json(pin)','exported=self.json(pin)',1)
point='    def yaml(self,pin): return yaml.load(self.raw(pin),Loader=RecordLoader)'
assert s.count(point)==1
helper='''    def sealed_json(self,pin):
        require(re.fullmatch('[0-9a-f]{64}',need(pin,'identity_sha256')) is not None,'Explicit claimed receipt identity pin required')
        require(type(need(pin,'canonical_ensure_ascii')) is bool,'Explicit boolean receipt canonical_ensure_ascii required')
        # json() recomputes the compact seal from exact SHA-pinned original bytes.
        # Only receipt sites use this gate; original unsealed public output stays.
        return self.json(pin)
'''
s=s.replace(point,helper+point,1);new.write_text(s)
ot=ast.parse(old.read_text());nt=ast.parse(s)
oc=next(n for n in ot.body if isinstance(n,ast.ClassDef) and n.name=='Reader')
nc=next(n for n in nt.body if isinstance(n,ast.ClassDef) and n.name=='Reader')
oldmethods={n.name:n for n in oc.body if isinstance(n,ast.FunctionDef)}
newmethods={n.name:n for n in nc.body if isinstance(n,ast.FunctionDef)}
assert set(newmethods)==set(oldmethods)|{'sealed_json'}
class Narrow(ast.NodeTransformer):
    def visit_Call(self,n):
        self.generic_visit(n)
        if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='self' and n.func.attr=='sealed_json':n.func.attr='json'
        return n
for name,node in oldmethods.items():
    normalized=Narrow().visit(copy.deepcopy(newmethods[name]))
    assert ast.dump(node,include_attributes=False)==ast.dump(normalized,include_attributes=False),name
# Every other module symbol/public projection stays AST-exact.
def without_reader(t):
    return ast.Module(body=[n for n in t.body if not isinstance(n,ast.ClassDef) or n.name!='Reader'],type_ignores=[])
assert ast.dump(without_reader(ot),include_attributes=False)==ast.dump(without_reader(nt),include_attributes=False)
sites=[]
for name,n in newmethods.items():
    for call in ast.walk(n):
        if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=='self' and call.func.attr in ('json','sealed_json'):
            sites.append({'method':name,'reader':call.func.attr,'line':call.lineno,'source':ast.get_source_segment(s,call)})
assert [r['method'] for r in sites if r['reader']=='json']==['sealed_json','trajectory']
diff=T/'lanl17-auditor-a2r1s1-seal-gate-source-diff-20261007.txt'
diff.write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),s.splitlines(True),fromfile=str(old),tofile=str(new))))
collector=T/'lanl17_compact_attempt_custody_a2r1_20261007.py'
assert sha(collector.read_bytes())=='b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
assert sha(old.read_bytes())=='5be66dfa7d12feb0230e3e7b11e3571bc6631718ace1c1fe2c5f2cdbc6860d07'
for path in (new,collector):
    tree=ast.parse(path.read_text())
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('eval','exec','compile','Store') for n in ast.walk(tree))
result={'format':'swdb.lanl17-auditor-r1s1-seal-gate-source-preparation.v1','source_C':'f893fed400347ed23d92e917d8bde21b75e5375d','original_r1_auditor_sha256':sha(old.read_bytes()),'unchanged_collector_sha256':sha(collector.read_bytes()),'all_existing_Reader_methods_AST_exact_after_only_sealed_json_call_reversal':True,'all_other_public_scientific_module_AST_exact':True,'source_AST_parsed':True,'sealed_reader_sites':sites,'new_sealed_sites':sum(r['reader']=='sealed_json' for r in sites),'unsealed_public_export_reader_preserved':True,'actual_inputs_execution_imports_Store_tests_native_provider_SSH_staging':False,'status':'Prospective source-only parent review pending','files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in (new,diff,pathlib.Path(__file__))]}
result['identity_sha256']=digest(result);out=T/'lanl17-auditor-a2r1s1-seal-gate-preparation-20261007.json';out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'proof':str(out),'seal':result['identity_sha256'],'file_sha256':sha(out.read_bytes()),'auditor':result['files'][0],'sealed_sites':result['new_sealed_sites'],'AST_only':True}))

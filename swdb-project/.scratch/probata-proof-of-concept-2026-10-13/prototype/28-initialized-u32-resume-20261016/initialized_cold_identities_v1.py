"""2026-10-16 ET. INERT source-derived initialized fixture identities.

Exact passive identity expressions reused from the audited ordinary-register
reader, with the initialized method ID selected explicitly. Source files are
read as data/AST only. The method function uses YAML parsing, not project imports.
This module has no runtime/tool discovery or executable main.
"""
from pathlib import Path
import ast
import hashlib
import json
H = lambda data: hashlib.sha256(data).hexdigest()
LINEUP = {"frama-c-wp": "33.0", "z3": "5.1.0", "cvc5": "1.2.1", "alt-ergo": "2.6.4"}

def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def digest(value):
    return H(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def source_identity(project,compiler):
 # Read the pinned primary identity expression, interpreting only its small
 # byte/hash/concatenation vocabulary. No Python eval or production import.
 folder=project/'swdb';text=(folder/'c_lowering.py').read_text();tree=ast.parse(text);identity=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='identity')
 digest_assignment=next(n for n in identity.body if isinstance(n,ast.Assign) and any(isinstance(q,ast.Name) and q.id=='digest' for q in n.targets));root=digest_assignment.value.func.value.args[0]
 def flatten(n):return flatten(n.left)+flatten(n.right) if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add) else [n]
 source_names=[];bytes_parts=[]
 bounded=H((folder/'bounded_initialization.py').read_bytes()+(folder/'proof_semantics.py').read_bytes()+(folder/'bounded_std_initialization.py').read_bytes()).encode()
 for n in flatten(root):
  expr=ast.get_source_segment(text,n)
  if expr=='here.read_bytes()':name='c_lowering.py';data=(folder/name).read_bytes()
  elif expr=='Path(terminal_release.__file__).read_bytes()':name='terminal_release.py';data=(folder/name).read_bytes()
  elif expr=='Path(cpu_effects.__file__).read_bytes()':name='cpu_effects.py';data=(folder/name).read_bytes()
  elif expr=='policy':name='cpu_memory_admission.py';data=(folder/name).read_bytes()
  elif expr=='bounded_initialization.identity()["sha256"].encode()':name='bounded_initialization composite';data=bounded
  elif expr=='wp_pointer_bounds.identity()["sha256"].encode()':name='wp_pointer_bounds.py sha';data=sha(folder/'wp_pointer_bounds.py').encode()
  elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='read_bytes' and isinstance(n.func.value,ast.Call) and isinstance(n.func.value.func,ast.Attribute) and n.func.value.func.attr=='with_name' and isinstance(n.func.value.func.value,ast.Name) and n.func.value.func.value.id=='here':
   name=ast.literal_eval(n.func.value.args[0]);assert isinstance(name,str) and '/' not in name;data=(folder/name).read_bytes()
  elif expr=='json.dumps(stdlib_provenance.runtime_identity(tool), sort_keys=True).encode()':name='captured compiler context';data=json.dumps(compiler,sort_keys=True).encode()
  else:raise AssertionError('unreviewed lowerer identity byte expression')
  source_names.append(name);bytes_parts.append(data)
 return {'sha256':H(b''.join(bytes_parts)),'byte_expression_components':source_names}

def checker_dependencies(project):
 # Exact typed interpretation of the pinned primary identity's dependency list,
 # including ordered vocabulary extensions. No production import or eval.
 text=(project/'swdb/proof_setup.py').read_text();tree=ast.parse(text);names=[];versions={}
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for target in n.targets:
    if isinstance(target,ast.Name) and target.id in {'SETUP_VERSION','READING_VERSION'}:versions[target.id]=ast.literal_eval(n.value)
    if isinstance(target,ast.Name) and target.id=='CHECK_SOURCES':names=list(ast.literal_eval(n.value))
  if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='CHECK_SOURCES':names.extend(ast.literal_eval(n.value))
 identity=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='identity')
 extensions=[n.value for n in identity.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='dependencies' and n.value.func.attr=='extend']
 assert len(extensions)==1 and len(extensions[0].args)==1 and not extensions[0].keywords,'unreviewed primary dependency extension'
 gen=extensions[0].args[0];assert isinstance(gen,ast.GeneratorExp) and len(gen.generators)==1 and isinstance(gen.elt,ast.Tuple) and len(gen.elt.elts)==2,'unreviewed vocabulary extension shape'
 binding=gen.generators[0];assert isinstance(binding.target,ast.Name) and binding.target.id=='name' and not binding.ifs and not binding.is_async
 def shape(node):return ast.dump(node,include_attributes=False)
 expected=ast.parse('("vocab/"+name,paths.VOCAB/name)',mode='eval').body
 assert shape(gen.elt)==shape(expected),'unreviewed identity dependency path expression'
 vocab=ast.literal_eval(binding.iter);assert isinstance(vocab,tuple) and vocab==('proof_failure_classes.yaml','proof_subject_kinds.yaml'),'ordered exact e4 vocabulary closure differs'
 assert names and len(names)==len(set(names)) and all(isinstance(n,str) and '/' not in n for n in names)
 return {'versions':versions,'paths':['swdb/'+n for n in names]+['vocab/'+n for n in vocab]}

def checkers_identity(project):
 dependencies=checker_dependencies(project);d=digest([{'path':name,'sha256':sha(project/name)} for name in dependencies['paths']]);v=dependencies['versions']
 return {'proof_setup_check':{'version':v['SETUP_VERSION'],'sha256':d},'verdict_reading':{'version':v['READING_VERSION'],'sha256':d}}

def fixture_job_bounds(project):
 tree=ast.parse((project/'tests/testkit/dx100_trust.py').read_text());values=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='run_swdb':
   for index,arg in enumerate(node.args):
    if isinstance(arg,ast.Constant)and arg.value=='--bounds':
     assert index+1<len(node.args)and isinstance(node.args[index+1],ast.Constant)
     values.append(json.loads(node.args[index+1].value))
 assert values==[{'threads':1,'input_size':1}],'public fixture launch bounds changed'
 return values[0]

def expected_fixture_method(project,checker,lowering,naming):
 import yaml
 # Replay only the explicit data transformations in the pinned public fixture.
 # No production import, generated method execution or provider/tool query.
 base=yaml.safe_load((project/'tests/fixtures/proof/methods/contract-fixture-1.yaml').read_text())
 folder=project/'swdb';tree=ast.parse((folder/'cbmc_translator.py').read_text());values={}
 for node in tree.body:
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'TOOL_ID','TOOL_VERSION'}:values[node.targets[0].id]=ast.literal_eval(node.value)
 cbmc={'id':values['TOOL_ID']+'-'+values['TOOL_VERSION'],'sha256':H((folder/'cbmc_translator.py').read_bytes()+(folder/'bounded_entry_windows.py').read_bytes())}
 constants=ast.parse((folder/'cbmc_adapter.py').read_text());frozen=next(ast.literal_eval(q.value) for q in constants.body if isinstance(q,ast.Assign) and any(isinstance(n,ast.Name) and n.id=='FROZEN'for n in q.targets))
 base['c_lowering']['translators']=[lowering['c_lowering'],cbmc]
 next(q for q in base['lineup']if q['tool']=='cbmc')['flags']=list(frozen)
 next(q for q in base['lineup']if q['tool']=='frama-c-wp')['flags']+=['-rte-initialized','@all','-wp-no-filter-init','-machdep','x86_64']
 base.update(id='method.dx100-initialized-register-partial-fixture-v1',sequence=2)
 base['checks'].update(checker);base['c_lowering']['naming_rules']=naming
 next(q for q in base['lineup']if q['tool']=='frama-c-wp')['flags']+=['-wp-prover','z3,cvc5,alt-ergo']
 for q in base['lineup']:
  if q['tool']in LINEUP:q['version']=LINEUP[q['tool']]
 return base

"""2026-10-16 ET. Stdlib-only compiler-observation packet author; no project import."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import textwrap
import zlib

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
POC = HERE.parents[2]
PREVIOUS = POC/'prototype/25-owned-source-view-20261016/public9-v3/inert-032e1851-public9-v3'
OUT = HERE/'inert-032e1851-compiler-v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}


def main():
    packet = json.loads((PREVIOUS/'packet.json').read_bytes())
    for key, name in [('entry','entry.py'), ('expected','expected.json'), ('root_command','root-command.json')]:
        assert pin(PREVIOUS/name)['sha256'] == packet[key]['sha256']
    before = (PREVIOUS/'entry.py').read_text()
    tree = ast.parse(before)
    main_node = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    lines = before.splitlines(keepends=True)
    nested = {n.name: textwrap.dedent(''.join(lines[n.lineno-1:n.end_lineno]))
              for n in main_node.body if isinstance(n,ast.FunctionDef)}
    assert set(nested) == {'source_check','runtime_check','remaining'}
    prefix = before[:before.index('def main():')]
    doc = ast.get_source_segment(before,tree.body[0])
    prefix = prefix.replace(doc, repr('2026-10-16 ET. Compiler-only portable closed move source observation; no verifier or proof records.'), 1)
    for name in ('layout_dependencies','layout_pin','layout_checks','canonical_check','normal_task_census'):
        node = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        value = ast.get_source_segment(before,node)
        assert prefix.count(value)==1
        prefix = prefix.replace(value,'')
    original_guard = next(ast.get_source_segment(before,n) for n in tree.body
                          if isinstance(n,ast.FunctionDef) and n.name=='guarded_generation')
    compiler_guard = original_guard.replace('def guarded_generation(', 'def guarded_compiler(').replace("'frama-c.log'", "'compiler.log'")
    assert compiler_guard.replace('def guarded_compiler(', 'def guarded_generation(').replace("'compiler.log'", "'frama-c.log'")==original_guard
    prefix = prefix.replace(original_guard, compiler_guard)
    expected = copy.deepcopy(json.loads((PREVIOUS/'expected.json').read_bytes()))
    assert expected['source_commit']=='032e1851eec7b195c7a3737997d5f5ea1d1343a5'
    for key in ('method_id','elements','canonical_manifest','canonical_files','target_ids','layout_policy','explicit_method_binding'):
        del expected[key]
    expected['resource_policy'].update(profile_seconds=180,root_whole_seconds=240,
        root_outer_seconds=360,leaf_timeout_seconds=150,output_budget_bytes=512*1024**2)
    expected.update(function='vector_owned_move_capture',
        scope='Original portable closed int move C++→C/anchor/AST/provenance observation only. No verifier, native user-program execution, records, mathematical/source/member/Typed/caller admission.',
        cost_estimate='One public lowering plus one additional filtered AST parse;150s worker/180sprofile/240swhole/360souter;8GiB/oneworker/512MiB aggregate raw,4MiB root headroom.',
        proof_policy={'verifier_calls':0,'native_user_program_executions':0,'proof_records':0,
                      'public_lower_calls':1,'additional_original_function_AST_parses':1})
    fixture = PROJECT/'tests/fixtures/proof/lowering/vector_owned_transfer.cc'
    for key, path, name in [('fixture',fixture,'vector_owned_transfer.cc'),('worker',HERE/'worker.py','worker.py')]:
        raw = path.read_bytes()
        expected[key] = {'name':name,'bytes':len(raw),'sha256':sha(raw),'base64':base64.b64encode(raw).decode()}
    expected_raw=encode(expected)
    main_source=(HERE/'main_template.py').read_text()
    guards='\n\n'.join(textwrap.indent(nested[name],'    ') for name in ('remaining','source_check','runtime_check'))
    main_source=main_source.replace('# __UNCHANGED_NESTED_GUARDS__',guards)
    entry=(prefix+main_source).replace(packet['expected']['sha256'],sha(expected_raw)).encode()
    ast.parse(entry)
    command=json.loads((PREVIOUS/'root-command.json').read_bytes())
    replacements=[(packet['entry']['sha256'],sha(entry)),
        (packet['expected']['sha256'],sha(expected_raw)),
        (base64.b64encode(zlib.compress((PREVIOUS/'entry.py').read_bytes(),9)).decode(),base64.b64encode(zlib.compress(entry,9)).decode()),
        (base64.b64encode(zlib.compress((PREVIOUS/'expected.json').read_bytes(),9)).decode(),base64.b64encode(zlib.compress(expected_raw,9)).decode()),
        ('owned-source9-public-v3','owned-move-compiler-observation-v1'),
        ('owned-source9-public-root-early-preflight.json','owned-move-compiler-root-early-preflight.json')]
    original=command[6];changed=original
    for first,last in replacements:
        assert first in changed
        changed=changed.replace(first,last)
    inverse=changed
    for first,last in reversed(replacements):inverse=inverse.replace(last,first)
    assert inverse==original and len(changed.encode())<120000
    ast.parse(changed);command[6]=changed
    OUT.mkdir(exist_ok=False)
    for name,raw in [('entry.py',entry),('expected.json',expected_raw),('root-command.json',encode(command))]:(OUT/name).write_bytes(raw)
    summary={'date':'2026-10-16 ET','status':'INERT_UNEXECUTED_ROOT_REVIEW_REQUIRED',
        'root_kind':'t25-owned-move-compiler-observation-v1','source_commit':expected['source_commit'],
        'entry':pin(OUT/'entry.py'),'expected':pin(OUT/'expected.json'),'root_command':pin(OUT/'root-command.json'),
        'worker':pin(HERE/'worker.py'),'fixture':pin(fixture),'author':pin(Path(__file__)),
        'template':pin(HERE/'main_template.py'),'predecessor':pin(PREVIOUS/'packet.json'),
        'resource_policy':expected['resource_policy'],'all_nested_source_runtime_guard_bodies_exact':True,
        'compiler_worker_guard_delta':'Exact previous generation guard, only function name and log filename changed; inverse checked.',
        'compressed_bootstrap_inverse_exact':True,'proof_policy':expected['proof_policy'],
        'raw_C_AST_remain_remote':True,'actual_compiler_or_native_or_verifier_execution':False,
        'proof_or_source_or_caller_or_Typed_acceptance':False}
    (OUT/'packet.json').write_bytes(encode(summary))
    print(json.dumps({'packet':pin(OUT/'packet.json'),'entry':summary['entry'],'fixture':summary['fixture']},sort_keys=True))


if __name__=='__main__':
    main()

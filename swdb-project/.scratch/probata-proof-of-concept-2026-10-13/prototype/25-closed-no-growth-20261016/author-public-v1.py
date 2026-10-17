"""2026-10-16 ET. Inert projected-C observation author: Git/stdlib only.

Never imports SWDB or runs a compiler, native helper, verifier or solver.
"""
import ast
import base64
import copy
import hashlib
import importlib.util
import json
import subprocess
import zlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
SOURCE='615ddf504fed61b9f6c6e4663760d006ecaf255b'
REMOTE='/data1/yanruj/probata-resume-20261016-615ddf50/swdb-project'
OUTPUT=HERE/'inert-615ddf50-public-v1'
PREDECESSOR=HERE.with_name('25-private-lifetime-frame-20261016')/'inert-f918f5d5-public-v1'
GENERATOR=HERE.with_name('25-original-no-growth-generation-20261016')/'inert-c978393b-v3'
LINEAGE=HERE/'inert-mac-lineage-758092d5'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()


def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':digest(raw)}


def git(*args):
    return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects','-C',str(REPO),*args],timeout=60)


def blob(relative):
    return git('show',SOURCE+':swdb-project/'+relative)


def definitions(raw,names):
    lines=raw.decode().splitlines(keepends=True)
    found={n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in names}
    assert set(found)==set(names)
    return found


def main():
    assert git('rev-parse',SOURCE).decode().strip()==SOURCE
    predecessors=[]
    for directory in (PREDECESSOR,GENERATOR):
        packet=json.loads((directory/'packet.json').read_bytes())
        for key,name in [('entry','entry.py'),('expected','expected.json'),('root_command','root-command.json')]:
            assert pin(directory/name)['sha256']==packet[key]['sha256']
        predecessors.append(pin(directory/'packet.json'))
    old=json.loads((PREDECESSOR/'expected.json').read_bytes())
    generation=json.loads((GENERATOR/'expected.json').read_bytes())
    predecessor_entry=(PREDECESSOR/'entry.py').read_bytes()
    keep=('linux_clang_component_origin','linux_clang_components','linux_launch_binding','linux_prefix',
          'linux_project_identity_derivation','metadata_origin','portable_import_surfaces','portable_surface_origin',
          'source_consumer_trees','tools','why3_config','wp_artifacts','runtime_sources')
    expected={key:copy.deepcopy(old[key]) for key in keep}
    helper_path=HERE.with_name('25-prefix10-resume-20261016')/'author.py'
    spec=importlib.util.spec_from_file_location('inert_metadata_author',helper_path)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    assert helper.compiler_identity(old['source_commit'],old['linux_project_identity_derivation']['runtime'],old['linux_project_identity_derivation']['predicted_identity'])==old['linux_project_identity_derivation']['predicted_identity']
    runtime=copy.deepcopy(old['linux_project_identity_derivation']['runtime']);changed=0
    for i,value in enumerate(runtime['frontend']):
        for flag in ('-fdebug-compilation-dir=','-fcoverage-compilation-dir='):
            if value==flag+old['remote_project']:
                runtime['frontend'][i]=flag+REMOTE;changed+=1
    assert changed==2
    runtime['check']['sha256']=digest(blob('swdb/stdlib_provenance.py'))
    expected['linux_project_identity_derivation']={'runtime':runtime,
        'predicted_identity':helper.compiler_identity(SOURCE,runtime,old['linux_project_identity_derivation']['predicted_identity']),
        'scope':'Prospective exact Git/context digest only; fresh actual Linux identity required.'}
    expected['source_blobs']=[]
    for raw in git('ls-tree','-r','-z',SOURCE,'--','swdb-project/swdb').split(b'\0'):
        if not raw:continue
        meta,path=raw.decode().split('\t');mode,kind,oid=meta.split()
        assert mode in {'100644','100755'} and kind=='blob'
        relative=path.removeprefix('swdb-project/')
        expected['source_blobs'].append({'path':path,'relative':relative,'blob':oid,'sha256':digest(blob(relative))})
    for relative,row in expected['source_consumer_trees'].items():
        row['oid']=git('rev-parse',SOURCE+':swdb-project/'+relative).decode().strip()
    expected['test_helper_pins']=[{'relative':row['relative'],'sha256':digest(blob(row['relative']))} for row in old['test_helper_pins']]
    lineage=json.loads((LINEAGE/'lineage.json').read_bytes())
    for row in lineage['files']:
        assert pin(LINEAGE/row['path'])['sha256']==row['sha256']
    assert digest(blob('swdb/vector_reallocation_closed_view.py'))==lineage['module_sha256']=='758092d5997274b29e22f2196c46af361b7cfdfd5c9eb83ee328ae6a877eb757'
    assert digest(blob(generation['source_relative']))==generation['source_sha256']==lineage['source_cpp_sha256']
    assert digest((LINEAGE/'original-lowering.c').read_bytes())==generation['lowered_sha256']
    certificate=json.loads((LINEAGE/'certificate.mac-lineage.json').read_bytes())
    assert certificate['original_lowering_inverse_equal'] is True and certificate['source_typed_bridge_established'] is False
    assert certificate['caller_premises_added']==[] and certificate['current_proof_records_admitted']==[]
    projected=(LINEAGE/'projected.c').read_bytes();merged=(LINEAGE/'wp-input.expected.c').read_bytes()
    clauses=json.loads((LINEAGE/'formal-texts.json').read_bytes())
    assert clauses==generation['contract_clauses']
    anchor='/* swdb-anchor '+generation['function']+'.contract */\n'
    block='/*@ '+'\n    '.join(clauses)+' */\n'
    assert projected.count(anchor.encode())==1 and projected.replace(anchor.encode(),(anchor+block).encode())==merged
    constructor='std_vector_int_ctor_count_value(&v, (unsigned long)n, 7);'
    assert projected.decode().splitlines().count('  '+constructor)==1
    policy={'cap_bytes':8*1024**3,'workers':1,'root_whole_seconds':800,'root_outer_seconds':920,
            'profile_seconds':600,'leaf_timeout_seconds':300,'output_budget_bytes':2*1024**3,'metadata_reserve_bytes':4*1024**2}
    expected.update(created='2026-10-16 ET',status='INERT / UNREVIEWED / NOT EXECUTED',source_commit=SOURCE,
        remote_project=REMOTE,method_id='method.wp-closed-no-growth-v1',resource_policy=policy,
        source_relative=generation['source_relative'],source_sha256=generation['source_sha256'],function=generation['function'],
        lowered_sha256=generation['lowered_sha256'],cached_anchor_lineage=generation['cached_anchor_lineage'],
        projected_sha256=digest(projected),wp_input_sha256=digest(merged),contract_clauses=clauses,constructor_call=constructor,
        scope='Complete fresh projected-C no-growth caller diagnostic under original three-clause contract and existing allocator/library TCB. Current constructor body dependency and source allocation/Typed/lifetime bridge remain unadmitted. No original source/caller proof, universal setup attestation or public proof record.',
        explicit_pending=['current constructor body/source dependency','source-created allocator freshness/freeability/private identity binding','Typed-to-Heap incoming-live observation and allocation/lifetime correspondence','conditional math9 source predecessor discharge','complete independent task/hypothesis cold review'],
        proof_policy={'fresh_original_lowering':True,'fresh_full_TU_provenance':True,'actual_public_closed_prepare_check':True,
            'original_contract_unchanged':True,'caller_premises_added':[],'all_ordinary_RTE_initialization_frame_smoke_retained':True,
            'property_filtering':False,'source_function_selection_only':True,'solver_portfolio':['alt-ergo','z3','cvc5'],'solver_seconds':30,
            'normal_flags_lineup_native_and_outcome_readers':True,'primitive_allocator_free_TCB_only':True,
            'constructor_body_record_admitted':False,'universal_proof_setup_attested':False,'public_proof_record_created':False},
        lineage_packet=pin(LINEAGE/'lineage.json'),mac_certificate_policy='Historical source lineage only; Linux creates and retains its full freshly checked certificate. No full-certificate cross-host equality claim.',
        cost_estimate='Unmeasured allowance: one complete root at three solvers/30seconds,300seconds native,600profile,800whole,920outer,8GiB one worker,2GiB raw. No outcome guarantee.')
    expected_bytes=encoded(expected)
    names=('sha','pin','write','surface','linux_admission','consumer_closure','initialize_workspace',
           'guarded_generation','raw_bytes','bounded_bytes','bounded_json')
    helpers=definitions(predecessor_entry,names)
    lineage_definition=definitions((GENERATOR/'entry.py').read_bytes(),('lineage',))['lineage']
    census_definition=definitions(predecessor_entry,('normal_task_census',))['normal_task_census']
    start=census_definition.index("    log_path = directory/'frama-c.log'\n")
    stop=census_definition.index("    census = {'target':")
    streaming=census_definition[start:stop]
    common="def common_exports(directory, goals, peers):\n"+streaming+"    return {'common_exports': exports, 'internal_qed_inventory_only': [g['goal'] for g in inventory_only], 'missing_noninternal_tasks': missing_tasks}\n"
    ast.parse(common)
    template=(HERE/'entry-template-public-v1.py').read_text()
    entry=template.replace('# __REVIEWED_HELPERS__','\n\n'.join(helpers.values())).replace('# __LINEAGE__',lineage_definition).replace('# __COMMON_EXPORTS__',common).replace('__EXPECTED_SHA256__',digest(expected_bytes)).encode()
    ast.parse(entry);assert definitions(entry,names)==helpers
    command=json.loads((PREDECESSOR/'root-command.json').read_bytes());bootstrap=command[6]
    replacements=[(digest(predecessor_entry),digest(entry)),(digest((PREDECESSOR/'expected.json').read_bytes()),digest(expected_bytes)),
        (base64.b64encode(zlib.compress(predecessor_entry,9)).decode(),base64.b64encode(zlib.compress(entry,9)).decode()),
        (base64.b64encode(zlib.compress((PREDECESSOR/'expected.json').read_bytes(),9)).decode(),base64.b64encode(zlib.compress(expected_bytes,9)).decode()),
        ('private-frame9-public-root-early-preflight.json','closed-no-growth-public-root-early-preflight.json'),
        ('private-frame9-public-v1','closed-no-growth-public-v1')]
    for before,after in replacements:
        assert before in bootstrap;bootstrap=bootstrap.replace(before,after)
    inverse=bootstrap
    for before,after in reversed(replacements):inverse=inverse.replace(after,before)
    assert inverse==command[6];ast.parse(bootstrap);assert len(bootstrap.encode())<120000
    command[6]=bootstrap
    OUTPUT.mkdir(exist_ok=False)
    for name,raw in [('entry.py',entry),('expected.json',expected_bytes),('root-command.json',encoded(command)),('wp-input.expected.c',merged),('projected.expected.c',projected)]:
        (OUTPUT/name).write_bytes(raw)
    packet={'created':'2026-10-16 ET','status':'INERT / UNREVIEWED / NOT EXECUTED','source_commit':SOURCE,'remote_project':REMOTE,
        'root_kind':'t25-closed-no-growth-public-v1','entry':pin(OUTPUT/'entry.py'),'expected':pin(OUTPUT/'expected.json'),'root_command':pin(OUTPUT/'root-command.json'),
        'author':pin(Path(__file__)),'template':pin(HERE/'entry-template-public-v1.py'),'predecessor_packets':predecessors,
        'reviewed_helpers_exact':list(names),'streaming_export_block_exact':True,'streaming_export_block_sha256':digest(streaming.encode()),
        'original_lineage_helper_exact':True,'bootstrap_inverse_predecessor_equal':True,'bootstrap_bytes':len(bootstrap.encode()),
        'source_package_count':len(expected['source_blobs']),'resource_policy':policy,'projected_sha256':digest(projected),'wp_input_sha256':digest(merged),
        'project_runtime_imports':0,'compiler_native_verifier_calls':0,'actual_generations':0,'actual_proofs':0,
        'proof_acceptance':False,'source_typed_bridge_established':False,'body_acceptance':False,'caller_acceptance':False,
        'public_proof_records_created':0,'universal_proof_setup_attested':False,'ticket_closure':False,'independent_entry_review_pending':True,'root_admission_pending':True}
    (OUTPUT/'packet.json').write_bytes(encoded(packet))
    print(json.dumps({'packet':pin(OUTPUT/'packet.json'),'entry':packet['entry'],'expected':packet['expected'],'root_command':packet['root_command'],'bootstrap_bytes':packet['bootstrap_bytes'],'source_package_count':packet['source_package_count']},indent=2))


if __name__=='__main__':
    main()

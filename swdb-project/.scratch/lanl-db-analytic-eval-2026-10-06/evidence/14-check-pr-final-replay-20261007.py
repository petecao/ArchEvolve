#!/usr/bin/env python3
"""Read-only acceptance of an actual PR/final CPU unknown-transfer replay.
Prepared 2026-10-07 ET. Public freeze/estimate run separately under parent control.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

CHAR='pagerank.jacobi.kron-g16.cpu.t1.characterization.generality.a1'
CHAR_SHA='73b9bd54b5e3a89f431325b4d6ac211c18a925aecafaba5fdd994cf9c2c70e18'
CHAR_FILE_SHA='168204cc10fb9b0956add8a974ff702da41f9acbc9a74c90320701f8d1b05c76'
TARGET='mbit10.cpu.lanl20261006.t1.services.v1'
IMPL='gapbs-pr-jacobi-analytic-v1'
SNAPSHOT='pagerank-jacobi-20261006.cpu.t1.a1.source'
PR_SOURCE='ea1e58b6957b0bcc1e76f4fde54131aa52bdefd2014dae604a9b7d9d1a5dae70'
INPUT='kron-g16-k16'
ROI='gapbs.functional_trial_lambda.v1'
ARGV=['-g','16','-k','16','-n','5']
ALLOWED={f'{kernel}.kron-g{scale}.t1.characterization.objects.a1' for kernel in ('bfs','bc') for scale in (16,17)}
REQUIRED_MISSING={'service_scope.characterization_allowlist','memory_scenario.characterization_allowlist'}


def require(condition,message):
    if not condition:raise ValueError(message)


def bound_missing(regions):
    return {reason for region in regions for bound in region.get('bounds',[])+region.get('overheads',[]) for reason in bound.get('missing',[])}


def validate_outputs(*,char,target,protocol,estimate,expected_char_sha256,expected_target_sha256,expected_bundle,digest):
    require(char['kind']=='workload_characterization' and char['id']==CHAR and digest(char)==expected_char_sha256,'Actual PR count pin differs')
    require(char['evidence_kind']=='execution' and char['binding']['state']=='verified' and char['coverage']['whole_timed_call'] is True,'Actual registered whole-call evidence required')
    require(char['subject']=={'kind':'implementation','id':IMPL} and char['source']['sha256']==PR_SOURCE,'Original registered Jacobi source differs')
    require(char['binding']['threads']==1 and char['binding']['roi']==ROI and char['input']==INPUT and char['source']['run_arguments']==ARGV,'Actual PR input/ROI/argv/T differs')
    identities=[(t['position'],t['sources']) for t in char['trials']]
    require(identities==[(i,[]) for i in range(5)],'Five exact PR trial identities required')
    require(target['kind']=='target_description' and target['id']==TARGET and target['target']=='mbit10' and target['threads']==1 and digest(target)==expected_target_sha256,'Actual final services target pin differs')
    allow=target['extensions']['cpu_services_binding']['characterization_allowlist']
    require(len(allow)==4 and {r['id'] for r in allow}==ALLOWED,'CPU service admission must retain four exact BF/BC scopes')
    for mechanism in target['mechanisms']:
        selected=mechanism.get('selector',{}).get('characterization_allowlist')
        require(selected is None or sorted(selected,key=lambda r:r['id'])==sorted(allow,key=lambda r:r['id']),'Mechanism admission differs from the four-scope target')
    settings=protocol['settings']
    require(protocol['kind']=='protocol' and protocol['state']=='frozen' and settings['mode']=='estimated','Frozen estimated protocol required')
    require(settings['estimator_sha256']==estimate['estimator_sha256']==expected_bundle,'Final complete source bundle differs')
    require(settings['target_description']['id']==TARGET and settings['target_description']['sha256']==expected_target_sha256 and digest(settings['target_description']['snapshot'])==expected_target_sha256,'Frozen target snapshot differs')
    require(settings['threads']==1 and settings['inputs']==[INPUT] and settings['roi']==ROI and settings['input_run_arguments']=={INPUT:ARGV} and set(settings['sources'])=={IMPL,SNAPSHOT},'Frozen actual PR scope differs')
    require(estimate['kind']=='estimate' and estimate['basis']=='estimated' and estimate['characterization']==CHAR and estimate['characterization_sha256']==expected_char_sha256,'Estimate count binding differs')
    require(estimate['target_description']==TARGET and estimate['target_description_sha256']==expected_target_sha256 and digest(estimate['target_description_snapshot'])==expected_target_sha256,'Estimate target snapshot differs')
    require(estimate['target']=='mbit10' and estimate['threads']==1 and estimate['input']==INPUT and estimate['subject']==char['subject'],'Estimate execution scope differs')
    require(estimate['protocol']==protocol['id'] and estimate['protocol_sha256']==protocol['identity_sha256'],'Estimate frozen protocol seal differs')
    require(all(estimate[k] is None for k in ('seconds','ratio','baseline','error_band')),'Unadmitted PR cost, ratio, baseline and band must stay unknown')
    require([(t['position'],t['sources']) for t in estimate['trials']]==identities and all(t['seconds'] is None for t in estimate['trials']),'Every exact PR trial total must remain unknown')
    require(REQUIRED_MISSING<=bound_missing(estimate['regions']),'Aggregate bounds must state both unsupported PR admission scopes')
    for trial in estimate['trials']:
        require(REQUIRED_MISSING<=bound_missing(trial['regions']),'Each trial must state both unsupported PR admission scopes')
    return {'trials':5,'seconds':None,'ratio':None,'error_band':None,'missing':sorted(REQUIRED_MISSING),'four_scope_allowlist':allow}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('source','records','output'):parser.add_argument('--'+key,required=True,type=Path)
    for key in ('source-sha','estimator-sha256','target-sha256','protocol','estimate'):parser.add_argument('--'+key,required=True)
    args=parser.parse_args();source=args.source.resolve();records=args.records.resolve();output=args.output.resolve()
    require(re.fullmatch('[a-f0-9]{40}',args.source_sha) is not None and all(re.fullmatch('[a-f0-9]{64}',v) for v in (args.estimator_sha256,args.target_sha256)),'Explicit final source/bundle/target pins required')
    require(not output.exists() and source not in output.parents and records not in output.parents and source not in records.parents,'Fresh external proof and copied records required')
    def git(*argv):return subprocess.check_output(['git','-C',str(source),*argv],text=True,timeout=30).strip()
    require(git('rev-parse','HEAD')==args.source_sha and git('status','--porcelain')=='','Final source must remain clean and exact')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(source/'swdb-project'))
    from swdb import artifacts,analytic_binding
    from swdb.store import Store
    from swdb.estimate_protocol import estimator_identity,validate_frozen
    require(estimator_identity()==args.estimator_sha256,'Current complete estimator bundle differs')
    store=Store(records);require(not store.problems,'Copied record catalog parse failed')
    def get(rid,kind):
        data=store.get(rid,kind);require(data is not None,'Missing actual '+kind+' '+rid);return data
    char=get(CHAR,'workload_characterization');target=get(TARGET,'target_description');protocol=get(args.protocol,'protocol');estimate=get(args.estimate,'estimate')
    require(artifacts.file_hash(records/store.path_of(CHAR))==CHAR_FILE_SHA,'Immutable actual PR YAML bytes differ')
    require(not analytic_binding.verify_binding(char,store,require_available=False),'Registered PR source/input/ROI proof differs')
    validate_frozen(protocol,store)
    result=validate_outputs(char=char,target=target,protocol=protocol,estimate=estimate,expected_char_sha256=CHAR_SHA,expected_target_sha256=args.target_sha256,expected_bundle=args.estimator_sha256,digest=artifacts.digest)
    for row in result['four_scope_allowlist']:require(artifacts.digest(get(row['id'],'workload_characterization'))==row['sha256'],'Four-scope source pin differs')
    require(estimator_identity()==args.estimator_sha256 and git('rev-parse','HEAD')==args.source_sha and git('status','--porcelain')=='','Final source changed during acceptance')
    proof={'format':'swdb.lanl14-actual-pr-final-services-acceptance.v1','updated':'2026-10-07 ET','scope':'Actual immutable Jacobi g16/T1 counts and final CPU service descriptor; unsupported transfer remains unknown. No numerical retuning, native/provider execution or raw IR read.',
        'source_commit':args.source_sha,'estimator_sha256':args.estimator_sha256,'target_description_sha256':args.target_sha256,'characterization_sha256':CHAR_SHA,
        'protocol':{'id':protocol['id'],'identity_sha256':protocol['identity_sha256'],'sha256':artifacts.digest(protocol)},'estimate':{'id':estimate['id'],'sha256':artifacts.digest(estimate)},
        'result':result,'source_clean':True,'application_execution':0,'provider_calls':0,'helper_sha256':artifacts.file_hash(__file__)}
    proof['identity_sha256']=artifacts.digest(proof);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'output':str(output),'identity_sha256':proof['identity_sha256']}))


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,TypeError,subprocess.SubprocessError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(2)

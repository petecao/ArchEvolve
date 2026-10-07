"""Strict-functional correctness plus analytic speed. Updated: 2026-10-06 ET.

The command reuses exact current certification execution receipts. It runs no
simulator and never turns functional host wall time into hardware performance.
"""
import copy
import re
from types import SimpleNamespace

from swdb import analytic, artifacts, certification_procedures, kernels, paths, workflow, writer
from swdb.cli import Failure
from swdb.store import Store

EVALUATOR='swdb.strict-functional-estimate.v1'


class IncorrectCandidate(Failure):
    """An exact current execution receipt failed a positive correctness check."""



def _require(condition, reason):
    if not condition:
        raise Failure(reason)


def _certified(store, candidate, certification_id, library_root=None):
    from swdb.library import Library
    receipt=store.get(certification_id,'certification')
    _require(receipt is not None,'strict-functional certification record does not exist')
    _require(receipt.get('evidence_kind')=='execution',
        'strict-functional correctness requires execution certification')
    identity=receipt.get('candidate',{})
    _require(identity.get('id')==candidate['id'] and identity.get('tree_sha256')==candidate['artifact']['sha256']
        and identity.get('snapshot')==candidate['source_snapshot'],
        'strict-functional certification belongs to another candidate artifact or source snapshot')
    catalog=Library(library_root or paths.HOME / "library",store=store)
    _require(catalog.current_certification(receipt),'strict-functional normative contract or dependency changed')
    _require(identity.get('contract')==receipt['entry']['id']
        and identity.get('contract_sha256')==receipt['entry']['content_sha256'],
        'strict-functional certification contract identity differs')
    implementation=store.get(candidate['implementation'],'implementation')
    _require(implementation is not None,'candidate implementation does not exist')
    plugin=kernels.require(implementation['kernel'],'strict-functional evaluation')
    proc=certification_procedures.procedure(certification_procedures.CANDIDATE)
    command=receipt.get('command',{})
    manifest=certification_procedures.manifest(proc,catalog.root,plugin)
    _require(proc.process_split and command.get('family')==proc.family and command.get('version')==proc.version
        and command.get('sources_match_version') is True
        and command.get('sources_sha256')==manifest['sources_sha256']
        and command.get('sources')==manifest['sources']
        and command.get('kernel_sources')==manifest['kernel_sources'],
        'strict-functional certification procedure or kernel correctness check changed; certify again')
    matrix=receipt.get('matrix',[]);controls=receipt.get('negative_controls',[])
    if receipt.get('verdict')=='failed' and any(row.get('status')=='failed' for row in matrix):
        raise IncorrectCandidate('strict-functional candidate failed a positive correctness check')
    _require(receipt.get('verdict')=='certified',
        'strict-functional correctness requires passing execution certification')
    _require(matrix and all(row.get('status')=='passed' for row in matrix)
        and controls and all(row.get('status')=='rejected' for row in controls)
        and all(row.get('matched') is True for row in receipt.get('clause_controls',[]) if row.get('enforceable')),
        'strict-functional certification has incomplete positive checks or negative controls')
    return receipt,plugin


def run(args):
    _require(workflow.CREATION_TAGS.get('mode')!='extensa','evaluate-functional requires ArchEvolve mode')
    encoded=args.file.read_bytes()
    _require(len(encoded)<=10*1024**2,'functional evaluation request exceeds 10 MiB')
    request=workflow.message_from_text(encoded.decode())
    fields={'message_version','id','candidate','certification','characterization','target_description','protocol','baseline'}
    _require(isinstance(request,dict) and request.get('message_version')=='1.0',
        'functional evaluation requires message_version 1.0')
    _require(not request.keys()-fields,'unknown functional evaluation request fields: '+str(sorted(request.keys()-fields)))
    _require(all(isinstance(request.get(key),str) and request[key] for key in fields-{'baseline'}),
        'functional evaluation requires candidate, certification, characterization, target_description and protocol IDs')
    _require(request.get('baseline') is None or isinstance(request['baseline'],str) and request['baseline'],
        'functional baseline must name a retained estimate ID')
    _require(re.fullmatch('[a-z0-9][a-z0-9._-]*',request['id']),'invalid functional evaluation ID')
    store=Store(args.records)
    from swdb.archevolve import require_team_safe
    target=analytic._load(store,request['target_description'],'target_description')
    characterization=analytic._load(store,request['characterization'],'workload_characterization')
    require_team_safe(store,request,target,characterization,command='evaluate-functional')
    _require(store.get(request['id']) is None and store.get(request['id']+'.estimate') is None,
        'functional evaluation ID already exists; use a fresh ID')
    candidate=store.get(request['candidate'],'candidate')
    _require(candidate is not None,'functional evaluation candidate does not exist')
    hardware=store.get(target['target'],'hardware_target')
    _require(hardware is not None and hardware.get('backend',{}).get('id')=='functional-source',
        'functional evaluation needs a source-only functional analytic hardware target')
    data=workflow.record('evaluation',request['id'],request=request,candidate=candidate['id'],
        proposal=candidate.get('proposal'),source_snapshot=candidate['source_snapshot'],
        implementation=candidate['implementation'],outcome={'state':'running','stage':'certification','reason':None},
        stages=[],timing=[],correctness={'state':'unverified','checks':[]},
        profiling={'state':'not_collected','reasons':['Per-region analytic evidence is in the referenced estimate.']},
        raw_artifacts=[],gain_claim=False,evidence_kind=characterization['evidence_kind'],
        context={'evaluator':EVALUATOR,'target':target['target'],'basis':'estimated','threads':target['threads'],
            'candidate_sha256':candidate['artifact']['sha256'],'protocol':request['protocol'],
            'roi':characterization['binding']['roi'],'correctness_scope':'functional-target',
            'hardware_correctness_claim':False,'performance_timing_collected':False})
    stage='certification'
    started=writer.now()
    try:
        receipt,plugin=_certified(store,candidate,request['certification'],args.library)
        data['correctness']={'state':'passed','checks':[{'passed':True,'graph':row.get('graph'),
            'source':row.get('source'),'tile_size':row.get('tile_size'),'threads':row.get('threads'),
            'result_check':copy.deepcopy(row.get('result_check'))} for row in receipt['matrix']]}
        data['context'].update(verifier=plugin.native_verifier,certification=_certification_context(receipt))
        data['stages'].append({'stage':stage,'state':'complete','started':started,'finished':writer.now()})
        stage='estimate';started=writer.now()
        _require(characterization['subject']=={'kind':'candidate','id':candidate['id']},
            'functional estimate characterization belongs to another source subject')
        _require(characterization['evidence_kind']=='contract_fixture' or
            characterization['binding']['subject_source_identity'].get('adapter')=='registered-functional.v1',
            'functional evaluation requires verified registered-functional whole-call counts')
        estimate=analytic.estimate(SimpleNamespace(records=args.records,
            characterization=request['characterization'],target_description=request['target_description'],
            protocol=request['protocol'],baseline=request.get('baseline'),id=request['id']+'.estimate'))
        data['context']['analytic_estimate']=_estimate_context(estimate)
        data['stages'].append({'stage':stage,'state':'complete','started':started,'finished':writer.now()})
        data['outcome']={'state':'complete','stage':'estimate','reason':None}
    except Failure as exc:
        state='incorrect' if isinstance(exc,IncorrectCandidate) else 'incompatible'
        if state=='incorrect':data['correctness']['state']='failed'
        data['stages'].append({'stage':stage,'state':state,'started':started,'finished':writer.now(),'reason':str(exc)})
        data['outcome']={'state':state,'stage':stage,'reason':str(exc)}
    writer.commit(args.records,new=[data])
    return data


def _certification_context(receipt):
    return {'id':receipt['id'],'sha256':artifacts.digest(receipt),'basis':receipt['evidence_basis'],
        'scope':'finite strict-functional certification matrix, including the kernel correctness check',
        'reuse':'retained_exact_current_identity','created_at':receipt.get('created_at'),
        'command':copy.deepcopy(receipt['command']),'negative_controls':len(receipt['negative_controls'])}


def _estimate_context(estimate):
    return {'id':estimate['id'],'sha256':artifacts.digest(estimate),
        **{key:copy.deepcopy(estimate[key]) for key in ('basis','seconds','ratio','verdict','error_band','baseline')},
        **{key:estimate[key] for key in ('characterization','characterization_sha256',
            'target_description','target_description_sha256','protocol','protocol_sha256','estimator_sha256')}}


def verify(data,store):
    """Verify archived bindings without applying today's procedure to old history."""
    context=data.get('context',{})
    if not isinstance(context,dict) or context.get('evaluator')!=EVALUATOR:
        return
    _require(context.get('basis')=='estimated' and context.get('correctness_scope')=='functional-target'
        and context.get('hardware_correctness_claim') is False
        and context.get('performance_timing_collected') is False
        and data.get('timing')==[] and data.get('gain_claim') is False,
        'functional evaluation cannot carry measured/simulated timing or hardware correctness claims')
    candidate=store.get(data.get('candidate'),'candidate')
    _require(candidate is not None and candidate['artifact']['sha256']==context.get('candidate_sha256')
        and candidate['source_snapshot']==data.get('source_snapshot')
        and candidate['implementation']==data.get('implementation'),
        'functional evaluation candidate binding changed')
    request=data.get('request',{})
    _require(request.get('id')==data['id'] and request.get('candidate')==candidate['id']
        and request.get('protocol')==context.get('protocol'),
        'functional evaluation request binding differs')
    pin=context.get('certification')
    if pin is not None:
        receipt=store.get(pin.get('id'),'certification')
        _require(receipt is not None and pin.get('id')==request.get('certification')
            and pin==_certification_context(receipt)
            and receipt.get('verdict')=='certified' and receipt.get('evidence_kind')=='execution',
            'functional certification reference changed')
        identity=receipt.get('candidate',{})
        _require(identity.get('id')==candidate['id']
            and identity.get('tree_sha256')==context['candidate_sha256']
            and identity.get('snapshot')==data['source_snapshot'],
            'functional certification candidate binding differs')
        checks=[{'passed':True,'graph':row.get('graph'),'source':row.get('source'),
            'tile_size':row.get('tile_size'),'threads':row.get('threads'),
            'result_check':row.get('result_check')} for row in receipt['matrix']]
        _require(data.get('correctness')=={'state':'passed','checks':checks},
            'functional correctness checks differ from their certification')
    compact=context.get('analytic_estimate')
    if compact is not None:
        estimate=store.get(compact.get('id'),'estimate')
        _require(estimate is not None and estimate['id']==data['id']+'.estimate'
            and compact==_estimate_context(estimate),
            'functional estimate reference or compact fields changed')
        characterization=store.get(estimate['characterization'],'workload_characterization')
        target=estimate.get('target_description_snapshot')
        _require(characterization is not None and target is not None
            and characterization['subject']=={'kind':'candidate','id':candidate['id']}
            and estimate['characterization']==request['characterization']
            and estimate['protocol']==context['protocol']
            and (estimate.get('baseline') or {}).get('id')==request.get('baseline')
            and artifacts.digest(target)==estimate['target_description_sha256']
            and target['target']==context['target'] and target['threads']==context['threads']
            and characterization['binding']['roi']==context['roi']
            and characterization['evidence_kind']==data['evidence_kind'],
            'functional estimate request, subject or target binding differs')
        hardware=store.get(target['target'],'hardware_target')
        _require(hardware is not None and hardware.get('backend',{}).get('id')=='functional-source',
            'functional estimate requires a source-only functional hardware target')
    if data.get('outcome',{}).get('state')=='complete':
        _require(pin is not None and compact is not None and data['correctness']['state']=='passed',
            'complete functional evaluation needs certification and estimate references')


def validate_record(record,ctx):
    from swdb.problems import Problem
    try:
        verify(record.data,ctx.store)
    except (Failure,KeyError,TypeError,ValueError,AttributeError) as exc:
        yield Problem(record.rel,'context',str(exc))

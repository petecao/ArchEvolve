"""Saved proposal adapter connecting OfflineEvolution to real hardware handoffs.

This is structural replay. No live model, executable rewrite or performance eval.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path, PurePosixPath
import json
import yaml

from archevolve.__main__ import ROOT, reference_context
from archevolve.evidence_select import capability_requests, select_evidence_candidates
from archevolve.evolution_runtime import OfflineEvolution
from archevolve.evolution_store import digest
from archevolve.hardware_catalog import validate_catalog
from archevolve.hardware_planning import plan_hardware, planning_artifacts
from archevolve.intrinsic_handoff import build_handoff_artifacts
from archevolve.normalize import load_normalized
from archevolve.parameter_exploration import enumerate_configurations, template
from archevolve.workload_context import bind_context, request_groups
from tools.render_mermaid import RequestError, build_artifacts, load_request


def require(condition, message):
    if not condition: raise RequestError('Saved planning proposal: '+message)


def pipeline_hash():
    return digest({p:sha256((ROOT/p).read_bytes()).hexdigest() for p in (
        'archevolve/planning_bridge.py','archevolve/planning_replay.py','archevolve/evolution_runtime.py','archevolve/evolution_policy.py',
        'archevolve/evolution_store.py','archevolve/evidence_select.py','archevolve/hardware_planning.py',
        'archevolve/hardware_catalog.py','archevolve/normalize.py','archevolve/measurement_methods.py',
        'archevolve/workload_context.py','archevolve/intrinsic_handoff.py','archevolve/hardware_behavior.py',
        'archevolve/mechanisms.py','archevolve/parameter_exploration.py','archevolve/__main__.py','tools/render_mermaid.py')})


class HardwarePlanningBridge:
    def __init__(self, store, input_path, catalog_path, source_context_path):
        self.store=store
        self.catalog,self.catalog_hash=load_request(catalog_path)
        validate_catalog(self.catalog)
        self.case=load_normalized(input_path,reference_context(ROOT))
        self.case['input_ref']='input.received.yaml'
        context,context_hash=load_request(source_context_path)
        self.case=bind_context(self.case,context,context_hash,'source-context.snapshot.yaml')
        require(self.case['source_context']['status']=='bound_manual_source_review','Source context must bind the exact workload source before replay.')
        requests,_=capability_requests(self.case)
        self.plan=plan_hardware(self.case,requests,request_groups(self.case,requests))
        self.bindings={'input_sha256':self.case['input_sha256'],'catalog_sha256':self.catalog_hash,
                       'source_context_sha256':context_hash,'hardware_plan_sha256':digest(self.plan),
                       'pipeline_sha256':pipeline_hash()}
        self.task_input={'bindings':self.bindings,'hardware_plan':self.plan}
        self.task_id=self.case['case_id']
        self.snapshots={'input.received.yaml':input_path.read_text(),'catalog.snapshot.yaml':catalog_path.read_text(),
                        'source-context.snapshot.yaml':source_context_path.read_text()}

    def seed(self, proposal_count):
        strategy,_=load_request(ROOT/'prompts/evolution/strategy.seed.yaml')
        reflector,_=load_request(ROOT/'prompts/evolution/reflector.seed.yaml')
        return {'catalog':self.catalog,'core':(ROOT/'prompts/evolution/core.md').read_text(),
                'strategy':strategy,'reflector':reflector,'policy':{
                    'mode':'offline_planning','max_calls':proposal_count+8,'max_tokens':(proposal_count+8)*1000,
                    'max_evaluations':proposal_count,'tokens_per_call':1000,'proposals_per_task':proposal_count,
                    'area_limit_mm2':None,'min_relative_gain':0,
                    'tasks':[{'id':self.task_id,'split':'development','input':self.task_input,
                              'cohort':None,'baseline_latency_ms':None}]}}

    def evaluate(self, request):
        proposal=request['candidate']; generated=False; issues=[]; bundle_ref=None
        try:
            require(request['mode']=='offline_planning','Use a structural-only campaign.')
            require(request['task']['id']==self.task_id and request['task']['input']==self.task_input,
                    'Workload or planning snapshot differs from the campaign.')
            require(proposal['mutation'] in {'placement','simplification'},'Replay only selects existing block options or retains CPU execution; synthesis and parameter edits are separate.')
            design=proposal['design']
            require(set(design)=={'format','bindings','block_choices'} and design['format']=='hardware-block-selection-v0.1',
                    'Only the block-selection format is accepted; no injected capabilities or configuration values.')
            require(design['bindings']==self.bindings,'Stale input, catalog, source context, plan or pipeline binding.')
            hardware,trace=select_evidence_candidates(self.case,self.catalog,'catalog.snapshot.yaml',self.catalog_hash,
                max_candidates=len(self.plan['blocks'])+1,block_choices=design['block_choices'])
            request_text=yaml.safe_dump(hardware,sort_keys=False)
            request_hash=sha256(request_text.encode()).hexdigest()
            files={**self.snapshots,'normalized.yaml':yaml.safe_dump(self.case,sort_keys=False),
                   'hardware-request.yaml':request_text,'selection-trace.yaml':yaml.safe_dump(trace,sort_keys=False)}
            files.update(planning_artifacts(trace['hardware_plan'],trace['block_catalog_results']))
            for name,content in build_artifacts(hardware,'hardware-request.yaml',request_hash).items():
                files['diagrams/'+name]=content
            for name,content in build_handoff_artifacts(hardware,request_hash).items():
                files['handoffs/'+name]=content
            for candidate in hardware['candidates'][1:]:
                if candidate['missing_evidence']:
                    issues.append({'category':'missing_capability_evidence','candidate_id':candidate['id'],
                                   'fields':candidate['missing_evidence']})
                issues.append({'category':'mapping_review_required','candidate_id':candidate['id'],
                               'requirement_ids':[r['id'] for r in candidate['requirements']],
                               'note':'Retrieval does not discharge concurrency, visibility, ownership or completion requirements.'})
                space=template(candidate,self.bindings['input_sha256'],self.bindings['catalog_sha256'])
                exploration=enumerate_configurations(candidate,space)
                if exploration['unknowns']:
                    issues.append({'category':'parameter_exploration_blocked','candidate_id':candidate['id'],
                                   'unknowns':exploration['unknowns']})
            files['README.md']='\n'.join(['# Saved hardware proposal handoff','',
                'Structural replay only. No software rewrite, simulator run, cost estimate or evaluated speedup.','',
                '[Block plan](planning.md) · [Hardware request](hardware-request.yaml) · [Intrinsic packages](handoffs/README.md)',
                '', 'CPU-retained choices stay explicit. Generated alternatives are conditional catalog mappings, not verified accelerators.',''])
            bundle_ref=self.store.put({'kind':'hardware_handoff_bundle','proposal_ref':request['candidate_ref'],
                                       'bindings':self.bindings,'files':files})
            generated=True;status='needs_information' if issues else 'handoff_generated'
        except (RequestError,TypeError,KeyError) as exc:
            status='rejected'
            issues=[{'category':'invalid_or_unsupported_proposal','message':str(exc)}]
        detail={'kind':'hardware_planning_feedback','proposal_ref':request['candidate_ref'],
                'bindings':self.bindings,'planning_status':status,'handoff_generated':generated,
                'issues':issues,'artifact_bundle_ref':bundle_ref,'performance_evaluated':False}
        detail_ref=self.store.put(detail)
        return {**detail,'candidate_sha256':request['candidate_ref'],'synthetic':False,
                'evidence_kind':'planning_feedback','evidence_refs':[detail_ref]+([bundle_ref] if bundle_ref else []),
                'cohort':None,'latency_ms':None,'area_mm2':None,'power_w':None}


class SavedHardwareProposals:
    """Replay exact saved choices. Does not synthesize or repair their contents."""
    def __init__(self, store, document):
        require(isinstance(document,dict) and set(document)=={'format','provenance','entries'} and
                document['format']=='saved-hardware-proposals-v0.1','Invalid saved proposal file.')
        require(isinstance(document['provenance'],str) and document['provenance'].strip(),'Record where saved proposals came from.')
        require(isinstance(document['entries'],list) and document['entries'],'Saved entries required.')
        for entry in document['entries']:
            require(isinstance(entry,dict) and set(entry)=={'id','task_id','core_sha256','strategy_sha256','history_sha256','content'},'Invalid saved entry envelope.')
            require(isinstance(entry['id'],str) and entry['id'],'Entry ID required.')
            require(isinstance(entry['content'],dict), 'Saved content must be a mapping.')
        require(len({e['id'] for e in document['entries']})==len(document['entries']),'Duplicate replay IDs.')
        self.store=store;self.document=deepcopy(document)
        self.source_ref=store.put(document)

    def __call__(self, request):
        require(request['operation']=='propose','This adapter only replays hardware proposals.')
        index=request['sequence']
        require(index<len(self.document['entries']),'No saved response for this call; export new context rather than reuse a stale response.')
        entry=self.document['entries'][index];ctx=request['context']
        require(entry['task_id']==ctx['task']['id'],'Saved proposal belongs to another task.')
        require(entry['core_sha256']==digest(ctx['core']), 'Saved proposal belongs to another fixed core.')
        require(entry['strategy_sha256']==digest(ctx['strategy']) and entry['history_sha256']==digest(ctx['history_refs']),
                'Saved proposal was authored for another strategy/history snapshot.')
        require(entry['content'].get('parent_ref')==ctx['parent_ref'],'Saved parent differs; it is never silently rebound.')
        self.store.append('saved_response_use',{'source_ref':self.source_ref,'entry_id':entry['id'],'sequence':index,
                                              'request_sha256':digest(request),'llm_calls':0})
        return {'content':deepcopy(entry['content']),'tokens':0}


def reflection_exchange(loop, kind):
    require(kind in {'strategy','reflector'},'Unknown reflection kind.')
    require(loop.history(),'Collect development feedback before reflection.')
    context=loop._context(loop.active('reflector'),loop.active('strategy'))
    request={'operation':'revise_'+kind,'context':context,'max_tokens':loop.policy['tokens_per_call'],
             'sequence':loop.usage()['calls'],'mode':loop.policy['mode']}
    return {'format':'saved-reflection-exchange-v0.1','provenance':None,
            'request_sha256':digest(request),'request':request,'response':None}


def replay_reflection(loop, exchange):
    require(isinstance(exchange,dict) and set(exchange)=={'format','provenance','request_sha256','request','response'} and
            exchange['format']=='saved-reflection-exchange-v0.1','Invalid reflection exchange.')
    operation=exchange['request'].get('operation')
    require(operation in {'revise_strategy','revise_reflector'},'Only strategy/reflector revision exchanges supported.')
    kind=operation.removeprefix('revise_')
    expected=reflection_exchange(loop,kind)
    require(exchange['request_sha256']==expected['request_sha256'] and exchange['request']==expected['request'],
            'Reflection context changed; export a new exchange. Do not silently rebind feedback.')
    require(isinstance(exchange['provenance'],str) and exchange['provenance'].strip(),'Saved reflection provenance required.')
    response=exchange['response']
    require(isinstance(response,dict) and set(response)=={'content','tokens'} and type(response['tokens']) is int and response['tokens']==0,
            'Saved replay response requires content and tokens: 0; no live model calls occur.')
    source_ref=loop.store.put(exchange)
    def provider(request):
        require(digest(request)==exchange['request_sha256'],'Saved reflection request mismatch.')
        loop.store.append('saved_response_use',{'source_ref':source_ref,'request_sha256':digest(request),'llm_calls':0})
        return deepcopy(response)
    original=loop.proposer
    loop.proposer=provider
    try: return loop.revise(kind)
    finally: loop.proposer=original


def export_run(store, directory):
    require(not directory.exists(),'Use a fresh export directory; previous artifacts are never overwritten.')
    output={'memory.json':json.dumps(store.export(),indent=2)+'\n'}
    summary=[]
    for index,event in enumerate(store.events('observation'),1):
        obs=event['record'];evaluation=store.get(obs['evaluation_ref']) if obs['evaluation_ref'] else {}
        folder=f'proposal-{index:03d}'
        output[folder+'/proposal.yaml']=yaml.safe_dump(store.get(obs['candidate_ref']),sort_keys=False)
        output[folder+'/feedback.yaml']=yaml.safe_dump(evaluation or obs,sort_keys=False)
        bundle=evaluation.get('artifact_bundle_ref')
        if bundle:
            for name,content in store.get(bundle)['files'].items():
                path=PurePosixPath(name)
                require(not path.is_absolute() and '..' not in path.parts and '\\' not in name,'Unsafe artifact path.')
                output[folder+'/'+name]=content
        summary.append({'folder':folder,'observation_ref':event['ref'],'planning_status':evaluation.get('planning_status','adapter_failure'),
                        'handoff_generated':evaluation.get('handoff_generated',False),'eligible_for_performance_ranking':obs['eligible']})
    report={'format':'hardware-planning-replay-report-v0.1','llm_calls':0,'hardware_evaluations':0,
            'observations':summary,'selected_winner':None,'note':'Source-bound structural replay, not autonomous search or measured improvement.'}
    output['report.yaml']=yaml.safe_dump(report,sort_keys=False)
    output['README.md']='\n'.join(['# Hardware-planning replay','',report['note'],'',
        '| Proposal | Structural result | Handoff |','|---|---|---|']+
        [f"| [{s['folder']}]({s['folder']}/proposal.yaml) | {s['planning_status']} | "+
         (f"[Package]({s['folder']}/README.md)" if s['handoff_generated'] else f"[Feedback]({s['folder']}/feedback.yaml)")+" |" for s in summary]+['',
         '[Machine-readable report](report.yaml) · [Complete experiment memory](memory.json)',''])
    directory.mkdir(parents=True)
    for name,content in output.items():
        path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    return report

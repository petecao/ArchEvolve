"""2026-10-16 ET. Stdlib-only inert cold-auditor author; never runs the auditor."""
import ast
import hashlib
import itertools
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]


def pin(path):
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}


def main():
    frozen=HERE/'inert-fb197c5d-public-v1'
    pins={'packet.json':'853a2f425917e49ba5beed3c3f13ac3856e5c0abf061b0c042b457442b348bc0',
          'entry.py':'76a687229c3d28e504102aad1bdd2c3efc47b1992cf1703c94a2291ec6f7c263',
          'expected.json':'a10f2ee5864b8c39c22e72b29f34e3195b59839e0fdc9a6ae9e5c6c5f7ecd4b2',
          'root-command.json':'bcc571f2916e00b2ca3cdbec4b8fdd837e1ad405f2b032491119cb5a84231080'}
    for name,wanted in pins.items():assert pin(frozen/name)['sha256']==wanted
    prior=BASE/'evidence/t25-private-frame9-passive-cold-audit-20261016.py'
    raw=prior.read_bytes();assert pin(prior)['sha256']=='12cd78dcbdda5d7d8a1c7a2a60ef99992a6214ea1d22426b382a663771133250'
    names=['require','digest','pin','read','snapshot','forms','expand','strip_comments','canon']
    lines=raw.decode().splitlines(keepends=True)
    helpers={n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(raw).body
             if isinstance(n,ast.FunctionDef) and n.name in names}
    assert set(helpers)==set(names)
    refs=[BASE/'evidence'/name for name in ['t25-private-frame9-passive-cold-metadata-v3-20261016.json',
          't25-private-frame9-independent-cold-decision-20261016.json',
          't25-private-frame9-passive-cold-support-supplement-20261016.json']]
    old=json.loads(refs[0].read_text())
    support=sorted({x for task in old['materialized_tasks'] for x in task['support_body_sha256']})
    assert len(support)==46
    command=json.loads((frozen/'root-command.json').read_text())
    source='/data1/yanruj/probata-resume-20261016-fb197c5d'
    root='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-fb197c5d-t25-closed-lifetime6-public-v1'
    actual=[x.replace('{SOURCE}',source).replace('{OUTPUT}',root) for x in command]
    command_sha=hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    goals=(HERE/'cold-goals-v1.py').read_text()
    template=(HERE/'cold-main-template-v1.py').read_text()
    text=template.replace('# __REVIEWED_PARSER_HELPERS__','\n\n'.join(helpers[n] for n in names))
    text=text.replace('# __INDEPENDENT_GOALS_AND_DEFINITIONS__',goals)
    text=text.replace('__COMMAND_SHA__',command_sha).replace('__PRIOR_SUPPORT_HASHES__',repr(support))
    text=text.replace('__PRIOR_SUPPORT_PINS__',repr([pin(p) for p in refs]));ast.parse(text)
    auditor=HERE/'cold-auditor-v1.py';auditor.write_text(text)
    # Scripted, compiler-free parse/definition-closure controls only.
    scope={'re':re,'json':json,'hashlib':hashlib,'itertools':itertools,'CHECKS':[]}
    exec(compile('\n\n'.join(helpers[n] for n in ['require','digest','forms','expand','canon'])+'\n'+goals,
                 '<inert-source-transcription-control>','exec'),scope)
    expected=json.loads((frozen/'expected.json').read_text());controls=[]
    for ident in expected['target_ids']:
        tree=scope['source_goal'](ident);canonical=scope['canon'](tree)
        closure=scope['required_definitions'](ident);assert closure<=set(scope['SOURCE_DEFINITIONS'])
        assert not({'check_lemma_','wp_goal'}&scope['symbols'](tree))
        controls.append({'id':ident,'source_form_parses':True,'required_source_definitions':sorted(closure),
                         'canonical_goal_digest':scope['digest'](canonical)})
    for name,(bindings,body) in scope['SOURCE_DEFINITIONS'].items():
        scope['forms']('(forall ('+bindings+') '+body+')')
    receipt={'created':'2026-10-16 ET','status':'INERT / NOT EXECUTED / COLD INSPECTION ONLY AFTER ROOT SETTLEMENT',
        'author':pin(Path(__file__)),'auditor':pin(auditor),'template':pin(HERE/'cold-main-template-v1.py'),
        'independent_source_transcription':pin(HERE/'cold-goals-v1.py'),'prior_reviewed_parser':pin(prior),
        'exact_reused_helpers':names,'prior_source_attribution_inputs':[pin(p) for p in refs],
        'known_support_assertion_hashes':46,'frozen_profile_inputs':{n:pin(frozen/n) for n in pins},
        'actual_command_sha256':command_sha,
        'required_settlement_arguments':['--node ROOT_CONFIRMED_NODE','--generation ROOT_CONFIRMED_GENERATION','--ended-utc ROOT_CONFIRMED_END_UTC'],
        'source_transcription_controls':controls,'actual_project_compiler_native_verifier_solver_runs':0,
        'actual_auditor_executions':0,'SSH_calls':0,'source_typed_bridge_established':False,'caller_acceptance':False,
        'scope':'Stdlib AST/helper extraction, independent six source-goal/definition transcriptions and syntax/closure controls only. No actual native/task proof observation or acceptance. Root confirms settlement before any exact-root cold run.'}
    path=BASE/'evidence/t25-closed-lifetime6-cold-auditor-preparation-v1-20261016.json'
    path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'auditor':pin(auditor),'receipt':pin(path),'actual_command_sha256':command_sha},indent=2))


if __name__=='__main__':
    main()

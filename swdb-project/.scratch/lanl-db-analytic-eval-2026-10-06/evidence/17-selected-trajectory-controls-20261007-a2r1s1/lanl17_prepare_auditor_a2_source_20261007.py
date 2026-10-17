# Source preparation only. Reads Python source, extracts AST text and writes new
# /private/tmp preparation artifacts. Never imports/executes any projected code.
import ast,hashlib,json,pathlib,textwrap
T=pathlib.Path('/private/tmp'); P=pathlib.Path('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
original=T/'lanl17_selected_record_trajectory_auditor_20261007.py'; old=original.read_text()
assert sha(original.read_bytes())=='77907ba07636397c55ce38cf337034d3dca5d0217bfaea4678b4b05ffd9dfd2d'
collector=T/'lanl17_compact_attempt_custody_a2_20261007.py'; col=collector.read_text()
projections=[]
def segment(path,name,parent=None,new=None):
    source=(P/path).read_text();tree=ast.parse(source)
    pool=tree.body
    if parent:pool=next(n for n in pool if isinstance(n,ast.ClassDef) and n.name==parent).body
    node=next(n for n in pool if (getattr(n,'name',None)==name or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets)))
    first=min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])
    text=textwrap.dedent('\n'.join(source.splitlines()[first-1:node.end_lineno]))
    if new:text=text.replace('def '+name+'(', 'def '+new+'(',1)
    projections.append({'source_path':str(P/path),'source_sha256':sha((P/path).read_bytes()),'name':name,'parent':parent,'auditor_name':new or name,'source_AST_sha256':sha(ast.dump(node,include_attributes=False).encode()),'transformation':'method lifted to module and function name changed' if new else 'exact source text / AST'})
    return text
search_names=['StopReason','STOP_PRECEDENCE','IterationOutcome','COMPLETED_ITERATION_OUTCOMES','CallOutcome','UNCOUNTED_CALL_OUTCOMES','BUDGET_KEYS','SearchBudget','CallRecord','IterationRecord','CallRefused','SearchLedger']
blocks=[segment('swdb/extensa/search.py',n) for n in search_names]
blocks += [segment('swdb/campaign.py',n) for n in ('LEVEL_RANK','selection_key','select')]
blocks += [segment('swdb/campaign_targets.py','_pairing_request','Gem5Adapter','source_pairing_request'), segment('swdb/extensa_pairing.py','_context','PairingLedger','source_pairing_context')]
# Source class name confirmed via AST, never module import.
new=old.replace('import datetime as dt','from dataclasses import dataclass\nfrom enum import Enum\nfrom typing import Optional\nimport datetime as dt',1)
point='class Reader:\n'; assert point in new
new=new.replace(point,'\n\n'.join(blocks)+'\n\n'+point,1)
# Collector projection snippets remain exact except documented local function renames.
ctree=ast.parse(col); snippets=[ast.get_source_segment(col,n) for n in ctree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('CALL_KEYS','CANDIDATE_KEYS','ITERATION_KEYS','STATE_KEYS') for t in n.targets)]
for name in ('calls','candidate','iteration','project_state'):
    node=next(n for n in ctree.body if getattr(n,'name',None)==name)
    raw=ast.get_source_segment(col,node)
    for oldname,fresh in [('calls','project_calls'),('candidate','project_candidate'),('iteration','project_iteration')]:
        raw=raw.replace('def '+oldname+'(', 'def '+fresh+'(').replace(oldname+'(',fresh+'(') if oldname != name else raw
    # Token-wise rename via source positions is unnecessary here; exact whole-word
    # names only are changed, and the proof records that preparation transform.
    import re
    raw=ast.get_source_segment(col,node)
    for oldname,fresh in [('calls','project_calls'),('candidate','project_candidate'),('iteration','project_iteration')]:raw=re.sub(r'\b'+oldname+r'(?=\()',fresh,raw)
    snippets.append(raw)
new=new.replace('class Reader:\n','\n\n'.join(snippets)+'\n\nclass Reader:\n',1)
new=new.replace('class Refused(ValueError): pass',"def safe_code(code):\n    require(isinstance(code,str) and re.fullmatch('[a-z0-9_.-]+',code),'Closed reason code required');return code\nclass Refused(ValueError): pass",1)
methods=(T/'lanl17_auditor_a2_methods_20261007.txt').read_text()
methods=methods.replace("used_summary['provider_wait_hours']==round(state['provider_wait_hours'],6)", "used_summary.get('provider_wait_hours',0)==round(state['provider_wait_hours'],6)")
methods=methods.replace("                require(need(admission,'selected_reader_source_sha256')==selected['reader_sha256'] if 'reader_sha256' in selected else need(admission,'reader_source_pin')['sha256']==need(admission,'selected_reader_source_sha256'),'CPU original reader source pin missing')", "                require(sha(self.raw(need(admission,'reader_source_pin')))==need(admission,'selected_reader_source_sha256'),'CPU original reader source pin differs')")
new=new.replace('    def trajectory(self,row):\n',methods+'\n    def trajectory(self,row):\n',1)
# Source hashes for accounting/linkage are required at future final R, in addition
# to the original exact public D30 computation sources.
values={'swdb/campaign.py':sha((P/'swdb/campaign.py').read_bytes()),'swdb/extensa/search.py':sha((P/'swdb/extensa/search.py').read_bytes()),'swdb/campaign_targets.py':sha((P/'swdb/campaign_targets.py').read_bytes()),'swdb/bfs_protocol.py':sha((P/'swdb/bfs_protocol.py').read_bytes())}
pos=new.index('PINNED_SOURCE_FILES=');end=new.index('\n',pos)
new=new[:end]+'\nPINNED_SOURCE_FILES.update('+repr(values)+')'+new[end:]
new=new.replace("require(projection['format']=='swdb.lanl17-trajectory-audit-projection.v1'", "require(projection['format']=='swdb.lanl17-trajectory-audit-projection.v2'")
new=new.replace("        require(state['iterations']==summary['iterations'],'Original completed state rows differ from summary')", "        require(state['iterations']==[project_iteration(r) for r in summary['iterations']],'Original completed state projection differs from summary')\n        require(state['setup_calls']==project_calls(summary['setup']['provider_calls']),'Original setup calls differ')\n        require(state['stop_detail_sha256']==digest(summary.get('stop_detail')),'Original stop detail hash differs')")
new=new.replace("interrupted==summary.get('interrupted_iteration')", "interrupted==(project_iteration(summary['interrupted_iteration']) if summary.get('interrupted_iteration') else None)")
new=new.replace("        final_dispatch,final_stop,final_release=stopped[-1]", "        attempt_custody=self.attempt_states(attempts,projection,cid,stopped)\n        final_dispatch,final_stop,final_release=stopped[-1]")
# Replace weak terminal checks with exact retained accounting and selection.
needle="        pairing_policy={'format':LEDGER"
start=new.index(needle)
new=new[:start]+"        accounting=self.retained_ledger(summary,state,projection)\n        selection=self.selection_replay(summary)\n"+new[start:]
# Include interrupted candidates as real roots without adding completed iterations.
oldloop="        for iteration in summary['iterations']:\n            for candidate in iteration['candidates']:\n                candidate_rows+=1"
newloop="        for iteration in summary['iterations']+([summary['interrupted_iteration']] if summary.get('interrupted_iteration') else []):\n            for candidate in iteration['candidates']:\n                candidate_rows+=1"
assert oldloop in new;new=new.replace(oldloop,newloop,1)
new=new.replace("        reached=self.closure(roots,index)", "        linkage=self.outcome_linkage(summary,projection,roots)\n        reached=self.closure(roots,index)\n        omitted={r['id'] for r in summary.get('interrupted_iteration',{}).get('candidates',[]) if r.get('id')}\n        if omitted:\n            extra=self.json(need(row,'interrupted_selected_body_custody'))\n            require(extra['format']=='swdb.lanl17-interrupted-selected-bodies.v1' and extra['campaign']==cid and set(extra['candidate_ids'])==omitted and extra['record_index_sha256']==digest(index) and extra['public_full_validation_returncode']==0 and extra['public_finalize_exported_these_candidates'] is False,'Interrupted selected bodies must be separately pinned/validated; final helper does not export them')\n            require(set(extra['record_ids'])<=reached and omitted<=set(extra['record_ids']),'Interrupted selected closure incomplete')")
new=new.replace("'source_of_completion':'Pinned original state/ledger, not summary existence'", "'source_of_completion':'Pinned original per-attempt state/ledger, not summary existence','attempt_state_custody':attempt_custody,'retained_accounting':accounting,'timing_selection_replay':selection,'exact_outcome_linkage':linkage")
start=new.index("        for key in ('final_ticket11_acceptance','final_ticket14_acceptance'):\n",new.index('    def audit(self):'))
end=new.index('        self.selected_records();freeze=self.freeze()',start)
new=new[:start]+"        dependency_admission=self.dependencies()\n"+new[end:]
new=new.replace("'strict_additive_custody':custody,", "'strict_additive_custody':custody,'final_dependency_admission_boundaries':dependency_admission,",1)
new=new.replace("swdb.lanl17-selected-read-only-audit.v1", "swdb.lanl17-selected-read-only-audit.v2")
new=new.replace("swdb.lanl17-selected-admission-pins.v1", "swdb.lanl17-selected-admission-pins.v2")
# Dependency exports are read solely to prove their explicit ancestry in final R.
new=new.replace("        self.refs={C,self.R['commit'],self.EF['commit'],self.ER['commit']}", "        self.refs={C,self.R['commit'],self.EF['commit'],self.ER['commit']}\n        self.refs.update(need(self.pins,k)['actual_export_commit'] for k in ('final_ticket11_acceptance','final_ticket14_acceptance'))")
selection='''    def selection_replay(self,summary):
        require(summary.get('pilot') is None,'Gem5Adapter HAS_PILOT=False; unexpected pilot cannot be ignored')
        previous={};pool=[]
        for row in summary['iterations']:
            pool.extend(row['candidates']);improved=[]
            for cls in (r['class'] for r in summary['workload_classes']):
                best,_,_=select([c for c in pool if c['class']==cls])
                if best is not None and (cls not in previous or selection_key(best)>selection_key(previous[cls])):
                    previous[cls]=best;improved.append(cls)
            require(set(improved)==set(row['improved_classes']),'Original timing-only class improvement differs')
        for row in summary['per_class']:
            best,faster,verdict=select([c for c in pool if c['class']==row['class']])
            require(row['best']==(best['id'] if best else None) and row['best_level']==(best['level'] if best else None) and row['verdict']==verdict and row['faster_uncertified']==faster,'Original timing-only terminal selection differs')
        return {'source':'Exact C campaign.select / selection_key','completed_candidate_rows_only':True,'interrupted_candidates_do_not_advance_selection':True}

'''
new=new.replace('    def retained_ledger(self,summary,state,projection):\n',selection+'    def retained_ledger(self,summary,state,projection):\n',1)
# Preserve aggregate context/observations as well as ID digests.
new=new.replace("                require(not component.get('component_evaluations')", "                require(value['context']['component_contexts'][component['id']]==component['context'] and value['context']['component_bindings'][component['id']]==component['context'].get('execution_binding'),'Aggregate copied context/binding differs')\n                require(digest(value['build'])==digest(component['build']),'Aggregate/component build differs')\n                require(not component.get('component_evaluations')")
new=new.replace("        return {'linked_execution_components'", "            require(value['timing']==[r for e in components for r in self.record(e['evaluation'],'evaluation')['timing']] and value['correctness']['checks']==[r for e in components for r in self.record(e['evaluation'],'evaluation')['correctness']['checks']],'Aggregate timed/correctness rows differ')\n        return {'linked_execution_components'") if False else new
new=new.replace("        roots=set();artifacts_seen=set();candidate_rows=0", "        roots=set();artifacts_seen=set();candidate_rows=0;prematerialization_refusals=0;interrupted_roots=set()")
new=new.replace("                if not candidate.get('id'):continue  # Real refusal", "                if not candidate.get('id'):continue  # Real refusal")
new=new.replace("                if not candidate.get('id'):continue  # Real refusal before materialization, not an artifact.", "                if not candidate.get('id'):\n                    prematerialization_refusals+=1;continue  # Actual refusal before materialization; no artifact/pair invented.")
new=new.replace("                if not candidate.get('id'):continue  # Real refusal before materialization, not an artifact.", "                if not candidate.get('id'):\n                    prematerialization_refusals+=1;continue")
# Original wording is verified explicitly; do not silently miss this source seam.
new=new.replace("                if not candidate.get('id'):continue  # Real refusal before materialization, not an artifact.", "                if not candidate.get('id'):\n                    prematerialization_refusals+=1;continue")
# Pin all roots belonging to the interrupted row, including cert/comparison components.
new=new.replace("        omitted={r['id'] for r in summary.get('interrupted_iteration',{}).get('candidates',[]) if r.get('id')}", "        interrupted_roots={r['id'] for r in summary.get('interrupted_iteration',{}).get('candidates',[]) if r.get('id')}\n        for candidate in summary.get('interrupted_iteration',{}).get('candidates',[]):\n            if (candidate.get('certification') or {}).get('record'):interrupted_roots.add(candidate['certification']['record'])\n            for c in candidate.get('comparisons',[]):\n                comparison=self.record(c['comparison'],'comparison_result');interrupted_roots.update((c['comparison'],comparison['baseline_evaluation'],comparison['candidate_evaluation']))\n        omitted={r['id'] for r in summary.get('interrupted_iteration',{}).get('candidates',[]) if r.get('id')}")
new=new.replace("set(extra['record_ids'])<=reached and omitted<=set(extra['record_ids'])", "set(extra['root_ids'])==interrupted_roots and set(extra['record_ids'])==self.closure(interrupted_roots,index)")
new=new.replace("'candidate_rows':candidate_rows,", "'candidate_rows':candidate_rows,'prematerialization_refusal_rows':sum(1 for it in summary['iterations']+([summary['interrupted_iteration']] if summary.get('interrupted_iteration') else []) for candidate in it['candidates'] if not candidate.get('id')),")
new=new.replace('(Refused,KeyError,TypeError,ValueError,yaml.YAMLError,subprocess.SubprocessError,OSError)', '(Refused,KeyError,TypeError,ValueError,RuntimeError,yaml.YAMLError,subprocess.SubprocessError,OSError)')
out=T/'lanl17_selected_record_trajectory_auditor_a2_20261007.py';out.write_text(new)
# Only AST/source validation is permitted. No executable imports or assertions
# against actual campaign data; these are syntax/projection preparation checks.
ast.parse(new);ast.parse(col)
originalproof=json.loads((T/'lanl17_selected_record_trajectory_auditor_pure_projection_20261007.json').read_text())
proof={'format':'swdb.lanl17-auditor-a2-source-preparation.v1','source_C':'f893fed400347ed23d92e917d8bde21b75e5375d','original_auditor_sha256':sha(original.read_bytes()),'original_artifacts_preserved':True,'source_AST_parse_passed':True,'auditor_executed':False,'collector_executed':False,'Store_tests_actual_inputs_native_provider_SSH':False,'new_exact_public_projections':projections,'original_public_projections_retained':originalproof['projections'],'collector_projection_transform':'Copy exact functions, rename only local projection helper function names','files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in (out,collector,T/'lanl17_auditor_a2_methods_20261007.txt',T/'lanl17_prepare_auditor_a2_source_20261007.py')],'limitations':['No actual final R or campaigns','Unsaved provider/step-time/DU completeness requires explicit parent-attestation boundary','Collector cannot atomically own frozen helper lane lock; parent immediate dispatch-state corroboration required','Interrupted materialized/rejected bodies may require separately validated selected exports beyond original finalize']}
proof['identity_sha256']=digest(proof);dest=T/'lanl17-auditor-a2-source-preparation-20261007.json';dest.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'auditor':proof['files'][0],'collector':proof['files'][1],'proof':str(dest),'proof_identity':proof['identity_sha256'],'proof_file_sha256':sha(dest.read_bytes()),'AST_only':True}))

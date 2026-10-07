"""2026-10-07 ET: pure source/cap arithmetic proposal, no action or helper rewrite."""
import ast,datetime,hashlib,json
from pathlib import Path
source=Path('/private/tmp/lanl17_parent_helpers_caps_a2.py')
raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='09136ee553984b2c0cf929a6746f037aa4e1874f863aa2e83e0e0842a8b65ed9'
tree=ast.parse(raw.decode());sites=[]
new_caps=[3600,6000,3600,6000,14400,3600]
selectors=['validate-before-freeze','population-freeze','validate-<campaign>','export-<campaign>','final-agreement-report','validate-final-export']
multiplicities=[1,1,4,4,1,1]
for function in tree.body:
 if isinstance(function,ast.FunctionDef) and function.name in ('prepare','finalize'):
  calls=sorted((node for node in ast.walk(function) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='run_cli'),key=lambda node:node.lineno)
  for call in calls:
   index=len(sites);assert isinstance(call.args[4],ast.Constant)
   sites.append({'action':function.name,'line':call.lineno,'selector':selectors[index],'multiplicity':multiplicities[index],
    'current_child_cap_s':call.args[4].value,'proposed_child_cap_s':new_caps[index]})
assert len(sites)==6 and [site['current_child_cap_s'] for site in sites]==[1400,1400,1400,900,1200,1400]
def caps(action,key):return sum(row[key]*row['multiplicity'] for row in sites if row['action']==action)
# Success-path directly bounded helper commands, outside run_cli children:
# prepare: capacity2 + wrapper3 + source fetch/ref/worktree3 + clean2+2 + export7.
# finalize: load clean2 + wrapper3 + source status1 + export7.
counts={'prepare':19,'finalize':13}
whole={}
for action,outer in [('prepare',18000),('finalize',78000)]:
 public=caps(action,'proposed_child_cap_s');direct=counts[action]*120+10
 whole[action]={'current_public_cli_cap_sum_s':caps(action,'current_child_cap_s'),
  'current_direct_bounded_command_count_120s':counts[action],'direct_bounded_commands_sum_s':direct,
  'direct_command_accounting':'120s commands plus official --version cap10; includes nested final Git export.',
  'current_full_bounded_command_sum_s':caps(action,'current_child_cap_s')+direct,
  'proposed_public_cli_cap_sum_s':public,'proposed_full_bounded_command_sum_s':public+direct,
  'proposed_supervisor_metadata_wait_s':outer,'uncapped_work_reserve_s':outer-public-direct,
  'proposed_enclosing_term_deadline_s':outer+120,'proposed_enclosing_kill_after_s':60,
  'proposed_parent_envelope_s':outer+300,
  'reserve_scope':'Direct full Store/certification/library work, live graph/model/source pins, YAML/JSON/copies/hashes and Git file publication/owned cleanup. Administrative allowance, no elapsed guarantee.'}
assert whole['prepare']['proposed_full_bounded_command_sum_s']==11890 and whole['prepare']['uncapped_work_reserve_s']==6110
assert whole['finalize']['proposed_full_bounded_command_sum_s']==57970 and whole['finalize']['uncapped_work_reserve_s']==20030
value={'format':'swdb.lanl17-metadata-cap-proposal.v1','updated':'2026-10-07 ET','state':'parent_review_pending_not_selected',
 'helper_09136_sha256':hashlib.sha256(raw).hexdigest(),'source_C':'f893fed400347ed23d92e917d8bde21b75e5375d',
 'estimator_sha256':'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3',
 'completed_model_evidence':{'origin':'Parent verified completed actual a3 CLI/public-validation/lane receipts; Git compact export pending at proposal creation.',
  'administrative_only':True,'bc_freeze_s':1266.086,'forecast_stages_s':[729.741,773.625,796.940,834.880],
  'public_validate_s':326.655,'catalog_records':672,'catalog_yaml_bytes':574754793,'application_outcomes_opened':False,
  'meaning':'Past metadata-stage observations, not latency models or predictions for future stores.'},
 'sites':sites,'whole_actions':whole,
 'source_counts':{'prepare_full_stores':5,'prepare_full_validations':3,'prepare_indexes':1,
  'finalize_full_stores':'22+M+3k','finalize_full_validations':'11+k+q','finalize_indexes':1,
  'all_four_new_exports_stores':'34+M','all_four_new_exports_validations':19,
  'candidate_filter_rows':'At most16 final candidate ID rows per successful two-class/eight-completed-iteration summary; at most64 across four. No unique-content/eligible-pair claim.'},
 'preserved_budgets':{'campaign_lane_hours':24,'disk_gb':20,'max_iterations':8,'plateau_iterations':4,'provider_calls_per_iteration':3,'provider_calls_setup':1,'simultaneous_campaign_lanes':2},
 'no_runtime_scaling_or_upper_bound_proof':True,'caps_are_administrative_choices':True,
 'current_helper_original_proofs_unchanged':True,'new_helper_created':False,'new_supervisor_created':False,
 'actual_17_metadata_actions':0,'actual_17_campaigns':0,'provider_calls':0,'cli_or_ssh_execution':False,
 'required_before_any_new_helper_prepare':['Parent selection and exact six literal-call edit proof, all other helper bytes unchanged.',
  'Fresh actual original4d Linux cleanup receipt pins selected new helper/hash and existing processes.py.',
  'Distinct supervisor variant changes only HELPER_SHA; actual revised a848 fixture pins that supervisor/helper, no science action.',
  'Retain all091/31e/4d/a1/a2/current supervisor receipts and failed preparation history.',
  'Final enriched sourceW/F6 and actual complete catalog/stage evidence pinned before prospective population freeze.'],
 'scope':'Source-only proposal. Finite caps may still stop unknown future direct work; metadata failure preserves partial canonical chronology and never triggers scientific replay/padding.'}
value['identity_sha256']=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
Path('/private/tmp/lanl17-metadata-cap-proposal-20261007.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'sites':sites,'whole_actions':whole,'identity_sha256':value['identity_sha256']},indent=2))

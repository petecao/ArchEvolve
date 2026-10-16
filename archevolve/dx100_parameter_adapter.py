"""Import Eric's pinned DX100 domain handoff as proposals, never legal-domain admission."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import yaml

from archevolve.evolution_policy import is_sha
from archevolve.evolution_store import digest
from archevolve.parameter_exploration import template
from tools.render_mermaid import load_request, RequestError

SOURCE = 'e4fc4afdf894f295442cef3604667a469fab8e62'
DESIGN = 'dx100-artifact-e4fc4af'
TILES = [1024, 2048, 4096, 8192, 16384, 32768]
PARAMETERS = {
    'num_tiles_per_core','num_tile_elements','num_regs_per_core','num_instructions_per_core',
    'num_row_table_rows_per_slice','num_row_table_entries_per_subslice_row','num_row_table_config_cache_entries',
    'num_request_table_addresses','num_request_table_entries_per_address','reconfigure_row_table','no_reorder',
    'force_cache_access','num_initial_row_table_slices','spd_read_latency','spd_write_latency',
    'num_spd_read_ports_per_maa','num_spd_write_ports_per_maa','rowtable_latency','ALU_lane_latency',
    'num_ALU_lanes','cache_snoop_latency','max_outstanding_cache_side_packets','max_outstanding_cpu_side_packets',
    'num_memory_channels','num_cores','num_maas'}
COUPLINGS = {'software_hardware_layout','payload_and_offsets','length_width','operand_id_encoding',
    'wide_values','bfs_worker_limits','core_instance_geometry','row_table_slice_family','row_table_capacity',
    'request_table_capacity','ports_lanes_latency','area_model_scope'}
ALIASES = {
    'tile_elements': {'model_parameter':'num_tile_elements','meaning':'catalog_reference_only_not_effective_setting'},
    'effective_tile_elements': {'model_parameter':'num_tile_elements','meaning':'proposed_effective_setting_pending_validation'},
    'row_table_rows_per_slice': {'model_parameter':'num_row_table_rows_per_slice','meaning':'proposed_reference_freeze_pending_validation'},
    'row_table_entries_per_subslice_row': {'model_parameter':'num_row_table_entries_per_subslice_row','meaning':'proposed_reference_freeze_pending_validation'}}


def require(ok, message):
    if not ok: raise RequestError('DX100 domain adapter: '+message)


def read_handoff(contract_path, verification_path, published_path):
    contract, contract_hash = load_request(contract_path)
    verification, _ = load_request(verification_path)
    published, published_hash = load_request(published_path)
    require(verification.get('contract_sha256')==contract_hash, 'Contract differs from its verification record.')
    require(verification.get('published_results_sha256')==published_hash, 'Published-result snapshot differs from verification record.')
    require(verification.get('source_commit')==SOURCE and verification.get('status')=='passed_source_contract_checks', 'Unexpected source verification scope.')
    require(verification.get('declared_defaults_checked_against_SimObject_AST')==26 and verification.get('source_file_hashes_checked_against_git_objects')==17, 'Unexpected source-check inventory.')
    require(verification.get('independently_validated_target_configurations')==0, 'This adapter does not import new target-admission claims; review the changed handoff.')
    require(contract.get('format')=='dx100-explorer-domain-handoff-v1' and contract.get('source_commit')==SOURCE and contract.get('design_id')==DESIGN,
            'Unsupported design, source revision or handoff format.')
    require(contract.get('independently_validated_configurations')==[], 'Target receipts require a separate admission path.')
    params=contract.get('parameters',[])
    require(isinstance(params,list) and all(isinstance(p,dict) and isinstance(p.get('id'),str) for p in params), 'Malformed parameter inventory.')
    require(len(params)==len(PARAMETERS) and {p['id'] for p in params}==PARAMETERS, 'Expected the 26 pinned model parameters exactly once.')
    by_id={p['id']:p for p in params}
    for p in params:
        value=p.get('reference_default')
        require((p.get('type')=='Bool' and type(value) is bool) or
                (p.get('type') in {'Unsigned','Cycles'} and type(value) is int and value>0), 'Reference type/count mismatch: '+p['id'])
        require(p.get('cli_option') is None or (isinstance(p['cli_option'],str) and p['cli_option'].startswith('--')), 'Invalid CLI metadata.')
        require(p.get('legal_domain') is None and p.get('independently_validated_values')==[], 'Do not silently upgrade newly changed domain/validation fields.')
    profile=contract.get('initial_explorer_profile',{})
    require(profile.get('status')=='proposed_pending_matched_correctness_validation' and
            profile.get('vary')=={'num_tile_elements':TILES} and profile.get('freeze_other_parameters_to_reference') is True,
            'Only the six-point proposed tile sweep with other reference settings frozen is supported.')
    tile=by_id['num_tile_elements']
    require(tile.get('kernel_supported_values')==TILES and tile.get('author_reported_values')==TILES,
            'Tile candidates must retain both source-support and author-reported labels.')
    for p in params:
        expected='enumerate_kernel_supported_sizes_pending_target_validation' if p['id']=='num_tile_elements' else 'freeze_reference_pending_validation'
        require(p.get('initial_explorer_policy')==expected,'Unsupported knob variation policy.')
    rules=contract.get('coupling_constraints',[])
    require(isinstance(rules,list) and len(rules)==len(COUPLINGS) and {r['id'] for r in rules}==COUPLINGS,
            'Coupling inventory changed; review before adapting.')
    sources=contract.get('source_files',[])
    require(len(sources)==17 and len({s['path'] for s in sources})==17 and all(is_sha(s.get('sha256')) for s in sources),
            'Pinned source-file hash inventory required.')
    require(published.get('source_commit')==SOURCE, 'Published observations refer to another source revision.')
    return contract,contract_hash,verification,published,published_hash


def prepare_candidates(candidate,input_sha256,catalog_sha256,contract_path,verification_path,published_path,max_candidates=6):
    """Return six (or a bounded prefix of) non-executable validation candidates."""
    require(candidate.get('catalog_design_revision')==SOURCE, 'Candidate source edition differs from the domain contract.')
    require(candidate.get('catalog_design_id')==DESIGN, 'Supply an artifact DX100 candidate, not another design or paper-only record.')
    require(type(max_candidates) is int and 0<max_candidates<=len(TILES), 'Budget must be an integer from 1 to 6.')
    strict_space=template(candidate,input_sha256,catalog_sha256)
    contract,ch,verification,published,ph=read_handoff(contract_path,verification_path,published_path)
    pinned={s['path']:s['sha256'] for s in contract['source_files']}
    evidence={s['title']:s for s in candidate.get('source_evidence',{}).get('sources',{}).values()}
    require({'benchmarks/gapbs/src/bfs.cc','benchmarks/API/MAA_gem5.hpp','src/mem/MAA/MAA.py'}<=set(evidence),
            'Candidate must retain the pinned BFS/API/model evidence.')
    for path in set(evidence)&set(pinned):
        require(evidence[path].get('edition')==SOURCE and evidence[path].get('sha256')==pinned[path], 'Conflicting candidate/source evidence: '+path)
    params={p['id']:p for p in contract['parameters']}
    defaults={p['id']:p['reference_default'] for p in contract['parameters']}
    catalog_params={p['id']:p for p in candidate['parameter_contract']}
    require(set(catalog_params)==set(ALIASES), 'Catalog parameter alias set changed; explicit mapping review required.')
    for name,alias in ALIASES.items():
        p=catalog_params[name]
        if name=='effective_tile_elements':
            require(p['state']=='unknown' and p['value'] is None, 'Effective tile setting is already bound differently.')
        else:
            require(p['state']=='fixed_reference' and p['value']==defaults[alias['model_parameter']], 'Catalog/source reference conflict: '+name)
    cores=defaults['num_cores'];tiles=defaults['num_tiles_per_core'];regs=defaults['num_regs_per_core'];instances=defaults['num_maas']
    require(cores==4 and instances==1 and cores%instances==0 and tiles==8 and regs==8, 'Initial stock API/core/instance geometry requires review.')
    require(cores*tiles<=255 and cores*regs<=255, 'Reference operand namespace exceeds the pinned encoding.')
    bindings={'candidate_sha256':digest(candidate),'input_sha256':input_sha256,'catalog_sha256':catalog_sha256,
              'contract_sha256':ch,'published_results_sha256':ph,'source_commit':SOURCE}
    profile={'format':'dx100-candidate-domain-v0.1','bindings':bindings,'parameter_aliases':deepcopy(ALIASES),
        'vary':{'num_tile_elements':{'candidate_values':TILES,'legal_domain':None,
            'evidence_status':'kernel_supported_and_author_reported_pending_target_validation','independently_validated_values':[]}},
        'frozen_reference_values':{k:v for k,v in defaults.items() if k!='num_tile_elements'},
        'reference_freeze_status':'proposed_pending_effective_configuration_validation',
        'parameter_inventory':deepcopy(contract['parameters']),'coupling_constraints':deepcopy(contract['coupling_constraints']),
        'source_files':deepcopy(contract['source_files']),'unresolved':deepcopy(contract['unresolved']),
        'required_preflight':deepcopy(contract['initial_explorer_profile']['required_preflight']),
        'validation_status':'no_independently_validated_configurations',
        'mapping_scope':'Six sizes are supported by the pinned authors BFS. This does not validate the selected read-offload or five-tile hybrid mapping.',
        'cost_reference':{'status':'scoped_proxy_reference_only_not_executed',
            'source_rule':deepcopy(next(r for r in contract['coupling_constraints'] if r['id']=='area_model_scope')),
            'area_mm2':None,'power_w':None,'latency_ms':None,'cost_model':None}}
    profile_hash=digest(profile)
    proposals=[]
    for n in TILES[:max_candidates]:
        values={**defaults,'num_tile_elements':n}
        require(n<=65535, 'Tile candidate violates the necessary uint16 length bound.')
        compile_constants={'TILE_SIZE':n,'NUM_CORES':cores,'NUM_TILES_PER_CORE':tiles,'NUM_REGS_PER_CORE':regs}
        identity={**bindings,'candidate_domain_sha256':profile_hash,'proposed_model_parameters':values,'required_compile_constants':compile_constants}
        proposal_hash=digest(identity)
        checks=[{'id':'tile_length_representable','status':'necessary_bound_passed','details':f'{n} <= 65535; not proof of complete legality.'},
                {'id':'operand_namespace','status':'necessary_bound_passed','details':f'{cores*tiles} tiles and {cores*regs} scalar slots; IDs must remain 0..254.'},
                {'id':'core_instance_divisibility','status':'necessary_bound_passed','details':f'{cores} cores divisible by {instances} instance(s); not a validated instance tuple.'}]
        blockers=[{'id':'effective_config','status':'unbound','required':'Bind actual config.ini values and hash; launcher overrides are authoritative.'},
            {'id':'dram_topology','status':'unbound','required':'Bind channels/ranks/bankgroups/banks, enumerate the source slice family, check divisibility/coverage and initial slice membership.'},
            {'id':'compiled_binary','status':'unbound','required':'Rebuild and pin the binary with TILE_SIZE matching num_tile_elements; record all compile constants and memory-map agreement.'},
            {'id':'worker_ownership','status':'unbound','required':f'Bind actual workers <= {cores}, with 8 tiles and 8 scalar slots per stock BFS worker and exclusive lifetimes.'},
            {'id':'selected_mapping','status':'unreviewed','required':'Confirm applicability to the selected hardware/software mapping; do not inherit the stock BFS proof into a different read-offload or hybrid kernel.'},
            {'id':'request_and_address_bounds','status':'unbound','required':'Bound request-table per-address multiplicity, index/byte-offset ranges, tile lengths, wide-slot allocation and completion behavior.'}]
        obligations={'proposal_sha256':proposal_hash,'source_commit':SOURCE,'binary_sha256':None,'config_ini_sha256':None,
            'effective_model_parameters':None,'compiled_constants':None,'dram_topology':None,'memory_size_bytes':None,
            'worker_count':None,'input_sha256':None,'root':None,'roi':None,
            'mapping_review':{'status':'not_run','evidence_refs':[]},
            'correctness':{'status':'not_run','oracle':None,'evidence_refs':[]},
            'intended_path':{'status':'not_run','evidence_refs':[]},
            'resource_length_address_checks':{'status':'not_run','evidence_refs':[]},
            'timing_validation':{'status':'not_run','evidence_refs':[]}}
        proposals.append({'id':'dx100-tile-'+str(n)+'-'+proposal_hash[:16],'sha256':proposal_hash,'identity':identity,
            'status':'candidate_pending_validation','evidence_status':'kernel_supported_and_author_reported',
            'independently_validated':False,'ready_to_execute':False,'eligible_for_performance_ranking':False,
            'necessary_checks':checks,'execution_preflight':blockers,
            'derived_storage':{'scratchpad_payload_bytes':4*cores*tiles*n,'scalar_payload_bytes':4*cores*regs,
                'size_mmio_bytes':2*cores*tiles,'ready_mmio_bytes':2*cores*tiles,
                'basis':'source-derived payload accounting only; aliased data mappings counted once; excludes separate tables/control and is not area'},
            'build_validation_request':{'compile_constants':compile_constants,
                'expected_cli_values':{p['cli_option']:values[p['id']] for p in contract['parameters'] if p['cli_option'] is not None},
                'direct_configuration_required':{p['id']:values[p['id']] for p in contract['parameters'] if p['cli_option'] is None},
                'cli_note':'Declarative expected values, not shell arguments. False Boolean flags must not be emitted as enabling flags. No jobs are submitted.',
                'source_contract_ref':'contract.snapshot.yaml','candidate_ref':'candidate.snapshot.yaml',
                'software_changes':params['num_tile_elements']['api_or_kernel_change'],
                'batching_note':'TILE_SIZE changes the pinned BFS batching/fallback behavior; compare as a hardware/software experiment.',
                'required_receipts':obligations},
            'metrics':{'latency_ms':None,'area_mm2':None,'power_w':None}})
    plan={'format':'dx100-provisional-parameter-exploration-v0.1','synthetic':False,
        'candidate_domain_sha256':profile_hash,'bindings':bindings,'status':'candidates_pending_validation',
        'candidate_count':len(proposals),'total_source_candidates':len(TILES),'budget':{'max_candidates':max_candidates},
        'truncated':len(proposals)<len(TILES),'candidates':proposals,'admitted_configurations':[],
        'selected_winner':None,'evaluation_performed':False,'ready_to_execute':False}
    files={'candidate.snapshot.yaml':yaml.safe_dump(candidate,sort_keys=False),
        'contract.snapshot.yaml':contract_path.read_text(),'verification.snapshot.json':verification_path.read_text(),
        'published-results.snapshot.json':published_path.read_text(),
        'candidate-domain.yaml':yaml.safe_dump(profile,sort_keys=False),'exploration.yaml':yaml.safe_dump(plan,sort_keys=False),
        'strict-space.template.yaml':yaml.safe_dump(strict_space,sort_keys=False)}
    for p in proposals:
        root='candidates/'+p['id']+'/'
        files[root+'configuration-proposal.yaml']=yaml.safe_dump(p,sort_keys=False)
        files[root+'build-validation-request.yaml']=yaml.safe_dump(p['build_validation_request'],sort_keys=False)
        files[root+'receipt.template.yaml']=yaml.safe_dump(p['build_validation_request']['required_receipts'],sort_keys=False)
    lines=['# DX100 tile candidates pending validation','',
        '**Source-supported candidate points, not a validated legal domain. No builds, simulations or performance evaluation were run.**','',
        '[Imported domain](candidate-domain.yaml) · [Exploration](exploration.yaml) · [Unmodified source contract](contract.snapshot.yaml)',
        '', '| Tile elements | Candidate package | Status |','|---|---|---|']
    for p in proposals:
        lines.append(f"| {p['identity']['proposed_model_parameters']['num_tile_elements']} | [Build/validation request](candidates/{p['id']}/build-validation-request.yaml) | Pending validation; execution blocked |")
    lines += ['', 'All other model knobs retain proposed reference values, pending actual config.ini binding. The separate strict explorer template remains unresolved.',
              'Bind topology, binary, workers, input/root/ROI and mapping/resource bounds before a run. Correctness and intended-path evidence are required before admission.',
              'The cost proxy is preserved only as a scoped source reference; all area, power and latency estimates remain null.',
              'Artifact references in records are relative to the bundle root. Receipt templates are requests for evidence, not approval or automatic promotion.','']
    files['README.md']='\n'.join(lines)
    files['manifest.json']=json.dumps({'format':'dx100-domain-adapter-manifest-v0.1','bindings':bindings,
        'adapter_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'source_hash_verification':'handoff snapshot hashes matched; target validation not performed',
        'artifact_sha256':{k:sha256(v.encode()).hexdigest() for k,v in files.items()}},indent=2)+'\n'
    return files,plan

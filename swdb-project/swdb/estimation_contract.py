"""Closed, outcome-free provider wire contracts. Created: 2026-10-06 ET."""

def closed(properties):
    return {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties)}

TEXT={'type':'string','minLength':1}
NUMBER={'type':['number','null']}
COUNT={'type':['integer','null'],'minimum':0}
HASH={'type':'string','pattern':'^[0-9a-f]{64}$'}
SHAPES=['stream','single_valued_indirect','ranged_indirect','pointer_chase','data_dependent_merge','constant',None]
OUTPUT_SCHEMA=closed({'parameters':{'type':'array','items':closed({
    'parameter':TEXT,'value':NUMBER,'unit':TEXT,'basis':{'enum':['estimated','unknown']},'reason':TEXT})}})
PARAMETERS_SCHEMA=closed({'format':{'enum':['swdb.estimation-parameters.v1']},
    'target_sha256':HASH,'threads':{'type':'integer','minimum':1},
    'known':{'type':'array','items':closed({'parameter':TEXT,'model':TEXT,'value':{'type':'number'},
        'unit':TEXT,'basis':{'enum':['measured','reported','inferred','estimated','code_reading','simulated']}})},
    'unknown':{'type':'array','items':closed({'parameter':TEXT,'model':TEXT,'unit':TEXT,
        'domain':{'enum':['positive','positive_integer','unsupported']}})}})
ACCESS_SCHEMA=closed({'shape':{'enum':SHAPES},'update':{'enum':['read','write','compare-and-swap',
    'add-update','min-max-update','unknown']},'element_bytes':COUNT,'elements':COUNT,'useful_bytes':COUNT})
LOGICAL_NAMES=('line_requests','row_groups','staged_bytes','unique_lines','windows')
REGION_SCHEMA=closed({'region_sha256':HASH,'operations':{'type':'array','items':closed({
    'category':{'enum':['integer','floating_point','branch','atomic']},'count':COUNT})},
    'footprint_bytes':COUNT,'active_workers':COUNT,'access_groups':{'type':'array','items':ACCESS_SCHEMA},
    'logical_counts':{'type':'array','items':closed({'description_sha256':HASH,
        **{name:COUNT for name in LOGICAL_NAMES}})}})
CHARACTERIZATION_SCHEMA=closed({'format':{'enum':['swdb.estimation-characterization.v1']},
    'record_sha256':HASH,'input_sha256':HASH,'roi_sha256':HASH,'source_ir_sha256':HASH,
    'trials':{'type':'array','items':closed({'position':{'type':'integer','minimum':0},
        'regions':{'type':'array','items':REGION_SCHEMA}})}})
PROFILE_SCHEMA=closed({'format':{'enum':['swdb.estimation-profile.v1']},'record_sha256':HASH,
    'regions':{'type':'array','items':closed({'region_sha256':HASH,
        'kind':{'enum':['loop','function','statement','unknown']}})}})
INPUT_SCHEMAS={'characterization.json':CHARACTERIZATION_SCHEMA,'profile.json':PROFILE_SCHEMA,
    'parameters.json':PARAMETERS_SCHEMA}

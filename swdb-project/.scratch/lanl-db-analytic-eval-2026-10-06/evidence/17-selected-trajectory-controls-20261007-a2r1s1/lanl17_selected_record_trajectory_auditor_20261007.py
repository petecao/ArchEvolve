"""Prospective read-only selected-record/trajectory auditor; no actual inputs admitted.

Use only after parent approval of explicit local pins. Git reads and compact files
only: no Store, SWDB imports, network, process control, scientific commands, auth,
full argv, provider prompts or raw logs. It does not substitute full public validation.
"""
import argparse,ast,copy,hashlib,json,math,os,pathlib,random,re,subprocess,sys
import datetime as dt
from datetime import datetime
from types import SimpleNamespace
import yaml
sys.dont_write_bytecode=True
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
HELPER='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
SUPERVISOR='fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'
GUARD='9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'
PROCESSES='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
CIDS=tuple('extensa-gem5-bfs-20261006-p'+str(i) for i in range(1,5))
NORMAL={'max_iterations','plateau','lane_hours','provider_calls','disk'}
S='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/'; EVIDENCE=S+'evidence/'
BUDGETS={'max_iterations':8,'plateau_iterations':4,'lane_hours':24,'provider_calls_per_iteration':3,'provider_calls_setup':1,'disk_gb':20,'lanes':1}
class Refused(ValueError): pass
class Pending(ValueError): pass
def require(condition,reason):
    if not condition: raise Refused(reason)
def need(obj,key):
    if key not in obj: raise Pending('Explicit input missing: '+key)
    return obj[key]
def sha(data): return hashlib.sha256(data).hexdigest()
def strict_json(data):
    def unique_pairs(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'Duplicate JSON mapping key');result[key]=value
        return result
    return json.loads(data,object_pairs_hook=unique_pairs)
def digest(value,*,ensure_ascii=True):
    return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=ensure_ascii,allow_nan=False).encode())
def receipt_seal(value,expected,*,ensure_ascii=True):
    require(value.get('identity_sha256')==expected==digest({k:v for k,v in value.items() if k!='identity_sha256'},ensure_ascii=ensure_ascii),'Compact receipt seal differs')
def utc(text):
    value=datetime.fromisoformat(text)
    require(value.tzinfo is not None and value.utcoffset().total_seconds()==0,'UTC timestamp required')
    return value
artifacts=SimpleNamespace(digest=digest)
def _fail(condition,message): require(condition,message)
# Exact pure public projections appended below; no public module is imported.

FORMAT = 'swdb.extensa-paired-estimate.v1'

LEDGER = 'swdb.extensa-pairing-ledger.v1'

VERSION = 'swdb.extensa-pairing.v1'

PAYLOAD = ('format', 'mode', 'campaign', 'basis', 'estimator_variant', 'estimator_version',
           'estimator_sha256', 'policy_sha256', 'timing_context', 'context_sha256',
           'estimated_at', 'seconds', 'state', 'structural_missing', 'evidence_kind',
           'eligible_for_agreement')


def paired_identity(data):
    return artifacts.digest({key: data[key] for key in PAYLOAD})


def request_identity(context):
    """Match record aliases of the same outcome-free observation request.

    Keep the actual context in the receipt/event. Only subject record names and
    a guest build's output name/path may differ; guest executable bytes and every
    compiler/backend/input/configuration fact must remain equal. This reuses an
    unknown forecast, never functional/MMIO counts or an application estimate.
    """
    facts = copy.deepcopy(context)
    facts.pop('prior_outcome_exposure', None)
    facts['subject'].pop('id', None)
    execution = facts['execution']
    binary, build = execution.get('binary', {}), execution.get('timing_policy', {}).get('build', {})
    if (binary.get('sha256') and binary.get('sha256') == build.get('binary_sha256') and
            all(key in build for key in ('compiler', 'compiler_version', 'flags', 'adapter'))):
        execution.pop('candidate_build', None)
        binary.pop('path', None)
    return artifacts.digest(facts)


def _time(value):
    value = datetime.fromisoformat(value)
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ValueError('pairing timestamps must declare UTC')
    return value


def ledger_problems(ledger, campaign):
    """Validate a self-contained copied ledger, without reopening raw timing files."""
    rows = ledger['records']
    by_id = {row['id']: row for row in rows}
    if len(by_id) != len(rows):
        yield 'records contain duplicate paired estimate IDs'
    if not ledger['enabled'] and (rows or ledger['outcome_accesses']):
        yield 'disabled legacy pairing cannot carry paired evidence'
    for row in rows:
        if row['campaign'] != campaign or row['mode'] != 'extensa':
            yield 'record belongs to a different campaign/mode'
        if paired_identity(row) != row['identity_sha256'] or not row['id'].endswith('.' + paired_identity(row)[:16]):
            yield 'embedded paired estimate immutable payload/hash differs'
        if artifacts.digest(row['timing_context']) != row['context_sha256']:
            yield 'embedded paired estimate context/hash differs'
        try:
            _time(row['estimated_at'])
        except (ValueError, TypeError):
            yield 'embedded estimate timestamp is not UTC'
    for event in ledger['outcome_accesses']:
        contexts = event.get('timing_contexts')
        if contexts is not None and (len(contexts) != len(event['paired_estimates']) or any(
                rid not in by_id or request_identity(context) != request_identity(by_id[rid]['timing_context'])
                for context, rid in zip(contexts, event['paired_estimates']))):
            yield 'outcome request differs from the preceding immutable artifact/input/build/policy estimate'
        try:
            started = _time(event['outcome_access_started_at'])
            if not event['paired_estimates'] or any(rid not in by_id or
                    _time(by_id[rid]['estimated_at']) >= started for rid in event['paired_estimates']):
                yield 'outcome access lacks a preceding immutable paired estimate'
        except (ValueError, TypeError):
            yield 'outcome access timestamp is not UTC'

extensa_pairing=SimpleNamespace(_time=_time,request_identity=request_identity,identity=paired_identity,ledger_problems=ledger_problems)

D30 = {'minimum_unique_eligible_dx100_pairs': 20, 'minimum_tau': 0.6,
       'minimum_95_interval_lower_bound': 0.3,
       'gem5_best_in_estimate_top3_every_campaign': True}

STATISTICS = {'rank_measure': 'kendall_tau_b', 'ratio': 'baseline_seconds/candidate_seconds',
    'interval': 'connected_dependency_cluster_percentile_bootstrap', 'bootstrap_samples': 10000,
    'bootstrap_seed': 20261006, 'confidence_level': 0.95, 'quantiles': [0.025, 0.975],
    'quantile_interpolation': 'linear', 'minimum_supported_independent_components': 4,
    'minimum_defined_bootstrap_replicates': 9500,
    'dependency_links': ['shared_generator_seed', 'candidate_artifact', 'provider_trajectory_or_parent_lineage',
                         'reused_baseline_outcome', 'campaign_trajectory'],
    'unresolved_dependency': 'unsupported_interval',
    'top3_scope': 'every_campaign_and_workload_class',
    'top3_order': 'estimated_speedup_descending_then_artifact_sha256',
    'top3_requires_complete_ranking': True,
    'interval_assumption': 'exchangeable_supported_dependency_components_only'}

POLICY_KEYS = ('format', 'mode', 'campaign', 'basis', 'estimator_variant', 'frozen_at',
    'estimator_sha256', 'provider_config_sha256', 'population', 'statistics', 'D30', 'structural_missing')

REPORT_KEYS = ('format', 'mode', 'campaign', 'basis', 'estimator_variant', 'policy', 'policy_sha256',
    'policy_snapshot', 'reported_at', 'summaries', 'summary_identities', 'counts', 'pairs',
    'blind_order', 'rank', 'top3', 'gate', 'recommendation', 'selection_policy', 'evidence_kind')


def kendall_tau_b(pairs):
    """Tie-aware rank statistic for finite mathematical pairs; no evidence admission.

    Definition: SciPy primary documentation, scipy.stats.kendalltau (tau-b).
    Undefined/constant rankings return None, rather than an agreement value.
    """
    pairs = list(pairs)
    if any(len(row) != 2 or any(type(value) not in (int, float) or not math.isfinite(value)
                               for value in row) for row in pairs):
        raise ValueError('rank pairs must contain two finite mathematical numbers')
    concordant = discordant = tied_x = tied_y = 0
    for i, (x1, y1) in enumerate(pairs):
        for x2, y2 in pairs[i + 1:]:
            dx, dy = (x1 > x2) - (x1 < x2), (y1 > y2) - (y1 < y2)
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tied_x += 1
            elif dy == 0:
                tied_y += 1
            elif dx == dy:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt((concordant + discordant + tied_x) *
                            (concordant + discordant + tied_y))
    return (concordant - discordant) / denominator if denominator else None


def rank_statistics(samples):
    """Conditional mathematical ranking; samples never acquire application eligibility.

    Dependency keys are explicit facts. A shared key unions its samples, including
    transitive candidate/seed/trajectory links. Unknown closure cannot support CI.
    """
    samples = list(samples)
    if len(samples) > 256:
        raise ValueError('bounded mathematical rank interface supports at most 256 samples')
    pairs = [(row['estimated_speedup'], row['timing_speedup']) for row in samples]
    result = {'state': 'unsupported', 'tau_b': kendall_tau_b(pairs), 'interval_95': None,
              'dependency_component_count': 0, 'defined_bootstrap_replicates': 0,
              'reason': 'zero_eligible_numeric_application_pairs'}
    if not samples:
        return result
    if any(not row.get('dependencies_complete') or not row.get('dependency_keys') or
           any(not isinstance(key, str) or not key for key in row['dependency_keys']) for row in samples):
        result.update(dependency_component_count=None, reason='unresolved_dependency_closure')
        return result
    parent, owner = list(range(len(samples))), {}
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, row in enumerate(samples):
        for key in row['dependency_keys']:
            if key in owner:
                parent[root(i)] = root(owner[key])
            else:
                owner[key] = i
    groups = {}
    for i, pair in enumerate(pairs):
        groups.setdefault(root(i), []).append(pair)
    result['dependency_component_count'] = len(groups)
    if len(groups) < STATISTICS['minimum_supported_independent_components']:
        result['reason'] = 'too_few_supported_dependency_components'
    elif result['tau_b'] is None:
        result['reason'] = 'degenerate_ranking'
    else:
        rng = random.Random(STATISTICS['bootstrap_seed'])
        blocks, draws = list(groups.values()), []
        for _ in range(STATISTICS['bootstrap_samples']):
            draw = [pair for block in rng.choices(blocks, k=len(blocks)) for pair in block]
            tau = kendall_tau_b(draw)
            if tau is not None:
                draws.append(tau)
        result['defined_bootstrap_replicates'] = len(draws)
        if len(draws) < STATISTICS['minimum_defined_bootstrap_replicates']:
            result['reason'] = 'too_few_defined_bootstrap_replicates'
            return result
        draws.sort()
        limits = []
        for quantile in STATISTICS['quantiles']:
            position = (len(draws) - 1) * quantile
            lo, hi = math.floor(position), math.ceil(position)
            limits.append(draws[lo] + (draws[hi] - draws[lo]) * (position - lo))
        if limits[0] == limits[1]:
            result['reason'] = 'degenerate_bootstrap_distribution'
        else:
            result.update(state='supported', interval_95=limits, reason=None)
    return result


def agreement_identity(data):
    keys = POLICY_KEYS if data['kind'] == 'agreement_policy' else REPORT_KEYS
    return artifacts.digest({key: data[key] for key in keys})


def _forecasts(ledger, artifact, workload):
    return [row for row in ledger.get('records', [])
        if row['timing_context']['subject']['artifact_sha256'] == artifact
        and row['timing_context']['input']['id'] == workload
        and not row['timing_context']['execution'].get('protocol_companion')
        and row['timing_context']['execution'].get('protocol_role', 'candidate') == 'candidate']


def _analyse(policy, summaries):
    planned = {row['campaign']: row for row in policy['population']}
    pairs, strata, seen, blind_problems = [], [], set(), []
    for summary in summaries:
        _summary_checked(summary)
        cid = summary['campaign']
        _fail(cid in planned, 'summary campaign is outside the frozen population')
        plan = planned[cid]
        _fail(summary['campaign_file']['sha256'] == plan['campaign_file_sha256'],
              'summary campaign configuration differs from prospective freeze')
        _fail(summary['target'] == 'dx100_gem5', 'agreement summary target is not DX100')
        _fail({row['role']: row['candidate'] for row in summary['baselines']} ==
              {row['role']: row['candidate'] for row in plan['baselines']},
              'summary baseline population differs from prospective freeze')
        for row in plan['baselines']:
            _fail(all(receipt['timing_context']['subject']['artifact_sha256'] == row['artifact_sha256']
                      for receipt in (summary.get('paired_estimates') or {}).get('records', [])
                      if receipt['timing_context']['subject']['id'] == row['candidate']),
                  'baseline forecast source artifact differs from prospective freeze')
        classes = {row['class']: row['id'] for row in plan['workloads']}
        _fail({row['class']: row['workload'] for row in summary['workload_classes']} == classes,
              'summary workload population differs from prospective freeze')
        ledger = summary.get('paired_estimates') or {}
        if not ledger.get('records') or not ledger.get('outcome_accesses'):
            blind_problems.append({'campaign': cid, 'reason': 'missing_preceding_estimate_receipts'})
        for row in ledger.get('records', []):
            _fail(row['estimator_sha256'] == policy['estimator_sha256'], 'forecast model differs from frozen policy')
            _fail(extensa_pairing._time(policy['frozen_at']) < extensa_pairing._time(row['estimated_at']),
                  'agreement policy did not precede campaign forecast/outcome access')
        for event in ledger.get('outcome_accesses', []):
            _fail(event.get('timing_contexts'), 'fresh outcome access lacks exact timing request contexts')
        accessed_requests = {extensa_pairing.request_identity(context)
            for event in ledger.get('outcome_accesses', []) for context in event['timing_contexts']}
        for iteration in summary['iterations']:
            for candidate in iteration['candidates']:
                for comparison in candidate.get('comparisons', []):
                    if comparison['baseline_role'] != plan['configuration']['base_source']:
                        continue
                    forecasts = _forecasts(ledger, candidate['artifact_sha256'], classes[candidate['class']])
                    exclusions = []
                    if summary['evidence_kind'] == 'contract_fixture' or any(
                            row['evidence_kind'] == 'contract_fixture' for row in forecasts):
                        exclusions.append('contract_fixture')
                    if not forecasts:
                        exclusions.append('missing_preceding_estimate_receipts')
                    if not forecasts or any(extensa_pairing.request_identity(row['timing_context'])
                                             not in accessed_requests for row in forecasts):
                        exclusions.append('missing_matching_outcome_request')
                        blind_problems.append({'campaign': cid, 'candidate': candidate['id'],
                                               'reason': 'missing_matching_outcome_request'})
                    if any(row['seconds'] is None for row in forecasts):
                        exclusions.append('unknown_forecast')
                    # Ticket16 currently admits no application numeric forecast.
                    exclusions.extend(['no_verified_complete_call_numeric_adapter', 'unverified_unique_pair_content'])
                    key = artifacts.digest({'campaign_configuration': plan['configuration'],
                        'input': next(row for row in plan['workloads'] if row['class'] == candidate['class']),
                        'candidate_artifact_sha256': candidate['artifact_sha256'],
                        'baseline_role': comparison['baseline_role'],
                        'forecast_contexts': [extensa_pairing.request_identity(r['timing_context']) for r in forecasts]})
                    if key in seen:
                        exclusions.append('repeated_pair_content')
                    seen.add(key)
                    pairs.append({'campaign': cid, 'class': candidate['class'], 'candidate': candidate['id'],
                        'candidate_artifact_sha256': candidate['artifact_sha256'], 'comparison': comparison['comparison'],
                        'baseline_evaluation': comparison['baseline_evaluation'], 'pair_identity_sha256': None,
                        'request_digest_sha256': key,
                        'forecast_ids': [row['id'] for row in forecasts], 'timing_speedup': comparison['ratio'],
                        'timing_basis': summary['evidence_basis'], 'timing_evidence_kind': summary['evidence_kind'],
                        'structural_missing': sorted({reason for row in forecasts for reason in row['structural_missing']}),
                        'estimated_speedup': None, 'relative_error': None, 'eligible': False,
                        'exclusions': exclusions})
        for row in summary['per_class']:
            strata.append({'campaign': cid, 'class': row['class'], 'best': row['best'],
                           'state': 'unsupported', 'estimate_top3': None,
                           'reason': 'complete_finite_application_prediction_ranking_unavailable'})
    absent = sorted(set(planned) - {summary['campaign'] for summary in summaries})
    return {'evidence_kind': ('unavailable' if not summaries else 'mixed_sources' if
                             len({s['evidence_kind'] for s in summaries}) > 1 else summaries[0]['evidence_kind']),
        'counts': {'observed_candidate_rows': len(pairs), 'unique_observed_pair_contents': None, 'unique_retained_request_digests': len(seen),
            'unique_eligible_dx100_pairs': 0, 'excluded_candidate_rows': len(pairs),
            'planned_campaigns': len(planned), 'observed_campaigns': len(summaries)},
        'pairs': pairs,
        'blind_order': {'state': 'unverified' if blind_problems or absent else 'verified',
                        'problems': blind_problems, 'missing_campaigns': absent,
                        'scope': 'receipt_order_only; unknown forecasts never establish numeric agreement'},
        'rank': rank_statistics([]),
        'top3': {'state': 'unsupported', 'strata': strata},
        'gate': {'state': 'unsupported', 'D30': copy.deepcopy(D30),
                 'reason': 'minimum20_eligible_pairs_and_supported_rank_interval_top3_not_demonstrated'},
        'recommendation': 'do_not_switch_to_flow_b', 'selection_policy': 'unchanged_timing_only'}

PINNED_SOURCE_FILES={'swdb/extensa_pairing.py': '30a62539769c21f5d0ecbc3fb2800bd60c935332f13a6c6c1eba638558a1896a', 'swdb/extensa_agreement.py': 'd078cf8a26fbbd65f0d27d0a64dbde56e4f190e1ec4c07b9e4eb311ad3a5174f'}

class RecordLoader(getattr(yaml,'CSafeLoader',yaml.SafeLoader)): pass
RecordLoader.yaml_implicit_resolvers={first:[(tag,regexp) for tag,regexp in rows if tag!='tag:yaml.org,2002:timestamp'] for first,rows in RecordLoader.yaml_implicit_resolvers.items()}
def no_duplicates(loader,node,deep=False):
    seen=set()
    for key_node,_ in node.value:
        key=loader.construct_object(key_node,deep=deep)
        if key in seen: raise Refused('Duplicate YAML mapping key')
        seen.add(key)
    return loader.construct_mapping(node,deep=deep)
RecordLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,no_duplicates)

def _summary_checked(summary):
    # Deliberately selected facts, not a substitute for the required original full
    # public validation. _analyse's pure admission computation remains exact.
    require(summary['kind']=='campaign_summary' and summary['mode']=='extensa','Actual Extensa summary required')
    require(summary['evidence_kind']=='execution' and summary['evidence_basis']=='simulated','Fixture/replay cannot supply an actual DX trajectory')
    require(summary['target']=='dx100_gem5' and summary['swdb_commit']==CURRENT_R,'Summary source differs from required final R')
    ledger=summary['paired_estimates']
    require(ledger['format']==LEDGER and ledger['enabled'] is True,'Enabled actual pairing ledger required')
    require(ledger['eligible_application_estimates']==0 and ledger['selection_policy']=='unchanged_timing_only','Pairing selection/admission differs')
    require(not list(ledger_problems(ledger,summary['campaign'])),'Embedded pairing ledger differs or is unordered')
    require(bool(ledger['records']) and bool(ledger['outcome_accesses']),'Actual ordered outcome metadata missing')
    for row in ledger['records']:
        require(row['kind']=='paired_estimate' and row['format']==FORMAT and row['estimator_version']==VERSION,'Paired format/version differs')
        require(row['state']=='unknown' and row['seconds'] is None and row['eligible_for_agreement'] is False,'No numeric application adapter is admitted')
        require(row['evidence_kind']=='execution' and row['structural_missing'],'Actual structural unknown required')
        require(row['estimator_sha256']==F6 and row['basis']=='estimated' and row['estimator_variant']=='research','Frozen forecast source/basis differs')
    for event in ledger['outcome_accesses']:
        require(event.get('timing_contexts') and len(event['timing_contexts'])==len(event['paired_estimates']),'Exact outcome contexts required')

class Reader:
    def __init__(self,repository,pins):
        self.repository=pathlib.Path(repository).resolve(strict=True);self.pins=pins;self.records={};self.record_pins={}
        self.R=need(pins,'final_R');self.EF=need(pins,'freeze_export');self.ER=need(pins,'report_export')
        for row in (self.R,self.EF,self.ER):
            require(re.fullmatch('[0-9a-f]{40}',need(row,'commit')) is not None,'Explicit full Git commit required')
            require(re.fullmatch('[0-9a-f]{40}',need(row,'tree')) is not None,'Explicit full Git tree required')
        self.refs={C,self.R['commit'],self.EF['commit'],self.ER['commit']}
    def git(self,*args):
        return subprocess.check_output(['git','-c','protocol.allow=never','-C',str(self.repository),*args],timeout=60,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'})
    def text(self,*args): return self.git(*args).decode().strip()
    def blob(self,ref,path):
        require(ref in self.refs and path.startswith('swdb-project/') and '..' not in pathlib.PurePosixPath(path).parts,'Unpinned Git reference/path')
        return self.git('show',ref+':'+path)
    def tree(self,ref):
        require(ref in self.refs,'Unpinned Git tree')
        result={}
        for row in self.git('ls-tree','-r','-z',ref).split(b'\0'):
            if row:
                meta,path=row.split(b'\t');result[path.decode()]=meta.decode()
        return result
    def raw(self,pin):
        size=need(pin,'bytes');expected=need(pin,'sha256')
        require(type(size) is int and 0<=size<=32*1024*1024,'Bounded selected compact file required')
        require(re.fullmatch('[0-9a-f]{64}',expected) is not None,'Explicit file SHA required')
        if 'commit' in pin: raw=self.blob(pin['commit'],need(pin,'path'))
        else:
            p=pathlib.Path(need(pin,'path'));require(p.is_absolute() and p.is_file() and not p.is_symlink(),'Pinned local regular compact file required')
            require(p.stat().st_size==size,'Pinned compact file size differs');raw=p.read_bytes()
        require(len(raw)==size and sha(raw)==expected,'Selected compact/Git file bytes differ')
        return raw
    def json(self,pin):
        value=strict_json(self.raw(pin))
        if 'identity_sha256' in pin: receipt_seal(value,pin['identity_sha256'],ensure_ascii=need(pin,'canonical_ensure_ascii'))
        return value
    def yaml(self,pin): return yaml.load(self.raw(pin),Loader=RecordLoader)
    def inventory(self,ref,folder):
        return {p[len(folder):]:sha(self.blob(ref,p)) for p in self.tree(ref) if p.startswith(folder)}
    def custody(self):
        require(self.pins['source_C']==C and self.pins['estimator_sha256']==F6,'Required frozen C/F6 differs')
        require(sha(pathlib.Path(__file__).read_bytes())==need(self.pins,'auditor_sha256'),'Reviewed auditor bytes differ')
        self.git('merge-base','--is-ancestor',C,self.R['commit'])
        base=self.tree(self.R['commit']);code={p:meta for p,meta in base.items() if p.startswith('swdb-project/swdb/') and p.endswith('.py')}
        ccode={p:meta for p,meta in self.tree(C).items() if p.startswith('swdb-project/swdb/') and p.endswith('.py')}
        require(code==ccode and len(code)==185,'R source modules differ from C')
        require(digest({p[len('swdb-project/swdb/'):]:sha(self.blob(self.R['commit'],p)) for p in sorted(code)})==F6,'Portable source bundle differs')
        for rel,expected in PINNED_SOURCE_FILES.items():require(sha(self.blob(self.R['commit'],'swdb-project/'+rel))==expected,'Copied pure public source differs')
        out={}
        for label,export in (('freeze',self.EF),('report',self.ER)):
            ref=export['commit'];require(self.text('rev-parse',ref+'^{tree}')==export['tree'],'Export tree pin differs')
            require(self.text('show','-s','--format=%P',ref)==self.R['commit'],'Pure export must have sole parent R')
            incoming=self.tree(ref);require(all(incoming.get(p)==meta for p,meta in base.items()),'Export changes a prior blob/mode')
            adds=sorted(set(incoming)-set(base));require(adds==sorted(need(export,'allowed_additions')),'Exact export additions differ')
            receipt=need(export,'receipt');allowed=set(need(export,'record_paths'))|{receipt['path']}
            if label=='freeze':allowed|=set(need(export,'configuration_paths'))
            require(set(adds)==allowed and all(p.startswith('swdb-project/records/') and p.endswith('.yaml') for p in export['record_paths']),'Unexpected pure export paths')
            require(receipt['commit']==ref and receipt['path'].startswith(EVIDENCE),'Pinned compact export receipt differs')
            out[label]={'prior_blobs_unchanged':len(base),'additions':len(adds),'commit':ref,'tree':export['tree']}
        require(self.text('rev-parse',self.R['commit']+'^{tree}')==self.R['tree'],'R tree pin differs')
        return out
    def selected_records(self):
        for pin in need(self.pins,'selected_records'):
            data=self.yaml(pin);rid=need(data,'id');require(rid==pin['id'] and data['kind']==pin['kind'] and digest(data)==pin['record_sha256'],'Selected record metadata pin differs')
            if rid in self.records:require(self.records[rid]==data,'Record ID aliases different content')
            self.records[rid]=data;self.record_pins[rid]=pin
    def record(self,rid,kind=None):
        if rid not in self.records:raise Pending('Selected closure record missing: '+rid)
        value=self.records[rid];require(kind is None or value['kind']==kind,'Selected referenced kind differs');return value
    def closure(self,roots,index):
        # Exact boundary walk semantics: only IDs in the complete validated index
        # become references. Index alone is not a body; every reached record is pinned.
        found=set();pending=list(roots)
        def references(value):
            if isinstance(value,str): return {value} if value in index else set()
            if isinstance(value,dict): return set().union(*(references(v) for v in value.values())) if value else set()
            if isinstance(value,list): return set().union(*(references(v) for v in value)) if value else set()
            return set()
        while pending:
            rid=pending.pop()
            if rid in found:continue
            require(rid in index,'Closure root missing from complete validated index')
            data=self.record(rid);pin=self.record_pins[rid];row=index[rid]
            require(row['kind']==data['kind'] and row['sha256']==pin['sha256'] and row['record_sha256']==digest(data),'Selected closure/index mismatch')
            found.add(rid);pending.extend(references({k:v for k,v in data.items() if k not in {'id','kind'}})-found)
        return found
    def supervisor(self,pin,action):
        row=self.json(pin);require(row['format']=='swdb.lanl17-metadata-supervisor.v1' and row['action']==action,'Actual metadata action receipt differs')
        require(row['state']=='child_returned' and row['child_exit']==row['supervisor_exit']==0 and row['fixture'] is False,'Actual metadata action did not succeed')
        require(row['timed_out'] is False and row['signal_received'] is None and not row['cleanup_errors'] and row['error_type'] is None,'Metadata action interrupted or failed')
        require(row['cleanup']['subreaper'] is True and row['cleanup']['survivors']=={},'Metadata owned cleanup incomplete')
        require(row['helper_sha256']==row['cleanup_implementation_sha256']==HELPER and row['supervisor_sha256']==SUPERVISOR and row['processes_py_sha256']==PROCESSES and row['estimator_sha256']==F6,'Metadata control/source pins differ')
        require(row['provider_calls']==row['application_outcomes']==0,'Metadata action scope differs')
        require(utc(row['started_utc'])<utc(row['ended_utc']),'Metadata time order differs');return row
    def freeze(self):
        m2=self.json(need(self.pins,'manifest_M2'));fr=self.json(self.EF['receipt']);ar=self.json(self.ER['receipt'])
        require(fr['format']=='swdb.lanl17-freeze-receipt.v1' and fr['population_frozen'] is True and fr['application_outcomes_opened']==0,'Prospective freeze custody differs')
        require(ar['format']=='swdb.lanl17-actual-agreement-compact.v1' and ar['source_clean'] is True and ar['raw_transferred'] is False,'Actual final compact receipt differs')
        m1=fr['manifest'];receipt_seal(m1,m1['identity_sha256'])
        require({k:v for k,v in m2.items() if k not in {'identity_sha256','freeze_export'}}=={k:v for k,v in m1.items() if k!='identity_sha256'},'M2 is not the exact M1 plus freeze export')
        require(ar['manifest']==m2 and m2['source_commit']==self.R['commit'] and m2['source_clean'] is True and m2['helper_sha256']==HELPER and m2['estimator_sha256']==F6,'Manifest/source binding differs')
        require(m2['initial_record_files']==self.inventory(self.R['commit'],'swdb-project/records/') and m2['initial_library_files']==self.inventory(self.R['commit'],'swdb-project/library/'),'Frozen original catalog inventory differs from R')
        freeze=m2['freeze_export'];require(freeze['commit']==self.EF['commit'] and sorted(freeze['paths'])==sorted(self.EF['allowed_additions']) and freeze['raw_transferred'] is False,'M2 freeze export differs')
        policy=self.record(need(self.pins,'policy_id'),'agreement_policy');report=self.record(need(self.pins,'report_id'),'agreement_report')
        require(fr['public_policy']==policy and ar['public_report']==report and report['policy_snapshot']==policy,'Public policy/report compact snapshots differ')
        for value in (policy,report):require(value['identity_sha256']==agreement_identity(value) and value['id'].endswith('.'+value['identity_sha256'][:16]),'Public projected identity differs')
        require(m2['policy']=={k:policy[k] for k in ('id','identity_sha256','frozen_at')},'Manifest policy differs')
        cleanup=m2['linux_cleanup_proof'];proof=cleanup['receipt'];receipt_seal(proof,proof['identity_sha256'])
        require(proof['identity_sha256']=='18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1' and proof['format']=='swdb.lanl17-linux-cleanup-smoke.v1' and proof['passed'] is True and proof['helper_sha256']==HELPER and proof['processes_py_sha256']==PROCESSES,'Original full-helper actual cleanup proof differs')
        require(proof['cleanup']['survivors']=={} and proof['unrelated_sibling_survived'] is True and proof['provider_calls']==proof['application_outcomes']==0,'Original tested owned cleanup/scope differs')
        require(policy['D30']==D30 and policy['statistics']==STATISTICS and policy['estimator_sha256']==F6,'Frozen D30/statistics/source changed')
        require(policy['structural_missing']==['no_verified_canonical_graph_complete_call_mmio_numeric_adapter'],'The frozen structural bridge gap changed')
        policy_pin=self.record_pins[policy['id']];report_pin=self.record_pins[report['id']]
        require(policy_pin.get('commit') in (self.EF['commit'],self.ER['commit']) and report_pin.get('commit')==self.ER['commit'],'Policy/report must be original Git export records')
        require(policy_pin['path'] in self.EF['record_paths'] and report_pin['path'] in self.ER['record_paths'],'Selected public records are not in declared exports')
        require(self.blob(self.EF['commit'],policy_pin['path'])==self.blob(self.ER['commit'],policy_pin['path']),'Freeze/report policy overlap bytes differ')
        require(m2['frozen_base_record_files']==self.inventory(self.EF['commit'],'swdb-project/records/'),'Frozen base inventory differs from the pure freeze export')
        require(set(row['campaign'] for row in policy['population'])==set(CIDS) and len(policy['population'])==4,'Four exact frozen campaigns required')
        require(policy['mode']=='extensa' and policy['basis']=='code_reading' and policy['estimator_variant']=='research','Policy boundary differs')
        provider_path=need(self.EF,'provider_configuration_path');require(sha(self.blob(self.EF['commit'],provider_path))==policy['provider_config_sha256'],'Frozen provider config differs')
        configs=need(self.EF,'campaign_configuration_paths');require(set(configs)==set(CIDS),'Frozen config path inventory differs')
        require(set(configs.values())|{provider_path}==set(self.EF['configuration_paths']),'Frozen configuration export has unexpected files')
        require(all(path.startswith(EVIDENCE+'17-frozen-configs-'+m2['tag']+'/') for path in self.EF['configuration_paths']),'Frozen config folder differs from original helper export')
        require({pathlib.PurePosixPath(path).name:sha(self.blob(self.EF['commit'],path)) for path in self.EF['configuration_paths']}==m2['configuration_files'],'M2 frozen configuration byte inventory differs')
        for plan in policy['population']:
            cid=plan['campaign'];data=yaml.load(self.blob(self.EF['commit'],configs[cid]),Loader=RecordLoader)
            require(data==plan['configuration'] and sha(self.blob(self.EF['commit'],configs[cid]))==plan['campaign_file_sha256'],'Frozen config bytes/snapshot differ')
            require(data['budgets']==BUDGETS and data['paired_estimates']=={'enabled':True} and data['protocol']['sources']==[0] and data['target']=='dx100_gem5','Scientific campaign budgets/input scope differ')
            for baseline in plan['baselines']:
                source=self.record(baseline['candidate'],'candidate');require(digest(source)==baseline['record_sha256'] and source['artifact']['sha256']==baseline['artifact_sha256'],'Frozen baseline artifact/metadata differs')
            for workload in plan['workloads']:
                source=self.record(workload['id'],'workload');definition=source['definition']
                require(digest(source)==workload['record_sha256'] and source['identity_sha256']==workload['identity_sha256'] and definition['canonical_sha256']==workload['canonical_sha256'] and definition['sources']==workload['sources'] and {'family':definition['family'],'generator':definition.get('generator')}==workload['generation'],'Exact input representation/generator source pin differs')
        prepare=self.supervisor(need(self.pins,'prepare_supervisor'),'prepare');finalize=self.supervisor(need(self.pins,'finalize_supervisor'),'finalize')
        for action in ('prepare','finalize'):
            prereg=self.json(need(self.pins,action+'_preregistration'))
            require(prereg['format']=='swdb.lanl17-metadata-dispatch-preregistration.v1' and prereg['action']==action and prereg['final_source_commit']==self.R['commit'] and prereg['source_code_equivalent_F6'] is True and prereg['estimator_sha256']==F6,'Original metadata guard admission/source binding differs')
            require(prereg['guard_sha256']==GUARD and prereg['helper_sha256']==HELPER and prereg['supervisor_sha256']==SUPERVISOR and prereg['processes_sha256']==PROCESSES,'Metadata guard selected controls differ')
            require(prereg['actual_cleanup_proof']['identity_sha256']==proof['identity_sha256'] and prereg['actual_supervisor_proof']['identity_sha256']=='ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b','Original selected actual Linux proof pins differ')
            require(prereg['account_HOME_unchanged'] is True and prereg['CODEX_HOME_original_verified'] is True and prereg['authentication_contents_read'] is False,'Metadata guard provider HOME/privacy scope differs')
        require(utc(policy['frozen_at'])<=utc(fr['checked_utc'])<utc(prepare['ended_utc'])<utc(report['reported_at'])<=utc(ar['checked_utc'])<=utc(finalize['ended_utc']),'Prepare/freeze/report chronology differs')
        publication=self.json(need(self.pins,'freeze_publication_custody'))
        require(publication['format']=='swdb.lanl17-freeze-publication-custody.v1' and publication['source_commit']==self.R['commit'] and publication['freeze_export_commit']==self.EF['commit'] and publication['manifest_sha256']==m2['identity_sha256'] and publication['policy_sha256']==policy['identity_sha256'],'Parent-accepted export-publication projection differs')
        require(publication['prepare_supervisor_identity']==prepare['identity_sha256'] and publication['application_outcomes_opened']==0 and publication['completed_export_exit_code']==0,'Actual freeze publication success missing')
        require(publication['input_model_baseline_pins_sha256']==digest(m2['input_model_baseline_pins']) and publication['frozen_live_files_verified'] is True,'Parent-accepted original live metadata pin check missing')
        require(utc(prepare['ended_utc'])<=utc(publication['checked_utc']),'Publication observation precedes prepare completion')
        self.m2,self.policy,self.report,self.actual,self.published=m2,policy,report,ar,utc(publication['checked_utc'])
        return {'M1_identity':m1['identity_sha256'],'M2_identity':m2['identity_sha256'],'policy':policy['id'],'freeze_export_commit':self.EF['commit'],'publication_checked_utc':publication['checked_utc']}
    def trajectory(self,row):
        cid=need(row,'campaign');projection=self.json(need(row,'projection'))
        require(projection['format']=='swdb.lanl17-trajectory-audit-projection.v1' and projection['campaign']==cid and projection['source_commit']==self.R['commit'] and projection['estimator_sha256']==F6 and projection['manifest_sha256']==self.m2['identity_sha256'],'Actual trajectory projection binding differs')
        summary=self.record(cid+'.summary','campaign_summary');_summary_checked(summary)
        require(projection['summary_sha256']==digest(summary),'Original supplied summary identity differs')
        require(summary in self.report['summaries'],'Actual summary absent from final public snapshot')
        index=projection['record_index'];require(projection['record_index_sha256']==digest(index),'Full compact record index differs')
        validation=projection['public_validation'];require(validation['returncode']==0 and validation['records_index_sha256']==digest(index) and validation['summary_sha256']==digest(summary),'Original full-catalog public validation binding missing')
        for key in ('stdout_sha256','stderr_sha256','source_state_file_sha256'):
            value=projection[key] if key=='source_state_file_sha256' else validation[key]
            require(re.fullmatch('[0-9a-f]{64}',value) is not None,'Exact original raw compact source pin missing')
        state=projection['state'];require(state['campaign']==cid and state['campaign_sha256']==summary['campaign_file']['sha256'],'Original state/config identity differs')
        require(state['iterations']==summary['iterations'],'Original completed state rows differ from summary')
        ledger=state['ledger'];completed=[r for r in ledger['iterations'] if r['outcome'] in ('improved','not_improved')]
        require(ledger['iterations_completed']==len(completed)==len(summary['iterations'])==summary['budgets']['used']['iterations'],'Completed iteration accounting differs')
        require([r['index'] for r in completed]==[r['index'] for r in summary['iterations']]==list(range(1,len(completed)+1)),'Completed iteration indices differ or contain padding')
        require(summary['budgets']['limits']=={k:BUDGETS[k] for k in summary['budgets']['limits']} and set(summary['budgets']['limits'])==set(BUDGETS),'Summary scientific limits differ')
        interrupted=state.get('interrupted_iteration');require(interrupted==summary.get('interrupted_iteration'),'Interrupted iteration evidence differs')
        for iteration in summary['iterations']:
            require(utc(iteration['started'])<utc(iteration['ended']),'Completed iteration has no actual end')
            require(iteration['improved_classes'] or next(r for r in completed if r['index']==iteration['index'])['outcome']=='not_improved','Ledger/selection improvement differs')
        attempts=need(row,'attempts');require(attempts,'Actual attempt records missing');stopped=[]
        for number,attempt in enumerate(attempts,1):
            dispatch=self.json(need(attempt,'dispatch'));stop=self.json(need(attempt,'stopped'));release=self.json(need(attempt,'release_custody'))
            require(dispatch['format']=='swdb.lanl17-campaign-dispatch.v1' and stop['format']=='swdb.lanl17-stopped-attempt.v1','Actual original attempt formats differ')
            require(dispatch['campaign']==stop['campaign']==cid and dispatch['attempt']==number and dispatch['node'] in (0,1),'Actual attempt identity/order differs')
            for value in (dispatch,stop):require(value['source_commit']==self.R['commit'] and value['manifest_sha256']==self.m2['identity_sha256'] and value['policy']==self.m2['policy'],'Attempt changes R/M2/policy')
            require(dispatch['estimator_sha256']==F6 and stop['estimator_sha256_after']==F6 and stop['dispatch_sha256']==dispatch['identity_sha256'],'Attempt forecast/dispatch binding differs')
            require(dispatch['resume']==(number>1),'Fresh/resumed attempt flag differs')
            require(utc(dispatch['checked_utc'])>self.published and utc(stop['started_utc'])>=utc(dispatch['checked_utc']) and utc(stop['ended_utc'])>utc(stop['started_utc']),'Actual publication/launch chronology differs')
            require(stop['process_cleanup']['subreaper'] is True and stop['process_cleanup']['survivors']=={} and stop['source_clean_after'] is True and stop['original_codex_home_restored'] is True and stop['account_home_unchanged'] is True,'Owned cleanup/source/HOME metadata differs')
            require(release['format']=='swdb.lanl17-attempt-release-custody.v1' and release['campaign']==cid and release['attempt']==number and release['dispatch_identity']==dispatch['identity_sha256'] and release['stopped_identity']==stop['identity_sha256'],'Parent-accepted wrapper/release projection differs')
            require(release['lease_released'] is True and release['node']==dispatch['node'] and type(release['lease_generation']) is int and utc(release['checked_utc'])>=utc(stop['ended_utc']),'Actual lane release missing')
            require(release['runner_exit_code']==stop['runner_exit_code'] and release['public_exit_code']==stop['public_exit_code'],'Original exit-code custody differs')
            for key in ('lane_record_sha256','wrapper_exit_file_sha256'):require(re.fullmatch('[0-9a-f]{64}',release[key]) is not None,'Actual wrapper/lane source hash missing')
            require(stop in self.actual['stopped_attempts'],'Original stopped attempt absent from final receipt')
            stopped.append((dispatch,stop,release))
        final_dispatch,final_stop,final_release=stopped[-1]
        final_success=final_stop['runner_exit_code']==final_stop['public_exit_code']==final_release['wrapper_exit_code']==0 and final_stop['infrastructure_error'] is None and final_dispatch['baselines_only'] is False
        require(summary['stop_reason']==state.get('stop_reason') and state.get('stopped') is True,'Summary does not bind a terminal original state')
        normal=summary['stop_reason'] in NORMAL and final_success
        if summary['stop_reason']=='max_iterations':require(len(completed)==BUDGETS['max_iterations'],'Max-iteration terminal lacks actual complete rows')
        if summary['stop_reason']=='plateau':require(ledger['plateau']>=BUDGETS['plateau_iterations'],'Plateau terminal lacks ledger exhaustion')
        pairing_policy={'format':LEDGER,'campaign':cid,'version':VERSION,'estimator_sha256':F6,'enabled':True,'configuration':{'enabled':True},'fixture_model':None}
        forecasts=summary['paired_estimates']['records'];events=summary['paired_estimates']['outcome_accesses']
        for forecast in forecasts:
            require(forecast['policy_sha256']==digest(pairing_policy),'Campaign-local pairing policy differs; it is not the public agreement policy hash')
            require(utc(self.policy['frozen_at'])<utc(forecast['estimated_at']),'Forecast precedes the prospective agreement freeze')
        for event in events:require(utc(event['outcome_access_started_at'])>self.published,'An outcome preceded recorded freeze publication')
        roots=set();artifacts_seen=set();candidate_rows=0
        for baseline in summary['baselines']:
            roots.add(baseline['candidate']);roots.update(baseline['evaluation_ids_by_class'].values())
            for eid in baseline['evaluation_ids_by_class'].values():require(self.record(eid,'evaluation')['candidate']==baseline['candidate'] and self.record(eid,'evaluation').get('mode')=='extensa' and self.record(eid,'evaluation').get('campaign')==cid,'Baseline timing subject/mode/campaign differs')
        for iteration in summary['iterations']:
            for candidate in iteration['candidates']:
                candidate_rows+=1
                if not candidate.get('id'):continue  # Real refusal before materialization, not an artifact.
                roots.add(candidate['id']);source=self.record(candidate['id'],'candidate')
                require(source['campaign']==cid and source['mode']=='extensa' and source['artifact']['sha256']==candidate['artifact_sha256'],'Actual candidate artifact identity differs')
                artifacts_seen.add(candidate['artifact_sha256'])
                if candidate.get('certification') and candidate['certification'].get('record'):roots.add(candidate['certification']['record'])
                for comparison in candidate.get('comparisons',[]):
                    roots.update([comparison['comparison'],comparison['baseline_evaluation']]);record=self.record(comparison['comparison'],'comparison_result')
                    require(record.get('mode')=='extensa' and record.get('campaign')==cid and record['baseline_evaluation']==comparison['baseline_evaluation'] and record['metrics']['roi_speedup']==comparison['ratio'],'Comparison snapshot/mode/evaluation differs')
                    roots.add(record['candidate_evaluation']);evaluation=self.record(record['candidate_evaluation'],'evaluation')
                    require(evaluation['candidate']==candidate['id'] and type(comparison['ratio']) in (int,float) and math.isfinite(comparison['ratio']) and comparison['ratio']>0,'Candidate comparison is not real matching finite evidence')
        for forecast in forecasts:
            roots.add(forecast['id']);require(self.record(forecast['id'],'paired_estimate')==forecast,'Original paired record absent/different from embedded ledger')
        reached=self.closure(roots,index)
        exported_candidates=set()
        for pin in need(row,'public_candidate_exports'):
            exported=self.json(pin);require(exported['format']=='swdb.campaign-export.v1' and exported['campaign']==cid and exported['dry_run'] is False,'Actual candidate export receipt differs')
            require(all(c['level']!='rejected' for c in exported['candidates']),'Rejected candidate was promoted/exported')
            exported_candidates.update(c['id'] for c in exported['candidates'])
            for record in exported['records']:
                value=self.record(record['id'],record['kind']);require(self.record_pins[record['id']]['sha256']==record['sha256'],'Public exported closure bytes differ')
        require(exported_candidates==set(need(projection,'public_export_candidate_ids')),'Original public selected-candidate export inventory is missing/different')
        interrupted_index=interrupted.get('index') if interrupted else None
        return {'campaign':cid,'attempts':len(attempts),'lanes':[d['node'] for d,s,r in stopped],'terminal_reason':summary['stop_reason'],'normal_terminal':normal,'substantive_completed_iterations':len(completed)>0,'completed_iterations':len(completed),'interrupted_iteration':interrupted_index,'candidate_rows':candidate_rows,'distinct_materialized_artifact_hashes':len(artifacts_seen),'selected_closure_records':len(reached),'outcome_accesses':len(events),'prior_exposure_forecasts':sum(bool(f['timing_context'].get('prior_outcome_exposure')) for f in forecasts),'eligible_pairs':0,'final_attempt_succeeded':final_success,'terminal_infrastructure_summary_not_resumable':summary['stop_reason']=='infrastructure_failure','source_of_completion':'Pinned original state/ledger, not summary existence'}
    def audit(self):
        global CURRENT_R
        CURRENT_R=self.R['commit'];custody=self.custody()
        for key in ('final_ticket11_acceptance','final_ticket14_acceptance'):
            acceptance=need(self.pins,key);pin=need(acceptance,'receipt_pin');self.json(pin)
            require(pin.get('identity_sha256')==acceptance['receipt_identity'],'Final dependency actual receipt pin differs')
        self.selected_records();freeze=self.freeze()
        rows=need(self.pins,'campaigns');require(len(rows)==4 and {r['campaign'] for r in rows}==set(CIDS),'Exactly four actual campaign projections required')
        summaries=[self.record(cid+'.summary','campaign_summary') for cid in CIDS]
        require(len(self.report['summaries'])==4 and {s['campaign'] for s in self.report['summaries']}==set(CIDS),'Four distinct actual public snapshots required')
        require(self.report['summary_identities']=={s['id']:digest(s) for s in summaries},'Original summary identities differ')
        require(self.report['policy']==self.policy['id'] and self.report['policy_sha256']==self.policy['identity_sha256'] and utc(self.report['reported_at'])>utc(self.policy['frozen_at']),'Report/public policy identity order differs')
        expected=_analyse(self.policy,self.report['summaries'])
        require(all(self.report[key]==value for key,value in expected.items()),'Report differs from exact frozen public D30 analysis')
        trajectories=[self.trajectory(row) for row in sorted(rows,key=lambda r:r['campaign'])]
        require(expected['counts']['unique_eligible_dx100_pairs']==0 and expected['gate']['state']=='unsupported' and expected['recommendation']=='do_not_switch_to_flow_b','Current public admission cannot become an accuracy gate')
        trajectory_complete=all(row['normal_terminal'] and row['substantive_completed_iterations'] for row in trajectories)
        blind=expected['blind_order']['state']=='verified' and not expected['blind_order']['problems'] and not expected['blind_order']['missing_campaigns']
        return {'format':'swdb.lanl17-selected-read-only-audit.v1','audited_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'actual_execution':'Parent-approved compact/Git reading only; no experiment rerun','source_C':C,'final_R':self.R,'estimator_sha256':F6,'strict_additive_custody':custody,'freeze':freeze,'campaigns':trajectories,'four_normal_substantive_trajectories':trajectory_complete,'recorded_blind_order_verified':blind,'public_counts':expected['counts'],'rank':expected['rank'],'top3':expected['top3'],'gate':expected['gate'],'recommendation':expected['recommendation'],'selection_policy':expected['selection_policy'],'custody_state':'accepted_selected_custody','actual_ticket17_evidence_state':'ready_for_parent_review' if trajectory_complete and blind else 'incomplete_actual_trajectory_or_order','generation_dependency_facts':[{'campaign':plan['campaign'],'workloads':[{'id':w['id'],'family':w['generation']['family'],'explicit_generator_seed':(w['generation']['generator'] or {}).get('seed'),'seed_missing_means_unknown':True} for w in plan['workloads']]} for plan in self.policy['population']],'dependency_admission':'Zero eligible application components; four campaign IDs are not independent clusters','numerical_agreement':'unsupported; zero eligible pairs; no D30 achievement','limits':'Public full-catalog validation and parent-accepted raw projections remain required; receipt-order checks do not prove global historical blindness or live processes.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repository',required=True);parser.add_argument('--accepted-pins',required=True);parser.add_argument('--accepted-pins-sha256',required=True)
    args=parser.parse_args();path=pathlib.Path(args.accepted_pins)
    require(path.is_absolute() and path.is_file() and not path.is_symlink() and path.stat().st_size<=8*1024*1024,'Bounded accepted local pin file required')
    raw=path.read_bytes();require(sha(raw)==args.accepted_pins_sha256,'Explicit parent-accepted pin file SHA differs')
    pins=strict_json(raw);require(pins['format']=='swdb.lanl17-selected-admission-pins.v1','Accepted pins format differs');receipt_seal(pins,pins['identity_sha256'])
    require(pins['parent_approved_actual_inputs'] is True and pins['fixtures_or_replays_allowed'] is False,'Actual parent-approved evidence only')
    for key in ('final_ticket11_acceptance','final_ticket14_acceptance'):
        require(key in pins and pins[key]['accepted'] is True and re.fullmatch('[0-9a-f]{64}',pins[key]['receipt_identity']) is not None,'Explicit final dependency admission pending')
    result=Reader(args.repository,pins).audit();result['accepted_pins_identity_sha256']=pins['identity_sha256'];result['auditor_sha256']=sha(pathlib.Path(__file__).read_bytes());result['identity_sha256']=digest(result)
    print(json.dumps(result,indent=2));return 0 if result['actual_ticket17_evidence_state']=='ready_for_parent_review' else 2
if __name__=='__main__':
    try:sys.exit(main())
    except Pending as exc:print(json.dumps({'state':'pending','reason':str(exc),'actual_campaign_admission':False}));sys.exit(2)
    except (Refused,KeyError,TypeError,ValueError,yaml.YAMLError,subprocess.SubprocessError,OSError) as exc:
        print(json.dumps({'state':'refused','reason':str(exc) if isinstance(exc,(Refused,Pending)) else type(exc).__name__,'actual_campaign_admission':False}));sys.exit(3)

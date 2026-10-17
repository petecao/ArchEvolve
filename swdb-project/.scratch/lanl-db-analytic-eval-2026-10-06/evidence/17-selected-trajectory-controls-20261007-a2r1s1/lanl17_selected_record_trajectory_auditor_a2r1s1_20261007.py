"""Prospective read-only selected-record/trajectory auditor; no actual inputs admitted.

Use only after parent approval of explicit local pins. Git reads and compact files
only: no Store, SWDB imports, network, process control, scientific commands, auth,
full argv, provider prompts or raw logs. It does not substitute full public validation.
"""
import argparse,ast,copy,hashlib,json,math,os,pathlib,random,re,subprocess,sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional
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
def safe_code(code):
    require(isinstance(code,str) and re.fullmatch('[a-z0-9_.-]+',code),'Closed reason code required');return code
class Refused(ValueError): pass
class Pending(ValueError): pass
Failure=Refused  # Coherent fail-closed name used by the exact lifted public context method.
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
PINNED_SOURCE_FILES.update({'swdb/campaign.py': '13e3e66a469c3934dee2f0f372a5c17812f5a680cb451f63766ad889d13c3d1d', 'swdb/extensa/search.py': '348b07b38a7955a65b5c13629dd8234453609f152a78d27524df6bf840a989e7', 'swdb/campaign_targets.py': '727d4399e4bde1996484e3013770e5ab21ef4a30e8fa7313c4697aaa6359211f', 'swdb/bfs_protocol.py': 'fdf5d38c29e321dbb300a3eb681f0c9a5619a0bd05733aabb410991de3589596'})

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

class StopReason(str, Enum):
    """Decision D6's closed stop-reason set."""
    MAX_ITERATIONS = "max_iterations"
    PLATEAU = "plateau"
    LANE_HOURS = "lane_hours"
    PROVIDER_CALLS = "provider_calls"
    DISK = "disk"
    BASELINE_UNSTABLE = "baseline_unstable"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    STOPPED_BY_YANRU = "stopped_by_yanru"

STOP_PRECEDENCE = (StopReason.INFRASTRUCTURE_FAILURE, StopReason.BASELINE_UNSTABLE,
                   StopReason.STOPPED_BY_YANRU, StopReason.DISK, StopReason.LANE_HOURS,
                   StopReason.PROVIDER_CALLS, StopReason.MAX_ITERATIONS, StopReason.PLATEAU)

class IterationOutcome(str, Enum):
    IMPROVED = "improved"                       # some class's best improved in selection order
    NOT_IMPROVED = "not_improved"               # completed, nothing improved: plateau advances
    INFRASTRUCTURE_FAILED = "infrastructure_failed"   # stops; plateau unchanged
    PAUSED = "paused"                           # usage limit / login: not an iteration

COMPLETED_ITERATION_OUTCOMES = frozenset({IterationOutcome.IMPROVED, IterationOutcome.NOT_IMPROVED})

class CallOutcome(str, Enum):
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    MALFORMED_OUTPUT = "malformed_output"
    GUARD_REFUSED = "guard_refused"
    FAILED = "failed"
    USAGE_LIMIT = "usage_limit"
    LOGIN = "login"
    #: SWDB addition, ticket 73 (2026-10-05 ET): transient provider-side unavailability (D7, uncounted).
    PROVIDER_CAPACITY = "provider_capacity"
    #: SWDB addition, ticket 74 (2026-10-05 ET): the provider guard stopped the call for the harness's own
    #: limit on the provider runtime, not for anything the model did (D7: not a real attempt, uncounted).
    GUARD_INFRASTRUCTURE = "guard_infrastructure"

UNCOUNTED_CALL_OUTCOMES = frozenset({CallOutcome.USAGE_LIMIT, CallOutcome.LOGIN, CallOutcome.PROVIDER_CAPACITY,
                                     CallOutcome.GUARD_INFRASTRUCTURE})

BUDGET_KEYS = ("max_iterations", "plateau_iterations", "lane_hours", "provider_calls_per_iteration",
               "provider_calls_setup", "disk_gb", "lanes")

@dataclass(frozen=True)
class SearchBudget:
    """The campaign file's budgets. No value here has a code default."""

    max_iterations: int
    plateau_iterations: int
    lane_hours: float
    provider_calls_per_iteration: int
    provider_calls_setup: int
    disk_gb: float
    lanes: int
    source: str
    """Which campaign file (path and sha256) these numbers were copied from."""

    def __post_init__(self) -> None:
        for name in ("max_iterations", "plateau_iterations", "provider_calls_per_iteration", "lanes"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"budget {name} must be a positive integer")
        if type(self.provider_calls_setup) is not int or self.provider_calls_setup < 0:
            raise ValueError("budget provider_calls_setup must be a nonnegative integer")
        for name in ("lane_hours", "disk_gb"):
            value = getattr(self, name)
            if type(value) not in (int, float) or value <= 0:
                raise ValueError(f"budget {name} must be positive")
        if not self.source:
            raise ValueError("a budget must name the campaign file it was copied from; none is invented")

    @classmethod
    def from_mapping(cls, budgets: dict, source: str) -> "SearchBudget":
        if not isinstance(budgets, dict):
            raise ValueError("budgets must be a mapping")
        missing = [key for key in BUDGET_KEYS if key not in budgets]
        if missing:
            raise ValueError("campaign budgets have no code defaults; missing: " + ", ".join(missing))
        unknown = set(budgets) - set(BUDGET_KEYS)
        if unknown:
            raise ValueError("unknown budget keys: " + ", ".join(sorted(unknown)))
        return cls(**{key: budgets[key] for key in BUDGET_KEYS}, source=source)

    def to_dict(self) -> dict:
        return {key: getattr(self, key) for key in BUDGET_KEYS}

@dataclass
class CallRecord:
    index: int
    iteration: int            # 0 for the setup call
    role: str
    invocation: str
    outcome: Optional[str] = None
    counted: bool = True

    def to_dict(self) -> dict:
        return {"index": self.index, "iteration": self.iteration, "role": self.role,
                "invocation": self.invocation, "outcome": self.outcome, "counted": self.counted}

@dataclass
class IterationRecord:
    index: int
    outcome: IterationOutcome
    advanced_plateau: bool
    plateau_after: int

    def to_dict(self) -> dict:
        return {"index": self.index, "outcome": self.outcome.value,
                "advanced_plateau": self.advanced_plateau, "plateau_counter": self.plateau_after}

class CallRefused(RuntimeError):
    """Opening this call would exceed the provider-call cap (D7)."""

class SearchLedger:
    """Budget and plateau accounting for one Extensa campaign."""

    def __init__(self, budget: SearchBudget):
        self.budget = budget
        self.iteration = 0              # index of the open iteration (0 = setup)
        self.iterations_completed = 0
        self.plateau = 0
        self.calls: list[CallRecord] = []
        self.iterations: list[IterationRecord] = []
        self._terminal: Optional[StopReason] = None
        self._iteration_calls = 0
        self._setup_calls = 0

    # -- state ------------------------------------------------------------
    @property
    def counted_calls(self) -> int:
        return sum(1 for c in self.calls if c.counted)

    @property
    def uncounted_calls(self) -> int:
        return sum(1 for c in self.calls if not c.counted)

    @property
    def plateau_reached(self) -> bool:
        return self.plateau >= self.budget.plateau_iterations

    @property
    def iterations_exhausted(self) -> bool:
        return self.iterations_completed >= self.budget.max_iterations

    def calls_remaining_this_iteration(self) -> int:
        if self.iteration == 0:
            return max(0, self.budget.provider_calls_setup - self._setup_calls)
        return max(0, self.budget.provider_calls_per_iteration - self._iteration_calls)

    def may_open_iteration(self) -> bool:
        return self._terminal is None and not self.iterations_exhausted and not self.plateau_reached

    # -- iterations --------------------------------------------------------
    def begin_iteration(self) -> int:
        if not self.may_open_iteration():
            raise RuntimeError("the campaign has stopped; no further iteration may open")
        self.iteration = self.iterations_completed + 1
        self._iteration_calls = 0      # unused calls never carry over
        return self.iteration

    def record_iteration(self, outcome: IterationOutcome) -> IterationRecord:
        if self._terminal is not None:
            raise RuntimeError("a terminal outcome cannot be followed by another iteration")
        if self.iteration == 0:
            raise RuntimeError("no iteration is open")
        advanced = False
        if outcome is IterationOutcome.PAUSED:
            # Not an iteration: it is retried from its start after resume.
            record = IterationRecord(self.iteration, outcome, False, self.plateau)
            self.iterations.append(record)
            self.iteration = 0
            return record
        if outcome is IterationOutcome.IMPROVED:
            self.plateau = 0
        elif outcome is IterationOutcome.NOT_IMPROVED:
            self.plateau += 1
            advanced = True
        else:
            self._terminal = StopReason.INFRASTRUCTURE_FAILURE
        if outcome in COMPLETED_ITERATION_OUTCOMES:
            self.iterations_completed += 1
        record = IterationRecord(self.iteration, outcome, advanced, self.plateau)
        self.iterations.append(record)
        self.iteration = 0
        return record

    # -- provider calls -----------------------------------------------------
    def open_call(self, role: str, invocation: str) -> CallRecord:
        """Charge one opened call, or refuse to open it (D7: the cap is never exceeded)."""
        if self._terminal is not None:
            raise CallRefused("the campaign has stopped")
        if self.calls_remaining_this_iteration() < 1:
            raise CallRefused("provider-call cap reached for "
                              + ("setup" if self.iteration == 0 else f"iteration {self.iteration}"))
        if self.iteration == 0:
            self._setup_calls += 1
        else:
            self._iteration_calls += 1
        call = CallRecord(len(self.calls) + 1, self.iteration, role, invocation)
        self.calls.append(call)
        return call

    def close_call(self, call: CallRecord, outcome: CallOutcome) -> CallRecord:
        call.outcome = CallOutcome(outcome).value
        if CallOutcome(outcome) in UNCOUNTED_CALL_OUTCOMES:
            # D7: recorded, never counted; the slot is returned for the retried iteration.
            call.counted = False
            if call.iteration == 0:
                self._setup_calls -= 1
            else:
                self._iteration_calls -= 1
        return call

    # -- stopping -----------------------------------------------------------
    def terminate(self, reason: StopReason) -> None:
        """End on a condition no iteration reported. The first terminal reason wins."""
        if self._terminal is None:
            self._terminal = StopReason(reason)

    def stop(self) -> tuple[Optional[StopReason], tuple[StopReason, ...]]:
        conditions = []
        if self._terminal is not None:
            conditions.append(self._terminal)
        if self.iterations_exhausted:
            conditions.append(StopReason.MAX_ITERATIONS)
        if self.plateau_reached:
            conditions.append(StopReason.PLATEAU)
        ordered = tuple(r for r in STOP_PRECEDENCE if r in conditions)
        return (ordered[0] if ordered else None), ordered

    # -- persistence (SWDB addition: a paused campaign resumes from its state file) ----
    def to_state(self) -> dict:
        return {"iteration": self.iteration, "iterations_completed": self.iterations_completed,
                "plateau": self.plateau, "calls": [c.to_dict() for c in self.calls],
                "iterations": [r.to_dict() for r in self.iterations],
                "terminal": self._terminal.value if self._terminal else None,
                "iteration_calls": self._iteration_calls, "setup_calls": self._setup_calls}

    @classmethod
    def from_state(cls, budget: SearchBudget, state: dict) -> "SearchLedger":
        ledger = cls(budget)
        ledger.iteration = state["iteration"]
        ledger.iterations_completed = state["iterations_completed"]
        ledger.plateau = state["plateau"]
        ledger.calls = [CallRecord(**c) for c in state["calls"]]
        ledger.iterations = [IterationRecord(r["index"], IterationOutcome(r["outcome"]), r["advanced_plateau"],
                                             r["plateau_counter"]) for r in state["iterations"]]
        ledger._terminal = StopReason(state["terminal"]) if state["terminal"] else None
        ledger._iteration_calls = state["iteration_calls"]
        ledger._setup_calls = state["setup_calls"]
        return ledger

    def to_dict(self) -> dict:
        winner, coincident = self.stop()
        return {"budget": self.budget.to_dict(), "iterations_completed": self.iterations_completed,
                "plateau_counter": self.plateau, "provider_calls_counted": self.counted_calls,
                "provider_calls_uncounted": self.uncounted_calls,
                "calls": [c.to_dict() for c in self.calls],
                "iterations": [r.to_dict() for r in self.iterations],
                "stop_reason": winner.value if winner else None,
                "coincident_stop_conditions": [c.value for c in coincident]}

LEVEL_RANK = {"certified": 2, "uncertified": 1}

def selection_key(candidate):
    return (LEVEL_RANK[candidate["level"]], candidate["selection"]["lower"])

def select(candidates):
    """Per class: (best, faster_uncertified, verdict). Rejected artifacts never compete.

    Certified before uncertified, then by the lower bound (point ratio on gem5) against
    the base-source baseline; only gain artifacts can be best; an uncertified one is best
    only when no certified one passes."""
    eligible = [c for c in candidates if c["level"] in LEVEL_RANK and c.get("selection")]
    passing = [c for c in eligible if c["selection"]["verdict"] == "gain"]
    if not passing:
        if eligible and all(c["selection"]["verdict"] == "inconclusive" for c in eligible):
            return None, [], "inconclusive"
        return None, [], "no_gain"
    best = max(passing, key=selection_key)
    faster = [c["id"] for c in passing if c["level"] == "uncertified" and best["level"] == "certified"
              and c["selection"]["lower"] > best["selection"]["lower"]]
    return best, sorted(faster), "gain"

def source_pairing_request(self, request, build):
    out = copy.deepcopy(request)
    settings = self.protocol['settings']
    role = request['protocol_role']
    out['timing_policy'] = {key: copy.deepcopy(settings[key]) for key in
        ('mode', 'roi', 'threads', 'sampling', 'simulation_identity') if key in settings}
    out['timing_policy']['instrumentation'] = copy.deepcopy(settings['instrumentation'][role])
    out['timing_policy']['target'] = copy.deepcopy(settings['targets'][role])
    out['timing_policy']['build'] = {key: copy.deepcopy(build['build'][key]) for key in
        ('compiler', 'compiler_version', 'flags', 'adapter', 'binary_sha256') if key in build['build']}
    out['backend'] = 'gem5_mmio'
    return out

def source_pairing_context(self, store, request):
    candidate = store.get(request['candidate'], 'candidate')
    workload = store.get(request['workload']['id'], 'workload')
    if candidate is None or workload is None:
        raise Failure('paired estimate requires its actual candidate and registered workload')
    definition = workload['definition']
    # Preserve exact representation hashes and canonical graph identity, never
    # substitute equal vertex/edge totals for the registered graph.
    input_facts = {key: copy.deepcopy(definition[key]) for key in
                   ('canonical_sha256', 'canonical_format', 'normalization', 'sources', 'source_policy')
                   if key in definition}
    input_facts['representations'] = [{key: row[key] for key in
        ('id', 'sha256', 'format', 'application', 'canonical_sha256', 'adjacency_verified') if key in row}
        for row in definition.get('representations', [])]
    execution = {key: copy.deepcopy(value) for key, value in request.items()
                 if key not in {'id', 'message_version', 'candidate', 'workload', 'budget', 'build_directory'}}
    selected = {key: copy.deepcopy(value) for key, value in request['workload'].items() if key != 'id'}
    if isinstance(selected.get('representation'), dict):
        selected['representation'].pop('path', None)
    execution['selected_input'] = selected
    execution['target'] = self.campaign['target']
    execution.setdefault('roi', self.campaign['protocol']['roi'])
    execution.setdefault('threads', self.campaign['protocol']['threads'])
    execution.setdefault('sources', list(self.campaign['protocol']['sources']))
    execution.setdefault('repetitions', self.campaign['protocol']['repetitions'])
    return {'subject': {'id': candidate['id'], 'artifact_sha256': candidate['artifact']['sha256']},
            'input': {'id': workload['id'], 'identity_sha256': workload['identity_sha256'], **input_facts},
            'execution': execution}

CALL_KEYS=('role','invocation','outcome','counted','model','effort')
CANDIDATE_KEYS=('id','class','artifact_sha256','patch_sha256','level')
ITERATION_KEYS=('index','started','ended','improved_classes')
STATE_KEYS=('campaign','campaign_sha256','started','stopped','stop_reason','clean_exit','setup_done','resumes','lane_hours','provider_wait_hours','disk_bytes_peak')
PROJECTION_CONTRACT='swdb.lanl17-safe-control-projection.v1'

def public_token(value,nullable=False):
    if value is None and nullable:return None
    require(isinstance(value,str) and len(value)<=256 and re.fullmatch('[A-Za-z0-9_.:/+-]+',value),'bounded public scalar token required')
    return value

def public_scalar(value):
    require(value is None or type(value) in (int,float,bool,str),'public scalar required')
    if isinstance(value,str):return public_token(value)
    if type(value) is float:require(value==value and abs(value)!=float('inf'),'finite public scalar required')
    return value

def public_fields(row,keys):
    require(isinstance(row,dict),'public field mapping required')
    return {k:public_scalar(row[k]) for k in keys if k in row}

def excluded_fields(row,keys):
    # Hash the entire excluded values; do not copy their nested content or text.
    return {k:{'json_type':type(row[k]).__name__,'semantic_sha256':digest(row[k]),'values_exported':False} for k in keys if k in row}

def project_calls(rows):
    require(isinstance(rows,list) and len(rows)<=500,'bounded public call rows required')
    return [{**public_fields(r,CALL_KEYS),'excluded_metadata':excluded_fields(r,('classification',))} for r in rows]

def project_candidate(row):
    result=public_fields(row,CANDIDATE_KEYS)
    result['excluded_provider_values']=excluded_fields(row,('knobs','contracts'))
    certification=row.get('certification')
    result['certification']=None if certification is None else {
        **public_fields(certification,('record','outcome','level_at_summary')),
        'excluded_metadata':excluded_fields(certification,('failed_checks',))}
    comparisons=row.get('comparisons',[])
    require(isinstance(comparisons,list) and len(comparisons)<=32,'bounded comparison rows required')
    result['comparisons']=[{**public_fields(r,('baseline_role','comparison','baseline_evaluation','ratio','lower','upper','relative_ci_width','spread','verdict')),'excluded_metadata':excluded_fields(r,('level_mix',))} for r in comparisons]
    selection=row.get('selection')
    result['selection']=None if selection is None else public_fields(selection,('lower','verdict','ratio'))
    return result

def project_iteration(row):
    result=public_fields(row,('index','started','ended'))
    improved=row.get('improved_classes',[])
    require(isinstance(improved,list) and len(improved)<=32,'bounded improved class IDs required')
    result.update(improved_classes=[public_token(x) for x in improved],provider_calls=project_calls(row.get('provider_calls',[])),
        candidates=[project_candidate(r) for r in row.get('candidates',[])],source_row_sha256=digest(row))
    return result

def project_state(state):
    result=public_fields(state,STATE_KEYS)
    result['projection_contract']=PROJECTION_CONTRACT
    result['ledger']={k:state['ledger'][k] for k in ('iteration','iterations_completed','plateau','calls','iterations','terminal','iteration_calls','setup_calls')}
    result['ledger']['calls']=[public_fields(r,('index','iteration','role','invocation','outcome','counted')) for r in state['ledger']['calls']]
    result['ledger']['iterations']=[public_fields(r,('index','outcome','advanced_plateau','plateau_counter')) for r in state['ledger']['iterations']]
    require(result['ledger']==state['ledger'],'unexpected private/unknown ledger field')
    result['ledger_sha256']=digest(state['ledger'])
    result['iterations']=[project_iteration(r) for r in state['iterations']]
    result['setup_calls']=project_calls(state.get('setup_calls',[]))
    result['pauses']=[{**public_fields(r,('at','resumed_at','iteration')),
        'reason':safe_code(r['reason']),'provider_calls':project_calls(r.get('provider_calls',[])),
        'source_row_sha256':digest(r)} for r in state['pauses']]
    if state.get('interrupted_iteration'):result['interrupted_iteration']=project_iteration(state['interrupted_iteration'])
    result['prepared']=[public_token(x) for x in state.get('prepared',[])]
    result['preflights']=[public_fields(r,('step','state')) for r in state.get('preflights',[])]
    result['baselines']={public_token(k):public_token(v) for k,v in state.get('baselines',{}).items()}
    result['protocol_id']=public_token(state.get('protocol',{}).get('id'),nullable=True)
    result['protocol_identity_sha256']=public_token(state.get('protocol',{}).get('identity_sha256'),nullable=True)
    result['stop_detail_sha256']=digest(state.get('stop_detail'))
    result['source_state_semantic_sha256']=digest(state)
    return result

class Reader:
    def __init__(self,repository,pins):
        self.repository=pathlib.Path(repository).resolve(strict=True);self.pins=pins;self.records={};self.record_pins={}
        self.R=need(pins,'final_R');self.EF=need(pins,'freeze_export');self.ER=need(pins,'report_export')
        for row in (self.R,self.EF,self.ER):
            require(re.fullmatch('[0-9a-f]{40}',need(row,'commit')) is not None,'Explicit full Git commit required')
            require(re.fullmatch('[0-9a-f]{40}',need(row,'tree')) is not None,'Explicit full Git tree required')
        self.refs={C,self.R['commit'],self.EF['commit'],self.ER['commit']}
        self.refs.update(need(self.pins,k)['actual_export_commit'] for k in ('final_ticket11_acceptance','final_ticket14_acceptance'))
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
            p=pathlib.Path(need(pin,'path'));require(p.is_absolute() and '..' not in p.parts and p.is_file() and all(not x.is_symlink() for x in (p,*p.parents)),'Pinned local regular compact file without symlink components required')
            require(p.stat().st_size==size,'Pinned compact file size differs');raw=p.read_bytes()
        require(len(raw)==size and sha(raw)==expected,'Selected compact/Git file bytes differ')
        return raw
    def json(self,pin):
        value=strict_json(self.raw(pin))
        if 'identity_sha256' in pin: receipt_seal(value,pin['identity_sha256'],ensure_ascii=need(pin,'canonical_ensure_ascii'))
        return value
    def sealed_json(self,pin):
        require(re.fullmatch('[0-9a-f]{64}',need(pin,'identity_sha256')) is not None,'Explicit claimed receipt identity pin required')
        require(type(need(pin,'canonical_ensure_ascii')) is bool,'Explicit boolean receipt canonical_ensure_ascii required')
        # json() recomputes the compact seal from exact SHA-pinned original bytes.
        # Only receipt sites use this gate; original unsealed public output stays.
        return self.json(pin)
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
        row=self.sealed_json(pin);require(row['format']=='swdb.lanl17-metadata-supervisor.v1' and row['action']==action,'Actual metadata action receipt differs')
        require(row['state']=='child_returned' and row['child_exit']==row['supervisor_exit']==0 and row['fixture'] is False,'Actual metadata action did not succeed')
        require(row['timed_out'] is False and row['signal_received'] is None and not row['cleanup_errors'] and row['error_type'] is None,'Metadata action interrupted or failed')
        require(row['cleanup']['subreaper'] is True and row['cleanup']['survivors']=={},'Metadata owned cleanup incomplete')
        require(row['helper_sha256']==row['cleanup_implementation_sha256']==HELPER and row['supervisor_sha256']==SUPERVISOR and row['processes_py_sha256']==PROCESSES and row['estimator_sha256']==F6,'Metadata control/source pins differ')
        require(row['provider_calls']==row['application_outcomes']==0,'Metadata action scope differs')
        require(utc(row['started_utc'])<utc(row['ended_utc']),'Metadata time order differs');return row
    def freeze(self):
        m2=self.sealed_json(need(self.pins,'manifest_M2'));fr=self.sealed_json(self.EF['receipt']);ar=self.sealed_json(self.ER['receipt'])
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
        self.provider_configuration=yaml.load(self.blob(self.EF['commit'],provider_path),Loader=RecordLoader)
        require(self.provider_configuration['kind']=='codex','Actual official provider config required; fixture calls are not campaign work')
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
            prereg=self.sealed_json(need(self.pins,action+'_preregistration'))
            require(prereg['format']=='swdb.lanl17-metadata-dispatch-preregistration.v1' and prereg['action']==action and prereg['final_source_commit']==self.R['commit'] and prereg['source_code_equivalent_F6'] is True and prereg['estimator_sha256']==F6,'Original metadata guard admission/source binding differs')
            require(prereg['guard_sha256']==GUARD and prereg['helper_sha256']==HELPER and prereg['supervisor_sha256']==SUPERVISOR and prereg['processes_sha256']==PROCESSES,'Metadata guard selected controls differ')
            require(prereg['actual_cleanup_proof']['identity_sha256']==proof['identity_sha256'] and prereg['actual_supervisor_proof']['identity_sha256']=='ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b','Original selected actual Linux proof pins differ')
            require(prereg['account_HOME_unchanged'] is True and prereg['CODEX_HOME_original_verified'] is True and prereg['authentication_contents_read'] is False,'Metadata guard provider HOME/privacy scope differs')
        require(utc(policy['frozen_at'])<=utc(fr['checked_utc'])<utc(prepare['ended_utc'])<utc(report['reported_at'])<=utc(ar['checked_utc'])<=utc(finalize['ended_utc']),'Prepare/freeze/report chronology differs')
        publication=self.sealed_json(need(self.pins,'freeze_publication_custody'))
        require(publication['format']=='swdb.lanl17-freeze-publication-custody.v1' and publication['source_commit']==self.R['commit'] and publication['freeze_export_commit']==self.EF['commit'] and publication['manifest_sha256']==m2['identity_sha256'] and publication['policy_sha256']==policy['identity_sha256'],'Parent-accepted export-publication projection differs')
        require(publication['prepare_supervisor_identity']==prepare['identity_sha256'] and publication['application_outcomes_opened']==0 and publication['completed_export_exit_code']==0,'Actual freeze publication success missing')
        require(publication['input_model_baseline_pins_sha256']==digest(m2['input_model_baseline_pins']) and publication['frozen_live_files_verified'] is True,'Parent-accepted original live metadata pin check missing')
        require(utc(prepare['ended_utc'])<=utc(publication['checked_utc']),'Publication observation precedes prepare completion')
        self.m2,self.policy,self.report,self.actual,self.published=m2,policy,report,ar,utc(publication['checked_utc'])
        return {'M1_identity':m1['identity_sha256'],'M2_identity':m2['identity_sha256'],'policy':policy['id'],'freeze_export_commit':self.EF['commit'],'publication_checked_utc':publication['checked_utc']}
    def dependencies(self):
        result={}
        for ticket,key in ((11,'final_ticket11_acceptance'),(14,'final_ticket14_acceptance')):
            admission=need(self.pins,key);selected=self.sealed_json(need(admission,'receipt_pin'))
            require(admission['accepted'] is True and selected['identity_sha256']==admission['receipt_identity'],'Explicit accepted dependency pin differs')
            export=need(admission,'actual_export_commit');require(re.fullmatch('[0-9a-f]{40}',export),'Full dependency export commit required')
            self.git('merge-base','--is-ancestor',export,self.R['commit'])
            require(selected['export_commit']==export and selected['estimator_sha256']==F6,'Dependency export/F6 differs')
            inherited=self.sealed_json(need(admission,'actual_export_receipt_pin'))
            require(inherited['identity_sha256']==admission['actual_export_receipt_identity'],'Dependency actual export receipt differs')
            sole_source=C if ticket==11 else need(admission,'final_source_commit')
            require(self.text('rev-list','--parents','-n','1',export).split()==[export,sole_source],'Dependency export does not have its declared actual source as sole parent')
            require(inherited['source_commit']==sole_source and inherited['source_clean'] is True,'Dependency original clean source receipt differs')
            require(inherited['format']==('swdb.cpu-band-report-compact-receipt.v1' if ticket==11 else 'swdb.lanl14-final-report-export.v1'),'Dependency actual export receipt format differs')
            if ticket==11:
                require(selected['format']=='swdb.cpu-future-phase-local-readonly-admission.v1' and selected['phase']=='report' and selected['admitted'] is True and selected['source_commit']==C,'Actual final CPU report admission missing')
                require(selected['actual_compact_receipt_identity']==inherited['identity_sha256'],'CPU reader/export receipt linkage differs')
                require(selected['native_or_provider_or_remote_invocations']==selected['store_or_writer_or_index_invocations']==0,'CPU selected-reader scope differs')
                require(sha(self.raw(need(admission,'reader_source_pin')))==need(admission,'selected_reader_source_sha256'),'CPU original reader source pin differs')
                scope='Checks existing selected-reader phase/admitted/C/F6/export semantics; its original full validation and numerical checks are inherited from pinned actual admission, not independently rerun'
            else:
                require(selected['format']=='swdb.lanl14-selected-nine-export-admission.v1' and selected['final_source_commit']==need(admission,'final_source_commit'),'Actual final generality selected-reader source differs')
                require(selected['receipt_identity_sha256']==inherited['identity_sha256'] and selected['prior_tracked_blobs_unchanged'] is True and selected['source_clean'] is True,'Generality source/export custody differs')
                require(len(selected['pairs'])==9 and {(r['kernel'],r['target']) for r in selected['pairs']}=={(k,t) for k in ('bfs','bc','pagerank') for t in ('cpu','dx100','maple')},'Nine actual disclosed pairs missing')
                direct=selected['direct_observations'];pre=selected['inherited_pinned_export_preconditions']
                require(direct['lane_exit_code']==0 and direct['cleanup_survivors']=={} and pre['runner_exit_code']==pre['wrapper_exit_code']==0 and pre['new_native_or_compiler_execution']==0,'Generality direct/inherited execution preconditions differ')
                require(selected['provider_calls']==selected['application_timings']==selected['reader_native_compiler_provider_remote_actions']==0,'Generality selected-reader scope differs')
                require(selected['reader_sha256']==sha(self.raw(need(admission,'reader_source_pin')))==need(admission,'selected_reader_source_sha256'),'Generality original reader source file pin differs')
                scope='Checks nine-pair selected disclosure/direct facts and explicitly inherited pinned-export/full-catalogue preconditions; no admitted:true is invented'
            result[str(ticket)]={'actual_export_commit':export,'receipt_identity':selected['identity_sha256'],'admission_boundary':scope,'numerical_accuracy_not_required_for_completed_dependency':True}
        return result

    def selection_replay(self,summary):
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

    def retained_ledger(self,summary,state,projection):
        ledger=state['ledger'];require(digest(ledger)==state['ledger_sha256'],'Retained ledger projection hash differs')
        calls_by_invocation={r['invocation']:r for r in ledger['calls']}
        require(len(calls_by_invocation)==len(ledger['calls']) and [r['index'] for r in ledger['calls']]==list(range(1,len(ledger['calls'])+1)),'Duplicate/nonconsecutive provider calls')
        replay=SearchLedger(SearchBudget.from_mapping(BUDGETS,summary['campaign_file']['sha256']));used=set();substantive=[]
        cfg=next(p['configuration'] for p in self.policy['population'] if p['campaign']==summary['campaign'])
        require(self.provider_configuration['kind']=='codex' and cfg['provider']['name']=='codex','Substantive work requires frozen actual official provider configuration')
        def replay_calls(rows,index):
            for row in rows:
                invocation=row['invocation'];require(invocation in calls_by_invocation and invocation not in used,'Provider projection missing/duplicated')
                saved=calls_by_invocation[invocation]
                require(saved['iteration']==index and all(saved[k]==row[k] for k in ('role','invocation','outcome','counted')),'Provider row/ledger differs')
                require(saved['index']==len(replay.calls)+1,'Provider projections do not preserve opened-call order')
                require(row['outcome'] is not None,'Open/unsaved provider call cannot be independently reconciled')
                call=replay.open_call(row['role'],invocation);replay.close_call(call,CallOutcome(row['outcome']))
                require(call.to_dict()==saved,'Counted/uncounted exception or provider slot differs');used.add(invocation)
        # A paused setup call raises before campaign._setup_call persists its row;
        # the retained ledger itself provides those exact setup invocation/outcomes.
        replay_calls([r for r in ledger['calls'] if r['iteration']==0],0)
        pauses=[r for r in state['pauses'] if r.get('iteration',0)>0];pause_position=0
        completed_by_index={r['index']:r for r in state['iterations']}
        for saved in ledger['iterations']:
            index=replay.begin_iteration();require(index==saved['index'],'Iteration/paused retry index differs')
            if saved['outcome']=='paused':
                require(pause_position<len(pauses),'Paused session provider custody missing');body=pauses[pause_position];pause_position+=1
                require(body['iteration']==index,'Pause partition index differs')
            elif saved['outcome'] in ('improved','not_improved'):
                body=completed_by_index[index]
                require(bool(body['improved_classes'])==(saved['outcome']=='improved'),'Improvement/plateau outcome differs')
            else:
                body=need(projection,'infrastructure_iteration_provider_partition')
                require(body['index']==index,'Infrastructure session partition differs')
            replay_calls(body['provider_calls'],index)
            if saved['outcome'] in ('improved','not_improved'):
                rewriting=[r for r in body['provider_calls'] if r['role']=='rewriting' and r['counted'] is True]
                require(rewriting and all(r['outcome'] is not None and r['outcome'] not in {x.value for x in UNCOUNTED_CALL_OUTCOMES} for r in rewriting),'Completed session lacks exact retained closed counted rewriting invocation')
                for call in rewriting:
                    require(call['model']==cfg['provider']['model'] and call['effort']==cfg['provider']['effort'] and call['counted'] is True,'Completed rewriting model/effort differs from frozen campaign provider')
                substantive.append({'index':index,'rewriting_invocations':[r['invocation'] for r in rewriting],'invalid_or_failed_output_still_closed_work':True,'candidate_not_required':True})
            require(replay.record_iteration(IterationOutcome(saved['outcome'])).to_dict()==saved,'Plateau/paused/completion transition differs')
        require(pause_position==len(pauses),'Additional paused session not in retained ledger')
        if ledger['iteration']:
            interrupted=state.get('interrupted_iteration')
            if interrupted is None:raise Pending('Open retained session has no original interrupted provider partition; explicit parent capture/attestation required')
            require(replay.begin_iteration()==ledger['iteration']==interrupted['index'],'Interrupted open session differs')
            replay_calls(interrupted['provider_calls'],ledger['iteration'])
        require(used==set(calls_by_invocation),'Provider calls lack exact setup/paused/completed/interrupted partition; do not group repeated iteration indices')
        if ledger['terminal']:replay.terminate(StopReason(ledger['terminal']))
        require(replay.to_state()==ledger,'Retained public SearchLedger state does not replay exactly')
        winner,conditions=replay.stop()
        require(winner is not None and winner.value==summary['stop_reason']==state['stop_reason'],'Terminal precedence differs')
        used_summary=summary['budgets']['used']
        require(used_summary['provider_calls_counted']==replay.counted_calls and used_summary['provider_calls_uncounted']==replay.uncounted_calls,'Summary provider totals differ')
        require(replay.counted_calls<=25,'Actual retained provider total exceeds fixed setup+iterations budget')
        if winner is StopReason.PROVIDER_CALLS:require(replay.counted_calls==25,'Local call-slot refusal alone is not a provider-budget terminal')
        require(used_summary['lane_hours']==round(state['lane_hours'],6),'Summary lane-hour rounding differs')
        if 'provider_wait_hours' in state:require(used_summary.get('provider_wait_hours',0)==round(state['provider_wait_hours'],6),'Provider-wait rounding differs')
        peak=state.get('disk_bytes_peak',0);summary_peak=used_summary['disk_gb_peak']
        require(type(peak) in (int,float) and peak>=0 and summary_peak>=0 and round(peak/1e9,6)<=summary_peak,'Summary disk peak is below retained peak')
        administrative=need(projection,'administrative_enforcement')
        require(administrative['basis']=='explicit_parent_attestation_of_original_source_enforcement' and administrative['accepted'] is True and administrative['source_commit']==self.R['commit'] and administrative['campaign_source_sha256']==PINNED_SOURCE_FILES['swdb/campaign.py'] and administrative['search_source_sha256']==PINNED_SOURCE_FILES['swdb/extensa/search.py'],'Administrative enforcement attestation missing/different')
        require(administrative['state_file_sha256']==projection['source_state_file_sha256'] and administrative['summary_sha256']==digest(summary) and administrative['terminal']==winner.value,'Administrative attestation evidence binding differs')
        require(administrative['unsaved_provider_or_step_events_independently_replayed'] is False and administrative['summary_time_disk_usage_independently_reconstructed'] is False,'Unsupported independent budget replay claim')
        if winner in (StopReason.LANE_HOURS,StopReason.DISK):
            require(administrative['terminal_premise']['state']=='parent_attested_from_original_source_enforcement' and administrative['terminal_premise']['prospective_refusal_may_occur_below_used_limit'] is True,'Exact unsaved exhaustion premise must be explicitly inherited, never guessed')
        return {'retained_ledger':'exact_public_replay','substantive_completed_sessions':substantive,'substantive_closed_rewriting_calls':sum(len(r['rewriting_invocations']) for r in substantive),'frozen_provider_config_sha256':self.policy['provider_config_sha256'],'completed':replay.iterations_completed,'plateau':replay.plateau,'provider_counted':replay.counted_calls,'provider_uncounted':replay.uncounted_calls,'terminal_conditions':[r.value for r in conditions],'lane_disk_unsaved_event_boundary':administrative,'disk_later_du_not_used':True}

    def attempt_states(self,attempts,projection,cid,stopped):
        previous=None;previous_invocations=None;facts=[]
        collector_pin=need(self.pins,'collector_source_pin');require(sha(self.raw(collector_pin))==need(self.pins,'collector_sha256'),'Reviewed collector bytes differ')
        for number,(attempt,triplet) in enumerate(zip(attempts,stopped),1):
            dispatch,stop,release=triplet
            before=self.sealed_json(need(attempt,'before_custody'));after=self.sealed_json(need(attempt,'after_custody'))
            for value,phase in ((before,'before'),(after,'after')):
                require(value['format']=='swdb.lanl17-attempt-control-custody.v2' and value['phase']==phase and value['campaign']==cid and value['attempt']==number,'Original state custody identity differs')
                require(value['source_commit']==self.R['commit'] and value['estimator_sha256']==F6 and value['helper_sha256']==HELPER and value['collector_sha256']==self.pins['collector_sha256'] and value['manifest_identity_sha256']==self.m2['identity_sha256'] and value['policy']==self.m2['policy'],'State custody changes R/M2/policy/control')
                require(value['raw_state_snapshots_transferred'] is False and value['provider_prompts_auth_logs_argv_read'] is False,'Private original state was transferred/read beyond scope')
                expected=need(self.pins,'collector_account');account=value['execution_account']
                require(expected['host']==account['host']=='mbit10' and account['platform']=='linux' and account['uid']==account['effective_uid']==expected['uid'] and type(expected['uid']) is int and expected['uid']>0 and account['user']==expected['user'],'Actual collector host/own-UID custody differs')
                require(value['projection_contract']==PROJECTION_CONTRACT and value['actual_git_worktree_root']==self.m2['source'] and value['actual_project_directory']==str(pathlib.Path(self.m2['source'])/'swdb-project'),'Collector does not bind exact frozen manifest source/project')
            require(before['resume']==dispatch['resume'] and before['baselines_only']==dispatch['baselines_only'],'State guard action differs from dispatch')
            require(after['before_identity_sha256']==before['identity_sha256'] and after['dispatch_identity_sha256']==dispatch['identity_sha256'] and after['stopped_identity_sha256']==stop['identity_sha256'] and after['released']==release,'Released post-state custody differs')
            require(utc(before['checked_utc'])<=utc(dispatch['checked_utc'])<=utc(stop['started_utc'])<utc(stop['ended_utc'])<=utc(release['checked_utc'])<=utc(after['checked_utc']),'Original before/launch/stop/release/after order differs')
            pre,post=before['state'],after['state']
            for control in (before,after):
                inventory=control['invocation_inventory'];require(inventory['names_sha256']==digest(inventory['provider_directories']) and inventory['provider_receipts_prompts_commands_inputs_opened'] is False,'Invocation-name custody differs/private metadata opened')
                if control['state']['present']:
                    known={r['invocation'] for r in control['state']['projection']['ledger']['calls']}
                    if not {r['invocation'] for r in inventory['provider_directories']}<=known:raise Pending('Unpersisted invocation directory requires concrete actual-call/budget admission; no free retry is inferred')
                cfg=next(p['configuration'] for p in self.policy['population'] if p['campaign']==cid)
                if cfg['library'].get('synthesize') or inventory['synthesis_directory_present']:raise Pending('Synthesis invocation metadata needs its separate exact source mapping; selected campaigns declare none')
            corroboration=self.sealed_json(need(attempt,'dispatch_state_corroboration'))
            require(corroboration['format']=='swdb.lanl17-dispatch-state-corroboration.v1' and corroboration['before_identity_sha256']==before['identity_sha256'] and corroboration['dispatch_identity_sha256']==dispatch['identity_sha256'] and corroboration['state_unchanged_under_parent_exclusive_campaign_ownership'] is True and corroboration['basis']=='explicit_parent_attestation_no_other_campaign_writer_between_capture_and_dispatch' and corroboration['parent_checked_pre_dispatch_state_sha256']==(pre['file']['sha256'] if pre['present'] else None),'State guard time-of-check gap lacks explicit parent capture')
            if number==1:require(pre['present'] is False and dispatch['resume'] is False,'Initial campaign state must be absent')
            else:
                require(before['invocation_inventory']==previous_invocations,'Resume directory-existence custody changed after previous release')
                require(pre['present'] is True and previous['present'] is True and pre['file']['sha256']==previous['file']['sha256'] and pre['projection']==previous['projection'],'Resume input is not exact prior released post-state')
                require(pre['projection'].get('stopped') is not True,'ALL prior stopped terminal states are nonresumable, including infrastructure failure')
                require(before['prior_after_identity_sha256']==facts[-1]['after_identity_sha256'],'Resume custody does not bind prior attempt')
                previous_release=stopped[number-2][2]
                if any(previous_release[k]!=0 for k in ('runner_exit_code','public_exit_code','wrapper_exit_code')):
                    unclean=self.sealed_json(need(before,'unclean_resume_admission_pin'))
                    require(unclean['format']=='swdb.lanl17-unclean-resume-admission.v1' and unclean['basis']=='explicit_parent_attestation_from_concrete_attempt_custody' and unclean['accepted'] is True and unclean['source_commit']==self.R['commit'] and unclean['prior_after_identity_sha256']==before['prior_after_identity_sha256'] and unclean['prior_state_sha256']==pre['file']['sha256'],'Unclean resume lacks concrete prior custody admission')
                    require(unclean['unaccounted_opened_calls']==0 and unclean['scientific_source_or_state_changed'] is False,'Lost/unknown provider calls cannot be treated as free retries or patched into frozen state')
            facts.append({'attempt':number,'before_identity_sha256':before['identity_sha256'],'after_identity_sha256':after['identity_sha256'],'before_present':pre['present'],'after_present':post['present'],'prior_stopped_refused':number>1,'resume_scope':'Exact captured nonterminal state only; no terminal infrastructure resumption'})
            previous=post;previous_invocations=after['invocation_inventory']
        require(previous['present'] and previous['file']['sha256']==projection['source_state_file_sha256'] and previous['projection']==projection['state'],'Final released state projection differs from trajectory input')
        return facts

    def outcome_linkage(self,summary,projection,roots):
        cid=summary['campaign'];protocol=self.record(summary['protocol']['id'],'protocol');cfg=next(p['configuration'] for p in self.policy['population'] if p['campaign']==cid)
        require(summary['protocol']['identity_sha256']==protocol['identity_sha256'],'Summary exact execution protocol differs')
        workload_classes={r['class']:r['workload'] for r in summary['workload_classes']}
        baseline_map={(r['role'],cls):(r['candidate'],eid) for r in summary['baselines'] for cls,eid in r['evaluation_ids_by_class'].items()}
        events=summary['paired_estimates']['outcome_accesses'];forecasts={r['id']:r for r in summary['paired_estimates']['records']}
        linked_components={};attested=[]
        for event in events:
            component_id=event['stage']+'.evaluation'
            if component_id not in self.records:
                raw=next((r for r in need(projection,'outcome_accesses_without_component') if r['event_sha256']==digest(event)),None)
                if raw is None:raise Pending('Outcome access lacks selected original component or explicit no-evaluator parent custody: '+component_id)
                require(raw['component_id']==component_id and raw['basis']=='explicit_parent_attestation_of_preflight_or_evaluator_refusal' and raw['accepted'] is True and raw['source_commit']==self.R['commit'],'Absent execution body cannot be treated as completed evidence')
                boundaries={'host_preflight_refused':'after_forecast_before_evaluator','evaluator_failed_without_record':'evaluator_invoked_no_record'}
                require(raw['refusal_class'] in boundaries and raw['refusal_stage']==event['stage'] and raw['refusal_boundary']==boundaries[raw['refusal_class']],'Missing execution requires closed concrete refusal class/stage/boundary')
                custody=self.sealed_json(need(raw,'refusal_custody_pin'))
                require(custody['format']=='swdb.lanl17-outcome-refusal-custody.v1' and custody['basis']=='explicit_parent_attestation_from_original_refusal_source' and custody['source_commit']==self.R['commit'] and custody['event_sha256']==digest(event) and custody['component_id']==component_id,'Original parent refusal custody does not bind the exact outcome boundary')
                require(all(custody[k]==raw[k] for k in ('refusal_class','refusal_stage','refusal_boundary')) and custody['execution_source_sha256']==PINNED_SOURCE_FILES['swdb/campaign_targets.py'],'Original refusal class/stage/source differs')
                require(re.fullmatch('[0-9a-f]{64}',custody['original_refusal_source_sha256']) and custody['original_refusal_source_sha256']==raw['original_refusal_source_sha256'],'Exact original sanitized refusal-source pin missing')
                require(custody['completed_execution_evidence'] is False and custody['raw_logs_or_exception_text_transferred'] is False and utc(custody['checked_utc'])>=utc(event['outcome_access_started_at']),'Refusal custody cannot claim completed evaluator work or transfer raw text')
                attested.append({'event_sha256':digest(event),'component_id':component_id,'refusal_class':raw['refusal_class'],'refusal_stage':raw['refusal_stage'],'refusal_boundary':raw['refusal_boundary'],'refusal_custody_identity':custody['identity_sha256'],'original_refusal_source_sha256':custody['original_refusal_source_sha256'],'scope':'Concrete original parent-attested refusal; no independent completed execution claim'});continue
            component=self.record(component_id,'evaluation');roots.add(component_id)
            request=component['request'];role=request['protocol_role'];workload=request['workload']['id'];subject=self.record(request['candidate'],'candidate')
            require(component['id']==request['id']==component_id and component.get('candidate',request['candidate'])==request['candidate'] and component.get('campaign')==cid and component.get('mode')=='extensa' and component['evidence_kind']=='execution','Execution request/subject/campaign/mode differs')
            require(request['protocol']==protocol['id'] and role in ('baseline','candidate') and not request.get('fixture'),'Execution protocol/role/actual scope differs')
            wrapper=SimpleNamespace(protocol=protocol)
            execution_build=component.get('build') or self.record(request['candidate_build'],'evaluation')['build']
            require(execution_build['binary_sha256']==request['binary']['sha256'],'Execution request/retained guest build bytes differ')
            paired_request=source_pairing_request(wrapper,request,{'build':execution_build})
            source=SimpleNamespace(campaign=cfg);catalog=SimpleNamespace(get=lambda rid,kind:self.record(rid,kind))
            expected=source_pairing_context(source,catalog,paired_request)
            matching=[(context,rid) for context,rid in zip(event['timing_contexts'],event['paired_estimates']) if request_identity(context)==request_identity(expected)]
            require(len(matching)==1,'Execution component does not match exact source-derived event context')
            context,rid=matching[0];forecast=forecasts[rid]
            require(request_identity(forecast['timing_context'])==request_identity(expected) and utc(forecast['estimated_at'])<utc(event['outcome_access_started_at']),'Execution lacks actual preceding immutable forecast')
            require(expected['subject']['artifact_sha256']==subject['artifact']['sha256'],'Exact execution artifact differs')
            if component.get('outcome',{}).get('state')=='complete':
                binding=component['context']['protocol_binding'];definition=self.record(workload,'workload')['definition']
                require(binding['protocol']==protocol['id'] and binding['frozen_sha256']==protocol['identity_sha256'] and binding['role']==role and binding['workload_id']==workload and binding['workload_sha256']==self.record(workload,'workload')['identity_sha256'],'Component protocol/workload binding differs')
                require(binding['settings_sha256']==digest(protocol['settings']),'Component exact frozen settings differ')
                require(component['context']['candidate_sha256']==subject['artifact']['sha256'] and component['context']['workload']['canonical_sha256']==definition['canonical_sha256'] and component['context']['sources']==[0],'Actual component artifact/input/source facts differ')
            linked_components[component_id]={'record_sha256':digest(component),'event_sha256':digest(event),'forecast':rid,'subject':subject['id'],'workload':workload,'role':role}
        def aggregate(eid,subject,workload,role):
            value=self.record(eid,'evaluation');roots.add(eid)
            require(value.get('mode')=='extensa' and value.get('campaign')==cid and value['candidate']==subject and value['evidence_kind']=='execution' and value['outcome']['state']=='complete','Aggregate actual subject/campaign/completion differs')
            require(value['request']['protocol']==protocol['id'] and value['request']['protocol_role']==role and value['context']['workload']['id']==workload,'Aggregate exact class/workload/protocol/role differs')
            components=value['component_evaluations'];require(components,'Aggregate has no real component execution')
            require(value['request']['evaluations']==[r['evaluation'] for r in components],'Aggregate component ID inventory differs')
            for entry in components:
                component=self.record(entry['evaluation'],'evaluation');require(digest(component)==entry['sha256'] and entry['evaluation'] in linked_components,'Aggregate component/digest/event linkage missing')
                link=linked_components[entry['evaluation']];require((link['subject'],link['workload'],link['role'])==(subject,workload,role),'Aggregate component exact role/class differs')
                require(value['context']['component_contexts'][component['id']]==component['context'] and value['context']['component_bindings'][component['id']]==component['context'].get('execution_binding'),'Aggregate copied context/binding differs')
                require(digest(value['build'])==digest(component['build']),'Aggregate/component build differs')
                require(not component.get('component_evaluations') and component['outcome']['state']=='complete' and component['correctness']['state']=='passed','Aggregate component is nested/incomplete/incorrect')
            require(value['timing']==[r for e in components for r in self.record(e['evaluation'],'evaluation')['timing']] and value['correctness']['checks']==[r for e in components for r in self.record(e['evaluation'],'evaluation')['correctness']['checks']],'Aggregate timed/correctness rows differ')
        for (role,cls),(subject,eid) in baseline_map.items():aggregate(eid,subject,workload_classes[cls],'baseline')
        iterations=summary['iterations']+([summary['interrupted_iteration']] if summary.get('interrupted_iteration') else [])
        for iteration in iterations:
            for candidate in iteration['candidates']:
                if not candidate.get('id'):continue
                selection=next((r for r in candidate.get('comparisons',[]) if r['baseline_role']==cfg['base_source']),None)
                require(candidate.get('selection')==({'lower':selection['lower'],'verdict':selection['verdict'],'ratio':selection['ratio']} if selection else None),'Candidate timing-only selection does not match base-source comparison')
                for row in candidate.get('comparisons',[]):
                    role=row['baseline_role'];cls=candidate['class'];subject,baseline=baseline_map[(role,cls)]
                    comparison=self.record(row['comparison'],'comparison_result');require(row['baseline_evaluation']==comparison['baseline_evaluation']==baseline,'Comparison is not the retained exact class/role baseline')
                    aggregate(comparison['candidate_evaluation'],candidate['id'],workload_classes[cls],'candidate')
                    require(comparison['evaluation_identities']=={baseline:digest(self.record(baseline,'evaluation')),comparison['candidate_evaluation']:digest(self.record(comparison['candidate_evaluation'],'evaluation'))},'Comparison original evaluation identity map differs')
                    require(comparison['metrics']['workload']==workload_classes[cls],'Comparison exact class workload differs')
                    require(comparison['protocol']==protocol['id'] and comparison['protocol_sha256']==protocol['identity_sha256'] and comparison['request']['baseline_evaluation']==baseline and comparison['request']['candidate_evaluation']==comparison['candidate_evaluation'],'Comparison request/frozen protocol differs')
                    verdict={'gain':'gain','no_gain':'no_gain','inconclusive':'inconclusive','regression':'no_gain'}.get(comparison['decision']['state'])
                    require(verdict is not None and row['verdict']==verdict and row['lower']==row['ratio'],'Gem5 exact point timing-only verdict/lower differs')
                    require(comparison.get('mode')=='extensa' and comparison.get('campaign')==cid and comparison['metrics']['roi_speedup']==row['ratio'],'Comparison actual ratio/campaign differs')
                    roots.update((row['comparison'],comparison['candidate_evaluation'],baseline))
                    for field in ('baseline_sha256','candidate_sha256'):
                        if field in comparison:require(comparison[field]==digest(self.record(comparison['baseline_evaluation' if field=='baseline_sha256' else 'candidate_evaluation'],'evaluation')),'Comparison retained evaluation digest differs')
        return {'linked_execution_components':len(linked_components),'class_baselines':len(baseline_map),'nonvacuous_baseline_forecast_checks':True,'absent_component_attestations':attested,'interrupted_roots_included':bool(summary.get('interrupted_iteration'))}

    def trajectory(self,row):
        cid=need(row,'campaign');projection=self.sealed_json(need(row,'projection'))
        require(projection['format']=='swdb.lanl17-trajectory-audit-projection.v2' and projection['campaign']==cid and projection['source_commit']==self.R['commit'] and projection['estimator_sha256']==F6 and projection['manifest_sha256']==self.m2['identity_sha256'],'Actual trajectory projection binding differs')
        summary=self.record(cid+'.summary','campaign_summary');_summary_checked(summary)
        require(projection['summary_sha256']==digest(summary),'Original supplied summary identity differs')
        require(summary in self.report['summaries'],'Actual summary absent from final public snapshot')
        index=projection['record_index'];require(projection['record_index_sha256']==digest(index),'Full compact record index differs')
        validation=projection['public_validation'];require(validation['returncode']==0 and validation['records_index_sha256']==digest(index) and validation['summary_sha256']==digest(summary),'Original full-catalog public validation binding missing')
        for key in ('stdout_sha256','stderr_sha256','source_state_file_sha256'):
            value=projection[key] if key=='source_state_file_sha256' else validation[key]
            require(re.fullmatch('[0-9a-f]{64}',value) is not None,'Exact original raw compact source pin missing')
        state=projection['state'];require(state['campaign']==cid and state['campaign_sha256']==summary['campaign_file']['sha256'],'Original state/config identity differs')
        require(state['iterations']==[project_iteration(r) for r in summary['iterations']],'Original completed state projection differs from summary')
        require(state['setup_calls']==project_calls(summary['setup']['provider_calls']),'Original setup calls differ')
        require(state['stop_detail_sha256']==digest(summary.get('stop_detail')),'Original stop detail hash differs')
        ledger=state['ledger'];completed=[r for r in ledger['iterations'] if r['outcome'] in ('improved','not_improved')]
        require(ledger['iterations_completed']==len(completed)==len(summary['iterations'])==summary['budgets']['used']['iterations'],'Completed iteration accounting differs')
        require([r['index'] for r in completed]==[r['index'] for r in summary['iterations']]==list(range(1,len(completed)+1)),'Completed iteration indices differ or contain padding')
        require(summary['budgets']['limits']=={k:BUDGETS[k] for k in summary['budgets']['limits']} and set(summary['budgets']['limits'])==set(BUDGETS),'Summary scientific limits differ')
        interrupted=state.get('interrupted_iteration');require(interrupted==(project_iteration(summary['interrupted_iteration']) if summary.get('interrupted_iteration') else None),'Interrupted iteration evidence differs')
        for iteration in summary['iterations']:
            require(utc(iteration['started'])<utc(iteration['ended']),'Completed iteration has no actual end')
            require(iteration['improved_classes'] or next(r for r in completed if r['index']==iteration['index'])['outcome']=='not_improved','Ledger/selection improvement differs')
        attempts=need(row,'attempts');require(attempts,'Actual attempt records missing');stopped=[]
        for number,attempt in enumerate(attempts,1):
            dispatch=self.sealed_json(need(attempt,'dispatch'));stop=self.sealed_json(need(attempt,'stopped'));release=self.sealed_json(need(attempt,'release_custody'))
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
        attempt_custody=self.attempt_states(attempts,projection,cid,stopped)
        final_dispatch,final_stop,final_release=stopped[-1]
        final_success=final_stop['runner_exit_code']==final_stop['public_exit_code']==final_release['wrapper_exit_code']==0 and final_stop['infrastructure_error'] is None and final_dispatch['baselines_only'] is False
        require(summary['stop_reason']==state.get('stop_reason') and state.get('stopped') is True,'Summary does not bind a terminal original state')
        normal=summary['stop_reason'] in NORMAL and final_success
        if summary['stop_reason']=='max_iterations':require(len(completed)==BUDGETS['max_iterations'],'Max-iteration terminal lacks actual complete rows')
        if summary['stop_reason']=='plateau':require(ledger['plateau']>=BUDGETS['plateau_iterations'],'Plateau terminal lacks ledger exhaustion')
        accounting=self.retained_ledger(summary,state,projection)
        selection=self.selection_replay(summary)
        pairing_policy={'format':LEDGER,'campaign':cid,'version':VERSION,'estimator_sha256':F6,'enabled':True,'configuration':{'enabled':True},'fixture_model':None}
        forecasts=summary['paired_estimates']['records'];events=summary['paired_estimates']['outcome_accesses']
        for forecast in forecasts:
            require(forecast['policy_sha256']==digest(pairing_policy),'Campaign-local pairing policy differs; it is not the public agreement policy hash')
            require(utc(self.policy['frozen_at'])<utc(forecast['estimated_at']),'Forecast precedes the prospective agreement freeze')
        for event in events:require(utc(event['outcome_access_started_at'])>self.published,'An outcome preceded recorded freeze publication')
        roots=set();artifacts_seen=set();candidate_rows=0;prematerialization_refusals=0;interrupted_roots=set()
        for baseline in summary['baselines']:
            roots.add(baseline['candidate']);roots.update(baseline['evaluation_ids_by_class'].values())
            for eid in baseline['evaluation_ids_by_class'].values():require(self.record(eid,'evaluation')['candidate']==baseline['candidate'] and self.record(eid,'evaluation').get('mode')=='extensa' and self.record(eid,'evaluation').get('campaign')==cid,'Baseline timing subject/mode/campaign differs')
        for iteration in summary['iterations']+([summary['interrupted_iteration']] if summary.get('interrupted_iteration') else []):
            for candidate in iteration['candidates']:
                candidate_rows+=1
                if not candidate.get('id'):
                    prematerialization_refusals+=1;continue  # Actual refusal before materialization; no artifact/pair invented.
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
        linkage=self.outcome_linkage(summary,projection,roots)
        reached=self.closure(roots,index)
        interrupted_roots={r['id'] for r in summary.get('interrupted_iteration',{}).get('candidates',[]) if r.get('id')}
        for candidate in summary.get('interrupted_iteration',{}).get('candidates',[]):
            if (candidate.get('certification') or {}).get('record'):interrupted_roots.add(candidate['certification']['record'])
            for c in candidate.get('comparisons',[]):
                comparison=self.record(c['comparison'],'comparison_result');interrupted_roots.update((c['comparison'],comparison['baseline_evaluation'],comparison['candidate_evaluation']))
        omitted={r['id'] for r in summary.get('interrupted_iteration',{}).get('candidates',[]) if r.get('id')}
        if omitted:
            extra=self.sealed_json(need(row,'interrupted_selected_body_custody'))
            require(extra['format']=='swdb.lanl17-interrupted-selected-bodies.v1' and extra['campaign']==cid and set(extra['candidate_ids'])==omitted and extra['record_index_sha256']==digest(index) and extra['public_full_validation_returncode']==0 and extra['public_finalize_exported_these_candidates'] is False,'Interrupted selected bodies must be separately pinned/validated; final helper does not export them')
            require(set(extra['root_ids'])==interrupted_roots and set(extra['record_ids'])==self.closure(interrupted_roots,index),'Interrupted selected closure incomplete')
        exported_candidates=set()
        for pin in need(row,'public_candidate_exports'):
            exported=self.json(pin);require(exported['format']=='swdb.campaign-export.v1' and exported['campaign']==cid and exported['dry_run'] is False,'Actual candidate export receipt differs')
            require(all(c['level']!='rejected' for c in exported['candidates']),'Rejected candidate was promoted/exported')
            exported_candidates.update(c['id'] for c in exported['candidates'])
            for record in exported['records']:
                value=self.record(record['id'],record['kind']);require(self.record_pins[record['id']]['sha256']==record['sha256'],'Public exported closure bytes differ')
        require(exported_candidates==set(need(projection,'public_export_candidate_ids')),'Original public selected-candidate export inventory is missing/different')
        selected=self.sealed_json(need(row,'public_candidate_export_selection_custody'))
        require(selected['format']=='swdb.lanl17-original-public-candidate-selection-custody.v1' and selected['basis']=='explicit_parent_check_of_original_28d_non_rejected_completed_selection' and selected['source_commit']==self.R['commit'] and selected['helper_sha256']==HELPER and selected['campaign']==cid and selected['summary_sha256']==digest(summary) and selected['accepted'] is True,'Original public selected-candidate choice requires concrete parent selection custody')
        require(set(selected['candidate_ids'])==exported_candidates and selected['selection_completeness_independently_derived_by_auditor'] is False,'Public export selection completeness is explicitly inherited; do not infer it from supplied IDs')
        completed_materialized={r['id'] for it in summary['iterations'] for r in it['candidates'] if r.get('id')}
        require(set(selected['completed_materialized_candidate_ids'])==completed_materialized and selected['original_named_candidate_ids']==sorted(exported_candidates) and exported_candidates<=completed_materialized,'Parent original named selection must bind the actual completed candidate population; interrupted candidates remain separate')
        interrupted_index=interrupted.get('index') if interrupted else None
        return {'campaign':cid,'attempts':len(attempts),'lanes':[d['node'] for d,s,r in stopped],'terminal_reason':summary['stop_reason'],'normal_terminal':normal,'substantive_completed_iterations':bool(completed) and len(accounting['substantive_completed_sessions'])==len(completed),'completed_iterations':len(completed),'interrupted_iteration':interrupted_index,'candidate_rows':candidate_rows,'prematerialization_refusal_rows':sum(1 for it in summary['iterations']+([summary['interrupted_iteration']] if summary.get('interrupted_iteration') else []) for candidate in it['candidates'] if not candidate.get('id')),'distinct_materialized_artifact_hashes':len(artifacts_seen),'selected_closure_records':len(reached),'outcome_accesses':len(events),'prior_exposure_forecasts':sum(bool(f['timing_context'].get('prior_outcome_exposure')) for f in forecasts),'eligible_pairs':0,'final_attempt_succeeded':final_success,'terminal_infrastructure_summary_not_resumable':summary['stop_reason']=='infrastructure_failure','source_of_completion':'Pinned original per-attempt state/ledger, not summary existence','attempt_state_custody':attempt_custody,'retained_accounting':accounting,'timing_selection_replay':selection,'exact_outcome_linkage':linkage,'public_candidate_export_selection_boundary':{'basis':selected['basis'],'receipt_identity':selected['identity_sha256'],'independently_derived_completeness':False}}
    def audit(self):
        global CURRENT_R
        CURRENT_R=self.R['commit'];custody=self.custody()
        dependency_admission=self.dependencies()
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
        return {'format':'swdb.lanl17-selected-read-only-audit.v2','audited_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'actual_execution':'Parent-approved compact/Git reading only; no experiment rerun','source_C':C,'final_R':self.R,'estimator_sha256':F6,'strict_additive_custody':custody,'final_dependency_admission_boundaries':dependency_admission,'freeze':freeze,'campaigns':trajectories,'four_normal_substantive_trajectories':trajectory_complete,'recorded_blind_order_verified':blind,'public_counts':expected['counts'],'rank':expected['rank'],'top3':expected['top3'],'gate':expected['gate'],'recommendation':expected['recommendation'],'selection_policy':expected['selection_policy'],'custody_state':'accepted_selected_custody','actual_ticket17_evidence_state':'ready_for_parent_review' if trajectory_complete and blind else 'incomplete_actual_trajectory_or_order','generation_dependency_facts':[{'campaign':plan['campaign'],'workloads':[{'id':w['id'],'family':w['generation']['family'],'explicit_generator_seed':(w['generation']['generator'] or {}).get('seed'),'seed_missing_means_unknown':True} for w in plan['workloads']]} for plan in self.policy['population']],'dependency_admission':'Zero eligible application components; four campaign IDs are not independent clusters','numerical_agreement':'unsupported; zero eligible pairs; no D30 achievement','limits':'Public full-catalog validation and parent-accepted raw projections remain required; receipt-order checks do not prove global historical blindness or live processes.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repository',required=True);parser.add_argument('--accepted-pins',required=True);parser.add_argument('--accepted-pins-sha256',required=True)
    args=parser.parse_args();path=pathlib.Path(args.accepted_pins)
    require(path.is_absolute() and '..' not in path.parts and path.is_file() and all(not x.is_symlink() for x in (path,*path.parents)) and path.stat().st_size<=8*1024*1024,'Bounded accepted local pin file without symlink components required')
    raw=path.read_bytes();require(sha(raw)==args.accepted_pins_sha256,'Explicit parent-accepted pin file SHA differs')
    pins=strict_json(raw);require(pins['format']=='swdb.lanl17-selected-admission-pins.v2','Accepted pins format differs');receipt_seal(pins,pins['identity_sha256'])
    require(pins['parent_approved_actual_inputs'] is True and pins['fixtures_or_replays_allowed'] is False,'Actual parent-approved evidence only')
    for key in ('final_ticket11_acceptance','final_ticket14_acceptance'):
        require(key in pins and pins[key]['accepted'] is True and re.fullmatch('[0-9a-f]{64}',pins[key]['receipt_identity']) is not None,'Explicit final dependency admission pending')
    result=Reader(args.repository,pins).audit();result['accepted_pins_identity_sha256']=pins['identity_sha256'];result['auditor_sha256']=sha(pathlib.Path(__file__).read_bytes());result['identity_sha256']=digest(result)
    print(json.dumps(result,indent=2));return 0 if result['actual_ticket17_evidence_state']=='ready_for_parent_review' else 2
if __name__=='__main__':
    try:sys.exit(main())
    except Pending as exc:print(json.dumps({'state':'pending','reason':str(exc),'actual_campaign_admission':False}));sys.exit(2)
    except (Refused,KeyError,TypeError,ValueError,RuntimeError,yaml.YAMLError,subprocess.SubprocessError,OSError) as exc:
        print(json.dumps({'state':'refused','reason':str(exc) if isinstance(exc,(Refused,Pending)) else type(exc).__name__,'actual_campaign_admission':False}));sys.exit(3)

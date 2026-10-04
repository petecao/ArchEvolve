#!/usr/bin/env python3
"""Pure T17 command preparation; never launches work. Dated 2026-09-27 ET."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('t17_plan_contract', HERE/'validate_plan.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)

# Every option with a CLI default is explicitly bound, so defaults cannot create
# an empirical allowance. These fields remain absent until T15 evidence exists.
REQUIRED = ('python', 'runtime', 'configuration', 'runs_dir', 'records', 'lane',
            'workload', 'protocol', 'primary_build', 'diagnostic_build',
            'total_seconds', 'checkpoint_seconds', 'run_seconds', 'diagnostic_seconds',
            'memory_gib', 'storage_gib', 'batch_storage_gib', 'verification_ticks',
            'owned_cleanup_ledger', 'owned_cleanup_binding')
LIMITS = {'total_seconds': (1,43200), 'checkpoint_seconds': (1,3600),
          'run_seconds': (1,3600), 'diagnostic_seconds': (180,600),
          'memory_gib': (1,48), 'storage_gib': (1,10),
          'batch_storage_gib': (1,40), 'verification_ticks': (1,10**15)}


def series_argv(row, bindings):
    """Render reviewed API wiring only; binding values do not authorize dispatch."""
    missing = [key for key in REQUIRED if bindings.get(key) is None]
    if missing:
        raise ValueError('unresolved operator bindings: '+', '.join(missing))
    if row['role'] not in ('baseline','candidate') or row['accelerated'] != (row['role']=='candidate'):
        raise ValueError('fixed baseline/candidate treatment changed')
    for name in ('primary_build','diagnostic_build'):
        if bindings[name] != row[name]['id']:
            raise ValueError('retained build differs from the fixed series')
    for key in ('python','runtime','configuration','runs_dir','records','owned_cleanup_ledger'):
        if not isinstance(bindings[key],str) or not Path(bindings[key]).is_absolute():
            raise ValueError('operator path must be absolute: '+key)
    if type(bindings['lane']) is not int or bindings['lane'] not in (0,1):
        raise ValueError('invalid explicit lane')
    for name,(low,high) in LIMITS.items():
        if type(bindings[name]) is not int or not low <= bindings[name] <= high:
            raise ValueError('explicit stage bound exceeds existing CLI contract: '+name)
    for name in ('workload','protocol','owned_cleanup_binding'):
        if not isinstance(bindings[name],str) or not bindings[name]:
            raise ValueError('empty required identity: '+name)
    args = [bindings['python'], '-s', '-B', str(Path(bindings['runtime'])/'scripts/bfs_simulator_series.py'),
            '--id',row['id'],'--candidate',row['candidate']['id'],
            '--build-evaluation','bfs-dx100-build-20260925-a2',
            '--protocol-role',row['role'],'--trace-transport','gem5-gzip.v1',
            '--verifier','dx100.bfs.verifier.v2','--require-capacity']
    for name in REQUIRED:
        if name not in ('python','runtime'):
            args += ['--'+name.replace('_','-'), str(bindings[name])]
    if row['accelerated']:
        args += ['--accelerated']
    return args


def preview(value):
    contract.validate(value)
    return {'created':'2026-09-27','state':'fixed_operator_dependencies_unresolved',
            'dispatch_allowed':False,'new_allocation':False,'execution_implemented':False,
            'aggregate_seconds':value['budget_derivation']['aggregate_seconds'],
            'aggregate_retained_bytes':value['budget_derivation']['aggregate_retained_bytes'],
            'original_outer_deadline':value['budget_derivation']['original_outer_deadline'],
            'diagnostic_prerequisite':value['remaining_diagnostic_prerequisite'],
            'series':[{'id':row['id'],'family':row['family'],'role':row['role'],
                       'candidate':row['candidate'],'primary_build':row['primary_build'],
                       'diagnostic_build':row['diagnostic_build'],
                       'required_runtime_bindings':list(REQUIRED)} for row in value['series']],
            'remaining_gates':value['remaining_bindings']+[
                'Whole next series plus remaining shared cleanup fits the original allocated clock',
                'Fresh immutable runtime, Linux proof, host lease/capacity and all artifact bindings',
                'Actual freeze result and paired-package correspondence before comparison/retrieval'],
            'scope':'Command construction only; no subprocess, provider, lease, compiler, or evaluator call.'}


if __name__ == '__main__':
    print(json.dumps(preview(json.loads((HERE/'manifest-template.json').read_text())),indent=2))

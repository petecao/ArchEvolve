#!/usr/bin/env python3
"""Bounded real Callgrind ROI-order control experiment. Updated 2026-09-25.

The old order must reproduce invalid counters and the fixed order must pass with
one and four OpenMP threads. This is collector validation, not BFS gain evidence.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, profile
from swdb.bfs_profiling import parse_callgrind
from swdb.cli import Failure, _require_valid
from bfs_diagnostic_driver import preflight, bounded

SOURCE = r'''#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <omp.h>
#include <valgrind/callgrind.h>
volatile uint64_t values[1024];
int main(int argc, char **argv) {
  const bool old_order = argc > 1 && argv[1][0] == 'o';
  for (int i = 0; i < 1024; ++i) values[i] = i;
  CALLGRIND_START_INSTRUMENTATION;
  if (old_order) { CALLGRIND_ZERO_STATS; }
  #pragma omp parallel for schedule(static)
  for (int i = 0; i < 1024; ++i)
    for (int j = 0; j < 64; ++j) values[i] += j;
  if (old_order) {
    CALLGRIND_STOP_INSTRUMENTATION;
    CALLGRIND_DUMP_STATS;
  } else {
    CALLGRIND_DUMP_STATS;
    CALLGRIND_STOP_INSTRUMENTATION;
  }
  uint64_t sum = 0;
  for (int i = 0; i < 1024; ++i) sum += values[i];
  printf("%llu\n", static_cast<unsigned long long>(sum));
  return sum == 2588160 ? 0 : 2;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=ROOT/'records')
    parser.add_argument('--lane', required=True)
    args = parser.parse_args()
    store = _require_valid(args.records)
    lane = preflight(args, store, profile)
    if not args.build_dir.resolve().is_relative_to('/data1/yanruj'):
        raise RuntimeError('build directory must be under /data1/yanruj')
    raw = args.runs_dir/(args.id+'.probe'); raw.mkdir(parents=True, exist_ok=False)
    build = args.build_dir; build.mkdir(parents=True, exist_ok=False)
    compiler = shutil.which('g++'); collector = shutil.which('valgrind')
    if not compiler or not collector: raise RuntimeError('existing g++ and valgrind are required')
    receipt = {'id':args.id, 'lane':lane, 'source_sha256':None,
               'gain_claim':False, 'purpose':'collector ROI-order control', 'runs':[]}
    def save(): (raw/'receipt.json').write_text(json.dumps(receipt, indent=2))
    def execute(name, command, seconds, env=None):
        profile._verified_lane(store.get('mbit10', 'machine'), args.lane)
        entry = {'name':name, 'argv':command, 'timeout_seconds':seconds, 'state':'running'}
        receipt.setdefault('commands', []).append(entry)
        save()
        output, error = raw/(name+'.stdout'), raw/(name+'.stderr')
        try: result = bounded(command, output, error, seconds, cwd=ROOT, env=env)
        except BaseException:
            entry['state'] = 'interrupted_or_timeout'; save(); raise
        entry.update(result, state='complete' if result['returncode']==0 else 'failed',
                     stdout_sha256=artifacts.file_hash(output), stderr_sha256=artifacts.file_hash(error)); save()
        if result['returncode']: raise RuntimeError(f'{name} returned {result["returncode"]}; see {raw}')
        return output.read_text().strip()
    source = build/'probe.cc'; source.write_text(SOURCE)
    receipt['source_sha256'] = artifacts.file_hash(source)
    receipt['compiler_version'] = execute('compiler-version', [compiler, '--version'], 15)
    receipt['collector_version'] = execute('collector-version', [collector, '--version'], 15)
    binary = build/'probe'
    execute('build', [compiler, '-std=c++11', '-O2', '-g', '-fopenmp', str(source), '-o', str(binary)], 60)
    receipt['binary_sha256'] = artifacts.file_hash(binary)
    for threads in (1, 4):
        for order in ('old', 'fixed'):
            name = f'{order}-{threads}'
            base = raw/(name+'.callgrind')
            command = [collector, '--tool=callgrind', '--cache-sim=yes', '--collect-atstart=yes',
                       '--instr-atstart=no', '--separate-threads=no', '--I1=32768,8,64',
                       '--D1=49152,12,64', '--LL=25165824,12,64', f'--callgrind-out-file={base}', str(binary), order]
            output = execute(name, command, 45, dict(os.environ, OMP_NUM_THREADS=str(threads), OMP_DYNAMIC='FALSE'))
            files = sorted(p for p in raw.glob(base.name+'*') if 'desc: Trigger: Client Request' in p.read_text())
            if len(files) != 1: raise RuntimeError('expected exactly one explicit client dump')
            file = files[0]
            row = {'order':order, 'threads':threads, 'checksum':int(output), 'raw_artifact':str(file),
                   'raw_sha256':artifacts.file_hash(file), 'header':[line for line in file.read_text().splitlines()
                        if line.startswith(('events:', 'summary:', 'totals:'))]}
            try:
                row['events'] = parse_callgrind(file, require_totals=True)
                row['state'] = 'valid'
            except Failure as error:
                row.update(state='invalid', reason=str(error))
            receipt['runs'].append(row); save()
            if row['checksum'] != 2588160: raise RuntimeError('control checksum failed')
            if order == 'old' and row['state'] != 'invalid': raise RuntimeError('old-order invalidity did not reproduce')
            if order == 'fixed' and (row['state'] != 'valid' or row['events'].get('Dr', 0) < 65536
                                    or row['events'].get('Dw', 0) < 65536):
                raise RuntimeError('fixed-order combined-thread reference coverage failed')
    receipt['state'] = 'passed'; save()
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__': main()

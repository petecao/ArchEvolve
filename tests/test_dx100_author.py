"""Actual C++ author-ROI wrapper contract; not simulator evidence. Updated: 2026-09-25."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from swdb.dx100_author import driver


def test_author_events_remain_and_pre_roi_scope_is_not_full_call_time(tmp_path):
    compiler = shutil.which('clang++') or shutil.which('g++')
    if not compiler:
        pytest.skip('C++ compiler unavailable')
    model = tmp_path / 'model'
    header = model / 'include/gem5/m5ops.h'; header.parent.mkdir(parents=True)
    header.write_text('''#pragma once
inline uint64_t m5_rpns(){static uint64_t ticks=0;return ++ticks;}
inline void m5_checkpoint(int,int){}
inline void m5_work_begin(int,int){}
inline void m5_work_end(int,int){}
inline void m5_reset_stats(uint64_t,uint64_t){std::puts("REAL_RESET");}
inline void m5_dump_stats(uint64_t,uint64_t){std::puts("REAL_DUMP");}
inline void m5_exit(int){std::puts("AUTHOR_ROI_EXIT");}
''')
    source = tmp_path / 'author.cc'
    source.write_text('''#include <vector>
using NodeID=int;
struct CLApp { CLApp(int,char**,const char*){} bool ParseArgs(){return true;} int start_vertex(){return 0;} bool logging_en(){return false;} };
struct Graph { int num_nodes()const{return 3;} };
struct Builder { Builder(CLApp&){} Graph MakeGraph(){return Graph();} };
std::vector<int> DOBFS(const Graph&,int,bool) {
  ::swdb_profile::Scope enclosing(0);
  m5_work_begin(0,0);m5_reset_stats(0,0);
  {::swdb_profile::Scope traversal(1);}
  m5_dump_stats(0,0);m5_work_end(0,0);m5_exit(0);
  return {0,0,1};
}
bool BFSVerifier(const Graph&,int,const std::vector<int>& p){return p[0]==0 && p[1]==0 && p[2]==1;}
int main(int,char**){return 99;}
''')
    runtime = Path(__file__).resolve().parents[1] / 'tools/bfs_profile/gem5_runtime.hpp'
    text = driver(source, model, 'DOBFS', {'regions': [{}, {}], 'runtime': {'path': str(runtime)}})
    generated = tmp_path / 'generated.cc'; generated.write_text(text)
    binary = tmp_path / 'binary'
    built = subprocess.run([compiler, '-std=c++11', str(generated), '-o', str(binary)], capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stderr
    run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
    assert run.returncode == 0, run.stderr
    assert run.stdout.count('REAL_RESET') == run.stdout.count('REAL_DUMP') == run.stdout.count('AUTHOR_ROI_EXIT') == 1
    assert run.stdout.index('AUTHOR_ROI_EXIT') < run.stdout.index('SWDB_DX100_REGIONS') < run.stdout.index('Verification: PASS')
    report = json.loads(next(line.split(' ', 1)[1] for line in run.stdout.splitlines() if line.startswith('SWDB_DX100_REGIONS ')))
    assert report['errors'] == 0
    assert report['regions'][0] == {'index': 0, 'inclusive_ns': 0, 'exclusive_ns': 0, 'invocations': 0}
    assert report['regions'][1]['invocations'] == 1 and report['regions'][1]['inclusive_ns'] > 0

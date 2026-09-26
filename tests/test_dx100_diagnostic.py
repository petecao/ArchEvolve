"""Simulated interval accounting contracts; not gem5 acceptance. Updated: 2026-09-25."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from swdb.cli import Failure
from swdb.dx100_diagnostic import counters


def test_simulated_nested_guards_report_inclusive_and_exclusive_elapsed(tmp_path):
    compiler = shutil.which('clang++') or shutil.which('g++')
    if not compiler:
        pytest.skip('C++ compiler unavailable')
    runtime = Path(__file__).resolve().parents[1] / 'tools/bfs_profile/gem5_runtime.hpp'
    source = tmp_path / 'diagnostic.cc'
    source.write_text('#include <cstdint>\nuint64_t current=0;\nuint64_t m5_rpns(){current+=10;return current;}\n'
        '#define SWDB_REGION_COUNT 2\n#include ' + json.dumps(str(runtime)) + '\n'
        'int main(){swdb_profile::start();{swdb_profile::Scope a(0);{swdb_profile::Scope b(1);}}'
        'swdb_profile::stop();std::puts("SWDB_DX100_ROI_SEALED");swdb_profile::write();}\n')
    binary = tmp_path / 'diagnostic'
    compiled = subprocess.run([compiler, '-std=c++11', str(source), '-o', str(binary)], capture_output=True, text=True, timeout=30)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(binary)], capture_output=True, text=True, check=True, timeout=10)
    log = tmp_path / 'output'
    log.write_text(result.stdout)
    rows = counters(log, 2)
    assert rows == [{'index': 0, 'inclusive_ns': 30, 'exclusive_ns': 20, 'invocations': 1},
                    {'index': 1, 'inclusive_ns': 10, 'exclusive_ns': 10, 'invocations': 1}]


@pytest.mark.parametrize('defect', ['unsealed', 'double', 'bad_clock', 'bad_count', 'exclusive'])
def test_simulated_counter_report_rejects_incompatible_observations(tmp_path, defect):
    row = {'index': 0, 'inclusive_ns': 20, 'exclusive_ns': 10, 'invocations': 1}
    data = {'format': 'swdb.dx100.regions.v1', 'clock': 'm5_rpns', 'errors': 0, 'regions': [row]}
    if defect == 'bad_clock': data['clock'] = 'wall'
    if defect == 'bad_count': data['regions'] = []
    if defect == 'exclusive': row['exclusive_ns'] = 30
    text = 'SWDB_DX100_REGIONS ' + json.dumps(data) + '\n'
    if defect != 'unsealed': text = 'SWDB_DX100_ROI_SEALED\n' + text
    if defect == 'double': text *= 2
    log = tmp_path / 'output'; log.write_text(text)
    with pytest.raises(Failure): counters(log, 1)

"""Coverage literal prefilters preserve evidence and bound regex work, 2026-09-27."""
import gzip
import random
from pathlib import Path
import subprocess
import types
from swdb import dx100_coverage as coverage


def reference():
    # Fixed pre-optimization implementation, not another implementation of the
    # literal filters under test. Pure local Git read; no remote or simulator.
    source=subprocess.check_output(['git','show','07baead5fe5cf3718e18e1d2313db6899f2638c8:swdb/dx100_coverage.py'],text=True)
    module=types.ModuleType('original_coverage');exec(compile(source,'original_coverage','exec'),module.__dict__)
    return module


def test_mixed_stream_matches_original_including_unicode_boundaries_and_collisions(tmp_path):
    events=[
      'I[0] Start [INSTR[opcode(INDIR_ST_VECTOR) datatype(INT32) baseAddr(0x4000)]]',
      'I[0] recvData: 2 entries received for addr(0x8000)',
      'I[0] recvData: new_data[2] = SPD[0][0] = 7/7/0.0!',
      'I[0] recvData: new_data[2] = SPD[0][1] = 9/-9/0.0!',
      'R[0] executeInstruction: tile size: 16384',
      'R[0] executeInstruction: tile size: 7',
      'I[0] End [INSTR] S[0] End [INSTR]',
      'S[0] End [INSTR]', 'R[0] End [INSTR]', 'A[0] End [INSTR]',
      'XI[0] End [not-a-word-boundary]',
      'I[0] recvData: new_data[2] = SPD[0][1] = 9/9/0.0! R[0] executeInstruction: tile size: 3',
      'éI[0] End [not-a-word-boundary]', '✓I[0] End [unicode-boundary]',
      'R[0] executeInstruction: tile size: nope', 'I[0] Start [not-store]',
      'I[0] recvData: new_data[2] = SPD[0][1] = 9/10/0.0!',
      'arbitrary unrelated diagnostic payload '*20]
    rng=random.Random(91)
    lines=['SWDB_BFS_PARENT_STORAGE address=4000 count=20 element_bytes=4\n']
    lines += [f'{100+i}: system.maa: {event}\n' for i,event in enumerate(events)]
    for _ in range(1000):lines.append(f'{rng.choice([99,100,150,200,201])}: {rng.choice(events)}\n')
    log=tmp_path/'stdout';log.write_text(''.join(lines))
    values={'simTicks':'100','finalTick':'200'}
    old=reference()
    assert coverage.observe(log,values,16384)==old.observe(log,values,16384)
    trace=tmp_path/'trace.gz';trace.write_bytes(gzip.compress(''.join(lines[1:]).encode()))
    log.write_text(lines[0]+'Verification: PASS\n')
    assert coverage.observe(log,values,16384,trace=trace)==old.observe(log,values,16384,trace=trace)


def test_unrelated_large_stream_does_not_run_coverage_searches(monkeypatch,tmp_path):
    log=tmp_path/'stdout';log.write_text('SWDB_BFS_PARENT_STORAGE address=4000 count=20 element_bytes=4\n')
    trace=tmp_path/'trace.gz';count=20000
    trace.write_bytes(gzip.compress(b'150: system.maa: unrelated diagnostic message\n'*count))
    searches=[];original=coverage.re.search
    def search(pattern,line,*args,**kwargs):
        searches.append(pattern);return original(pattern,line,*args,**kwargs)
    monkeypatch.setattr(coverage.re,'search',search)
    result=coverage.observe(log,{'simTicks':'100','finalTick':'200'},16384,trace=trace)
    assert searches==[]
    assert result['debug_trace']['lines']==count
    assert result['completed_trace_units']=={}
    assert result['competing_parent_updates']['parent_storage']['virtual_address']==0x4000


def test_corrupt_stream_failures_match_original(tmp_path):
    from swdb.cli import Failure
    import pytest
    log=tmp_path/'stdout';log.write_text('')
    raw=gzip.compress(b'150: I[0] End [INSTR]\n')
    cases=[raw[:-4],raw[:-1]+bytes([raw[-1]^1]),gzip.compress(b'150: \xff\n'),gzip.compress(b'x'*(1024*1024+1))]
    trace=tmp_path/'trace.gz';old=reference()
    for payload in cases:
        trace.write_bytes(payload)
        with pytest.raises(Failure) as before:old.observe(log,{'simTicks':'100','finalTick':'200'},16384,trace=trace)
        with pytest.raises(Failure) as after:coverage.observe(log,{'simTicks':'100','finalTick':'200'},16384,trace=trace)
        assert str(before.value)==str(after.value)

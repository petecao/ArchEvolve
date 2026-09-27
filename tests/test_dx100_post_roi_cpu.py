"""R12 opt-in atomic post-ROI verifier continuation contracts. Created 2026-09-27 ET.

Fixture-only: a fake gem5 module checks ordering (switch after the ROI seal and
trace enable) and the retained receipt. It cannot establish that the pinned DX100
model drains and switches cleanly; that needs the separate mbit10 lane proof.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_dx100 import case, reference  # noqa: F401 (fixture)
from test_dx100_v2 import assert_downstream_verifier_contract, v2_request

FAKE_SWITCH = r'''
    caller=['system.switch_cpus0']; switched=[]
    class CPU:
        def __init__(self,name,out,mode): self.name=name; self.out=out; self.mode=mode
        def path(self): return self.name
        def switchedOut(self): return self.out
        def memory_mode(self): return self.mode
    system=types.SimpleNamespace(switch_cpus=[CPU('system.switch_cpus%d'%i,False,'timing') for i in range(4)],
                                 cpu=[CPU('system.cpu%d'%i,True,'atomic') for i in range(4)])
    def switchCpus(target,pairs,verbose=True):
        assert calls==[1] and 'SyscallBase' in enabled and target is system
        assert 'post_roi_cpu' not in json.loads((out/'roi-seal.json').read_text())['verification']
        assert [(a.name,b.name) for a,b in pairs]==[('system.switch_cpus%d'%i,'system.cpu%d'%i) for i in range(4)]
        for old,new in pairs: old.out=True; new.out=False
        tick[0]+=7; caller[0]='system.cpu0'; switched.append(tick[0])
        (out/'switched.json').write_text(json.dumps(switched))
    m5.switchCpus=switchCpus
    objects=types.ModuleType('m5.objects')
    objects.Root=types.SimpleNamespace(getInstance=lambda:types.SimpleNamespace(system=system))
    m5.objects=objects; sys.modules['m5.objects']=objects
'''


def atomic_request(case, behavior='witness', requested=True):
    data = v2_request(case, behavior)
    simulator = Path(data['simulator']['path'])
    program = simulator.read_text()
    for body in ('Calling exit_group(0)...', 'Returned 0.'):
        old = "stream.write('%d: SyscallBase: system.switch_cpus0: T0 : syscall " + body + "\\n' % (before+10))"
        assert old in program
        program = program.replace(old, "stream.write('%d: SyscallBase: %s: T0 : syscall " + body
                                  + "\\n' % (before+10, caller[0]))")
    anchor = "    sys.modules['m5']=m5\n"
    assert anchor in program
    program = program.replace(anchor, anchor + FAKE_SWITCH)
    simulator.write_text(program)
    data['simulator'] = reference(simulator)
    if requested:
        data['verification']['post_roi_cpu'] = 'AtomicSimpleCPU'
    return data


def test_requested_atomic_continuation_switches_after_seal_and_validates(case):
    data = atomic_request(case)
    _, invoke, _ = case
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'complete', result['outcome']
    terminal = result['context']['sealed_roi']['verification']
    switch = terminal['post_roi_cpu']
    assert switch['type'] == 'AtomicSimpleCPU' and switch['memory_mode'] == 'atomic'
    assert switch['requested_tick'] == 31400 and switch['switched_tick'] == 31407
    assert switch['to'] == ['system.cpu%d' % i for i in range(4)]
    assert terminal['simulated_ticks'] == terminal['exit_tick'] - 31400
    assert terminal['exit_witness']['caller'] == {'cpu': 'system.cpu0', 'thread': 0}
    assert result['context']['instrumentation']['post_roi_cpu'] == {
        'type': 'AtomicSimpleCPU', 'memory_mode': 'atomic', 'scope': 'post-seal verifier continuation only'}
    assert_downstream_verifier_contract(result)
    from swdb.dx100_witness import validate_completed_witness
    from swdb.workflow import Failure
    validate_completed_witness(result)
    unrequested = deepcopy(result)
    del unrequested['request']['verification']['post_roi_cpu']
    with pytest.raises(Failure, match='post-ROI CPU'):
        validate_completed_witness(unrequested, verify_artifacts=False)
    relabeled = deepcopy(result)
    relabeled['correctness']['checks'][0]['continuation']['post_roi_cpu']['to'][0] = 'system.switch_cpus0'
    with pytest.raises(Failure):
        validate_completed_witness(relabeled, verify_artifacts=False)


def test_unrequested_execution_never_switches(case):
    data = atomic_request(case, requested=False)
    _, invoke, _ = case
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'complete', result['outcome']
    assert 'post_roi_cpu' not in result['context']['sealed_roi']['verification']
    assert 'post_roi_cpu' not in result['context']['instrumentation']
    trace = Path(result['context']['post_roi_trace']['path'])
    assert not trace.with_name('switched.json').exists()


@pytest.mark.parametrize('verification', [
    {'checker': 'dx100.bfs.verifier.v2', 'max_ticks': 1000, 'post_roi_trace': 'SyscallBase', 'post_roi_cpu': 'TimingSimpleCPU'},
    {'checker': 'dx100.bfs.verifier.v1', 'max_ticks': 1000, 'post_roi_cpu': 'AtomicSimpleCPU'}])
def test_post_roi_cpu_is_rejected_before_execution_unless_exact(case, verification):
    data = atomic_request(case)
    data['verification'] = verification
    _, invoke, _ = case
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'failed'
    assert 'post_roi_cpu' in result['outcome']['reason']
    assert not any(stage['stage'] in {'checkpoint', 'simulation'} for stage in result['stages'])

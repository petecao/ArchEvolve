"""Prospective counted induction search policy, 2026-10-15 ET; no proof acceptance."""
import hashlib
import math
import ctypes
import sys
import time
from pathlib import Path

METHOD = 'staged-induction-working-v1'
TOTAL_DEBT = 8
SECONDS = 300
REPAIRS = 4
PHASES = ('bridges', 'consumption', 'recovery')
GUIDANCE = (
    'Close local frame, range-source and readiness facts, then the exact gathered-parent/CAS history step and post-enqueue queue phase. Inspect actual contracts; author your own small checked bridges.',
    'Build consumption induction bottom-up using your own saved pre-issue cursor: scalar edge/row and batch position/range/chunk. Issuance is not consumption. Preserve safety and completeness together.',
    'Recovery only: repair or remove unsupported cuts and recover the incumbent. No new temporary candidate can start. Every final ordinary and hint obligation still must be proved.',
)


def identity():
    return {'id': METHOD, 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def schedule(start_s, stop_s):
    if not all(math.isfinite(x) for x in (start_s, stop_s)) or stop_s <= start_s:
        raise ValueError('staged search needs a finite positive counted-time interval')
    return {'start_s': float(start_s), 'stop_s': float(stop_s)}


def phase(plan, counted_s):
    start, stop = plan['start_s'], plan['stop_s']
    if stop <= start or not all(math.isfinite(x) for x in (start, stop, counted_s)):
        raise ValueError('invalid staged search clock/schedule')
    width = (stop - start) / 3
    index = 0 if counted_s < start + width else 1 if counted_s < start + 2*width else 2
    return {'index': index, 'name': PHASES[index], 'start_s': start + index*width,
            'end_s': start + (index+1)*width, 'guidance': GUIDANCE[index]}


def may_enter(plan, counted_s, remaining_s):
    return phase(plan, counted_s)['index'] < 2 and min(remaining_s, plan['stop_s'] - counted_s) >= SECONDS


_CLOCK = None
_CLOCK_INFO = None
_LAST = None


def clock():
    """One host-wide monotonic clock that includes suspend time, in seconds."""
    global _CLOCK, _CLOCK_INFO, _LAST
    if _CLOCK is None:
        if sys.platform == 'darwin':
            class Timebase(ctypes.Structure):
                _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]
            system = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
            system.mach_timebase_info.argtypes = [ctypes.POINTER(Timebase)]
            system.mach_timebase_info.restype = ctypes.c_int
            system.mach_continuous_time.argtypes = []
            system.mach_continuous_time.restype = ctypes.c_uint64
            scale = Timebase()
            if system.mach_timebase_info(ctypes.byref(scale)) or not scale.numer or not scale.denom:
                raise RuntimeError('cannot establish the continuous monotonic timebase')
            _CLOCK = lambda: system.mach_continuous_time() * scale.numer / scale.denom / 1e9
            _CLOCK_INFO = {'kind': 'continuous_monotonic', 'implementation': 'mach_continuous_time',
                           'includes_sleep': True, 'numer': scale.numer, 'denom': scale.denom}
        elif hasattr(time, 'CLOCK_BOOTTIME'):
            _CLOCK = lambda: time.clock_gettime(time.CLOCK_BOOTTIME)
            _CLOCK_INFO = {'kind': 'continuous_monotonic', 'implementation': 'CLOCK_BOOTTIME', 'includes_sleep': True}
        else:
            raise RuntimeError('method19 needs a suspend-inclusive monotonic clock')
    value = _CLOCK()
    if not math.isfinite(value) or value < 0 or (_LAST is not None and value < _LAST):
        raise RuntimeError('continuous monotonic clock moved backward or is invalid')
    _LAST = value
    return value


def clock_info():
    clock()
    return dict(_CLOCK_INFO)



def wait_seconds(payload, expected_clock, now, *, runner_pid=None):
    """Only explicitly matched continuous-clock durations earn budget exclusion."""
    if (payload.get('clock') != 'continuous_monotonic' or
            payload.get('clock_info') != expected_clock or
            (runner_pid is not None and payload.get('runner_pid') != runner_pid)):
        return 0.0
    settled, pending = payload.get('settled_s'), payload.get('pending_since')
    if (not isinstance(settled, (int, float)) or not math.isfinite(settled) or settled < 0 or
            (pending is not None and (not isinstance(pending, (int, float)) or
             not math.isfinite(pending) or pending < 0 or pending > now))):
        return 0.0
    return settled + (now-pending if pending is not None else 0.0)


HISTORICAL_INPUTS = {'tdstep_standin.c': 'b4a820bd20b197eee293616af17da884bbc63ed92f9252e77f261092387024de', 'dxc_summaries.h': 'd708c0ef974e5ede1aaadd2b5e66dd785affa5e1dc6ef37419bf9e72517ae0d2', 'gapbs_models.h': '401d8ccfa8fdc1ef3734c97563a1c110d003d8847508aaa24ec3f300a33eed3e', 'bfs_unit.h': '1bcbf4dac683d6a46269fcd5f896fefc2571adc49d059b46f93fb25eb0f7b235'}


def check_inputs(standin):
    """Method19 changes search policy, never the reviewed 996 source/model design."""
    for name, expected in HISTORICAL_INPUTS.items():
        if hashlib.sha256((Path(standin)/name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('method19 historical source/model pin changed: '+name)

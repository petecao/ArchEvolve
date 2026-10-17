#!/usr/bin/env python3
'10000-second local metadata envelope for the explicitly pinned cap-only runner.\nNo extra subprocesses, native/compiler/provider jobs or remote actions.\n'
import hashlib
import importlib.util
from pathlib import Path
import signal
import sys

RUNNER=Path('/private/tmp/lanl14-pr-final-local-runner-catalog-caps-20261007-a4.py')
RUNNER_SHA='d0209039a6f39f6824229918db3c927d47f68c468f90382aa58deecbd0be7ed7'

def interrupted(signum,frame):
    # Exception unwinding reaches the runner's child stop_group finally block.
    raise InterruptedError('local metadata envelope signal '+str(signum))

if __name__=='__main__':
    assert hashlib.sha256(RUNNER.read_bytes()).hexdigest()==RUNNER_SHA,'Pinned cap-only runner differs'
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('lanl14_local_caps_a2',RUNNER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for value in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(value,interrupted)
    signal.setitimer(signal.ITIMER_REAL,10000)
    try:module.main()
    except (ValueError,KeyError,OSError,module.subprocess.SubprocessError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(2)
    finally:signal.setitimer(signal.ITIMER_REAL,0)

"""Run actual WP fact controls behind the scripted adapter seam. Created: 2026-10-15 ET."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, sys.argv[1])
from swdb import framac, proof_setup, rss_watchdog, verifier_lock

case = int(sys.argv[2])
shutil.copyfile(Path(__file__).with_name('setup_facts.c'), 'wp_input.c')
with verifier_lock.hold(f'ticket36 fact {case}'):
    module = proof_setup.compile_report_module(Path.cwd())
    flags = ['-wp', '-wp-rte', '-wp-cache', 'none', '-machdep', 'x86_64', '-wp-model', '+real',
             '-wp-prover', 'alt-ergo', '-wp-timeout', '1', '-wp-par', '1', '-wp-smoke-tests',
             '-cpp-extra-args=-DCASE=' + str(case), '-wp-report-json', 'goals.json']
    if case == 10:  # Generated-but-untried false postcondition: JSON drops it.
        flags[flags.index('-wp-prover') + 1] = 'none'
        flags[flags.index('-cpp-extra-args=-DCASE=10')] = '-cpp-extra-args=-DCASE=9'
    command = [*framac.locate().command, *flags, 'wp_input.c', '-then', '-load-module', str(module),
               '-report', '-report-untried', '-report-csv', 'properties.csv']
    done = rss_watchdog.run(command, log=Path('wp.log'), cap_bytes=8*2**30, timeout=120,
                            cwd=Path.cwd(), env={**os.environ, 'SWDB_PROOF_REPORT_OUT': str(Path.cwd()/'inventory.json')})
    if not Path('goals.json').exists():
        Path('goals.json').write_text('[]')
    print(Path('wp.log').read_text())
    # Original log is kept by scripted adapter; inventory and per-goal reports are
    # fixture data carried through the actual adapter reader in this fresh run.
    sys.exit(done.exit_code)

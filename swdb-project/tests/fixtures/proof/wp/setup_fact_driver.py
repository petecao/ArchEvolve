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
if case == 12:
    Path('injected.h').write_text('/*@ axiomatic injected { axiom hidden_header_axiom: \\false; } */\n')
with verifier_lock.hold(f'ticket36 fact {case}'):
    module = proof_setup.compile_report_module(Path.cwd())
    flags = ['-wp', '-wp-rte', '-wp-cache', 'none', '-machdep', 'x86_64', '-wp-model', '+real', '-wp-no-filter-init',
             '-wp-prover', 'alt-ergo', '-wp-timeout', '1', '-wp-par', '1', '-wp-smoke-tests',
             '-cpp-extra-args=-DCASE=' + str(case), '-wp-report-json', 'goals.json']
    if case == 11:
        flags[flags.index('-cpp-extra-args=-DCASE=11')] = '-cpp-extra-args=-DCASE=9'
        fill = [*framac.locate().command, *flags, 'wp_input.c']
        fill[fill.index('none')] = 'update'
        fill += ['-wp-cache-dir', 'poison-cache']
        rss_watchdog.run(fill, log=Path('cache-fill.log'), cap_bytes=8*2**30, timeout=120, cwd=Path.cwd())
        entries = list(Path('poison-cache').glob('*.json'))
        assert entries, 'the negative control must create actual WP cache entries'
        for entry in entries:
            entry.write_text(entry.read_text().replace('"timeout"', '"valid"').replace('"unknown"', '"valid"'))
        poisoned = [*fill]
        poisoned[poisoned.index('update')] = 'offline'
        rss_watchdog.run(poisoned, log=Path('poisoned-offline.log'), cap_bytes=8*2**30, timeout=120, cwd=Path.cwd())
        print('tampered actual WP cache entries:', len(entries))
        print(Path('poisoned-offline.log').read_text())
        # The checked run below still has cache none and no cache-dir override.
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

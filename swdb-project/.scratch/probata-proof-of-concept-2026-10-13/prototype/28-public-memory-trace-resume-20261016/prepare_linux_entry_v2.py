"""2026-10-16 ET. Pure source assembly of separately versioned Linux trace V2.

The reviewed V1 helper functions are copied byte for byte, never imported or run.
No previous launcher, fixture, policy, evidence or global manifest is overwritten.
"""
import ast
import hashlib
import json
from pathlib import Path

BASIS_SHA = '4654bd036fa3db1455e49a76f061cd8a955aec335fae322b44300776b9e462ae'
HELPERS = ('consumer_closure', 'pin', 'ambient_check', 'validate_linux_launch', 'verified_linux_lane',
           'import_surface', 'compiler_preflight', 'compiler_components', 'normalize_compiler_selector', 'junit_census')


def prepare_v2():
    output = Path(__file__).resolve().parent
    basis = (output / 'linux_trace_entry_v1.py').read_bytes()
    if hashlib.sha256(basis).hexdigest() != BASIS_SHA:
        raise ValueError('reviewed V1 basis differs')
    text = basis.decode()
    functions = {node.name: node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
    parts = ['"""2026-10-16 ET. INERT root-only V2 public abstract trace controller.\n'
             'No body/hardware/current0.2/whole28 acceptance follows from this packet.\n"""\n',
             'import contextlib, hashlib, json, os, pathlib, re, shlex, shutil, stat, subprocess, sys\n',
             'from pathlib import Path\nimport xml.etree.ElementTree as ET\n\n']
    for name in HELPERS:
        parts.append(ast.get_source_segment(text, functions[name]) + '\n\n')
    body = (output / 'linux_trace_main_v2.py.inc').read_text()
    parts.append(body)
    result = ''.join(parts)
    ast.parse(result)
    (output / 'linux_trace_entry_v2.py').write_text(result)
    evidence = {'date': '2026-10-16 ET', 'basis_sha256': BASIS_SHA, 'unchanged_helpers': list(HELPERS),
                'entry_sha256': hashlib.sha256(result.encode()).hexdigest(),
                'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
                'status': 'INERT source assembly only; root owns fresh source/control/runtime admission and dispatch'}
    (output / 'linux-entry-source-v2.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    prepare_v2()

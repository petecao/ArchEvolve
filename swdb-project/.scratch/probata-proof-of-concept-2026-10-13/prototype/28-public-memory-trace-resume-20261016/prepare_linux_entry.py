"""2026-10-16 ET. Source-only Linux entry preparation, never dispatch.

Copy reviewed launch/lane/consumer/environment helpers as closed Python AST
source. Do not import or run the older entry, which has top-level execution.
"""
import ast
import hashlib
import json
from pathlib import Path


NAMES = ('consumer_closure', 'pin', 'ambient_check', 'validate_linux_launch',
         'verified_linux_lane', 'import_surface', 'compiler_preflight', 'compiler_components')
PARENT_ENTRY_SHA = '615f6c867a29101e1dee2072893fea212f6c2843c77f6bbd3d18538fc891300a'
NORMALIZER_SHA = 'c3dd0a66efec3559c51265bfaffe307f2efc4b628230bb5f529ef7691299dca0'


def prepare():
    output = Path(__file__).resolve().parent
    source_path = output.parent / '28-initialized-u32-resume-20261016/linux_pair_entry_v1.py'
    source = source_path.read_bytes()
    if hashlib.sha256(source).hexdigest() != PARENT_ENTRY_SHA:
        raise ValueError('reviewed Linux helper source changed')
    text = source.decode()
    tree = ast.parse(text)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    parts = ['"""2026-10-16 ET. INERT root-only Linux public abstract-memory trace entry.\n'
             'No body, hardware or whole ticket28 acceptance follows from this execution packet.\n'
             '"""\n', 'import contextlib, hashlib, json, os, pathlib, re, shlex, shutil, stat, subprocess, sys\n',
             'from pathlib import Path\nimport xml.etree.ElementTree as ET\n\n']
    for name in NAMES:
        function = ast.get_source_segment(text, functions[name])
        if name == 'compiler_preflight':
            anchor = " if not isinstance(command,list) or len(command)!=1 or not isinstance(command[0],str):\n"
            replacement = " if not isinstance(command,list) or len(command)!=1 or not isinstance(command[0],str) or not Path(command[0]).is_absolute():\n"
            if function.count(anchor) != 1:
                raise ValueError('absolute compiler guard source anchor changed')
            function = function.replace(anchor, replacement, 1)
        parts.append(function + '\n\n')
    normalizer_path = output.parent / '28-initialized-u32-resume-20261016/linux_pair_selector_v3.py.inc'
    normalizer = normalizer_path.read_bytes()
    if hashlib.sha256(normalizer).hexdigest() != NORMALIZER_SHA:
        raise ValueError('independently reviewed exact normalizer bytes changed')
    parts.append(normalizer.decode() + '\n')
    body = (output / 'linux_trace_main_v1.py.inc').read_text()
    parts.append(body)
    entry = ''.join(parts)
    ast.parse(entry)
    (output / 'linux_trace_entry_v1.py').write_text(entry)
    metadata = {'date': '2026-10-16 ET', 'status': 'INERT; root commit/source/runtime/CBMC admission unknown',
                'helper_basis': {'relative': str(source_path.relative_to(output.parents[3])),
                                 'sha256': PARENT_ENTRY_SHA, 'functions': list(NAMES)},
                'intentional_helper_change': 'compiler_preflight refuses nonabsolute singleton compiler commands before child execution',
                'normalizer_basis': {'relative': str(normalizer_path.relative_to(output.parents[3])),
                                     'sha256': NORMALIZER_SHA, 'review': 'parent reviewed exact V3 source helper; no producer weakening'},
                'entry_sha256': hashlib.sha256(entry.encode()).hexdigest(),
                'body_sha256': hashlib.sha256(body.encode()).hexdigest()}
    (output / 'linux-entry-source.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    prepare()

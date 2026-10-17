"""2026-10-16 ET. Exact reviewed initialized cold primitive copies.
No main, project import, child discovery or actual evidence audit.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types
H = lambda value: hashlib.sha256(value).hexdigest()
KERNEL_META = {'path': '/data1/yanruj/probata-verifiers/opam/framac-33/lib/frama-c/META', 'bytes': 2318,
    'sha256': '1d41605b5220bc71779ffac319ff9b06950245f5eab9f61894e865ddd9658002'}

def strict_json(text):
    def pairs(rows):
        result = {}
        for name, value in rows:
            assert name not in result, 'duplicate JSON key'
            result[name] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON constant refused: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def safe_yaml(yaml, text):
    class UniqueSafeLoader(yaml.SafeLoader):
        pass
    def mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            assert key not in result, 'duplicate YAML key'
            result[key] = loader.construct_object(value_node, deep=deep)
        return result
    UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    return yaml.load(text, Loader=UniqueSafeLoader)


def digest(value):
    return H(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def absolute(value):
    assert type(value) is str and value.startswith('/') and os.path.normpath(value) == value and '\0' not in value
    return Path(value)


def relative(value):
    assert type(value) is str and value and str(Path(value)) == value and not Path(value).is_absolute()
    assert all(part not in ('', '.', '..') for part in Path(value).parts)
    return value


def stable_stat(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


class Physical:
    """Stream physical hashes; keep metadata, never whole catalog/file contents."""
    def __init__(self):
        self.files = {}
        self.checks = 0

    def pin(self, path, expected=None, size=None):
        path = Path(path)
        before = path.lstat()
        assert stat.S_ISREG(before.st_mode), 'regular physical input required: ' + str(path)
        result = hashlib.sha256()
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            assert stable_stat(opened) == stable_stat(before), 'input changed while opening'
            for block in iter(lambda: stream.read(1048576), b''):
                result.update(block)
            after = os.fstat(stream.fileno())
        final = path.lstat()
        assert stable_stat(before) == stable_stat(after) == stable_stat(final), 'input changed while hashing'
        value = result.hexdigest()
        assert expected is None or value == expected, 'physical hash differs: ' + str(path)
        assert size is None or final.st_size == size, 'physical byte count differs: ' + str(path)
        row = {'sha256': value, 'bytes': final.st_size, 'stat': stable_stat(final)}
        if str(path) in self.files:
            assert self.files[str(path)] == row, 'input changed across passive reads'
        self.files[str(path)] = row
        self.checks += 1
        return value

    def pinned(self, row):
        assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
        absolute(row['path'])
        assert type(row['bytes']) is int and row['bytes'] >= 0
        assert re.fullmatch('[a-f0-9]{64}', row['sha256'])
        return self.pin(row['path'], row['sha256'], row['bytes'])

    def read(self, row):
        self.pinned(row)
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and H(data) == row['sha256'], 'input changed while capturing selected small data'
        return data

    def unchanged(self):
        for name, row in self.files.items():
            assert stable_stat(Path(name).lstat()) == row['stat'], 'physical source/runtime/evidence metadata changed'


def raw_snapshot(raw, physical):
    files, links = {}, {}
    assert raw.is_dir() and not raw.is_symlink() and raw.resolve() == raw
    for path in sorted(raw.rglob('*')):
        name = str(path.relative_to(raw)); mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            # Alias links are inventoried literally; evidence inputs themselves
            # must be physical files and cannot silently follow these aliases.
            links[name] = {'target': os.readlink(path)}
        elif stat.S_ISREG(mode):
            files[name] = {'sha256': physical.pin(path), 'bytes': path.stat().st_size}
        else:
            assert stat.S_ISDIR(mode), 'special raw member'
    assert 1 <= len(files) <= 20000 and sum(row['bytes'] for row in files.values()) <= 8589934592
    return {'files': files, 'symlinks': links}


def admit_reader(policy, expected, closed, physical):
    admission = policy['reader_admission']
    assert admission['admitted'] is True and admission['role'] == 'isolated-passive-cold-reader'
    assert sys.flags.isolated == sys.flags.no_user_site == 1 and sys.flags.safe_path is True
    assert not sys.flags.optimize and sys.dont_write_bytecode is True
    metadata = expected['python_surface_binding']
    receipt = closed.verify_python_metadata(metadata)
    interpreter = metadata['interpreter']
    assert sys.executable == interpreter['path'] == expected['linux_launch_binding']['python']
    physical.pinned(interpreter['target_pin'])
    assert closed._resolution(absolute(sys.executable), interpreter['chain']) == absolute(interpreter['resolved'])
    paths = expected['startup_roles']['package_sys_path']
    assert len(paths) == len(set(paths)) == 7 and list(sys.path) == paths == admission['sys_path']
    assert sys.prefix == expected['startup_roles']['prefix'] and sys.base_prefix == expected['startup_roles']['base_prefix']
    environment_names = {'PYTHONPATH', 'PYTHONPYCACHEPREFIX', 'PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE',
                         'PYTHONSAFEPATH', 'SETUPTOOLS_USE_DISTUTILS'}
    assert set(admission['environment']) == environment_names
    for name in sorted(environment_names):
        assert os.environ.get(name) == admission['environment'][name]
    assert sys.pycache_prefix == admission['pycache_prefix']
    assert not os.path.lexists(absolute(admission['pycache_prefix']))
    assert not any(name.startswith('PYTHON') and name not in admission['environment'] for name in os.environ)
    # Only the explicitly selected YAML parser enters this passive reader.
    import site
    assert site.ENABLE_USER_SITE is False
    import yaml
    wanted = expected['startup_roles']['module_origins']['yaml']
    assert str(Path(yaml.__file__).resolve()) == wanted['path'] and yaml.__spec__.origin == wanted['spec_origin']
    physical.pin(wanted['path'], wanted['sha256'])
    assert list(sys.path) == paths and site.ENABLE_USER_SITE is False
    return yaml, receipt


def source_membership(project, expected):
    found = set()
    for name in expected['source_consumer_trees']:
        root = project / relative(name)
        for path in ([root] if root.is_file() else root.rglob('*')):
            mode = path.lstat().st_mode
            assert stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'consumer symlink/special member'
            if stat.S_ISREG(mode): found.add(str(path.relative_to(project)))
    return found


def pure_runtime_helpers(entry_source, physical):
    """Compile exactly two reviewed pure AST functions; never execute entry main."""
    hashes = {'import_surface': '37332570894eae61fb41b21d7726f61c08f98f1ded38b85f2181eebb08e3c1c8',
              'header_surface_check_v4': 'a0c64a9458961cd997c8314a45f469e2e9eaa88cbeee8f7e75b634d6dd00c5aa'}
    selected = set(hashes)
    tree = ast.parse(entry_source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in selected]
    assert len(functions) == len(selected) and {node.name for node in functions} == selected
    for node in functions:
        assert H(ast.get_source_segment(entry_source, node).encode()) == hashes[node.name], 'unreviewed pure runtime helper'
    # The complete staged entry is independently pinned by original admission.
    namespace = dict(hashlib=hashlib, json=json, os=os, pathlib=__import__('pathlib'), Path=Path, stat=stat,
                     pin=lambda path: {'path': str(Path(path).resolve()), 'sha256': physical.pin(path)})
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<reviewed-pure-runtime-helpers>', 'exec'), namespace)
    return namespace


def runtime_closure(expected, closed, helpers, physical):
    for path, value in expected['runtime_files'].items(): physical.pin(path, value)
    assert expected['runtime_files'][KERNEL_META['path']] == KERNEL_META['sha256']
    physical.pinned(KERNEL_META)
    for row in expected['tools'].values():
        path = closed._resolution(absolute(row['path']), expected['python_surface_binding']['interpreter']['chain']) if row['path'] == expected['python_surface_binding']['interpreter']['path'] else closed._resolution(absolute(row['path']), [])
        physical.pin(path, row['sha256'])
    for path, value in expected['wp_artifacts'].items(): physical.pin(path, value)
    physical.pin(expected['config']['path'], expected['config']['sha256'])
    prefix = Path(expected['tools']['frama-c']['path']).parent.parent
    portable = {name: helpers['import_surface'](root, expected['portable_import_surfaces'][name]) for name, root in (
        ('why3_stdlib', prefix / 'share/why3/stdlib'), ('wp_why3_support', prefix / 'share/frama-c/share/wp/why3'),
        ('why3_drivers', prefix / 'share/why3/drivers'))}
    packages = {}
    for name, directory in expected['ocaml_packages'].items():
        root = Path(directory)
        wanted = [{'relative': str(Path(path).relative_to(root)), 'sha256': value}
                  for path, value in expected['runtime_files'].items() if Path(path).is_relative_to(root)]
        wanted.sort(key=lambda row: Path(row['relative']).parts)
        assert wanted
        packages[name] = helpers['import_surface'](root, wanted)
    headers = helpers['header_surface_check_v4'](expected['linux_header_surfaces'], expected['linux_clang_components']['headers'], closed)
    parser = expected['linux_clang_components']['parser']['sha256']
    paths = [path for path, value in expected['runtime_files'].items() if value == parser]
    assert len(paths) == 1 and Path(paths[0]).name == 'libclang.so.22.1.8'
    physical.pin(paths[0], parser)
    return {'portable': portable, 'packages': packages, 'headers': headers, 'parser': paths[0]}

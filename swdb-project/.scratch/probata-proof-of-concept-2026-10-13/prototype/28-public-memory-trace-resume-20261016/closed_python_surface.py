"""2026-10-16 ET. Closed Python filesystem/startup gate, standard library only.

Verification consumes root metadata; it never discovers an admissible policy,
executes .pth/startup code, imports a target module or starts a child. This is
separate from the existing no-symlink Why3 import_surface helper.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat


SCHEMA = 'closed-python-surface-metadata-1'


class Refused(ValueError):
    pass


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _keys(value, expected, description):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise Refused('closed ' + description + ' fields differ')


def _absolute(value):
    if (not isinstance(value, str) or not value.startswith('/') or
            os.path.normpath(value) != value or '\x00' in value):
        raise Refused('canonical absolute physical path required')
    return Path(value)


def _sha(value):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise Refused('exact SHA256 required')


def _integer(value):
    if type(value) is not int or value < 0:
        raise Refused('nonnegative exact integer required')


def _counts(value):
    _keys(value, ('entries', 'files', 'directories', 'symlinks'), 'inventory count')
    for number in value.values():
        _integer(number)
    if value['entries'] != value['files'] + value['directories'] + value['symlinks']:
        raise Refused('inventory count sum differs')


def _resolution(path, expected_chain):
    """Resolve each component; refuse an unlisted hop before following it."""
    path = _absolute(str(path))
    if not isinstance(expected_chain, list):
        raise Refused('explicit complete link chain required')
    for row in expected_chain:
        _keys(row, ('path', 'target'), 'link chain')
        _absolute(row['path'])
        if not isinstance(row['target'], str) or not row['target'] or '\x00' in row['target']:
            raise Refused('literal link target required')
    current, pending, observed = Path('/'), list(path.parts[1:]), []
    while pending:
        part = pending.pop(0)
        if part in ('', '.'):
            continue
        if part == '..':
            current = current.parent
            continue
        candidate = current / part
        mode = candidate.lstat().st_mode
        if stat.S_ISLNK(mode):
            row = {'path': str(candidate), 'target': os.readlink(candidate)}
            index = len(observed)
            if index >= len(expected_chain) or row != expected_chain[index] or index >= 40:
                raise Refused('unlisted or changed link chain hop: ' + str(candidate))
            observed.append(row)
            target = Path(row['target'])
            if target.is_absolute():
                current = Path('/')
                pending = list(target.parts[1:]) + pending
            else:
                pending = list(target.parts) + pending
        else:
            if pending and not stat.S_ISDIR(mode):
                raise Refused('non-directory resolution component')
            current = candidate
    if observed != expected_chain or current != path.resolve(strict=True):
        raise Refused('complete link chain or strict resolved target differs')
    return current


def _regular(path, *, capture=False):
    """Hash one stable nofollow regular file, never a symlink or special input."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise Refused('regular physical file required: ' + str(path))
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    chunks, digest = [], hashlib.sha256()
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise Refused('physical file changed while opening')
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
            if capture:
                chunks.append(block)
        after = os.fstat(stream.fileno())
    final = path.lstat()
    identity = lambda item: (item.st_dev, item.st_ino, item.st_mode, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
    if identity(before) != identity(opened) or identity(opened) != identity(after) or identity(after) != identity(final):
        raise Refused('unstable physical file')
    return {'path': str(path), 'bytes': final.st_size, 'sha256': digest.hexdigest()}, b''.join(chunks) if capture else None


def _file_pin(expected):
    _keys(expected, ('path', 'bytes', 'sha256'), 'startup/file pin')
    path = _absolute(expected['path'])
    _integer(expected['bytes'])
    _sha(expected['sha256'])
    if _resolution(path, []) != path:
        raise Refused('startup pin is not a canonical physical regular file')
    actual, _unused = _regular(path)
    if actual != expected:
        raise Refused('startup/target physical file bytes differ: ' + str(path))
    return actual


def _link(path, expected, ancestors):
    if not isinstance(expected, dict) or expected.get('target_kind') not in ('file', 'directory'):
        raise Refused('closed known link target kind required')
    base = {'target', 'resolved', 'target_kind', 'chain'}
    extra = {'bytes', 'sha256'} if expected['target_kind'] == 'file' else {'target_counts', 'target_total_bytes', 'target_inventory_sha256'}
    _keys(expected, base | extra, 'known link target')
    if os.readlink(path) != expected['target']:
        raise Refused('raw link target changed: ' + str(path))
    target = _resolution(path, expected['chain'])
    if target != _absolute(expected['resolved']):
        raise Refused('known link strict resolved physical target differs')
    if expected['target_kind'] == 'file':
        _file_pin({'path': str(target), 'bytes': expected['bytes'], 'sha256': expected['sha256']})
    else:
        # The reviewed current Babel target has no nested links. There is no
        # recursive arbitrary-link allowance hidden in this directory target.
        target_expected = {'path': str(target), 'counts': expected['target_counts'],
                           'total_bytes': expected['target_total_bytes'],
                           'inventory_sha256': expected['target_inventory_sha256'], 'symlinks': {}}
        _surface(target_expected, ancestors)
    return {'target': expected['target'], 'resolved': str(target)}


def _surface(expected, ancestors=()):
    _keys(expected, ('path', 'counts', 'total_bytes', 'inventory_sha256', 'symlinks'), 'Python surface')
    root = _absolute(expected['path'])
    _counts(expected['counts'])
    _integer(expected['total_bytes'])
    _sha(expected['inventory_sha256'])
    if root in ancestors or _resolution(root, []) != root or not root.is_dir() or root.is_symlink():
        raise Refused('canonical real nonrecursive Python root required')
    links = expected['symlinks']
    if not isinstance(links, dict):
        raise Refused('explicit closed Python symlink map required')
    for name in links:
        relative = PurePosixPath(name)
        if not isinstance(name, str) or relative.is_absolute() or any(part in ('', '.', '..') for part in relative.parts) or str(relative) != name:
            raise Refused('canonical relative link key required')
    rows, found_links = [], set()
    def visit(directory):
        with os.scandir(directory) as stream:
            children = sorted(stream, key=lambda child: child.name)
        for child in children:
            path = Path(child.path)
            relative = str(path.relative_to(root))
            mode = path.lstat().st_mode
            row = {'relative': relative}
            if stat.S_ISLNK(mode):
                if relative not in links:
                    raise Refused('unlisted Python link: ' + str(path))
                found_links.add(relative)
                row.update(kind='symlink', **_link(path, links[relative], (*ancestors, root)))
            elif stat.S_ISREG(mode):
                physical, _unused = _regular(path)
                row.update(kind='file', bytes=physical['bytes'], sha256=physical['sha256'])
            elif stat.S_ISDIR(mode):
                row.update(kind='directory')
                visit(path)
            else:
                raise Refused('special Python import input: ' + str(path))
            rows.append(row)
    visit(root)
    # Exact lane producer uses sorted(Path.rglob('*')), a component ordering;
    # raw relative-string ordering differs for paths such as dir/a and dir-z.
    rows.sort(key=lambda row: PurePosixPath(row['relative']).parts)
    counts = {'entries': len(rows), 'files': sum(r['kind'] == 'file' for r in rows),
              'directories': sum(r['kind'] == 'directory' for r in rows),
              'symlinks': sum(r['kind'] == 'symlink' for r in rows)}
    result = {'path': str(root), 'counts': counts, 'total_bytes': sum(r.get('bytes', 0) for r in rows),
              'inventory_sha256': canonical_digest(rows)}
    if (found_links != set(links) or counts != expected['counts'] or result['total_bytes'] != expected['total_bytes'] or
            result['inventory_sha256'] != expected['inventory_sha256']):
        raise Refused('complete canonical Python membership/count/content digest differs: ' + str(root))
    pth = [str(root / r['relative']) for r in rows if '/' not in r['relative'] and r['relative'].endswith('.pth')]
    return result, pth


def _pass(policy):
    surfaces = policy['surfaces']
    if not isinstance(surfaces, dict) or not surfaces:
        raise Refused('explicit complete physical Python roots required')
    receipts, pth_paths = {}, []
    for name, expected in sorted(surfaces.items()):
        if not isinstance(expected, dict) or expected.get('path') != name:
            raise Refused('Python root key and path differ')
        receipts[name], pth = _surface(expected)
        pth_paths.extend(pth)
    pins = policy['startup_pins']
    if not isinstance(pins, list) or not pins or len({row['path'] for row in pins}) != len(pins):
        raise Refused('explicit unique startup source/config pins required')
    startup = [_file_pin(row) for row in pins]
    pth = policy['pth']
    if not isinstance(pth, list) or len({row['path'] for row in pth}) != len(pth) or sorted(row['path'] for row in pth) != sorted(pth_paths):
        raise Refused('complete executable .pth census differs')
    for row in pth:
        _keys(row, ('path', 'bytes', 'sha256', 'lines_sha256'), 'executable .pth')
        _sha(row['lines_sha256'])
        expected_pin = {key: row[key] for key in ('path', 'bytes', 'sha256')}
        if expected_pin not in pins:
            raise Refused('executable .pth is not explicitly bound as startup source')
        actual, data = _regular(_absolute(row['path']), capture=True)
        if actual != expected_pin or canonical_digest(data.decode('utf-8').splitlines()) != row['lines_sha256']:
            raise Refused('executable .pth bytes/line digest differ')
    interpreter = policy['interpreter']
    _keys(interpreter, ('path', 'chain', 'resolved', 'target_pin'), 'interpreter')
    resolved = _resolution(_absolute(interpreter['path']), interpreter['chain'])
    if resolved != _absolute(interpreter['resolved']) or interpreter['target_pin']['path'] != str(resolved):
        raise Refused('explicit interpreter chain/resolved target differs')
    _file_pin(interpreter['target_pin'])
    absence = policy['absence']
    if not isinstance(absence, dict):
        raise Refused('explicit startup missing-path bindings required')
    for name, missing in absence.items():
        path = _absolute(name)
        if missing is not True or _resolution(path.parent, []) != path.parent or os.path.lexists(path):
            raise Refused('startup missing-path binding differs: ' + str(path))
    return {'surfaces': receipts, 'startup_pins': startup, 'pth': pth, 'interpreter': interpreter, 'absence': absence}


def verify_python_metadata(policy):
    """Two complete physical passes. Return compact evidence, never a policy."""
    try:
        if not isinstance(policy, dict) or policy.get('schema') != SCHEMA:
            raise Refused('exact closed Python metadata schema required')
        before = _pass(policy)
        after = _pass(policy)
        if before != after:
            raise Refused('Python membership/startup bindings changed between complete passes')
        return {'schema': SCHEMA, 'policy_sha256': canonical_digest({key: policy[key] for key in
                ('schema', 'surfaces', 'startup_pins', 'pth', 'interpreter', 'absence')}),
                'before': before, 'after': after, 'before_after_equal': True,
                'scope': 'closed physical Python bytes/membership/startup inputs only; guarded actual sys.path admission remains separate'}
    except (OSError, RuntimeError, KeyError, TypeError, UnicodeError, AttributeError) as error:
        raise Refused('closed Python metadata refused: ' + str(error)) from None


def check_guarded_startup(expected, observed, *, metadata):
    """Only root-admitted actual metadata, never candidate_expected_sys_path."""
    _keys(expected, ('admitted', 'root_metadata_sha256', 'sys_path', 'flags', 'executable',
                     'prefix', 'base_prefix', 'startup_environment'), 'guarded Python startup policy')
    if expected['admitted'] is not True:
        raise Refused('guarded actual Python startup admission is unknown')
    _sha(expected['root_metadata_sha256'])
    if not isinstance(expected['sys_path'], list) or not expected['sys_path'] or any(not isinstance(path, str) for path in expected['sys_path']):
        raise Refused('explicit root-observed actual sys.path required')
    for path in expected['sys_path']:
        _absolute(path)
    _keys(expected['flags'], ('isolated', 'no_user_site', 'dont_write_bytecode', 'optimize'), 'Python launch flags')
    if (expected['flags'] != {'isolated': 1, 'no_user_site': 1, 'dont_write_bytecode': True, 'optimize': 0} or
            any(type(expected['flags'][name]) is not int for name in ('isolated', 'no_user_site', 'optimize')) or
            type(expected['flags']['dont_write_bytecode']) is not bool):
        raise Refused('actual isolated nonoptimized no-bytecode startup required')
    if not isinstance(expected['startup_environment'], dict) or 'SETUPTOOLS_USE_DISTUTILS' not in expected['startup_environment']:
        raise Refused('explicit startup environment bindings required')
    for name in ('executable', 'prefix', 'base_prefix'):
        _absolute(expected[name])
    wanted = {key: value for key, value in expected.items() if key not in ('admitted', 'root_metadata_sha256')}
    if observed != wanted:
        raise Refused('guarded actual Python sys.path/flags/prefix/startup environment differs')
    if not isinstance(metadata, dict) or metadata.get('schema') != SCHEMA:
        raise Refused('guarded startup needs its exact closed physical metadata')
    if expected['executable'] != metadata['interpreter']['path']:
        raise Refused('guarded startup executable differs from pinned interpreter chain')
    startup_paths = {row['path'] for row in metadata['startup_pins']}
    if str(Path(expected['prefix']) / 'pyvenv.cfg') not in startup_paths:
        raise Refused('guarded startup venv configuration is not explicitly pinned')
    roots = [_absolute(name) for name in metadata['surfaces']]
    for name in expected['sys_path']:
        path = _absolute(name)
        if metadata['absence'].get(name) is True:
            if os.path.lexists(path):
                raise Refused('guarded startup missing sys.path input appeared')
        elif not any(path == root or root in path.parents for root in roots) or _resolution(path, []) != path or not path.is_dir():
            raise Refused('guarded actual sys.path input lacks closed physical coverage')
    return {'root_metadata_sha256': expected['root_metadata_sha256'], 'actual_startup_sha256': canonical_digest(observed),
            'scope': 'exact root-admitted observed startup state; no inferred path substitution'}

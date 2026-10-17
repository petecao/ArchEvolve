"""Read-only original administrative metadata transport, 2026-10-07 ET.

Fixed a1/a2/a3 lifecycle attempts only. No stream body, scientific record,
source import, selected main, process argv, environment or authentication read.
Base64 retains original JSON/exit bytes and their distinct seal policies.
"""
import base64, datetime, hashlib, json, os, stat, sys
from pathlib import Path

UID = 114316761
BASE = Path('/data/yanruj/EvolveSWDB_runs')
FILES = (
    'dispatch/receipt.json', 'dispatch/preregistration.json',
    'dispatch/dispatcher-cleanup.json', 'dispatch/lane.json',
    'dispatch/wrapper-exit-code.txt',
    'lanl14-export-reader-control-early-nonzero-a1/receipt.json',
    'lanl14-export-reader-control-early-nonzero-a1/harness-cleanup.json',
    'lanl14-export-reader-control-early-nonzero-a1/early-exit7/supervisor-receipt.json',
    'lanl14-export-reader-control-early-nonzero-a1/early-exit7/cleanup.json',
    'lanl14-export-reader-control-early-nonzero-a1/early-exit7/owned-children.json',
)
STREAMS = (
    'dispatch/wrapper.stdout', 'dispatch/wrapper.stderr',
    'lanl14-export-reader-control-early-nonzero-a1/sibling.stdout',
    'lanl14-export-reader-control-early-nonzero-a1/sibling.stderr',
    'lanl14-export-reader-control-early-nonzero-a1/early-exit7/worker.stdout',
    'lanl14-export-reader-control-early-nonzero-a1/early-exit7/worker.stderr',
    'lanl14-export-reader-control-early-nonzero-a1/early-exit7/supervisor-child.stdout',
    'lanl14-export-reader-control-early-nonzero-a1/early-exit7/supervisor-child.stderr',
)

def stable(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_uid, s.st_gid,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)

def checked(path, *, directory=False):
    assert path.is_absolute() and '..' not in path.parts
    assert all(not p.is_symlink() for p in (path, *path.parents))
    s = path.stat()
    assert s.st_uid == UID and (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
    assert stat.S_IMODE(s.st_mode) == (0o700 if directory else 0o600)
    return s

assert os.getuid() == os.geteuid() == UID
attempts = {}
for suffix in ('a1', 'a2', 'a3'):
    root = BASE / ('lanl14-lifecycle-administration-20261007-' + suffix)
    if not root.exists():
        attempts[suffix] = {'exists': False}
        continue
    checked(root, directory=True)
    originals, streams = {}, {}
    for relative in FILES:
        p = root / relative
        if not p.exists():
            originals[relative] = {'exists': False}
            continue
        s = checked(p)
        assert 0 < s.st_size <= 65536
        raw = p.read_bytes()
        assert len(raw) == s.st_size and stable(p.stat()) == stable(s)
        if p.suffix == '.json':
            json.loads(raw)
        originals[relative] = {
            'exists': True, 'path': str(p), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(), 'mode': '0600',
            'original_bytes_base64': base64.b64encode(raw).decode('ascii'),
            'policy_preserved_without_resealing': True,
        }
    for relative in STREAMS:
        p = root / relative
        if not p.exists():
            streams[relative] = {'exists': False}
            continue
        s = checked(p)
        assert s.st_size <= 8388608
        digest = hashlib.sha256()
        with p.open('rb') as stream:
            for block in iter(lambda: stream.read(65536), b''):
                digest.update(block)
        assert stable(p.stat()) == stable(s)
        streams[relative] = {
            'exists': True, 'path': str(p), 'bytes': s.st_size,
            'sha256': digest.hexdigest(), 'mode': '0600',
            'body_transferred': False,
        }
    attempts[suffix] = {'exists': True, 'originals': originals, 'private_stream_metadata': streams}

result = {
    'format': 'swdb.lanl14-original-administrative-metadata-transport.v1',
    'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'original_unsealed_transport': True, 'attempts': attempts,
    'scientific_admission': False,
    'scope': 'Fixed bounded original administrative JSON/exit bytes only; private stream hashes and sizes, no bodies. Originals are not reserialized or resealed.',
}
raw = (json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n').encode()
assert len(raw) <= 1048576
sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()

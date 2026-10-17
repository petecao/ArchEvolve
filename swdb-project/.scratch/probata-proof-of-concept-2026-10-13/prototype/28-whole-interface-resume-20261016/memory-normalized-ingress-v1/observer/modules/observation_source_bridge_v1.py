"""2026-10-16 ET. Fixed private observation bridge, not public SourceUnit admission."""
import hashlib
import json
from pathlib import Path
import stat
from swdb import dx100_whole_checked as contracts
from swdb._dx100_whole import whole_interface_v4 as binder
from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler
from swdb._dx100_whole import receiver_state_draws_v2 as receiver
CAPTURE_KIND = 'lossless-complete-original-tu-v1'

def complete_capture(*args, **kwargs):
    raise ValueError('private normalized observation cannot delegate legacy capture')

class Refused(ValueError):
    pass

def need(value, message):
    if not value:
        raise Refused(message)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def digest(value): return sha(canonical(value))

class Inputs:
    """Private physical read set; public callers provide no reader callbacks."""
    def __init__(self, library):
        self.library, self.pins = library, {}

    def absolute(self, row, *, retain=True, limit=8 * 1024 * 1024):
        selected = receiver.Pin.parse(row)
        old = self.pins.get(selected.path)
        need(old is None or old == selected, 'one physical input cannot have conflicting identities')
        value = receiver.check_file(selected, retain=retain, limit=limit)
        self.pins[selected.path] = selected
        return value

    def portable(self, row, *, limit=4 * 1024 * 1024):
        raw = contracts.pinned(self.library, row, limit=limit)
        path = str(Path(self.library.resolve(row)))
        return self.absolute({'path': path, 'bytes': len(raw), 'sha256': row['sha256']}, limit=limit)

    def selected(self, row, *, retain=True, limit=8 * 1024 * 1024):
        if type(row) is dict and set(row) == {'root', 'path', 'sha256'}:
            return self.portable(row, limit=limit)
        return self.absolute(row, retain=retain, limit=limit)

    def path(self, row):
        return Path(self.library.resolve(row)) if 'root' in row else Path(receiver.Pin.parse(row).path)

    def document(self, row): return contracts.document(self.selected(row))

    def stable(self):
        # Compression's chunk callback is deliberately cheap. Full hashes are
        # checked before and after decoding, never once per compressed chunk.
        for selected in self.pins.values():
            path = Path(selected.path)
            metadata = path.lstat()
            need(path.resolve(strict=True) == path and stat.S_ISREG(metadata.st_mode)
                 and metadata.st_size == selected.bytes, 'decoder input shape changed')

    def recheck(self):
        for selected in self.pins.values(): receiver.check_file(selected)

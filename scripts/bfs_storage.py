"""Process-free `du -sk` allocation semantics for owned monitors. 2026-09-26 ET."""
import os
from pathlib import Path
import stat
import time


def allocated_bytes(paths, *, deadline=None, check=None):
    """Count blocks without following links or spawning cleanup-owned children.

    Like the prior separate `du -sk ROOT` calls, deduplicate hard links within
    each root and round each root upward to KiB. This observation has a maximum
    30-second walk; callers' original work/guard/cleanup clocks still apply.
    Missing entries and unreadable metadata are errors, never zero observations.
    """
    end = time.monotonic() + 30
    if deadline is not None:
        end = min(end, deadline)

    def bounded():
        if time.monotonic() >= end:
            raise TimeoutError('allocated storage walk exceeded its existing observation bound')
        if check is not None:
            check()

    total = 0
    for value in paths:
        bounded()
        root = Path(value)
        if not root.is_absolute() or root != root.resolve(strict=True) or root.is_symlink():
            raise ValueError('charged storage root must be existing, absolute, and canonical')
        seen, blocks = set(), 0

        def visit(name, parent=None):
            nonlocal blocks
            bounded()
            metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
            identity = (metadata.st_dev, metadata.st_ino)
            if identity in seen:
                return
            seen.add(identity)
            if type(metadata.st_blocks) is not int or metadata.st_blocks < 0:
                raise ValueError('allocated storage block count is unavailable')
            blocks += metadata.st_blocks
            if stat.S_ISDIR(metadata.st_mode):
                # Keep descendants relative to an opened directory. A concurrent
                # replacement with a symlink must fail, not traverse its target.
                fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                try:
                    current = os.fstat(fd)
                    if (current.st_dev, current.st_ino) != identity:
                        raise ValueError('charged storage directory changed during observation')
                    with os.scandir(fd) as entries:
                        for entry in entries:
                            visit(entry.name, fd)
                finally:
                    os.close(fd)

        visit(root)
        bounded()
        total += ((blocks * 512 + 1023) // 1024) * 1024
    bounded()
    return total

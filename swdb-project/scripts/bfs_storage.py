"""Process-free `du -sk` allocation semantics for owned monitors. 2026-09-26 ET."""
import errno
import os
from pathlib import Path
import stat
import time


def allocated_bytes(paths, *, deadline=None, check=None):
    """Count blocks without following links or spawning cleanup-owned children.

    Like the prior separate `du -sk ROOT` calls, deduplicate hard links within
    each root and round each root upward to KiB. This observation has a maximum
    30-second walk; callers' original work/guard/cleanup clocks still apply.
    Missing charged roots and unreadable metadata fail closed. A nested entry
    deleted by a concurrent writer is omitted only after descriptor-relative,
    no-follow ENOENT revalidation. This is a sampled walk, not an atomic snapshot;
    the established quiescent post-helper recount remains required.
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
        seen, blocks, root_identity = set(), 0, None

        def metadata_for(name, parent):
            try:
                return os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError as error:
                if parent is None or error.errno != errno.ENOENT:
                    raise
                # The parent descriptor is still open. Confirm absence without
                # following a replacement symlink; if a new entry is present,
                # account that entry's actual metadata instead of assuming zero.
                bounded()
                try:
                    return os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError as confirmed:
                    if confirmed.errno != errno.ENOENT:
                        raise
                    return None

        def visit(name, parent=None):
            nonlocal blocks, root_identity
            bounded()
            metadata = metadata_for(name, parent)
            if metadata is None:
                return
            identity = (metadata.st_dev, metadata.st_ino)
            if parent is None:
                root_identity = identity
            if identity in seen:
                return
            if type(metadata.st_blocks) is not int or metadata.st_blocks < 0:
                raise ValueError('allocated storage block count is unavailable')
            if parent is None and stat.S_ISLNK(metadata.st_mode):
                raise ValueError('charged storage root became a symlink')
            if stat.S_ISDIR(metadata.st_mode):
                # Keep descendants relative to an opened directory. A concurrent
                # replacement with a symlink must fail, not traverse its target.
                try:
                    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                except FileNotFoundError as error:
                    if parent is None or error.errno != errno.ENOENT:
                        raise
                    bounded()
                    if metadata_for(name, parent) is None:
                        return
                    raise ValueError('charged storage directory changed during observation') from error
                try:
                    current = os.fstat(fd)
                    if (current.st_dev, current.st_ino) != identity:
                        raise ValueError('charged storage directory changed during observation')
                    # Do not mark a disappeared/renamed directory as visited:
                    # a subsequently enumerated live name must still be counted.
                    seen.add(identity); blocks += metadata.st_blocks
                    with os.scandir(fd) as entries:
                        for entry in entries:
                            visit(entry.name, fd)
                finally:
                    os.close(fd)
            else:
                seen.add(identity); blocks += metadata.st_blocks

        visit(root)
        bounded()
        retained_root = os.stat(root, follow_symlinks=False)
        if ((retained_root.st_dev, retained_root.st_ino) != root_identity
                or stat.S_ISLNK(retained_root.st_mode)):
            raise ValueError('charged storage root changed during observation')
        total += ((blocks * 512 + 1023) // 1024) * 1024
    bounded()
    return total

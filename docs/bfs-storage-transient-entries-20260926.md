# Transient retained-file accounting correction

Created: 2026-09-26 (Eastern Time).

The actual T15 corrective attempt failed before guest execution when the storage
monitor enumerated `.swdb.sqlite.3156540.tmp-journal` and SQLite removed that file
before its metadata lookup. The retained traceback reaches
`bfs_storage.allocated_bytes` through the batch monitor. Its failure, interrupted
record, original allowance and terminal evidence remain unchanged. This repair
neither resumes that attempt nor authorizes a retry.

The process-free walker now distinguishes a missing charged root from a nested
entry that disappeared during observation. A charged root must still exist at
canonical admission and lookup; unreadable metadata, unknown errors, directory
replacement and symlink traversal still fail. For a nested `ENOENT`, it checks
again using the already-open parent descriptor with `follow_symlinks=False`.
Confirmed absence contributes no retained bytes. If an entry has reappeared, its
actual no-follow metadata is counted, including a symlink's own allocation;
its target is never traversed. A directory disappearing before it can be opened
is omitted only after the same absence check. Reappearing or substituted
directories cannot be silently followed. A disappeared directory is not marked
visited, so a subsequently enumerated live name can still be counted.

This remains a sampled walk, not an atomic filesystem snapshot or a hard storage
quota. Concurrent creation or rename can change the tree while it is observed.
The existing independent post-helper, post-last-write recount must still inspect
the settled retained tree. The allocation metric is unchanged: `st_blocks * 512`,
including directory and symlink blocks, inode deduplication within each root, and
rounding each separate root upward to KiB. No subprocess is introduced; the
existing 30-second maximum walk and any earlier caller deadline/check still apply.
No memory, storage, work, cleanup, protocol or scientific threshold changes.

The local regression uses a real SQLite transaction in DELETE journal mode and
coordinates its actual commit between enumeration and metadata lookup. The old
walker raises the same `FileNotFoundError`; the corrected walker finishes and
matches `du -sk` after the commit. Additional fixtures cover repeated concurrent
SQLite commits, nested unlink/rename, reappearing symlinks, root removal and root
symlink substitution, permission errors, unchanged deadlines and allocation
parity. These are local contract checks, not a replacement for future exact-pin
Linux/runtime admission or empirical campaign acceptance.

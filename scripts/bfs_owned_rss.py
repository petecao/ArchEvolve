"""Identity-bound sampled process RSS. Created: 2026-09-26 (Eastern Time).

Read PID, start time, state and RSS from one /proc/PID/stat record. Linux's
field-24 RSS is approximate, as is VmRSS; neither is a peak or a kernel quota.
No unavailable measurement is replaced with zero. This observer never signals
or reaps processes and cannot establish terminal cleanup by itself.
"""
from datetime import datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo


RSS_SOURCE = 'linux.proc_pid_stat.field24.v1'
MAX_IDENTITIES = 4096


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


class DescendantRSS:
    """Observe owned ancestry across sessions and retain identities on failure."""

    def __init__(self, pid, proc=Path('/proc')):
        _require(type(pid) is int and pid > 0, 'owned root PID is invalid')
        self.pid, self.proc, self.known = pid, Path(proc), {}
        self.page_size = os.sysconf('SC_PAGE_SIZE')
        _require(type(self.page_size) is int and 0 < self.page_size <= 1024**2,
                 'owned RSS page size is unavailable')

    @staticmethod
    def _read_proc_text(path, folder, label):
        # Linux may report ESRCH for an already-open procfs file when its
        # process/task exits. Independently confirm directory absence, or
        # reopen once and use that actual identity/measurement. Neither the
        # first error nor an ambiguous confirmation authorizes a zero value.
        for attempt in range(2):
            try:
                return path.read_text()
            except (FileNotFoundError, ProcessLookupError):
                try:
                    folder.stat()
                except FileNotFoundError:
                    return None
                _require(attempt == 0, f'live owned {label} is unavailable')

    def _stat(self, pid):
        folder = self.proc / str(pid)
        raw = self._read_proc_text(folder / 'stat', folder, f'PID {pid} stat')
        if raw is None:
            return None
        try:
            prefix, suffix = raw.rsplit(')', 1)
            fields = suffix.split()
            actual_pid = int(prefix.split(' (', 1)[0])
            state, parent, start = fields[0], int(fields[1]), int(fields[19])
            _require(actual_pid == pid and parent >= 0 and start >= 0
                     and state in {'R', 'S', 'D', 'Z', 'T', 't', 'W', 'X', 'x', 'K', 'P', 'I'},
                     f'owned PID {pid} stat identity is malformed')
            # Remember ownership before parsing RSS in sample(), so an RSS
            # failure still exposes the observed identity to the terminal audit.
            return {'pid': pid, 'parent_pid': parent, 'start_ticks': start,
                    'state': state, '_fields': fields}
        except (IndexError, TypeError, ValueError) as exc:
            raise ValueError(f'owned PID {pid} stat is malformed: {exc}') from None

    def _children(self, row):
        folder = self.proc / str(row['pid'])
        children = []
        try:
            tasks = list((folder / 'task').iterdir())
            _require(len(tasks) <= MAX_IDENTITIES, 'owned task observation bound exceeded')
            for task in tasks:
                if not task.name.isdigit():
                    continue
                raw = self._read_proc_text(task / 'children', task, f'task {task.name} children')
                if raw is None:
                    continue
                values = raw.split()
                _require(len(values) <= MAX_IDENTITIES, 'owned child observation bound exceeded')
                children.extend(int(value) for value in values)
                _require(len(children) <= MAX_IDENTITIES, 'owned child observation bound exceeded')
        except (FileNotFoundError, ProcessLookupError):
            # A process may be reaped between the stat read and task traversal.
            current = self._stat(row['pid'])
            _require(current is None or current['start_ticks'] != row['start_ticks'],
                     f'live owned PID {row["pid"]} task telemetry is unavailable')
            return []
        _require(all(pid > 0 for pid in children), 'owned child PID is malformed')
        # Do not follow a new process's children if this PID was reused while
        # its task files were being read. Original owned identity stays known.
        current = self._stat(row['pid'])
        if current is None or current['start_ticks'] != row['start_ticks']:
            return []
        return children

    def sample(self):
        pending = [(self.pid, self.known.get(self.pid), None),
                   *((pid, start, None) for pid, start in self.known.items())]
        seen, rows = set(), []
        while pending:
            pid, expected_start, discovered_parent = pending.pop()
            row = self._stat(pid)
            if row is None or (expected_start is not None and row['start_ticks'] != expected_start):
                continue
            start = row['start_ticks']
            if discovered_parent is not None and self.known.get(pid) != start:
                parent_pid, parent_start = discovered_parent
                parent = self._stat(parent_pid)
                _require(parent is not None and parent['start_ticks'] == parent_start
                         and row['parent_pid'] == parent_pid,
                         f'child PID {pid}/{start} no longer belongs to its discovering parent')
            if (pid, start) in seen:
                continue
            seen.add((pid, start))
            _require(len(seen) <= MAX_IDENTITIES, 'owned process observation bound exceeded')
            self.known[pid] = start
            _require(len(self.known) <= MAX_IDENTITIES, 'retained owned identity bound exceeded')
            try:
                pages = int(row.pop('_fields')[21])
                _require(pages >= 0, 'negative RSS pages')
            except (IndexError, TypeError, ValueError) as exc:
                raise ValueError(f'owned PID {pid}/{start} RSS is unavailable or malformed: {exc}') from None
            row.update(rss_pages=pages, rss_bytes=pages * self.page_size)
            rows.append(row)
            children = self._children(row)
            _require(len(pending) + len(children) <= MAX_IDENTITIES,
                     'pending owned observation bound exceeded')
            pending.extend((child, None, (pid, start)) for child in children)
        _require(any(row['pid'] == self.pid for row in rows), 'driver RSS telemetry is unavailable')
        return {'sampled_at': datetime.now(ZoneInfo('America/New_York')).isoformat(),
                'rss_bytes': sum(row['rss_bytes'] for row in rows), 'processes': rows,
                'rss_source': RSS_SOURCE, 'page_size_bytes': self.page_size}

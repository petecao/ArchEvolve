"""Bounded host-only simulator phase observations. Updated: 2026-09-25.

This never traverses the statistics tree or changes allocator/model settings.
"""
import ctypes
import json
import os
from pathlib import Path
import time


class Observer:
    def __init__(self, folder):
        self.path = Path(folder) / 'host-memory-phases.jsonl'
        self.started = time.monotonic()
        self.calls = 0
        self.allocator = None
        try:
            self.allocator = ctypes.CDLL(None).MallocExtension_GetNumericProperty
            self.allocator.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
            self.allocator.restype = ctypes.c_int
        except (AttributeError, OSError):
            pass

    def write(self, phase, **extra):
        if self.calls >= 128:
            return
        self.calls += 1
        started = time.monotonic()
        row = {'phase': phase, 'pid': os.getpid(), 'elapsed_s': started - self.started,
               'host_time_ns': time.time_ns(), 'host_cost_is_bfs_performance': False, **extra}
        try:
            fields = {}
            for line in Path('/proc/self/status').read_text().splitlines():
                if line.split(':', 1)[0] in {'VmRSS', 'VmHWM', 'RssAnon', 'RssFile', 'VmSize'}:
                    key, value = line.split(':', 1)
                    fields[key] = value.strip()
            row['process_status'] = fields
        except OSError as exc:
            row['process_status_unavailable'] = str(exc)
        values = {}
        if self.allocator is not None:
            for key in ('generic.current_allocated_bytes', 'generic.heap_size',
                        'tcmalloc.pageheap_free_bytes', 'tcmalloc.pageheap_unmapped_bytes',
                        'tcmalloc.central_cache_free_bytes', 'tcmalloc.thread_cache_free_bytes'):
                value = ctypes.c_size_t()
                if self.allocator(key.encode(), ctypes.byref(value)):
                    values[key] = value.value
        row['allocator_numeric_properties'] = values
        row['observation_seconds'] = time.monotonic() - started
        with self.path.open('a') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n')

    def requestors(self, root):
        """Inspect exactly one vector through C++ resolveStat, without evaluating it."""
        try:
            stat = root.resolveStat('system.l3.ReadReq_T.hits')
            size = int(stat.size)
            if not 0 < size <= 256:
                raise ValueError('representative vector is outside the observation bound')
            self.write('requestor_vector', representative='system.l3.ReadReq_T.hits',
                       requestors=size, subnames=stat.subnames)
        except (AttributeError, KeyError, ValueError, RuntimeError) as exc:
            self.write('requestor_vector_unavailable', reason=str(exc))

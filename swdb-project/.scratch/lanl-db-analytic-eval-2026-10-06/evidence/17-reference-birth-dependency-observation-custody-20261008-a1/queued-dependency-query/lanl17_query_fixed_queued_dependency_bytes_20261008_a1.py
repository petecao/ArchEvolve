#!/usr/bin/env python3
"""Fixed queued-17 dependency byte query. Prepared 2026-10-08 ET; NOT RUN.

Only original byte hashes and path/stat metadata are emitted. No graph/record/model
parser, control import, compiler/version/simulator execution, writes, or admission.
1 GiB source-read bound is specific to this fixed query, not the storage guard.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import socket
import stat
import subprocess
import sys
import time

UID = 114316761
BASE = Path('/data1/yanruj')
RAW = Path('/data/yanruj/EvolveSWDB_runs')
PRIMARY = BASE / 'ArchEvolve'
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
MAX_FILE = 1024 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024 * 1024
MAX_OUTPUT = 256 * 1024
MAX_GIT_OUTPUT = 2 * 1024 * 1024
DEADLINE_SECONDS = 600
STAT_KEYS = ('dev', 'ino', 'mode', 'nlink', 'uid', 'gid', 'size', 'mtime_ns', 'ctime_ns')
IDENTITY_KEYS = ('dev', 'ino', 'mode', 'uid', 'gid')
GIT = Path('/usr/bin/git')
PYTHON = Path('/usr/bin/python3.12')
NATIVE_PINS = {
    str(GIT): {'bytes': 4019024, 'sha256': '06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'},
    str(PYTHON): {'bytes': 8020928, 'sha256': 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'},
}
ROUTE_PIN = {'path': '/private/tmp/lanl17-frozen-R-input-model-dependency-routes-20261008-a1.json', 'bytes': 96495, 'sha256': '2628a596f5683e3f3b0008fb5319ad87df17954849ba1bea8e90ba51a2b0e591', 'policy': 'Original UNSEALED source-only route audit; no availability claim'}
FIXED_FILES = [{'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k14/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k14.061b9007efcdebb7', 'pin': {'bytes': 27889273, 'canonical_sha256': 'b09810ebb77becb46667314439bd044c892f268fa9692df8b15338930d670f10', 'sha256': '057b291b9e74fc3b3af901bc668058162c03d5fc89e0572de848bc46d9d5a46d'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k14/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k14.061b9007efcdebb7', 'pin': {'bytes': 28937857, 'canonical_sha256': 'b09810ebb77becb46667314439bd044c892f268fa9692df8b15338930d670f10', 'sha256': '6d2630e322256c2a773e033cff99b0c474532a7e110c1032d9ad5e1d3ff43dc5'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k15/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k15.15b1ec00b24140f4', 'pin': {'bytes': 29694769, 'canonical_sha256': '91955e7e5528a8c43dcf03f6d3cdafb649e98ed33dd7c83bf8cbf1e09d269f5d', 'sha256': '98b26ec50c9e1fd8fea935b3326095fc120416089322242bb29cf55889eb7e58'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k15/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k15.15b1ec00b24140f4', 'pin': {'bytes': 30743353, 'canonical_sha256': '91955e7e5528a8c43dcf03f6d3cdafb649e98ed33dd7c83bf8cbf1e09d269f5d', 'sha256': '2b8ba2ba5bb5ffe4c7ce7e3aaee80d71d958f263fd7cdb339f64d57d1ad29bda'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k17/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k17.7c5f5ee1ddda25c4', 'pin': {'bytes': 33279465, 'canonical_sha256': '5e5f73be345c10f99bab522935aa4455e656de497301e4734784089f18873db3', 'sha256': 'ffb5c1be95e33373a23431124a9a97f4a7a72311d542cc021ddcf24fb449913e'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k17/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k17.7c5f5ee1ddda25c4', 'pin': {'bytes': 34328049, 'canonical_sha256': '5e5f73be345c10f99bab522935aa4455e656de497301e4734784089f18873db3', 'sha256': '7915eabf66188be9117175eba2577bcc2ef44a88c73c4494b42c60f1b8b649c8'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k18/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k18.feb23b36a57d4c05', 'pin': {'bytes': 35055097, 'canonical_sha256': 'a8230c56a80fee0503f51fdad6e8b4dc629bafdacfc9786fa9bc7b7d765c65e6', 'sha256': 'ccb58058e568aec62b8076829cce949a61a9a7a27ccdefab59a4b75f31ee5150'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-kronecker.g18.k18/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-kronecker.g18.k18.feb23b36a57d4c05', 'pin': {'bytes': 36103681, 'canonical_sha256': 'a8230c56a80fee0503f51fdad6e8b4dc629bafdacfc9786fa9bc7b7d765c65e6', 'sha256': 'b580c7572d5225354a8df599d9107610995a3afa11f9bebe691a34d59289aab1'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k14/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k14.9027c7c5f57e8926', 'pin': {'bytes': 30406989, 'canonical_sha256': 'b94b39953e922462ffd10813844e6aada09c9886420586f907380b1d94c5e3cc', 'sha256': '6390201bf8d08ac3d876a416d10f40b63fba818df314055bc4eeb47f8fce1c65'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k14/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k14.9027c7c5f57e8926', 'pin': {'bytes': 31455577, 'canonical_sha256': 'b94b39953e922462ffd10813844e6aada09c9886420586f907380b1d94c5e3cc', 'sha256': 'f88e85fbde5219af215b83769e3358ead93449f13d76e4a2dc7767ba768e4efc'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k15/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k15.34444aebb8080315', 'pin': {'bytes': 32503877, 'canonical_sha256': '22ab35e7e7cee0b8779c613cc4ae8bae5937c0ebe9ddb20d1be82b4dbce93fb9', 'sha256': '25394b3f3d123983fc309dbda4f93b8e979e29795328bc38cfa2ac479daae754'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k15/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k15.34444aebb8080315', 'pin': {'bytes': 33552465, 'canonical_sha256': '22ab35e7e7cee0b8779c613cc4ae8bae5937c0ebe9ddb20d1be82b4dbce93fb9', 'sha256': '5abecb2f3ecc4cf7eaa0de9ff34def7c34437e6210afc19e9da74d62cf6bfccf'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k17/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k17.451edf9faac833c0', 'pin': {'bytes': 36697701, 'canonical_sha256': 'ba748ecd829b1f8fee9402c6ea9356d9cacbe8472e150ddda97de3a59a851a2a', 'sha256': 'd13ac3c69856dffb0f8cf4c7e46c7a2047b7d56483a76a03226e175a3b4d1a43'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k17/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k17.451edf9faac833c0', 'pin': {'bytes': 37746289, 'canonical_sha256': 'ba748ecd829b1f8fee9402c6ea9356d9cacbe8472e150ddda97de3a59a851a2a', 'sha256': '6961434d06a2905e4daaacc700ebecdc2a89f1b9b5eb11e6413465c9d655dd29'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k18/graph-dx100.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k18.c0396050e37ceed6', 'pin': {'bytes': 38794573, 'canonical_sha256': '327b80162cc83609a18e13dcb67f1e66e4468edeb13e43112975fcfb7e524925', 'sha256': 'e03ad54f66292dbf9abe4dcb657ed4f1a1728a7ee80d88bacc1ea42ba7123914'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2/lanl17-prospective-20261006-a2-uniform_random.g18.k18/graph-upstream.sg', 'role': 'metadata_pins workload representation + source0 out-degree read', 'record': 'lanl17-prospective-20261006-a2-uniform_random.g18.k18.c0396050e37ceed6', 'pin': {'bytes': 39843161, 'canonical_sha256': '327b80162cc83609a18e13dcb67f1e66e4468edeb13e43112975fcfb7e524925', 'sha256': 'a3ecc6241ca27276fd3d8e0ea62fc5437ea1e783097b64528809b8e3a854ad23'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260926-a2/bfs-dx100-coverage-20260926-a2/graph/coverage.sg', 'role': 'metadata_pins companion representation read; later companion simulation input', 'record': 'bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e', 'pin': {'bytes': 622829, 'canonical_sha256': 'e03a3905f9105b898b730387092d92a68b854cdd44280adb39b1bd9423a4a968', 'sha256': 'd4697713f585b9670e1c44d26df94c72889f4c82fbd68b72e15627e6a0b39a56'}, 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af/build/X86/gem5.opt', 'role': 'metadata_pins _simulation_identity(check_files=True)', 'record': 'bfs-dx100-build-20260925-a2', 'pin': {'sha256': 'f4038c88318ee09085b6c07f163094a07a31a256f21b652d4f3cfa046feb1f6b', 'bytes': 676472872}, 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af/ext/ramulator2/ramulator2/libramulator.so', 'role': 'metadata_pins _simulation_identity(check_files=True)', 'record': 'bfs-dx100-build-20260925-a2', 'pin': {'bytes': 177789736, 'sha256': '46b5dbd87a77845ebadd1854e990d8e5c04c41253ad76315a766d61b77ca43dd'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-build-20260925-a2/build/build-receipt.json', 'role': 'metadata_pins _simulation_identity(check_files=True)', 'record': 'bfs-dx100-build-20260925-a2', 'pin': {'sha256': 'c465447ddc5cc37faa7cb3127a7f9f00b6b557c326e8319e5d694ee9933f8d6c'}, 'live_filesystem_dependency': True}, {'path': '/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-build-20260925-a2/runtime-dependencies.json', 'role': 'metadata_pins _simulation_identity(check_files=True)', 'record': 'bfs-dx100-build-20260925-a2', 'pin': {'sha256': 'ae7389a0b6848fa21eae7c527211948a88e3010f9a5135754a2241dc6f5542c4'}, 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af/ext/ramulator2/ramulator2/example_gem5_config.yaml', 'role': 'frozen simulation target Ramulator configuration', 'record': 'typed-library-bfs-gem5-20261003-a2.protocol.84229924369fc6b0', 'pin': {'sha256': 'aca6e27b58afdfbfd80b7ec41c3f0e7e574a1fc7355a3512981ead823f68731b'}, 'live_filesystem_dependency': True}, {'path': '/usr/bin/g++-13', 'role': 'frozen guest-build compiler identity', 'record': 'typed-library-bfs-gem5-20261003-a2.protocol.84229924369fc6b0', 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af/util/m5/src/abi/x86/m5op.S', 'role': 'later real dx100 candidate guest compilation', 'record': 'bfs-dx100-build-20260925-a2', 'live_filesystem_dependency': True}]
FIXED_DIRECTORIES = [{'path': '/data1/yanruj/EvolveSWDB_sources/d9edd7d0042ae3e6/typed-library-bfs-gem5-20261003-a2.baseline/source', 'role': 'saved baseline candidate artifact; later dx100-compile calls artifacts.verify', 'record': 'typed-library-bfs-gem5-20261003-a2.baseline', 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/EvolveSWDB_sources/bfs-dx100-compile-20260925-a1.source/source', 'role': 'saved full source snapshot artifact identity', 'record': 'bfs-dx100-compile-20260925-a1.source', 'live_filesystem_dependency': False}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af', 'role': 'pinned simulator model and runtime/include/config source tree', 'record': 'bfs-dx100-build-20260925-a2', 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af/include', 'role': 'later real dx100 candidate guest compilation include directory', 'record': 'bfs-dx100-build-20260925-a2', 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af/util/m5/src', 'role': 'later real dx100 candidate guest compilation include directory', 'record': 'bfs-dx100-build-20260925-a2', 'live_filesystem_dependency': True}, {'path': '/data1/yanruj/DX100-bfs-e4fc4af/benchmarks/API', 'role': 'later real dx100 candidate guest compilation include directory', 'record': 'bfs-dx100-build-20260925-a2', 'live_filesystem_dependency': True}]
SYMBOLIC_PENDING = [{'path': '${SWDB_HOME_OR_IMPORTED_SOURCE_SWDB}/apps/dx100/benchmarks/gapbs/src/bfs.cc', 'role': 'selected baseline implementation code', 'record': 'dx100-bfs-scalar', 'pin': {'sha256': '6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465'}, 'live_filesystem_dependency': True}, {'path': '${FROZEN_SOURCE_SWDB}/scripts/prepare_dx100_scalar_snapshot.py', 'role': 'campaign scalar-only source reconstruction', 'record': 'bfs-dx100-scalar-only-20260929-a1.source', 'pin': {'sha256': '34e27805753ecff9d5bf789166c13a061991c8278c94a48e42482ca0d473dc3c'}, 'live_filesystem_dependency': True}, {'path': '${SWDB_HOME_OR_IMPORTED_SOURCE_SWDB}/apps/dx100', 'role': 'metadata_pins baseline selected application source; full manifest comparison', 'record': 'dx100-gapbs', 'live_filesystem_dependency': True}, {'path': '${FROZEN_SOURCE_SWDB}/apps/dx100', 'role': 'scalar snapshot reconstruction full pinned original source', 'record': 'bfs-dx100-scalar-only-20260929-a1.source', 'live_filesystem_dependency': True}]
GIT_SOURCE_RELATIVE = [{'repo_path': 'swdb-project/scripts/dx100_verify.py', 'symbolic_future_path': '${FROZEN_SOURCE_SWDB}/scripts/dx100_verify.py', 'identity_policy': 'actual current frozen-source hash during protocol freeze; historical template verifier hash is replaced', 'source_pointer': 'campaign_targets988'}, {'repo_path': 'swdb-project/swdb/dx100_witness.py', 'symbolic_future_path': '${FROZEN_SOURCE_SWDB}/swdb/dx100_witness.py', 'identity_policy': 'actual current frozen-source hash during protocol freeze', 'source_pointer': 'campaign_targets989'}, {'repo_path': 'swdb-project/scripts/dx100_host_memory.py', 'symbolic_future_path': '${FROZEN_SOURCE_SWDB}/scripts/dx100_host_memory.py', 'identity_policy': 'actual current frozen-source hash during protocol freeze', 'source_pointer': 'campaign_targets990'}, {'repo_path': 'swdb-project/library/dx100/dxc_lowering.hpp', 'symbolic_future_path': '${FROZEN_SOURCE_SWDB}/library/dx100/dxc_lowering.hpp', 'identity_policy': 'current library is a campaign input copied by helper307–308; candidate source reference uses exact library header', 'source_pointer': 'campaign_targets967–969;484 onward'}]


class Refused(Exception):
    pass


def require(condition, code):
    if not condition:
        raise Refused(code)


def stamp(s):
    return dict(zip(STAT_KEYS, (s.st_dev, s.st_ino, s.st_mode, s.st_nlink,
                               s.st_uid, s.st_gid, s.st_size, s.st_mtime_ns, s.st_ctime_ns)))


def identity(s):
    return {key: s[key] for key in IDENTITY_KEYS}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode()


class Query:
    def __init__(self, args):
        self.args = args
        self.end = time.monotonic() + DEADLINE_SECONDS
        self.charged = 0
        self.ancestors = {}
        self.observed_files = {}
        self.aliases = {}
        self.output = {
            'format': 'swdb.fixed-queued17-dependency-byte-observation.v1', 'sealed': False,
            'started_utc': datetime.now(timezone.utc).isoformat(), 'finished_utc': None,
            'state': 'partial_read_only_query', 'failure': None,
            'expected_delivered_R': args.expected_primary,
            'parent_stdin_source_sha256': args.source_sha256,
            'stdin_source_byte_identity_is_parent_transport_custody_not_self_verified': True,
            'original_route_audit_pin': ROUTE_PIN,
            'limits': {'per_file_bytes': MAX_FILE, 'cumulative_read_bytes': MAX_TOTAL,
                       'seconds': DEADLINE_SECONDS, 'output_bytes': MAX_OUTPUT},
            'symbolic_future_routes_pending': SYMBOLIC_PENDING,
            'literal_directory_observations': [], 'literal_file_observations': [],
            'source_relative_Git_byte_pins': [], 'native_file_observations': [],
            'ancestor_identity_observations': self.ancestors,
            'original_file_stat_final_observations': {},
            'original_Graph_values_or_application_outcome_bodies_transferred': False,
            'selected_controls_or_SWDB_imported': False,
            'native_compiler_simulator_version_or_scientific_commands_executed': False,
            'filesystem_writes_or_Git_mutations': False,
            'global_availability_stability_clearance_or_admission_generated': False,
        }

    def tick(self):
        require(time.monotonic() < self.end, 'query_deadline')

    def charge(self, amount):
        self.tick()
        self.charged += amount
        require(self.charged <= MAX_TOTAL, 'cumulative_byte_limit')

    def put(self, key, value):
        self.output[key].append(value)
        if len(canonical(self.output)) > MAX_OUTPUT - 4096:
            self.output[key].pop()
            raise Refused('metadata_output_budget')

    def canonical_path(self, text):
        require(isinstance(text, str) and text.startswith('/') and '\x00' not in text,
                'literal_absolute_path_required')
        path = Path(text)
        require(str(path) == text and path.resolve(strict=True) == path,
                'unexpected_redirect_or_noncanonical_route')
        return path

    def route(self, path, *, native=False, leaf_directory=False):
        self.tick()
        path = self.canonical_path(str(path))
        if native:
            require(path == Path('/usr/bin') or Path('/usr/bin') in path.parents,
                    'native_route_outside_fixed_usr_bin')
        else:
            require(path == BASE or BASE in path.parents or path == RAW or RAW in path.parents,
                    'dependency_route_outside_fixed_physical_roots')
        parts = list(reversed(path.parents)) + ([path] if leaf_directory else [])
        refs = []
        for part in parts:
            self.tick()
            s = stamp(part.lstat())
            require(stat.S_ISDIR(s['mode']) and not s['mode'] & 0o5000,
                    'ancestor_type_or_suid_sticky')
            # Known account private BASE anchors the writable primary/model source namespace.
            # Plain owned C/account directories may have account GID; inherited SGID dirs use GID0.
            inside = part == BASE or BASE in part.parents or part == Path('/data/yanruj') or Path('/data/yanruj') in part.parents
            require(s['uid'] == (UID if inside else 0), 'ancestor_owner')
            if inside:
                require(s['gid'] in {0, UID}, 'ancestor_group_not_original_account_or_root')
                if s['mode'] & stat.S_ISGID:
                    require(s['gid'] == 0, 'setgid_ancestor_group_not_root')
            if part == BASE:
                require(stat.S_IMODE(s['mode']) == 0o700 and s['gid'] == 0,
                        'exact_private_BASE_mode_or_group')
            name = str(part)
            if name in self.ancestors:
                require(identity(s) == self.ancestors[name]['identity'], 'ancestor_identity_changed')
            else:
                self.ancestors[name] = {'path': name, 'stat_at_first_read': s, 'identity': identity(s)}
            refs.append(name)
        require(len(canonical(self.output)) <= MAX_OUTPUT - 4096, 'metadata_output_budget')
        return path, refs

    def read_file(self, path, expected=None, *, native=False):
        path, refs = self.route(path, native=native)
        before = stamp(path.lstat())
        require(stat.S_ISREG(before['mode']) and before['nlink'] == 1
                and not before['mode'] & 0o7000 and 0 <= before['size'] <= MAX_FILE,
                'bounded_regular_singlelink_file_required')
        require(before['uid'] == (0 if native else UID), 'file_owner')
        if native:
            require(stat.S_IMODE(before['mode']) == 0o755, 'native_mode_not_root_0755')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        h = hashlib.sha256()
        count = 0
        prefix = b''
        try:
            require(stamp(os.fstat(fd)) == before, 'file_replaced_before_hash')
            while True:
                self.tick()
                raw = os.read(fd, min(1024 * 1024, MAX_FILE - count + 1))
                if not raw:
                    break
                count += len(raw)
                self.charge(len(raw))
                require(count <= MAX_FILE, 'file_byte_limit')
                if len(prefix) < 64:
                    prefix += raw[:64 - len(prefix)]
                h.update(raw)
            after = stamp(os.fstat(fd))
            require(after == before == stamp(path.lstat()) and count == before['size'],
                    'file_content_identity_changed_during_hash')
        finally:
            os.close(fd)
        fact = {'literal_path': str(path), 'canonical_resolved_path': str(path),
                'ancestor_paths': refs, 'bytes': count, 'sha256': h.hexdigest(),
                'stat_before': before, 'stat_after': after,
                'expected_original_byte_pin': expected,
                'expected_byte_size_match': None if not expected or 'bytes' not in expected else count == expected['bytes'],
                'expected_whole_byte_sha_match': None if not expected or 'sha256' not in expected else h.hexdigest() == expected['sha256']}
        if native:
            fact['ELF_x86_64_header_observed'] = prefix[:4] == b'\x7fELF' and prefix[4:6] == b'\x02\x01' and prefix[18:20] == b'>\x00'
            require(fact['ELF_x86_64_header_observed'], 'native_not_ELF_x86_64')
        self.observed_files[str(path)] = before
        return fact

    def git(self, *args):
        self.tick()
        command = [str(GIT), '--no-replace-objects', '-c', 'core.hooksPath=/dev/null',
                   '-c', 'core.fsmonitor=false', '-c', 'diff.external=',
                   '-C', str(PRIMARY), *args]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1',
                     'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'},
                timeout=min(20, max(0.1, self.end - time.monotonic())))
        except subprocess.TimeoutExpired:
            raise Refused('fixed_read_only_Git_timeout') from None
        require(len(result.stdout) <= MAX_GIT_OUTPUT and len(result.stderr) <= MAX_GIT_OUTPUT,
                'read_only_Git_output_bound')
        require(result.returncode == 0, 'read_only_Git_refused')
        self.charge(len(result.stdout))
        return result.stdout

    def source_state(self):
        self.route(PRIMARY, leaf_directory=True)
        require(self.git('rev-parse', 'HEAD').decode().strip() == self.args.expected_primary,
                'primary_HEAD_not_expected_R')
        require(self.git('branch', '--show-current').decode().strip() == 'yanrujhou_main',
                'primary_branch_not_yanrujhou_main')
        require(self.git('rev-parse', 'refs/remotes/origin/yanrujhou_main').decode().strip() == self.args.expected_primary,
                'origin_yanrujhou_main_not_expected_R')
        require(self.git('rev-parse', 'codex/lanl-ticket11-source-c').decode().strip() == C,
                'retained_C_ref_not_exact')
        require(not self.git('diff', '--no-ext-diff', '--name-only')
                and not self.git('diff', '--cached', '--no-ext-diff', '--name-only'),
                'primary_tracked_or_staged_dirty')
        status = self.git('status', '--porcelain', '--untracked-files=all')
        require(status == b'?? swdb-project/records/.retention.lock\n', 'primary_retention_only')
        retained = self.read_file(PRIMARY / 'swdb-project/records/.retention.lock',
                                  {'bytes': 0, 'sha256': hashlib.sha256(b'').hexdigest()})
        require(retained['expected_byte_size_match'] and retained['expected_whole_byte_sha_match'],
                'retention_not_original_empty_bytes')
        crows = self.git('ls-tree', '-r', '-z', C, '--', 'swdb-project/swdb')
        rrows = self.git('ls-tree', '-r', '-z', self.args.expected_primary, '--', 'swdb-project/swdb')
        require(crows == rrows, 'C_core_namespace_changed')
        modules = sum(bool(z) and z.split(b'\t', 1)[1].endswith(b'.py') for z in crows.split(b'\0'))
        require(modules == 185, 'C_module_count_not_185')
        return {'primary_HEAD': self.args.expected_primary, 'branch': 'yanrujhou_main',
                'retained_C': C, 'Git_core_namespace_equal_C': True, 'Python_module_count': modules,
                'inherited_F6_from_exact_C_namespace': F6,
                'physical_future_source_S_not_inspected': True, 'retention_byte_fact': retained}

    def compiler_alias(self):
        alias = Path('/usr/bin/g++-13')
        self.route(alias.parent, native=True, leaf_directory=True)
        before = stamp(alias.lstat())
        require(before['uid'] == 0 and before['nlink'] == 1
                and (stat.S_ISLNK(before['mode']) or stat.S_ISREG(before['mode'])),
                'compiler_alias_not_root_native_route')
        target = alias.resolve(strict=True)
        require(target.parent == Path('/usr/bin'), 'compiler_alias_target_outside_usr_bin')
        link = os.readlink(alias) if stat.S_ISLNK(before['mode']) else None
        actual = self.read_file(target, native=True)
        require(stamp(alias.lstat()) == before and alias.resolve(strict=True) == target
                and (not stat.S_ISLNK(before['mode']) or os.readlink(alias) == link),
                'compiler_alias_changed')
        self.aliases[str(alias)] = {'stat': before, 'resolved': str(target), 'link': link}
        return {'literal_path': str(alias), 'intentional_original_native_alias': True,
                'alias_stat_before': before, 'alias_stat_after': stamp(alias.lstat()),
                'link_target': link, 'canonical_native_byte_fact': actual,
                'compiler_version_executed': False,
                'expected_original_compiler_byte_pin': None,
                'new_observed_byte_pin_not_a_new_compiler_admission': True}

    def run(self):
        require(platform.system() == 'Linux' and platform.machine() == 'x86_64'
                and socket.gethostname().split('.')[0] == 'mbit10' and os.getuid() == UID,
                'actual_host_architecture_or_account')
        require(Path(sys.executable).resolve(strict=True) == PYTHON, 'native_interpreter_route')
        for path, expected in NATIVE_PINS.items():
            fact = self.read_file(Path(path), expected, native=True)
            require(fact['expected_byte_size_match'] and fact['expected_whole_byte_sha_match'],
                    'fixed_native_byte_pin_changed')
            self.put('native_file_observations', fact)
        self.output['source_context_before'] = self.source_state()
        for row in FIXED_DIRECTORIES:
            path, refs = self.route(Path(row['path']), leaf_directory=True)
            self.put('literal_directory_observations', {'original_route': row,
                      'canonical_resolved_path': str(path), 'ancestor_paths': refs,
                      'directory_stat': stamp(path.lstat()),
                      'directory_content_inventory_or_manifest_comparison_performed': False})
        for row in FIXED_FILES:
            self.output['active_original_dependency_path'] = row['path']
            if row['path'] == '/usr/bin/g++-13':
                self.put('literal_file_observations', {'original_route': row,
                                                     'byte_observation': self.compiler_alias()})
            else:
                self.put('literal_file_observations', {'original_route': row,
                      'byte_observation': self.read_file(Path(row['path']), row.get('pin'))})
        for row in GIT_SOURCE_RELATIVE:
            rp = row['repo_path']
            entry = self.git('ls-tree', '-z', self.args.expected_primary, '--', rp)
            require(entry.endswith(b'\0') and entry.count(b'\0') == 1, 'relative_source_not_exact_one_Git_entry')
            info, name = entry[:-1].split(b'\t', 1)
            mode, kind, oid = info.decode().split()
            require(name.decode() == rp and kind == 'blob' and mode in {'100644', '100755'},
                    'relative_source_not_regular_Git_blob')
            data = self.git('show', self.args.expected_primary + ':' + rp)
            actual_oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            require(actual_oid == oid, 'relative_source_Git_bytes_not_object')
            self.put('source_relative_Git_byte_pins', {'original_future_role': row,
                     'revision': self.args.expected_primary, 'repo': str(PRIMARY),
                     'path': rp, 'Git_mode': mode, 'Git_blob_oid': oid,
                     'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                     'future_S_physical_route_or_alias_available': 'UNOBSERVED/PENDING'})
        self.output['active_original_dependency_path'] = None
        self.output['source_context_after'] = self.source_state()
        for name, before in self.observed_files.items():
            after = stamp(Path(name).lstat())
            require(after == before, 'observed_file_changed_before_query_end')
            self.output['original_file_stat_final_observations'][name] = after
        for name, old in self.ancestors.items():
            after = stamp(Path(name).lstat())
            require(identity(after) == old['identity'] and stat.S_ISDIR(after['mode']),
                    'ancestor_identity_changed_before_query_end')
            old['stat_at_final_read'] = after
        for name, old in self.aliases.items():
            path = Path(name)
            require(stamp(path.lstat()) == old['stat'] and str(path.resolve(strict=True)) == old['resolved']
                    and (old['link'] is None or os.readlink(path) == old['link']),
                    'native_alias_changed_before_query_end')
        self.tick()
        self.output['state'] = 'fixed_read_only_byte_query_finished'


def main():
    parser = argparse.ArgumentParser(description='Only this fixed original queued-dependency byte/metadata scope.')
    parser.add_argument('--expected-primary', required=True)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[0-9a-f]{40}', args.expected_primary), 'actual_delivered_R40_required')
    require(re.fullmatch('[0-9a-f]{64}', args.source_sha256), 'parent_stdin_source_pin_required')
    query = Query(args)
    result = 1
    try:
        query.run()
        result = 0
    except BaseException as error:
        query.output['failure'] = {'class': type(error).__name__,
              'code': str(error) if isinstance(error, Refused) else 'original_exception_text_not_transferred'}
        query.output['state'] = 'stopped_with_partial_byte_metadata'
    finally:
        query.output['finished_utc'] = datetime.now(timezone.utc).isoformat()
        query.output['cumulative_bytes_read'] = query.charged
        body = canonical(query.output) + b'\n'
        require(len(body) <= MAX_OUTPUT, 'final_metadata_output_budget')
        sys.stdout.buffer.write(body)
        sys.stdout.buffer.flush()
    return result


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Refused as error:
        print(json.dumps({'format': 'swdb.fixed-dependency-query-startup-refusal.v1',
                          'sealed': False, 'code': str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)

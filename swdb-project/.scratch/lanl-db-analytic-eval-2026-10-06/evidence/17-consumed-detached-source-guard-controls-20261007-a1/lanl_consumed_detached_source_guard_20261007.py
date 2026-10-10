"""Prospective exact-owner detached-source guard. NOT RUN; read-only without --remove.

No default removal set. The future parent must supply and review a sealed plan,
explicit row names, native Git pin, complete raw inventories and pending-alias
custody. This preparation does not clear any path or alter capacity/science.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import pwd
import re
import socket
import stat
import subprocess
import sys
import time

P = pathlib.Path
UID = 114316761
ACCOUNT = 'yanruj'
BASE = P('/data1/yanruj')
PRIMARY = BASE / 'ArchEvolve'
RAW = P('/data/yanruj/EvolveSWDB_runs')
C_PATH = BASE / 'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
COUNT_PATH = BASE / 'ArchEvolve-lanl-generality-counts-20261006-a1'
R14_PATH = BASE / 'ArchEvolve-lanl-generality-final-20261007-a1'
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
COUNT = '821023a86e6c3bb3bf9b2e4fca3722b0edddb4e2'
R14 = 'c4ab2fdbb0b0c57ee9f515522835897f24466d6b'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
EVIDENCE = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/'
LEASES = ('mbit10-evaluation-node0', 'mbit10-evaluation-node1', 'mbit10-evaluation')
# Exact values are generated only from the fully read immutable source audit.
ROWS = {'ArchEvolve-lanl-allocator-a2-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-allocator-a2-20261006', 'head': 'b9dabf361b429f0c07717f1891573f5d5f31b1ab', 'historical_allocated_bytes': 177709056, 'receipts': ['R1', 'R2']}, 'ArchEvolve-lanl-bulk-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-bulk-services-20261006-a1', 'head': 'aaf9a9d24a3b2f18af9a7ad8c445025fea366162', 'historical_allocated_bytes': 249249792, 'receipts': ['R3', 'R4']}, 'ArchEvolve-lanl-bulk-total-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-bulk-total-services-20261006-a1', 'head': '1703c98717ff303fdaa83b8044ac9b4060fedb78', 'historical_allocated_bytes': 275345408, 'receipts': ['R5']}, 'ArchEvolve-lanl-clock-a2-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-clock-a2-20261006', 'head': '05e1b7b05220c06fa1bea39af8881fdda38f818f', 'historical_allocated_bytes': 178987008, 'receipts': ['R6']}, 'ArchEvolve-lanl-float-memory-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-float-memory-services-20261006-a1', 'head': '3006d91e2d076db0104f3b7734131dec5f26caad', 'historical_allocated_bytes': 276357120, 'receipts': ['R7']}, 'ArchEvolve-lanl-independent-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-independent-services-20261006-a1', 'head': '1703c98717ff303fdaa83b8044ac9b4060fedb78', 'historical_allocated_bytes': 275345408, 'receipts': ['R8', 'R9']}, 'ArchEvolve-lanl-memory-a1-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-memory-a1-20261006', 'head': '8e54d74e64c08a29b20eec183b070f3e77a77e43', 'historical_allocated_bytes': 179073024, 'receipts': ['R10']}, 'ArchEvolve-lanl-estimation-role-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a1', 'head': 'a7a9b9e8b9d52245490b7dfd372f3be05f67ce27', 'historical_allocated_bytes': 179896320, 'receipts': ['R11']}, 'ArchEvolve-lanl-estimation-role-20261006-a2': {'path': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a2', 'head': 'a7a9b9e8b9d52245490b7dfd372f3be05f67ce27', 'historical_allocated_bytes': 179896320, 'receipts': ['R12', 'R13']}, 'ArchEvolve-lanl-openmp-projections-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-openmp-projections-20261006-a1', 'head': '8949e10fc228bc1009de19fa9df6c9e1a61808ef', 'historical_allocated_bytes': 152952832, 'receipts': ['R14']}, 'ArchEvolve-lanl-native-object-counts-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-native-object-counts-20261006-a1', 'head': '502fea76159cb7b4c692291ee779dd0235b20c8b', 'historical_allocated_bytes': 153907200, 'receipts': ['R15']}, 'ArchEvolve-lanl-count-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-count-20261006', 'head': 'cda8f2db11996402bcb483bf98440eedc07feaa7', 'historical_allocated_bytes': 113459200, 'receipts': ['O1']}, 'ArchEvolve-lanl-estimates-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-estimates-20261006', 'head': 'b5acc909ef9df813352004e88633fac4db4b55e7', 'historical_allocated_bytes': 136187904, 'receipts': ['O2']}, 'ArchEvolve-lanl-functional-evaluation-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-functional-evaluation-20261006-a1', 'head': 'bef54f9661d099dcf381538522bd4d9573d6fe0c', 'historical_allocated_bytes': 179683328, 'receipts': ['O3']}, 'ArchEvolve-lanl-functional-object-counts-20261006-a2': {'path': '/data1/yanruj/ArchEvolve-lanl-functional-object-counts-20261006-a2', 'head': '9ba9277b2b7cfed25569b4fa73aa683679a588e0', 'historical_allocated_bytes': 153993216, 'receipts': ['O4']}, 'ArchEvolve-lanl-functional-strict-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-functional-strict-20261006', 'head': 'dcb66fc4b9564dc742b310e036e6ee5495330df8', 'historical_allocated_bytes': 152883200, 'receipts': ['O5']}, 'ArchEvolve-lanl-prospective-inputs-20261006-a2': {'path': '/data1/yanruj/ArchEvolve-lanl-prospective-inputs-20261006-a2', 'head': 'c9be522053dffcd8e3308a7c723e2468b942e2a1', 'historical_allocated_bytes': 153923584, 'receipts': ['O6']}, 'ArchEvolve-lanl-root-projection-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-root-projection-20261006', 'head': '30f425b5275765c7ccdb5115ab8bb00f8b5f5e98', 'historical_allocated_bytes': 152977408, 'receipts': ['O7']}}
RECEIPTS = {'R1': {'file': '11-allocator-count-proof-export-mbit10-20261006-a2.json', 'sha256': 'b3bcb23c9af52ffbd713e1120a11292f1fa267bccfb22020604dfac97ea1456b', 'introduced': '40ed8e8e3d81df4435c6d073398d2fcc206c8ccc', 'raw_names': ['lanl-analytic-allocator-counts-20261006-a2']}, 'R2': {'file': '11-allocator-service-mbit10-20261006-a1.json', 'sha256': '71f039f421f38220400fb606e354a803bf8747bf261b75bcffa9151677c0d14f', 'introduced': '2aa3c92c54534fe7c75c23152e46378b68154297', 'raw_names': ['lanl-analytic-allocator-elapsed-20261006-a1']}, 'R3': {'file': '11-bulk-counts-mbit10-20261006-a2.json', 'sha256': '0442d9565ee7bd05490146b20b09155eff668e4c3cb21bdbe86258bb8508067a', 'introduced': '3cf1369979d6533f3e4e7565872fd56e5747dd9c', 'raw_names': ['lanl-analytic-bulk-count-20261006-a2']}, 'R4': {'file': '11-bulk-elapsed-failed-mbit10-20261006-a2.json', 'sha256': '2776f52e7dac7f9adaaa7666078730b7f98f8206aadf49d2740a00cdfe6580bb', 'introduced': '109b7b63c8b4147696e01ce62256fc39d8c8b437', 'raw_names': ['lanl-analytic-bulk-elapsed-20261006-a2']}, 'R5': {'file': '11-bulk-total-elapsed-mbit10-20261006-a1.json', 'sha256': '556dc1556c59c6cde6e24d7d4c2bb7b62b6355d92dc52eae634cf7b8b30074e8', 'introduced': '045990a3bf40240c130fac86274f376521d2edb4', 'raw_names': ['lanl-analytic-bulk-total-elapsed-20261006-a1']}, 'R6': {'file': '11-clock-service-mbit10-20261006-a2.json', 'sha256': '2b52c7e7bc737bd7188ba6a38d587bda828760bf77652b06cf4cf2d46e0eaf4f', 'introduced': '88fcdf6992f86ec0a29a1b5f4626d02ec1a625a5', 'raw_names': ['lanl-analytic-service-clock-20261006-a2']}, 'R7': {'file': '11-float-memory-elapsed-mbit10-20261006-a1.json', 'sha256': '42801f1ee05898b5508aa2fcebda5d79e34dd0033fc2225a1fd9c68fddf02d18', 'introduced': '310dcc1e7e6416b4f8109c47e549575ec86aae5b', 'raw_names': ['lanl-analytic-float-memory-elapsed-20261006-a1']}, 'R8': {'file': '11-openmp-elapsed-mbit10-20261006-a1.json', 'sha256': '4c979ef2f8d06ad0d551e817227b134fc05579cd90eb49476379f2ca896252aa', 'introduced': '3c968303eadb2a08c539ef823708c4f188f778c8', 'raw_names': ['lanl-analytic-openmp-elapsed-20261006-a1']}, 'R9': {'file': '11-allocator-extra-elapsed-mbit10-20261006-a1.json', 'sha256': 'e2b41c3058cfe739a24902d281a8d324c1055d53f4ccd57b83220608b549069b', 'introduced': '2cbd99dddda2f468c1b241efd86b327ef885acf3', 'raw_names': ['lanl-analytic-allocator-extra-elapsed-20261006-a1']}, 'R10': {'file': '11-memory-service-mbit10-20261006-a1.json', 'sha256': 'abc9ed15d2630d5796a86b72cc75cba8532ebe70076747d61acf52bacc8eceb3', 'introduced': '4f70136e4dd8a6862597d67ec5244fde807bc374', 'raw_names': ['lanl-analytic-service-memory-20261006-a1']}, 'R11': {'file': '10-estimation-role-failed-mbit10-20261006-a1.json', 'sha256': 'abc19a352f925afef52a85a7375ce31ab57446902dcd0976a742202112f8ef15', 'introduced': 'f9c6908f254673cd684992c86949bfaa8f16601c', 'raw_names': ['lanl-estimation-role-20261006-a1']}, 'R12': {'file': '10-estimation-role-postfill-custody-mbit10-20261006-a2.json', 'sha256': '371fd88f9aad6a889ee37fa28d93cf5ef1365f2249f07294be16be9defd7d24d', 'introduced': 'f9c6908f254673cd684992c86949bfaa8f16601c', 'raw_names': ['lanl-estimation-role-20261006-a2']}, 'R13': {'file': '10-estimation-role-mbit10-20261006-a2-postfill-a1.json', 'sha256': '15f6286ad05962435fd7c4e0a59fb53fc630b1e646aa5b780d0c02de8a6abcac', 'introduced': 'f9c6908f254673cd684992c86949bfaa8f16601c', 'raw_names': ['lanl-estimation-role-20261006-a2-postfill-a1']}, 'R14': {'file': '11-openmp-call-projections-mbit10-20261006-a1.json', 'sha256': '10a97b290c98862ab0be45c48371f2a0d66060f5a19db819bcd63472bf912e68', 'introduced': '538adc376f945eee9741da1dc1806cb5e22f37b5', 'raw_names': ['lanl-analytic-openmp-call-projections-20261006-a1']}, 'R15': {'file': '11-object-counts-mbit10-20261006-a1.json', 'sha256': 'b8ad78de127faef908cc74313ee6f6b4fbffe69bd03c3fc34ba00332d4ad39cb', 'introduced': 'e361e83b64578890003ac001e7d6e344556a1876', 'raw_names': ['lanl-analytic-cpu-object-counts-20261006-a1', 'lanl-analytic-cpu-object-counts-g17-20261006-a1']}, 'O1': {'file': 'cpu-count-equivalence-mbit10-20261006-a2.json', 'sha256': '45b95c1d4ce9817bfd87976d984fc0183010a1f19e94b8e80ec94d6ce45d88fe', 'introduced': 'eaa56d057bb0bbcfb42e64fdb4266d2d04c3f0d4', 'raw_names': ['lanl-analytic-count-equivalence-20261006-a2']}, 'O2': {'file': 'bound-calibration-fixture-mbit10-20261006-a1.json', 'sha256': 'f36c5b1f24cf09403c78bd94a6cdb87ebf74a4828c20625493fffbaff3935f91', 'introduced': '68df1ddbab971ca6cb51f66ae74ae2f4cb62acca', 'raw_names': ['lanl-analytic-bound-estimates-20261006-a1']}, 'O3': {'file': '12-functional-evaluation-mbit10-20261006-a1.json', 'sha256': 'eb4f41b6d067a9c1ed34e0e9f3fab7f1037f144f07178a945335b832e650b1b2', 'introduced': '6f6ab0092da57dbfdfa2e318a9a218bd73e6223f', 'raw_names': ['lanl-functional-evaluation-20261006-a1']}, 'O4': {'file': '09-functional-counts-mbit10-20261006-a2.json', 'sha256': '6e7aecd48fe04183da2b162fce5ef64fd26de1dcccaa66117262235755a71c84', 'introduced': 'c01c0e5645f87718128b4605261d0cb4dabcd84a', 'raw_names': ['lanl-functional-dx-object-counts-20261006-a2']}, 'O5': {'file': 'functional-bfs-certification-mbit10-20261006-a2.json', 'sha256': 'f449316d9482169e5708271f3dee930f6077f60564dbf38c727f5a2f4d311c78', 'introduced': '31b4de8a81fe4ade8e497565903bce14b2c475b8', 'raw_names': ['lanl-functional-bfs-strict-20261006-a2']}, 'O6': {'file': '17-prospective-inputs-mbit10-20261006-a2.json', 'sha256': 'bb9211833862ea8575b26d178da3abbb23129f89e723862882a04b397777e652', 'introduced': '490abaf96eb564b8f5b58ecf2beb1f615e523a27', 'raw_names': ['lanl17-prospective-inputs-20261006-a2']}, 'O7': {'file': '11-normalized-root-projection-mbit10-20261006-a1.json', 'sha256': 'dc8c3a6751b65bcd39f9af41e9d70ed3a61ded4b6305a4e68ba12fab3d9145d6', 'introduced': 'a5d983ac09fbc5b36babc4989d83ca4b87fe7e6a', 'raw_names': ['lanl-native-root-projection-20261006-a1']}}
FUTURE_SOURCE_HASHES = {'lanl17_parent_helpers_cleanup60_a4.py': {'bytes': 38195, 'sha256': '28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'}, 'lanl17_metadata_supervisor_cleanup60_a4.py': {'bytes': 8014, 'sha256': 'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'}, 'lanl17_metadata_dispatch_guard_cleanup60_a4_20261007.py': {'bytes': 14577, 'sha256': '9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'}, 'lanl17_compact_attempt_custody_a2r1_20261007.py': {'bytes': 24818, 'sha256': 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'}, 'lanl17_selected_record_trajectory_auditor_a2r1s1_20261007.py': {'bytes': 115130, 'sha256': '6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'}, 'lanl17_parent_capture_projection_producer_a3_20261007.py': {'bytes': 46165, 'sha256': '32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'}, 'lanl17_write_parent_full_record_index_20261007.py': {'bytes': 33445, 'sha256': '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'}, 'lanl17_author_parent_full_record_index_request_r1_20261007.py': {'bytes': 38266, 'sha256': 'a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d'}, 'lanl17_read_passive_one_catalog_inventory_20261007.py': {'bytes': 29653, 'sha256': '76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176'}, 'lanl17_author_first_publication_request_r1_20261007.py': {'bytes': 28419, 'sha256': '791f95b5f53c23740ce8b2bdd72fc8dcd625494a60f5399f30b5ed704347fb1a'}, 'lanl17_remote_original_index_writer_privacy_envelope_20261007.py': {'bytes': 38790, 'sha256': '1ee5ffbdf1ef322cfd5bfec4b6e402c29d23c776e855f01d25208ebbece0fcfc'}, 'lanl17_remote_original_index_writer_private_outer_capture_20261007.py': {'bytes': 34658, 'sha256': '59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544'}, 'lanl17_original_index_writer_outermost_private_bootstrap_20261007.sh': {'bytes': 6549, 'sha256': '0d1eb650d1bcb1a9f491d5fb790f083e371875ddd20fe0bf1f42d5fce05a9217'}}
PREPARATION_PINS = {
    'source_note': ('lanl17-storage-planning-source-note-20261007-r1.md', 13212, 'c4f6b466d711fee54050109261a6ff43a5b73e0bc7bb2444c8b3d29c3ac281f2'),
    'reference_audit': ('lanl17-consumed-detached-source-reference-audit-20261007-r1.md', 19094, '1c95063ca5364d5bafa98f87fe745c1450811ffaae11c3b7673459f639e9d8d3'),
    'original_export_guard': ('lanl-clean-consumed-old-exports-20261007.py', 5361, '0946444ab815d312b84afbf4b76084a7df07cd71e7c4ffc5d5907a29ce233701'),
}
# These are new finite storage-inspection limits, not scientific or job caps.
LIMITS = {'seconds': 3600, 'git_seconds': 120, 'git_output': 32*1024*1024,
          'plan_bytes': 2*1024*1024, 'inventory_bytes': 32*1024*1024,
          'one_file': 512*1024*1024, 'total_file_bytes': 16*1024*1024*1024,
          'walk_entries': 400000, 'tracked_entries': 20000,
          'processes': 10000, 'process_fds': 200000,
          'one_proc_bytes': 16*1024*1024, 'receipt_bytes': 256*1024}

class Refused(Exception):
    pass

def require(condition, code):
    if not condition:
        raise Refused(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()

def strict_json(raw):
    def pairs(rows):
        d = {}
        for k, v in rows:
            require(k not in d, 'duplicate_json_key')
            d[k] = v
        return d
    def bad(value):
        raise Refused('nonfinite_json')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def stamp(s):
    return {k: getattr(s, 'st_'+k) for k in
            ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'mtime_ns', 'ctime_ns')}

def inside(value, root):
    return value == str(root) or value.startswith(str(root)+'/')

def any_inside(value, paths):
    return any(inside(value.removesuffix(' (deleted)'), p) for p in paths)

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class Guard:
    def __init__(self, args):
        self.args = args
        self.deadline = time.monotonic()+LIMITS['seconds']
        self.read_bytes = 0
        self.walk_entries = 0
        self.proc_fds = 0
        self.plan = None
        self.selected = [BASE/name for name in args.select]
        self.protected_stats = {}
        self.protected_refs = None
        self.baseline = {}
        self.raw_before = {}
        self.current_removal = None
        self.output = None
        self.native_git_stat = None
        self.facts = {'format': 'swdb.consumed-detached-source-guard.v1',
                      'canonical_ensure_ascii': True, 'started_at': now(),
                      'remove_requested': args.remove, 'selected_rows': args.select,
                      'removed_rows': [], 'failure': None, 'admitted': False,
                      'historical_references_retain_original_bytes': True,
                      'capacity_gates_scientific_caps_provider_auth_raw_refs_objects_unchanged': True,
                      'inspection_limits': LIMITS, 'external_processes_killed': False,
                      'actual_recovery_not_guaranteed': True,
                      'admission_scope': 'selected storage inspection/removal only',
                      'scientific_admission': False}

    def left(self):
        n = self.deadline-time.monotonic()
        require(n > 0, 'inspection_deadline')
        return n

    def path(self, path, directory=False, allow_primary_mode=False):
        p = P(path)
        denied = [BASE/x for x in ('.codex', '.ssh', '.aws', '.claude')]
        require(not any(inside(str(p), q) for q in denied)
                and p.name not in ('auth.json', 'credentials', 'credentials.json', 'id_rsa', 'id_ed25519'),
                'auth_or_credential_route_refused')
        require(p.is_absolute() and '..' not in p.parts and '.' not in p.parts,
                'noncanonical_path')
        for q in (p, *p.parents):
            require(not q.is_symlink(), 'symlink_component')
        require(p.resolve(strict=True) == p, 'resolved_path_mismatch')
        s = p.lstat()
        require(s.st_uid == UID, 'wrong_owner')
        require(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode),
                'wrong_file_type')
        special = allow_primary_mode and p == PRIMARY and \
            p.parent.stat().st_uid == UID and stat.S_IMODE(p.parent.stat().st_mode) == 0o700
        require(not s.st_mode & 0o022 or special, 'writable_untrusted_path')
        require(not s.st_mode & 0o7000 or special, 'special_permission_bits')
        return p, s

    def read(self, path, cap=None):
        self.left()
        p, before = self.path(path)
        require(before.st_nlink == 1, 'linked_regular_file')
        cap = LIMITS['one_file'] if cap is None else cap
        require(before.st_size <= cap, 'file_size_limit')
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            require(stamp(os.fstat(fd)) == stamp(before), 'file_open_identity_changed')
            pieces = []
            count = 0
            while True:
                self.left()
                b = os.read(fd, min(1024*1024, cap-count+1))
                if not b:
                    break
                count += len(b)
                self.read_bytes += len(b)
                require(count <= cap and self.read_bytes <= LIMITS['total_file_bytes'],
                        'cumulative_read_limit')
                pieces.append(b)
            require(count == before.st_size and stamp(os.fstat(fd)) == stamp(before)
                    and stamp(p.lstat()) == stamp(before), 'file_read_identity_changed')
            return b''.join(pieces), stamp(before)
        finally:
            os.close(fd)

    def pinned(self, pin, cap=None):
        require(set(pin) >= {'path', 'bytes', 'sha256'} and
                (inside(pin['path'], BASE) or inside(pin['path'], RAW)), 'incomplete_or_outside_file_pin')
        raw, st = self.read(pin['path'], cap)
        require(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'file_pin_changed')
        if 'stat' in pin:
            require(st == pin['stat'], 'pinned_stat_changed')
        return raw

    def sealed(self, pin, cap=None):
        require(pin.get('canonical_ensure_ascii') is True and
                re.fullmatch('[0-9a-f]{64}', pin.get('identity_sha256', '')),
                'mandatory_seal_pin_missing')
        raw = self.pinned(pin, cap)
        d = strict_json(raw)
        require(d.get('canonical_ensure_ascii') is True and
                d.get('identity_sha256') == pin['identity_sha256']
                and pin.get('format') == d.get('format'), 'seal_policy_or_format_changed')
        body = dict(d)
        body.pop('identity_sha256')
        require(sha(canonical(body)) == pin['identity_sha256'], 'seal_changed')
        return d

    def native_git(self):
        p = P('/usr/bin/git')
        require(not any(x.is_symlink() for x in (p, *p.parents)), 'native_git_symlink')
        st = p.lstat()
        require(stat.S_ISREG(st.st_mode) and st.st_uid == 0 and not st.st_mode & 0o7022,
                'native_git_owner_mode')
        if self.native_git_stat is None:
            require(st.st_size <= LIMITS['inventory_bytes'], 'native_git_size_limit')
            fd = os.open(p, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
            try:
                require(stamp(os.fstat(fd)) == stamp(st), 'native_git_open_changed')
                chunks = []
                while True:
                    b = os.read(fd, 1024*1024)
                    if not b: break
                    chunks.append(b)
                raw = b''.join(chunks)
                require(stamp(os.fstat(fd)) == stamp(st) and stamp(p.lstat()) == stamp(st),
                        'native_git_read_changed')
                pin = self.plan['native_git_pin']
                require(pin['path'] == str(p) and pin['bytes'] == len(raw)
                        and pin['sha256'] == sha(raw), 'native_git_pin_changed')
                self.native_git_stat = stamp(st)
            finally:
                os.close(fd)
        require(stamp(st) == self.native_git_stat, 'native_git_replaced')

    def git(self, path, *args):
        self.left()
        self.native_git()
        env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'GIT_NO_LAZY_FETCH': '1',
               'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0', 'GIT_PAGER': 'cat',
               'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}
        command = ['/usr/bin/git', '-c', 'protocol.allow=never', '-c', 'core.fsmonitor=false',
                   '-c', 'core.hooksPath=/dev/null', '-C', str(path), *args]
        r = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           env=env, timeout=min(LIMITS['git_seconds'], self.left()), check=False)
        require(len(r.stdout)+len(r.stderr) <= LIMITS['git_output'], 'git_output_limit')
        self.native_git()
        require(r.returncode == 0 and not r.stderr, 'git_refused')
        return r.stdout

    def text_git(self, path, *args):
        return self.git(path, *args).decode().strip()

    def leases(self):
        facts = {}
        for name in LEASES:
            p = BASE/'lact-host-lease'/(name+'.meta.json')
            raw, st = self.read(p, 128*1024)
            d = strict_json(raw)
            require(d.get('state') == 'released', 'socket_lease_not_released')
            facts[name] = {'sha256': sha(raw), 'stat': st, 'state': 'released'}
        return facts

    def retain_git(self):
        expected = self.args.expected_primary
        require(self.text_git(PRIMARY, 'rev-parse', '--show-toplevel') == str(PRIMARY),
                'primary_path_changed')
        require(self.text_git(PRIMARY, 'branch', '--show-current') == 'yanrujhou_main',
                'primary_branch_changed')
        for ref in ('HEAD', 'refs/heads/yanrujhou_main', 'refs/remotes/origin/yanrujhou_main',
                    'refs/remotes/origin/codex/lanl-analytic-eval'):
            require(self.text_git(PRIMARY, 'rev-parse', ref) == expected,
                    'primary_not_fully_delivered')
        require(not self.git(PRIMARY, 'diff', '--name-only') and
                not self.git(PRIMARY, 'diff', '--cached', '--name-only'), 'primary_tracked_dirty')
        require(self.text_git(PRIMARY, 'rev-parse', 'codex/lanl-ticket11-source-c') == C,
                'retained_source_C_ref_changed')
        require(self.text_git(PRIMARY, 'rev-parse', '--show-object-format') == 'sha1',
                'unexpected_git_object_format')
        refs = self.git(PRIMARY, 'for-each-ref', '--format=%(refname) %(objectname)')
        if self.protected_refs is None:
            self.protected_refs = refs
        require(refs == self.protected_refs, 'retained_refs_changed')
        common = P(self.text_git(PRIMARY, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
        require(common == PRIMARY/'.git' and common.is_dir() and not common.is_symlink(),
                'shared_git_store_changed')
        for p, commit in ((C_PATH, C), (COUNT_PATH, COUNT), (R14_PATH, R14)):
            self.path(p, directory=True)
            require(self.text_git(p, 'rev-parse', 'HEAD') == commit and
                    not self.git(p, 'status', '--porcelain', '--untracked-files=all'),
                    'protected_execution_source_changed')
        # Compare exact Python entries; no estimator module import/Store construction.
        def python_entries(rev):
            rows = self.git(PRIMARY, 'ls-tree', '-r', '-z', rev, '--', 'swdb-project/swdb')
            return [x for x in rows.split(b'\0') if x and x.split(b'\t', 1)[1].endswith(b'.py')]
        a = python_entries(C)
        require(len(a) == 185 and a == python_entries(expected), 'F6_source_blob_changed')
        return {'expected_primary': expected, 'C': C, 'F6': F6,
                'retained_refs_sha256': sha(refs), 'Python_blob_entries_exact_C': 185}

    def tree(self, path, expected_head):
        self.path(path, directory=True)
        require(self.text_git(path, 'rev-parse', 'HEAD') == expected_head,
                'candidate_HEAD_changed')
        require(not self.text_git(path, 'branch', '--show-current'), 'candidate_not_detached')
        require(not self.git(path, 'status', '--porcelain', '--untracked-files=all'),
                'candidate_not_clean')
        require(not self.git(path, 'ls-files', '--others', '--ignored', '--exclude-standard', '-z'),
                'candidate_has_ignored_files')
        require(self.text_git(path, 'rev-parse', '--path-format=absolute', '--git-common-dir')
                == str(PRIMARY/'.git'), 'candidate_different_common_git')
        rows = [x for x in self.git(PRIMARY, 'ls-tree', '-r', '-z', expected_head).split(b'\0') if x]
        require(len(rows) <= LIMITS['tracked_entries'], 'tracked_entry_limit')
        total = 0
        allocated = 0
        inventory = []
        for row in rows:
            meta, name = row.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            require(kind == 'blob' and mode in ('100644', '100755', '120000'),
                    'unsupported_tracked_entry')
            rel = P(name.decode())
            require(not rel.is_absolute() and '..' not in rel.parts, 'tracked_path_escape')
            p = path/rel
            for parent in p.parents:
                if parent == path:
                    break
                require(not parent.is_symlink(), 'tracked_parent_symlink')
            before = p.lstat()
            require(before.st_uid == UID, 'tracked_file_wrong_owner')
            if mode == '120000':
                require(stat.S_ISLNK(before.st_mode), 'tracked_symlink_mode_changed')
                data = os.readlink(p).encode()
                require(stamp(p.lstat()) == stamp(before), 'tracked_symlink_changed')
            else:
                data, got = self.read(p)
                require(stat.S_IMODE(before.st_mode) == (0o755 if mode == '100755' else 0o644),
                        'tracked_permission_mode_changed')
                require(got == stamp(before), 'tracked_identity_changed')
            actual_oid = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            require(actual_oid == oid, 'tracked_source_bytes_changed')
            total += len(data)
            allocated += before.st_blocks*512
            inventory.append([mode, oid, str(rel), sha(data)])
        # Detached worktree registration/git-file is also required; no embedded repositories.
        gd, _ = self.read(path/'.git', 4096)
        require(gd.startswith(b'gitdir: '+str(PRIMARY/'.git/worktrees').encode()+b'/') and
                gd.count(b'\n') == 1, 'candidate_git_registration_changed')
        self.git(PRIMARY, 'merge-base', '--is-ancestor', expected_head, C)
        self.git(PRIMARY, 'merge-base', '--is-ancestor', expected_head, self.args.expected_primary)
        objects = self.git(PRIMARY, 'rev-list', '--objects', expected_head).splitlines()
        require(len(objects) <= LIMITS['walk_entries'], 'retained_object_limit')
        ids = [x.split(b' ', 1)[0] for x in objects]
        # cat-file --batch-check checks presence without serializing source/record bodies.
        self.native_git()
        r = subprocess.run(['/usr/bin/git', '-c', 'protocol.allow=never', '-C', str(PRIMARY),
                            'cat-file', '--batch-check=%(objectname) %(objecttype)'],
                           input=b'\n'.join(ids)+b'\n', stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=min(120, self.left()),
                           env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'GIT_NO_LAZY_FETCH': '1',
                                'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_NOSYSTEM': '1',
                                'GIT_CONFIG_GLOBAL': '/dev/null'}, check=False)
        self.native_git()
        require(r.returncode == 0 and not r.stderr and len(r.stdout) <= LIMITS['git_output']
                and len(r.stdout.splitlines()) == len(ids)
                and all(x.split()[-1] in (b'blob', b'tree', b'commit', b'tag')
                        for x in r.stdout.splitlines()), 'retained_git_object_missing')
        return {'head': expected_head, 'tree': self.text_git(path, 'rev-parse', 'HEAD^{tree}'),
                'tracked_entries': len(rows), 'tracked_logical_bytes': total,
                'tracked_allocated_bytes_observed': allocated,
                'tracked_mode_blob_source_inventory_sha256': sha(canonical(inventory)),
                'gitfile_sha256': sha(gd), 'directory_stat': stamp(path.lstat()),
                'retained_objects': len(ids), 'detached_clean_ignored0_untracked0': True}

    def walk(self, root):
        self.path(root, directory=True)
        for folder, dirs, files in os.walk(root, topdown=True, followlinks=False,
                                          onerror=lambda e: (_ for _ in ()).throw(Refused('walk_inaccessible'))):
            self.left()
            for name in sorted(dirs+files):
                self.left()
                p = P(folder)/name
                self.walk_entries += 1
                require(self.walk_entries <= LIMITS['walk_entries'], 'walk_entry_limit')
                s = p.lstat()
                require(s.st_uid == UID, 'walk_wrong_owner')
                yield p, s

    def raw_inventory(self, root):
        result = {}
        root = P(root)
        require(root.parent == RAW and root.name.startswith(('lanl-', 'lanl17-')),
                'raw_scope_escape')
        result['.'] = {'stat': stamp(root.lstat()), 'type': 'directory'}
        for p, s in self.walk(root):
            rel = str(p.relative_to(root))
            item = {'stat': stamp(s)}
            if stat.S_ISLNK(s.st_mode):
                item['type'] = 'symlink'
                item['link'] = os.readlink(p)
                try:
                    resolved = str(p.resolve(strict=True))
                except (OSError, RuntimeError):
                    raise Refused('raw_link_unresolved')
                require(not any_inside(resolved, self.selected), 'raw_link_live_source_dependency')
            elif stat.S_ISDIR(s.st_mode):
                item['type'] = 'directory'
            elif stat.S_ISREG(s.st_mode):
                item['type'] = 'file'
                b, got = self.read(p)
                require(got == stamp(s), 'raw_file_identity_changed')
                item['sha256'] = sha(b)
            else:
                raise Refused('unsupported_raw_entry')
            result[rel] = item
        return result

    def receipts_and_raw(self):
        for key, row in RECEIPTS.items():
            p = PRIMARY/EVIDENCE/row['file']
            raw, _ = self.read(p, LIMITS['inventory_bytes'])
            require(sha(raw) == row['sha256'], 'original_receipt_bytes_changed')
            # Receipt file bytes are fixed originals; no guessed canonical writer or reseal.
            self.git(PRIMARY, 'merge-base', '--is-ancestor', row['introduced'], self.args.expected_primary)
        needed = {str(RAW/name) for x in RECEIPTS.values() for name in x['raw_names']}
        siblings = self.plan['raw_control_sibling_paths']
        require(len(set(siblings)) == len(siblings), 'duplicate_control_sibling')
        routes = sorted(needed | set(siblings))
        require(self.plan['control_siblings_complete_review']['complete'] is True,
                'control_sibling_coverage_missing')
        parent_raw_names = {p.name for p in RAW.iterdir() if p.name.startswith(('lanl-', 'lanl17-'))}
        results = {}
        for root in routes:
            actual = self.raw_inventory(root)
            results[root] = sha(canonical(actual))
        for pin in self.plan['original_raw_file_pins']:
            require(pin['receipt_key'] in RECEIPTS and
                    any(inside(pin['path'], P(root)) for root in routes),
                    'original_raw_pin_outside_receipt_routes')
            self.pinned(pin)
        require(self.plan['original_raw_files_complete_review']['complete'] is True,
                'original_raw_file_pin_coverage_missing')
        # All current LANL raw links are checked, including unrelated retained runs.
        for name in sorted(parent_raw_names):
            root = RAW/name
            require(root.is_dir() and not root.is_symlink(), 'raw_root_redirect')
            for p, s in self.walk(root):
                if stat.S_ISLNK(s.st_mode):
                    try:
                        target = str(p.resolve(strict=True))
                    except (OSError, RuntimeError):
                        raise Refused('raw_link_unresolved')
                    require(not any_inside(target, self.selected), 'raw_link_live_source_dependency')
        return results

    def proc_read(self, path, cap):
        try:
            with open(path, 'rb') as f:
                b = f.read(cap+1)
            require(len(b) <= cap, 'process_read_limit')
            self.read_bytes += len(b)
            require(self.read_bytes <= LIMITS['total_file_bytes'], 'cumulative_process_read_limit')
            return b
        except FileNotFoundError:
            require(not path.parent.exists(), 'relevant_proc_field_missing')
            return None
        except PermissionError:
            raise Refused('relevant_proc_field_inaccessible')

    def process_references(self):
        pids = sorted(p for p in P('/proc').iterdir() if p.name.isdecimal())
        require(len(pids) <= LIMITS['processes'], 'process_count_limit')
        relevant = 0
        for proc in pids:
            self.left()
            status = self.proc_read(proc/'status', LIMITS['one_proc_bytes'])
            if status is None:
                continue
            fields = {}
            for line in status.decode().splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    fields[k] = v.strip()
            uids = [int(x) for x in fields['Uid'].split()]
            caps = int(fields['CapEff'], 16)
            # Private /data1/yanruj 0700 excludes foreign unprivileged processes.
            if UID not in uids and not (caps & ((1<<1)|(1<<2))):
                continue
            relevant += 1
            before = self.proc_read(proc/'stat', LIMITS['one_proc_bytes'])
            if before is None:
                continue
            start = before[before.rfind(b')')+2:].split()[19]
            if fields.get('State', '').startswith('Z'):
                require(self.proc_read(proc/'maps', LIMITS['one_proc_bytes']) == b''
                        and not list((proc/'fd').iterdir()), 'zombie_retains_references')
                continue
            if fields.get('Kthread') == '1':
                require(UID not in uids, 'unexpected_owner_kernel_thread')
                continue
            try:
                links = [proc/'cwd', proc/'root', proc/'exe']
                links.extend(sorted((proc/'fd').iterdir()))
                self.proc_fds += len(links)
                require(self.proc_fds <= LIMITS['process_fds'], 'process_fd_limit')
                for link in links:
                    try:
                        target = os.readlink(link)
                    except FileNotFoundError:
                        require(not proc.exists() or link.parent == proc/'fd',
                                'relevant_process_link_missing')
                        continue
                    except PermissionError:
                        raise Refused('relevant_process_link_inaccessible')
                    require(not any_inside(target, self.selected), 'live_process_source_dependency')
                    require(not inside(target.removesuffix(' (deleted)'), R14_PATH), 'live_final14_source_process')
                maps = self.proc_read(proc/'maps', LIMITS['one_proc_bytes'])
                cmd = self.proc_read(proc/'cmdline', LIMITS['one_proc_bytes'])
                if maps is None or cmd is None:
                    continue
                for line in maps.decode(errors='strict').splitlines():
                    pieces = line.split(None, 5)
                    if len(pieces) == 6:
                        require(not any_inside(pieces[5], self.selected), 'mapped_source_dependency')
                require(not any(str(p).encode() in cmd for p in self.selected),
                        'live_or_queued_helper_source_dependency')
                require(str(R14_PATH).encode() not in cmd, 'active_final14_command')
                after = self.proc_read(proc/'stat', LIMITS['one_proc_bytes'])
                if after is not None:
                    require(after[after.rfind(b')')+2:].split()[19] == start, 'process_PID_reused')
            except FileNotFoundError:
                require(not proc.exists(), 'relevant_process_field_disappeared')
        return {'relevant_processes': relevant, 'process_links_checked': self.proc_fds,
                'private_parent_excludes_foreign_unprivileged_UIDs': True,
                'inaccessible_privileged_or_owner_process_refuses': True,
                'raw_process_args_maps_auth_environment_not_serialized': True}

    def aliases_and_sources(self):
        require(self.plan['pending_alias_coverage_review']['complete'] is True and
                self.plan['pending_alias_coverage_review']['no_queued_source_consumers'] is True,
                'pending_alias_coverage_missing')
        history = {x['path']: x for x in self.plan['historical_reference_files']}
        require(len(history) == len(self.plan['historical_reference_files']), 'history_pin_duplicate')
        for pin in history.values():
            self.pinned(pin)
            require(pin['handling'] == 'historical_only_not_dereferenced'
                    and isinstance(pin['review_basis'], str) and pin['review_basis'],
                    'historical_classification_missing')
        # Original byte/string mentions are allowed only with exact reviewed custody.
        metadata_roots = [PRIMARY/'swdb-project/records', PRIMARY/EVIDENCE]
        metadata_roots += [RAW/name for row in RECEIPTS.values() for name in row['raw_names']]
        metadata_roots += [P(x) for x in self.plan['raw_control_sibling_paths']]
        metadata_roots = sorted(set(metadata_roots))
        suffixes = {'.json', '.yaml', '.yml', '.md', '.py', '.sh', '.txt'}
        for root in metadata_roots:
            for p, s in self.walk(root):
                if not stat.S_ISREG(s.st_mode) or p.suffix not in suffixes:
                    continue
                b, _ = self.read(p)
                if any(str(x).encode() in b for x in self.selected):
                    require(str(p) in history and sha(b) == history[str(p)]['sha256'],
                            'unclassified_physical_source_reference')
        for pin in self.plan['pending_control_files']:
            b = self.pinned(pin)
            require(not any(str(p).encode() in b for p in self.selected),
                    'pending_control_literal_source_dependency')
            for value in pin['dereferenced_paths']:
                target = P(value)
                require(target.is_absolute() and not any_inside(str(target), self.selected),
                        'pending_control_alias_dependency')
                require(not any_inside(str(target.resolve(strict=True)), self.selected),
                        'pending_control_resolved_alias_dependency')
        require(set(self.plan['future_source_pins']) == set(FUTURE_SOURCE_HASHES),
                'future_source_pin_set_changed')
        for name, expected in FUTURE_SOURCE_HASHES.items():
            pin = self.plan['future_source_pins'][name]
            p = P(pin['path'])
            require(p.parent != PRIMARY and inside(str(p), BASE) and
                    not any_inside(str(p), self.selected) and
                    pin['sha256'] == expected['sha256'] and pin['bytes'] == expected['bytes'],
                    'future_source_route_or_pin_changed')
            b = self.pinned(pin)
            require(not any(str(x).encode() in b for x in self.selected),
                    'future_source_has_selected_dependency')
        # Explicit parent source-byte proofs, when claimed by original receipts.
        for proof in self.plan['receipt_source_file_proofs']:
            require(proof['row'] in self.args.select and proof['receipt_key'] in ROWS[proof['row']]['receipts'],
                    'source_proof_scope_changed')
            require(proof['commit'] == ROWS[proof['row']]['head'], 'source_proof_commit_changed')
            rel = P(proof['relative_path'])
            require(not rel.is_absolute() and '..' not in rel.parts, 'source_proof_path_escape')
            body = self.git(PRIMARY, 'cat-file', 'blob', proof['commit']+':'+str(rel))
            require(sha(body) == proof['sha256'], 'retained_receipt_source_blob_changed')
            if proof['row'] not in self.facts['removed_rows']:
                actual, _ = self.read(BASE/proof['row']/rel)
                require(body == actual, 'receipt_source_byte_proof_changed')
            doc = strict_json(self.read(PRIMARY/EVIDENCE/RECEIPTS[proof['receipt_key']]['file'],
                                        LIMITS['inventory_bytes'])[0])
            for key in proof['receipt_json_path']:
                doc = doc[key]
            require(doc == proof['sha256'], 'original_source_hash_field_changed')
        require(self.plan['receipt_source_proofs_complete_review']['complete'] is True,
                'receipt_source_proof_coverage_missing')
        return {'historical_files': len(history), 'historical_classification_inherited_parent_review': True,
                'pending_alias_coverage_inherited_parent_review': True,
                'future_control_sources_byte_pinned': len(FUTURE_SOURCE_HASHES)}

    def protect(self):
        paths = [PRIMARY, C_PATH, COUNT_PATH, R14_PATH, RAW]
        paths += [P(x) for x in self.plan['additional_protected_paths']]
        for p in paths:
            require(not any_inside(str(p), self.selected) and
                    not any(inside(str(s), p) for s in self.selected), 'protection_scope_overlap')
            if p == PRIMARY:
                _, s = self.path(p, True, True)
            else:
                _, s = self.path(p, True)
            key = str(p)
            fixed = {k: stamp(s)[k] for k in ('dev', 'ino', 'mode', 'uid', 'gid')}
            if key not in self.protected_stats:
                self.protected_stats[key] = fixed
            require(fixed == self.protected_stats[key], 'protected_route_identity_changed')
        for route in self.plan['reserved_absent_paths']:
            p = P(route)
            require((p.parent == BASE and p.name.startswith('ArchEvolve-lanl17-'))
                    or (p.parent == RAW and p.name.startswith('lanl17-')),
                    'reserved_future_route_outside_exact17_family')
            require(not any_inside(str(p), self.selected) and not os.path.lexists(p),
                    'reserved_future_route_exists_or_selected')
        for pin in self.plan['protected_file_pins']:
            require(not any_inside(pin['path'], self.selected), 'protected_file_inside_selection')
            self.pinned(pin)

    def gate(self, compare=False):
        self.left()
        leases = self.leases()
        sources = self.retain_git()
        self.protect()
        trees = {p.name: self.tree(p, ROWS[p.name]['head']) for p in self.selected if p.name not in self.facts['removed_rows']}
        if compare:
            for k, v in trees.items():
                require(v == self.baseline[k], 'pre_remove_checkout_changed')
        raw = self.receipts_and_raw()
        if self.raw_before:
            require(raw == self.raw_before, 'original_raw_inventory_changed_between_checks')
        else:
            self.raw_before = raw
        aliases = self.aliases_and_sources()
        processes = self.process_references()
        later = self.leases()
        require({k:v['sha256'] for k,v in later.items()} == {k:v['sha256'] for k,v in leases.items()},
                'released_lease_generation_changed_during_check')
        self.retain_git()
        return {'leases': leases, 'sources': sources, 'trees': trees,
                'raw_tree_count': len(raw), 'raw_tree_inventory_sha256': sha(canonical(raw)),
                'aliases': aliases, 'processes': processes}

    def perform(self):
        require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
                and os.getuid() == os.geteuid() == UID
                and pwd.getpwuid(UID).pw_name == ACCOUNT, 'wrong_host_account')
        base, s = self.path(BASE, True)
        require(stat.S_IMODE(s.st_mode) == 0o700, 'private_source_parent_required')
        self.path(PRIMARY, True, True)
        self.path(RAW, True)
        require(re.fullmatch('[0-9a-f]{40}', self.args.expected_primary), 'primary_revision_required')
        require(len(set(self.args.select)) == len(self.args.select) and self.args.select,
                'explicit_unique_subset_required')
        require(P(self.args.plan).parent == BASE and P(self.args.plan).name.startswith('lanl-consumed-source-parent-plan-'),
                'parent_plan_route_required')
        raw, st = self.read(self.args.plan, LIMITS['plan_bytes'])
        require(stat.S_IMODE(st['mode']) == 0o600, 'private_parent_plan_required')
        require(sha(raw) == self.args.plan_sha256, 'reviewed_plan_file_changed')
        d = strict_json(raw)
        require(d.get('format') == 'swdb.consumed-detached-source-parent-plan.v1'
                and d.get('canonical_ensure_ascii') is True, 'reviewed_plan_format')
        require(d.get('identity_sha256') == sha(canonical({k:v for k,v in d.items() if k != 'identity_sha256'})),
                'reviewed_plan_seal')
        require(d['selected_rows'] == self.args.select and d['expected_primary'] == self.args.expected_primary,
                'parent_selected_subset_or_revision_changed')
        age = (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(d['checked_at'])).total_seconds()
        require(0 <= age <= 300, 'parent_plan_observation_stale')
        self.plan = d
        own, _ = self.read(P(__file__).absolute(), LIMITS['plan_bytes'])
        require(sha(own) == d['guard_source_sha256'], 'guard_source_changed')
        self.own_sha = sha(own)
        require(d['selection_reason'] and d['allocation_decision']['final_R17_revision']
                and d['allocation_decision']['minimal_selected_subset'] is True,
                'actual_allocation_subset_review_missing')
        # The source does not fabricate the not-yet-known finalR or size requirement.
        require(re.fullmatch('[0-9a-f]{40}', d['allocation_decision']['final_R17_revision']), 'final_R17_pin_missing')
        allocation_pin = d['allocation_observation_pin']
        allocation_raw = self.pinned(allocation_pin, LIMITS['inventory_bytes'])
        allocation = strict_json(allocation_raw)
        if allocation_pin['original_json_policy'] == 'original_unsealed':
            require('identity_sha256' not in allocation, 'original_unsealed_observation_changed')
        else:
            require(allocation_pin['original_json_policy'] == 'explicit_original_seal'
                    and type(allocation_pin['canonical_ensure_ascii']) is bool,
                    'original_allocation_policy_missing')
            body = dict(allocation); got = body.pop('identity_sha256')
            encoded = json.dumps(body,sort_keys=True,separators=(',',':'),
                                 ensure_ascii=allocation_pin['canonical_ensure_ascii'],allow_nan=False).encode()
            require(got == allocation_pin['identity_sha256'] == sha(encoded), 'original_allocation_seal_changed')
        require(d['allocation_decision']['observation_file_sha256'] == allocation_pin['sha256']
                and d['allocation_decision']['selected_rows'] == self.args.select,
                'allocation_decision_not_bound_to_actual_observation')
        review = self.sealed(d['parent_review_pin'], LIMITS['plan_bytes'])
        config = {k:v for k,v in d.items() if k not in ('identity_sha256', 'parent_review_pin')}
        require(review['format'] == 'swdb.consumed-detached-source-parent-review.v1'
                and review['accepted_for_exact_subset'] is True
                and review['reviewed_configuration_sha256'] == sha(canonical(config))
                and review['final14_completed_and_released'] is True,
                'concrete_parent_configuration_or_final14_review_missing')
        native = d['native_git_pin']
        require(native['path'] == '/usr/bin/git', 'fixed_native_git_path_required')
        self.native_git()
        output = BASE/('lanl-consumed-detached-source-guard-20261007-'+self.args.attempt)
        require(not os.path.lexists(output), 'receipt_attempt_already_exists')
        os.mkdir(output, 0o700)
        self.output = output
        for key in ('control_siblings_complete_review', 'pending_alias_coverage_review',
                    'receipt_source_proofs_complete_review', 'original_raw_files_complete_review'):
            require(d[key]['parent_review_identity_sha256'] == d['parent_review_pin']['identity_sha256'],
                    'parent_inherited_review_not_bound')
        self.facts['reviewed_plan_file_sha256'] = sha(raw)
        self.facts['reviewed_plan_identity_sha256'] = d['identity_sha256']
        self.facts['guard_source_sha256'] = self.own_sha
        self.facts['expected_primary'] = self.args.expected_primary
        self.facts['parent_review_identity_sha256'] = d['parent_review_pin']['identity_sha256']
        self.facts['final14_completed_and_released_is_parent_semantic_attestation'] = True
        self.facts['no_concurrent_dispatch_or_queued_writer_is_parent_attestation'] = True
        self.facts['free_before_bytes'] = {p: os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ('/data1','/data')}
        first = self.gate()
        self.baseline = first['trees']
        self.facts['initial_checks'] = first
        for name in self.args.select if self.args.remove else []:
            require(self.left() > LIMITS['git_seconds']+30, 'insufficient_remaining_remove_budget')
            self.gate(compare=True)
            require(sha(self.read(self.args.plan, LIMITS['plan_bytes'])[0]) == self.args.plan_sha256
                    and sha(self.read(P(__file__).absolute(), LIMITS['plan_bytes'])[0]) == self.own_sha,
                    'final_plan_or_own_source_changed')
            self.leases()
            self.process_references()
            # Sole destructive operation; exact audited enum path, no force/prune/GC/branch deletion.
            self.current_removal = {'row': name, 'started_at': now()}
            self.git(PRIMARY, 'worktree', 'remove', str(BASE/name))
            require(not os.path.lexists(BASE/name), 'worktree_remove_incomplete')
            self.current_removal = None
            self.facts['removed_rows'].append(name)
            self.retain_git()
            self.protect()
            require(self.receipts_and_raw() == self.raw_before, 'post_remove_raw_changed')
        self.leases()
        self.retain_git()
        self.protect()
        require(sha(self.read(self.args.plan, LIMITS['plan_bytes'])[0]) == self.args.plan_sha256
                and sha(self.read(P(__file__).absolute(), LIMITS['plan_bytes'])[0]) == self.own_sha,
                'end_plan_or_source_changed')
        self.facts['admitted'] = True
        self.facts['free_after_bytes'] = {p: os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ('/data1','/data')}
        self.facts['actual_data1_available_delta_bytes'] = self.facts['free_after_bytes']['/data1']-self.facts['free_before_bytes']['/data1']
        self.facts['capacity_admission'] = False

    def publish(self):
        self.facts['finished_at'] = now()
        self.facts['bytes_read'] = self.read_bytes
        self.facts['walk_entries_checked'] = self.walk_entries
        self.facts['identity_sha256'] = sha(canonical(self.facts))
        body = json.dumps(self.facts, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False).encode()+b'\n'
        require(len(body) <= LIMITS['receipt_bytes'], 'compact_receipt_limit')
        # Only a fresh private administrative receipt; raw/source/old scripts remain untouched.
        require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
                and os.getuid() == os.geteuid() == UID, 'receipt_host_account_required')
        self.path(BASE, True)
        out = self.output
        if out is None:
            out = BASE/('lanl-consumed-detached-source-guard-20261007-'+self.args.attempt)
            require(not os.path.lexists(out), 'receipt_attempt_already_exists')
            os.mkdir(out, 0o700)
        self.path(out, True)
        require(stat.S_IMODE(out.stat().st_mode) == 0o700, 'receipt_directory_mode_changed')
        fd = os.open(out/'receipt.json', os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(body); f.flush(); os.fsync(f.fileno())
        except BaseException:
            raise Refused('receipt_publication_failed')
        print(json.dumps({'format':'swdb.consumed-source-guard-return.v1',
                          'path':str(out/'receipt.json'), 'bytes':len(body), 'sha256':sha(body),
                          'identity_sha256':self.facts['identity_sha256'],
                          'admitted':self.facts['admitted'],
                          'removed_count':len(self.facts['removed_rows']),
                          'failure':self.facts['failure']},sort_keys=True))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--select', action='append', choices=sorted(ROWS), required=True)
    p.add_argument('--expected-primary', required=True)
    p.add_argument('--plan', required=True)
    p.add_argument('--plan-sha256', required=True)
    p.add_argument('--attempt', required=True)
    p.add_argument('--remove', action='store_true')
    a = p.parse_args()
    require(re.fullmatch('a[1-9][0-9]*', a.attempt), 'fixed_receipt_attempt_token')
    require(re.fullmatch('[0-9a-f]{64}', a.plan_sha256), 'plan_pin_required')
    g = Guard(a)
    import signal
    def stop(signum, frame):
        raise Refused('administrative_signal_'+str(signum))
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, stop)
    code = 0
    try:
        g.perform()
    except BaseException as e:
        code = 1
        # No exception text, full argv, raw logs, prompts, environment or credentials.
        g.facts['failure'] = str(e) if isinstance(e, Refused) else type(e).__name__
        g.facts['partial_failure_rows_already_removed'] = list(g.facts['removed_rows'])
        if g.current_removal is not None:
            g.facts['incomplete_removal_attempt'] = {**g.current_removal,
                'directory_present_after_failure': os.path.lexists(BASE/g.current_removal['row']),
                'disposition': 'unknown_until_parent_inspection_no_retry_or_rollback'}
    try:
        g.publish()
    except BaseException:
        print(json.dumps({'format':'swdb.consumed-source-guard-return.v1',
                          'admitted':False, 'receipt_publication_failed':True,
                          'removed_count':len(g.facts['removed_rows'])},sort_keys=True))
        code = 1
    return code

if __name__ == '__main__':
    raise SystemExit(main())

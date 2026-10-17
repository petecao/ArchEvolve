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
          'stat_checks': 2000000, 'processes': 10000, 'process_fds': 200000,
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

def tracked_mode_equivalent(physical_mode, git_mode, effective_private):
    # Keep all read/execute/owner bits exact; only historical optional 022 is allowed.
    require(git_mode in ('100644', '100755'), 'unsupported_tracked_permission_kind')
    expected = 0o755 if git_mode == '100755' else 0o644
    return physical_mode == expected or (effective_private and
                                          physical_mode & ~0o022 == expected)

def exact_account_pam_service_identification(identification_pin, parent_review_identity_sha256,
                                             check_deadline, charge_bytes):
    """Exact reviewed OS-role exclusion; protected references remain UNOBSERVED.

    Callers must bind the ordinary original file pin in their actual reviewed
    configuration. This helper checks current public identity, not reference
    freedom. Budget callbacks belong to that caller's finite metadata inspection.
    No service descendants, parent, or other unreadable consumer are exempted.
    """
    require(re.fullmatch('[0-9a-f]{64}', parent_review_identity_sha256),
            'account_service_parent_review_identity_missing')
    require(identification_pin['path'] == str(BASE/'lanl-account-pam-service-identification-20261008-a1/identification.json')
            and identification_pin['bytes'] == 3818
            and identification_pin['sha256'] == 'ece0155e6a1e61e07cabb8a05e2a13ac9577a9ee1418e8f8eed450ce310ce0fa',
            'account_service_original_identification_pin_changed')

    def read_fd(fd, cap):
        pieces, count = [], 0
        while True:
            check_deadline()
            part = os.read(fd, min(1024*1024, cap-count+1))
            if not part:
                break
            count += len(part)
            charge_bytes(len(part))
            require(count <= cap, 'account_service_read_limit')
            pieces.append(part)
        return b''.join(pieces)

    def regular_file(path, size, digest, owner, mode=None, original_stat=None):
        check_deadline()
        path = P(path)
        require(path.is_absolute() and path.resolve(strict=True) == path
                and not any(q.is_symlink() for q in (path, *path.parents)),
                'account_service_file_route_changed')
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_uid == owner
                and before.st_nlink == 1 and before.st_size == size
                and not before.st_mode & 0o7000, 'account_service_file_identity_changed')
        if mode is not None:
            require(stat.S_IMODE(before.st_mode) == mode, 'account_service_native_mode_changed')
        if original_stat is not None:
            require(stamp(before) == original_stat, 'account_service_original_file_stat_changed')
        fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            require(stamp(os.fstat(fd)) == stamp(before), 'account_service_file_open_changed')
            raw = read_fd(fd, size)
            require(len(raw) == size and sha(raw) == digest
                    and stamp(os.fstat(fd)) == stamp(before)
                    and stamp(path.lstat()) == stamp(before), 'account_service_file_bytes_or_stat_changed')
        finally:
            os.close(fd)
        return raw, stamp(before)

    # The original document remains UNSEALED; its exact returned bytes are checked.
    base_stat = BASE.lstat()
    require(not any(q.is_symlink() for q in (BASE, *BASE.parents))
            and BASE.resolve(strict=True) == BASE and stat.S_ISDIR(base_stat.st_mode)
            and base_stat.st_uid == UID and stat.S_IMODE(base_stat.st_mode) == 0o700,
            'account_service_original_private_ancestor_changed')
    original, original_stat = regular_file(identification_pin['path'], 3818,
        identification_pin['sha256'], UID, original_stat=identification_pin.get('stat'))
    document = strict_json(original)
    require(document['format'] == 'swdb.exact-account-pam-service-original-identification.v1'
            and document['sealed'] is False and 'identity_sha256' not in document
            and document['stable_exact_process_identities_and_public_metadata'] is True
            and document['semantic_service_classification_and_fresh_creation_chronology_require_parent_review'] is True
            and document['reference_free_or_global_visibility_or_cleanup_clearance_claimed'] is False,
            'account_service_original_identification_policy_changed')

    def proc_bytes(path):
        check_deadline()
        fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            return read_fd(fd, LIMITS['one_proc_bytes'])
        finally:
            os.close(fd)

    def current_process(pid, start, ppid, name, cmd_size, cmd_sha, child):
        proc = P('/proc')/str(pid)
        raw_stat = proc_bytes(proc/'stat')
        values = raw_stat[raw_stat.rfind(b')')+2:].split()
        require(int(values[19]) == start and int(values[1]) == ppid,
                'account_service_current_PID_or_parent_changed')
        fields = {}
        for line in proc_bytes(proc/'status').decode().splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                require(key not in fields, 'account_service_duplicate_status_field')
                fields[key] = value.strip()
        uids = [int(value) for value in fields['Uid'].split()]
        gids = [int(value) for value in fields['Gid'].split()]
        require(fields['Name'] == name and int(fields['PPid']) == ppid
                and uids == [UID]*4 and gids == [UID]*4,
                'account_service_current_name_UID_GID_or_parent_changed')
        require(all(int(fields[key], 16) == 0 for key in ('CapInh','CapPrm','CapEff','CapAmb'))
                and int(fields['CapBnd'], 16) == 0x000001ffffffffff,
                'account_service_capability_predicate_changed')
        if child:
            require(values[0] == b'S' and fields['State'].split()[0] == 'S'
                    and int(fields['Threads']) == 1 and int(fields['TracerPid']) == 0
                    and all(int(fields[key], 16) == 0 for key in ('SigPnd','ShdPnd')),
                    'account_service_child_state_thread_tracer_or_pending_changed')
        cmd = proc_bytes(proc/'cmdline')
        cgroup = proc_bytes(proc/'cgroup')
        require(len(cmd) == cmd_size and sha(cmd) == cmd_sha
                and len(cgroup) == 70
                and sha(cgroup) == 'f6b0978005408a4cbf4759816cf4703b0e097284eabe55f01f1cea870640e455',
                'account_service_current_command_or_cgroup_changed')
        # SigBlk is observed, never required zero/nonzero: wait may temporarily unblock.
        return {'pid':pid, 'start_ticks':start, 'ppid':ppid, 'name':name,
                'uids':uids, 'gids':gids, 'state':values[0].decode(),
                'capability_bound':fields['CapBnd'], 'signal_blocked_observed':fields['SigBlk'],
                'cmdline_pin':{'bytes':len(cmd), 'sha256':sha(cmd)},
                'cgroup_pin':{'bytes':len(cgroup), 'sha256':sha(cgroup)}}

    def boot_identity():
        rows = [line for line in proc_bytes(P('/proc/stat')).splitlines() if line.startswith(b'btime ')]
        require(len(rows) == 1 and int(rows[0].split()[1]) == 1785498067
                and os.sysconf('SC_CLK_TCK') == 100, 'account_service_boot_or_clock_changed')
        return {'boot_epoch':1785498067, 'clock_ticks':100}

    def current_pair():
        return [current_process(359656, 40749693, 359655, '(sd-pam)', 9,
                    '971490059d839d27af3ded30a476216b92689d837b0236a700723fb13640e370', True),
                current_process(359655, 40749691, 1, 'systemd', 49,
                    'a4eb13854c1664d48464c575a8c86538e8a379ecd5e1e40ab6c56b61b9b9ffb5', False)]

    boot_before = boot_identity()
    before = current_pair()
    require(os.readlink(P('/proc/359655/exe')) == '/usr/lib/systemd/systemd',
            'account_service_parent_executable_changed')
    native_constants = [('/usr/lib/systemd/systemd', 100816,
        'b472aadf808bef87c0eb203056a77cb64bd268b71b756306013a53de68a94173'),
        ('/usr/lib/systemd/systemd-executor', 137792,
        'b8424efa6f861031c04310fd7bfe485330bb74f53edae341803ffe3f487fd044')]
    require([(pin['path'], pin['bytes'], pin['sha256']) for pin in document['native_files']]
            == native_constants, 'account_service_original_native_pins_changed')
    native_pins = []
    for path, size, digest in native_constants:
        original_native = next(pin for pin in document['native_files'] if pin['path'] == path)
        raw_native, native_stat = regular_file(path, size, digest, 0, 0o755,
                                              original_native['stat'])
        if path.endswith('/systemd-executor'):
            require(b'(sd-pam)' in raw_native, 'account_service_executor_role_literal_missing')
        native_pins.append({'path':path, 'bytes':size, 'sha256':digest, 'stat':native_stat})
    after = current_pair()
    require([{key:value for key,value in item.items() if key != 'signal_blocked_observed'} for item in before]
            == [{key:value for key,value in item.items() if key != 'signal_blocked_observed'} for item in after]
            and os.readlink(P('/proc/359655/exe')) == '/usr/lib/systemd/systemd'
            and boot_identity() == boot_before, 'account_service_identity_changed_during_check')
    for pin in native_pins:
        require(stamp(P(pin['path']).lstat()) == pin['stat'], 'account_service_native_changed_after_check')
    regular_file(identification_pin['path'], 3818, identification_pin['sha256'], UID,
                 original_stat=original_stat)
    # Close the identity interval after all final public and original-file reads.
    for pid, start, ppid in ((359656,40749693,359655), (359655,40749691,1)):
        final_stat = proc_bytes(P('/proc')/str(pid)/'stat')
        final_values = final_stat[final_stat.rfind(b')')+2:].split()
        require(int(final_values[19]) == start and int(final_values[1]) == ppid
                and (pid != 359656 or final_values[0] == b'S'),
                'account_service_final_PID_parent_or_child_state_changed')
    require(stamp(BASE.lstat()) == stamp(base_stat), 'account_service_private_ancestor_changed_during_check')
    check_deadline()
    return {'classification':'excluded_exact_system_service', 'pid':359656,
            'start_ticks':40749693, 'parent_pid':359655, 'parent_start_ticks':40749691,
            'original_identification_pin':dict(identification_pin),
            'original_identification_policy':'original_unsealed',
            'parent_review_identity_sha256':parent_review_identity_sha256,
            'before_public_identity':before, 'after_public_identity':after,
            'boot_identity':boot_before, 'native_file_pins':native_pins,
            'classification_basis':'Exact current public identity plus parent-reviewed trusted OS lifecycle and original fresh-creation custodies; not file mtime inference.',
            'trusted_OS_role_and_fresh_creation_chronology_are_parent_semantic_binding':True,
            'child_executable_to_executor_relationship_is_inherited_OS_role_not_observed_exe':True,
            'protected_child_fields':{key:'UNOBSERVED' for key in ('fd','cwd','root','exe','maps','syscall','meaningful_wait_channel')},
            'reference_free_claimed':False, 'global_privileged_visibility_or_clearance_claimed':False,
            'other_consumers_parent_and_descendants_exempted':False,
            'signal_blocked_mask_zero_or_nonzero_is_not_predicated':True}

PORTAL_HELPER_SHA = 'c195eccf8f728f7752dd89e0588af4fe6f0c05f50c7aa6cb47e5bd95f9ecb46b'

def portal_inode_birth_rows(document, row_definitions, admin=False, check_deadline=None):
    """Pure metadata validation. No path reads; symlink targets are not covered."""
    fields = ['dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns']
    encoding = document['object_encoding']
    require(encoding['format']=='ordered-array.v1'
            and encoding['original_stat_fields']==fields
            and encoding['original_statx_fields']==['returned_mask','requested_mask','attributes',
                'attributes_mask','mount_id_or_null','birth_supported','birth_seconds','birth_nanoseconds']
            and encoding['object_fields']==['relative_path','original_stat','original_statx',
                'directory_names_count_or_null','directory_names_digest_or_null','type_code'],
            'portal_birth_array_encoding_changed')
    require(document['sealed'] is False and 'identity_sha256' not in document
            and document['cleanup_capacity_or_scientific_admission'] is False
            and document['boot_clock_interval_equal'] is True
            and document['clock_before']['boot_epoch_seconds']==1785498067
            and document['clock_after']['boot_epoch_seconds']==1785498067
            and document['clock_before']['clock_ticks_per_second']==100
            and document['clock_after']['clock_ticks_per_second']==100,
            'portal_original_birth_policy_or_boot_changed')
    if not admin:
        require(document['format']=='swdb.exact-portal-helper-checkout-inode-birth-query.v1'
                and document['all_eighteen_walks_completed_and_metadata_stable'] is True
                and document['g5_source_sha256']=='a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb'
                and document['symlink_targets_and_shared_git_admin_not_traversed'] is True,
                'portal_checkout_birth_original_changed')
    else:
        require(document['format']=='swdb.exact-portal-helper-worktree-administration-inode-birth-query.v1'
                and document['all_eighteen_walks_completed_and_metadata_stable'] is True
                and document['administration_anchor_metadata_interval_equal'] is True
                and document['public_identity_interval_equal'] is True
                and document['genuine_prior_checkout_birth_original_pin']['bytes']==14762700
                and document['genuine_prior_checkout_birth_original_pin']['sha256']=='e228811f4b119a7e0c97b666b7da249374f3637cef8b17c0b10b54c4ff422fb7',
                'portal_admin_birth_original_incomplete')
    originals = document['rows']
    require(isinstance(originals,list) and len(originals)==len(row_definitions)==18
            and {r['row'] for r in originals}==set(row_definitions), 'portal_birth_rows_incomplete')
    result = {}
    cutoff_numerator = (1785498067+1)*100+559081545+1
    for row in originals:
        if check_deadline is not None:check_deadline()
        name = row['row']
        root = str(PRIMARY/'.git/worktrees'/name) if admin else row_definitions[name]['path']
        require(name not in result and row['path']==root
                and row['first_pass_completed'] is True and row['second_pass_completed'] is True
                and row['metadata_equal_between_passes'] is True,
                'portal_birth_row_route_or_stability_changed')
        if admin:
            require(row['original_pointer_route']==root and row['g5_definition']==row_definitions[name],
                    'portal_admin_pointer_route_changed')
        else:
            require(row['g5_definition']==row_definitions[name]
                    and row['git_indirection']['original_pointer_route']==str(PRIMARY/'.git/worktrees'/name),
                    'portal_checkout_definition_or_git_pointer_changed')
        objects = row['original_objects']; digest=hashlib.sha256(); by_path={}; counts=[0,0,0]
        require(isinstance(objects,list) and 0<len(objects)<=400000, 'portal_original_object_count_limit')
        for obj in objects:
            if check_deadline is not None:check_deadline()
            require(isinstance(obj,list) and len(obj)==6, 'portal_birth_object_shape')
            relative, s, x, names_count, names_digest, kind = obj
            require(isinstance(relative,str) and relative and len(relative.encode())<=4096
                    and (relative=='.' or (not relative.startswith('/')
                         and all(part not in ('','.', '..') for part in relative.split('/'))))
                    and relative not in by_path and isinstance(s,list) and len(s)==10
                    and all(type(v) is int for v in s) and isinstance(x,list) and len(x)==8,
                    'portal_birth_path_or_stat_shape')
            require(s[0]==2097 and s[3]==UID and s[5]>0
                    and kind in (0,1,2) and type(kind) is int
                    and (stat.S_ISDIR(s[2]) if kind==0 else stat.S_ISREG(s[2]) if kind==1 else stat.S_ISLNK(s[2]))
                    and (kind==0 or s[5]==1), 'portal_birth_type_owner_device_or_links_changed')
            require(x[0]==8191 and x[1]==8191 and x[4]==136 and x[5] is True
                    and type(x[6]) is int and type(x[7]) is int
                    and x[6]>0 and 0<=x[7]<1000000000
                    and (x[6]*1000000000+x[7])*100 > cutoff_numerator*1000000000,
                    'portal_birth_unsupported_or_not_strictly_after_helper')
            require((kind==0 and type(names_count) is int and names_count>=0
                     and isinstance(names_digest,str) and re.fullmatch('[0-9a-f]{64}',names_digest))
                    or (kind!=0 and names_count is None and names_digest is None),
                    'portal_birth_directory_names_shape')
            if kind==2:
                require(not admin and relative in (
                    'swdb-project/weeklogs/2026-09-24/.build/node_modules',
                    'swdb-project/weeklogs/2026-09-30/.build/node_modules'),
                    'portal_birth_unreviewed_symlink')
            by_path[relative]=obj; counts[kind]+=1
            encoded=canonical(obj); digest.update(len(encoded).to_bytes(8,'big')); digest.update(encoded)
        require('.' in by_path and by_path['.'][5]==0
                and len(objects)==row['first_objects_observed']==row['second_objects_observed']
                and digest.hexdigest()==row['first_metadata_sha256']==row['second_metadata_sha256'],
                'portal_birth_count_or_complete_digest_changed')
        children_by_parent={relative:[] for relative,obj in by_path.items() if obj[5]==0}
        for relative in by_path:
            if check_deadline is not None:check_deadline()
            if relative!='.':
                parent,slash,leaf=relative.rpartition('/')
                parent=parent or '.'; leaf=leaf if slash else relative
                require(parent in children_by_parent, 'portal_birth_parent_object_missing')
                children_by_parent[parent].append(leaf)
        for relative,obj in by_path.items():
            if check_deadline is not None:check_deadline()
            if obj[5]==0:
                children=sorted(children_by_parent[relative], key=os.fsencode)
                require(len(children)==obj[3] and sha(b'\0'.join(os.fsencode(p) for p in children))==obj[4],
                        'portal_birth_complete_directory_inventory_changed')
        require(counts[2]==(0 if admin else 2), 'portal_birth_symlink_scope_changed')
        result[name]={'root':root,'objects':by_path,'count':len(objects),'counts':counts,
                      'metadata_sha256':digest.hexdigest(),
                      'git_pointer':None if admin else row['git_indirection']}
    return result

def exact_portal_autounmount_identification(review_pin, row_definitions, selected_rows, removed_rows,
                                            enclosing_review_identity, helper_sha256,
                                            check_deadline, charge_bytes, charge_metadata, continuity_rows=None):
    """One exact protected helper under explicit OS-image/clock assumptions.

    Caller ordinary reference, alias, Git retention and selection gates remain
    mandatory. This does not observe protected child fields or clear other tasks.
    """
    private=BASE/'lanl-portal-helper-inode-review-20261008-a1'
    require(review_pin['path']==str(private/'parent-review.json')
            and type(review_pin['bytes']) is int and 0<review_pin['bytes']<=256*1024
            and re.fullmatch('[0-9a-f]{64}',review_pin['sha256'])
            and re.fullmatch('[0-9a-f]{64}',enclosing_review_identity), 'portal_review_pin_missing')

    def stat_fact(s):
        return [getattr(s,'st_'+key) for key in
                ('dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns')]

    def actual_stat(path):
        check_deadline(); charge_metadata(0,1,0)
        return path.lstat()

    def route(path):
        require(path.is_absolute() and '..' not in path.parts, 'portal_noncanonical_path')
        for q in (path,*path.parents):
            require(not stat.S_ISLNK(actual_stat(q).st_mode), 'portal_route_symlink')
        charge_metadata(0,len(path.parts),0)  # Conservative debit for resolution's component stats.
        require(path.resolve(strict=True)==path, 'portal_route_redirect')
        return actual_stat(path)

    def read_file(pin, cap, owner=UID, mode=0o600):
        path=P(pin['path']); before=route(path)
        require(type(pin['bytes']) is int and 0<=pin['bytes']<=cap
                and stat.S_ISREG(before.st_mode) and before.st_uid==owner and before.st_nlink==1
                and stat.S_IMODE(before.st_mode)==mode and before.st_size==pin['bytes'],
                'portal_original_or_native_file_identity')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            charge_metadata(0,1,0)
            require(stat_fact(os.fstat(fd))==stat_fact(before), 'portal_file_open_changed')
            parts=[]; count=0
            while True:
                check_deadline(); part=os.read(fd,min(1024*1024,cap-count+1))
                if not part:break
                charge_bytes(len(part)); count+=len(part)
                require(count<=cap, 'portal_read_cap'); parts.append(part)
            raw=b''.join(parts); charge_metadata(0,1,0)
            require(len(raw)==pin['bytes'] and sha(raw)==pin['sha256']
                    and stat_fact(os.fstat(fd))==stat_fact(before)==stat_fact(actual_stat(path)),
                    'portal_original_or_native_bytes_changed')
        finally:os.close(fd)
        return raw, {'path':str(path),'bytes':len(raw),'sha256':sha(raw),'stat':stamp(before)}

    def review_binding(review):
        require(review['format']=='swdb.exact-portal-autounmount-semantic-parent-review.v1'
                and review['canonical_ensure_ascii'] is True
                and sha(canonical({k:v for k,v in review.items() if k!='identity_sha256'}))==review['identity_sha256']
                and review['accepted_exact_role_only'] is True
                and review['shared_helper_sha256']==helper_sha256
                and review['pid']==1654291 and review['start_ticks']==559081545
                and review['parent_pid']==1654279 and review['parent_start_ticks']==559081538,
                'portal_semantic_review_binding_changed')
        required_assumptions=('trusted_host_clock_and_inode_birth_history',
            'installed_native_image_matches_running_child',
            'installed_packages_correspond_to_reviewed_exact_source',
            'libfuse_3_14_wait_loop_has_only_control_socket_and_fixed_mount_target',
            'all_potentially_removed_checkout_and_git_admin_inodes_postdate_helper',
            'node_modules_symlink_targets_are_not_followed_or_removed',
            'ordinary_portal_parent_and_other_consumers_still_checked',
            'existing_git_shared_objects_refs_and_alias_gates_remain_mandatory')
        require(set(review['explicit_assumptions'])==set(required_assumptions)
                and all(review['explicit_assumptions'][k] is True for k in required_assumptions)
                and review['inherited_file_descriptors_not_generically_closed'] is True
                and review['protected_child_fields']=={k:'UNOBSERVED' for k in
                    ('fd','cwd','root','exe','maps','syscall','wait_channel')}
                and review['global_reference_free_or_cleanup_capacity_or_scientific_admission'] is False
                and review['other_consumers_parent_or_descendants_exempted'] is False,
                'portal_semantic_assumption_or_scope_missing')
        require(review['admin_birth_producer_pin']=={'bytes':52031,
                    'sha256':'b2b08374ea997679df9e08894fc14d139cce9f9c90ab3dabd324db36d6f661a3'},
                'portal_admin_birth_producer_review_pin_pending')
        require(review['lifecycle_research_pin']=={'bytes':13046,
                    'sha256':'9c83f802ed7d467c8411c3253be9bac330827ba01a935a11bb7a6ed9eb248840'},
                'portal_exact_lifecycle_research_pin_changed')

    base_before=actual_stat(BASE); private_before=route(private)
    require(stat.S_ISDIR(base_before.st_mode) and base_before.st_uid==UID
            and stat.S_IMODE(base_before.st_mode)==0o700
            and stat.S_ISDIR(private_before.st_mode) and private_before.st_uid==UID
            and stat.S_IMODE(private_before.st_mode)==0o700, 'portal_evidence_private_ancestor')
    raw_review,review_fact=read_file(review_pin,256*1024); review=strict_json(raw_review)
    review_binding(review)
    require(review_pin.get('canonical_ensure_ascii') is True
            and review_pin.get('identity_sha256')==review['identity_sha256'],
            'portal_review_pin_explicit_True_identity_missing')
    fixed_originals={
        'public_identity':('public-identity.json',4103,
            '1ea76b7519827bae6f81902c2bebd6b16e22c303fcada24257bf1bab73174489'),
        'checkout_birth':('checkout-inode-birth.json',14762700,
            'e228811f4b119a7e0c97b666b7da249374f3637cef8b17c0b10b54c4ff422fb7'),
        'git_admin_birth':('git-admin-inode-birth.json',139083,
            'a62b53bd4c9f89c3a212690750905c6cf13203fca8fceee560a9ad9ee25a1dd5')}
    documents={}; original_facts=[]
    for key,(name,size,digest) in fixed_originals.items():
        pin=review['original_pins'][key]
        require(pin['path']==str(private/name) and pin['bytes']==size and pin['sha256']==digest,
                'portal_fixed_original_pin_changed')
        raw,fact=read_file(pin,32*1024*1024); documents[key]=strict_json(raw); original_facts.append(fact)
    original=documents['public_identity']
    require(original['format']=='swdb.portal-fuse-service-public-identity.v1'
            and original['sealed'] is False and 'identity_sha256' not in original
            and original['public_role_identity_stable_at_end'] is True
            and original['parent_semantic_exclusion_cleanup_or_global_reference_free_claimed'] is False,
            'portal_original_identity_policy_changed')
    checkout=portal_inode_birth_rows(documents['checkout_birth'],row_definitions,check_deadline=check_deadline)
    admin=portal_inode_birth_rows(documents['git_admin_birth'],row_definitions,True,check_deadline)
    def continuity_scope(selected_rows,removed_rows,continuity_rows):
        require(isinstance(selected_rows,list) and len(set(selected_rows))==len(selected_rows)
                and set(selected_rows)<=set(row_definitions)
                and isinstance(removed_rows,list) and len(set(removed_rows))==len(removed_rows)
                and set(removed_rows)<=set(selected_rows), 'portal_removed_journal_scope_changed')
        remaining_rows=set(selected_rows)-set(removed_rows)
        require(continuity_rows is None or (isinstance(continuity_rows,list)
                and len(set(continuity_rows))==len(continuity_rows)
                and bool(continuity_rows) and set(continuity_rows)<=remaining_rows),
                'portal_continuity_scope_outside_actual_remaining')
        return sorted(remaining_rows if continuity_rows is None else continuity_rows)

    remaining=continuity_scope(selected_rows,removed_rows,continuity_rows)
    evidence_stats={x['path']:x['stat'] for x in original_facts+[review_fact]}

    def proc_read(path,cap):
        check_deadline(); fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            parts=[]; count=0
            while True:
                check_deadline(); part=os.read(fd,min(1024*1024,cap-count+1))
                if not part:break
                charge_bytes(len(part)); count+=len(part)
                require(count<=cap,'portal_proc_read_cap'); parts.append(part)
            return b''.join(parts)
        finally:os.close(fd)

    def process_fields(raw_stat,raw_status,pid,start,ppid,child):
        values=raw_stat[raw_stat.rfind(b')')+2:].split(); fields={}
        for line in raw_status.decode().splitlines():
            if ':' in line:
                key,value=line.split(':',1); require(key not in fields,'portal_duplicate_status'); fields[key]=value.strip()
        require(int(raw_stat.split(b' ',1)[0])==pid and int(values[19])==start
                and int(values[1])==ppid and int(fields['Pid'])==pid and int(fields['PPid'])==ppid
                and fields['Name']==('fusermount3' if child else 'xdg-document-po')
                and [int(v) for v in fields['Uid'].split()]==([UID,0,0,0] if child else [UID]*4)
                and [int(v) for v in fields['Gid'].split()]==[UID]*4
                and values[0]==b'S' and fields['State'].split()[0]=='S'
                and int(fields['TracerPid'])==0
                and (int(fields['Threads'])==1 if child else int(fields['Threads'])>0),
                'portal_current_public_process_identity_changed')
        caps={key:fields[key] for key in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb')}
        require(caps==original['child' if child else 'parent']['capability_hex'], 'portal_current_capabilities_changed')
        return {'pid':pid,'start_ticks':start,'ppid':ppid,'state':'S',
                'uids':[int(v) for v in fields['Uid'].split()], 'threads':int(fields['Threads'])}

    def public_link(path):
        check_deadline(); value=os.readlink(path); charge_metadata(0,1,0); charge_bytes(len(os.fsencode(value)))
        return value

    def current_pair():
        pair=[]
        for pid,start,ppid,child,key in ((1654291,559081545,1654279,True,'child'),
                (1654279,559081538,359655,False,'parent')):
            root=P('/proc')/str(pid)
            item=process_fields(proc_read(root/'stat',16384),proc_read(root/'status',32768),pid,start,ppid,child)
            cmd=proc_read(root/'cmdline',4096); pin=original[key+'_cmdline_pin']
            require(len(cmd)==pin['bytes'] and sha(cmd)==pin['sha256'], 'portal_current_fixed_command_changed')
            item['cmdline_pin']=pin; pair.append(item)
        require(public_link(P('/proc/1654279/exe'))=='/usr/libexec/xdg-document-portal', 'portal_parent_exe_changed')
        return pair

    def boot_and_mount():
        boot=[v for v in proc_read(P('/proc/stat'),1024*1024).splitlines() if v.startswith(b'btime ')]
        require(len(boot)==1 and int(boot[0].split()[1])==1785498067
                and os.sysconf('SC_CLK_TCK')==100, 'portal_current_boot_or_ticks_changed')
        require(public_link(P('/proc/self/ns/mnt'))==public_link(P('/proc/1654279/ns/mnt')),
                'portal_parent_mount_namespace_differs')
        mounts=[]
        for line in proc_read(P('/proc/1654279/mountinfo'),16*1024*1024).decode().splitlines():
            before,after=line.split(' - ',1); left=before.split(); right=after.split()
            if left[4]=='/run/user/114316761/doc':
                mounts.append({'mount_id':left[0],'parent_mount_id':left[1],'device':left[2],
                    'root':left[3],'mount_point':left[4],'mount_options':left[5],
                    'optional_fields':left[6:],'filesystem':right[0],'source':right[1],'super_options':right[2]})
        require(mounts==original['parent_namespace_exact_portal_mount'] and len(mounts)==1
                and mounts[0]['device']=='0:48' and mounts[0]['filesystem']=='fuse.portal'
                and mounts[0]['mount_point']=='/run/user/114316761/doc', 'portal_mount_route_changed')
        return mounts[0]

    def live_scope(scope):
        summaries=[]
        for name in remaining:
            row=scope[name]; root=P(row['root']); route(root); digest=hashlib.sha256(); observed={}
            stack=[(root,'.')]
            while stack:
                path,relative=stack.pop(); charge_metadata(1,0,0); before=actual_stat(path)
                require(relative in row['objects'] and stat_fact(before)==row['objects'][relative][1],
                        'portal_current_inode_or_stat_changed')
                obj=row['objects'][relative]; observed[relative]=stat_fact(before)
                if obj[5]==0:
                    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
                    try:
                        charge_metadata(0,1,0)
                        require(stat_fact(os.fstat(fd))==stat_fact(before),'portal_directory_open_changed')
                        names=[]
                        with os.scandir(fd) as entries:
                            for entry in entries:
                                check_deadline(); value=entry.name
                                require('/' not in value and value not in ('.','..')
                                        and len(names)<obj[3], 'portal_directory_names_invalid_or_added')
                                charge_bytes(len(os.fsencode(value))+1); names.append(value)
                        names.sort(key=os.fsencode)
                        name_bytes=b'\0'.join(os.fsencode(value) for value in names)
                        require(len(names)==obj[3] and sha(name_bytes)==obj[4], 'portal_directory_inventory_changed')
                        charge_metadata(0,1,0)
                        require(stat_fact(os.fstat(fd))==stat_fact(before)==stat_fact(actual_stat(path)),
                                'portal_directory_changed_during_listing')
                    finally:os.close(fd)
                    stack.extend((path/value, value if relative=='.' else relative+'/'+value) for value in reversed(names))
                else:
                    require(stat_fact(actual_stat(path))==stat_fact(before), 'portal_leaf_changed_during_metadata')
                encoded=canonical(obj); digest.update(len(encoded).to_bytes(8,'big')); digest.update(encoded)
            require(set(observed)==set(row['objects']) and digest.hexdigest()==row['metadata_sha256'],
                    'portal_current_full_inode_scope_incomplete')
            summaries.append({'row':name,'path':row['root'],'objects':len(observed),
                              'metadata_sha256':digest.hexdigest()})
        return summaries

    pair_before=current_pair(); mount_before=boot_and_mount(); native_facts=[]
    for name in remaining:
        pointer=checkout[name]['git_pointer']
        pin={'path':str(P(checkout[name]['root'])/'.git'),'bytes':pointer['bytes'],'sha256':pointer['sha256']}
        raw,fact=read_file(pin,4096,UID,stat.S_IMODE(pointer['file_stat']['mode']))
        require(stat_fact(actual_stat(P(pin['path'])))==[pointer['file_stat'][key] for key in
            ('dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns')]
            and raw==('gitdir: '+admin[name]['root']+'\n').encode(), 'portal_live_git_indirection_changed')
    for pin in original['native_file_pins']:
        expected=('/usr/bin/fusermount3',39296,'d278775c1528dd32efc85c2cb322423ee93aa8dcf76aaa595f7022d427910704',0o4755) if pin['path']=='/usr/bin/fusermount3' else (
            '/usr/libexec/xdg-document-portal',195560,'44dd7e1eb2df2a4de1d8c1189a3fee4451539ffab5db6ba4d21718c6d43af3dc',0o755)
        require((pin['path'],pin['bytes'],pin['sha256'])==expected[:3], 'portal_native_original_pin_changed')
        raw,fact=read_file(pin,256*1024,0,expected[3]); require(fact['stat']==pin['stat'],'portal_native_installed_identity_changed')
        native_facts.append(fact)
    first_checkout=live_scope(checkout); first_admin=live_scope(admin)
    second_checkout=live_scope(checkout); second_admin=live_scope(admin)
    require(first_checkout==second_checkout and first_admin==second_admin, 'portal_live_scope_interval_changed')
    pair_after=current_pair(); mount_after=boot_and_mount()
    require(pair_before==pair_after and mount_before==mount_after, 'portal_public_identity_interval_changed')
    for path,expected in evidence_stats.items():
        require(stamp(actual_stat(P(path)))==expected,'portal_original_or_review_stat_changed_at_end')
    for fact in native_facts:
        require(stamp(actual_stat(P(fact['path'])))==fact['stat'],'portal_native_stat_changed_at_end')
    require(stat_fact(actual_stat(BASE))==stat_fact(base_before)
            and stat_fact(actual_stat(private))==stat_fact(private_before), 'portal_private_ancestor_interval_changed')
    for pid,start,ppid in ((1654291,559081545,1654279),(1654279,559081538,359655)):
        raw=proc_read(P('/proc')/str(pid)/'stat',16384); values=raw[raw.rfind(b')')+2:].split()
        require(int(raw.split(b' ',1)[0])==pid and int(values[19])==start and int(values[1])==ppid
                and values[0]==b'S', 'portal_final_public_identity_anchor_changed')
    check_deadline()
    return {'classification':'excluded_exact_portal_autounmount_helper','pid':1654291,
        'start_ticks':559081545,'parent_pid':1654279,'parent_start_ticks':559081538,
        'semantic_review_identity_sha256':review['identity_sha256'],
        'enclosing_parent_review_identity_sha256':enclosing_review_identity,
        'original_file_pins':original_facts,'before_public_identity':pair_before,'after_public_identity':pair_after,
        'portal_mount':mount_before,'native_file_pins':native_facts,
        'remaining_checkout_inode_scopes':second_checkout,'remaining_git_admin_inode_scopes':second_admin,
        'selected_rows_from_unchanged_caller_scope':list(selected_rows),
        'already_removed_rows_only_from_completed_journal':list(removed_rows),
        'fresh_inode_continuity_rows':remaining,
        'all_eighteen_original_checkout_and_admin_metadata_rows_validated':True,
        'strict_helper_birth_upper_bound_rational':{'numerator':179108888346,'denominator':100},
        'protected_child_fields':review['protected_child_fields'],
        'explicit_assumptions':review['explicit_assumptions'],
        'inherited_file_descriptors_not_generically_closed':True,
        'symlink_targets_not_followed_or_removed_and_not_reference_cleared':True,
        'shared_git_objects_refs_and_unselected_administration_not_cleared':True,
        'parent_and_other_consumers_still_require_ordinary_checks':True,
        'global_reference_free_or_cleanup_capacity_or_scientific_admission':False}

RAW_TOP_LANE_SIDECAR_PIN={'path': '/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261006-a1.lane.json', 'bytes': 988, 'sha256': '83ba263a56756047716a2e550c3acc7a9d73eadefbbc9e245cdb697092369c1c', 'stat': {'ctime_ns': 1791344103814358923, 'dev': 2065, 'gid': 114316761, 'ino': 9345428, 'mode': 33204, 'mtime_ns': 1791344103814358923, 'nlink': 1, 'size': 988, 'uid': 114316761}}

def exact_original_raw_lane_sidecar(check_deadline, selected_paths):
    """One exact original regular RAW sibling; no generic regular-file waiver."""
    check_deadline()
    pin=RAW_TOP_LANE_SIDECAR_PIN;path=P(pin['path'])
    require(path.parent==RAW and path.name=='lanl17-cleanup-smoke-20261006-a1.lane.json'
            and path.resolve(strict=True)==path
            and not any(p.is_symlink() for p in (path,*path.parents)),
            'exact_original_top_sidecar_route')
    before=path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid==UID and before.st_nlink==1
            and stamp(before)==pin['stat'] and before.st_size==988,
            'exact_original_top_sidecar_stat')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        require(stamp(os.fstat(fd))==stamp(before),'exact_original_top_sidecar_open')
        parts=[];count=0
        while True:
            check_deadline()
            part=os.read(fd,min(988-count+1,988))
            if not part:break
            count+=len(part);require(count<=988,'exact_original_top_sidecar_read_bound');parts.append(part)
        raw=b''.join(parts)
        require(count==988 and sha(raw)==pin['sha256']
                and stamp(os.fstat(fd))==stamp(before)==stamp(path.lstat()),
                'exact_original_top_sidecar_returned_bytes')
    finally:os.close(fd)
    def unique(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'original_top_sidecar_duplicate_key');result[key]=value
        return result
    def bad(value):raise ValueError('original_top_sidecar_nonfinite_JSON')
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=bad)
    require(type(value) is dict and set(value)=={'socket_lane'},'original_top_sidecar_JSON_shape')
    refs=[]
    def visit(item,location):
        if type(item) is dict:
            for key,child in item.items():visit(child,location+[key])
        elif type(item) is list:
            for index,child in enumerate(item):visit(child,location+[index])
        elif type(item) is str and item.startswith('/'):
            require(not any(item==str(p) or item.startswith(str(p)+'/') for p in selected_paths),
                    'original_top_sidecar_JSON_selected_reference')
            refs.append({'JSON_location':location,'path':item})
    visit(value,[])
    require(not any(str(p).encode() in raw for p in selected_paths),
            'original_top_sidecar_literal_selected_reference')
    return {'path':str(path),'bytes':988,'sha256':pin['sha256'],'stat':stamp(before),
            'original_policy':'original_UNSEALED_socket_lane_metadata_no_reseal',
            'original_absolute_JSON_references':refs,
            'literal_and_original_JSON_selected_reference_checks':True,
            'unchanged_historical_mode0664_beneath_existing_private_RAW_ancestor':True}

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
        self.passive_stats = {}
        # Unread removal-initial metadata is not a byte-verified passive cache.
        self.initial_tracked_metadata_stats = {}
        self.passive_hashes = {}
        self.reference_hits = {}
        self.directory_stats = {}
        self.symlink_stats = {}
        self.raw_namespace = None
        self.stat_checks = 0
        self.private_root_stats = {}
        self.facts = {'format': 'swdb.consumed-detached-source-guard.v1',
                      'canonical_ensure_ascii': True, 'started_at': now(),
                      'remove_requested': args.remove, 'selected_rows': args.select,
                      'removed_rows': [], 'pre_remove_full_byte_checks': {},
                      'failure': None, 'admitted': False,
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

    def check_private_root(self, root):
        # Literal roots only. This is POSIX traversal privacy, not privileged clearance.
        require(root in (BASE, P('/data/yanruj')), 'private_ancestor_not_literal')
        require(not any(q.is_symlink() for q in (root, *root.parents))
                and root.resolve(strict=True) == root, 'private_ancestor_redirect')
        s = root.lstat()
        require(stat.S_ISDIR(s.st_mode) and s.st_uid == UID
                and stat.S_IMODE(s.st_mode) == 0o700, 'private_ancestor_owner_mode')
        current = stamp(s)
        fixed = {k: current[k] for k in ('dev', 'ino', 'mode', 'uid', 'gid')}
        key = str(root)
        if key not in self.private_root_stats:
            self.private_root_stats[key] = {'initial_stat': current,
                                            'fixed_privacy_identity': fixed,
                                            'latest_stat': current, 'checks': 1}
        else:
            previous = self.private_root_stats[key]
            require(previous['fixed_privacy_identity'] == fixed,
                    'private_ancestor_identity_or_mode_changed')
            previous['latest_stat'] = current
            previous['checks'] += 1
        # Own output creation/removal can change root times/nlink; never chmod them.
        return True

    def private_ancestor(self, path):
        p = P(path)
        if p == BASE or BASE in p.parents:
            return self.check_private_root(BASE)
        # Data-root privacy permits only the already-scoped RAW namespace, no siblings.
        if p == RAW or RAW in p.parents:
            return self.check_private_root(P('/data/yanruj'))
        return False

    def privacy_gate(self):
        for root in (BASE, P('/data/yanruj')):
            self.check_private_root(root)
        # Independent snapshots avoid mutating already-sealed receipt facts later.
        return {key: {'initial_stat': dict(value['initial_stat']),
                      'fixed_privacy_identity': dict(value['fixed_privacy_identity']),
                      'latest_stat': dict(value['latest_stat']),
                      'checks': value['checks']}
                for key, value in self.private_root_stats.items()}

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
        private = self.private_ancestor(p)
        require(not s.st_mode & 0o022 or special or private, 'writable_untrusted_path')
        inherited_setgid = directory and BASE in p.parents and private and \
            stat.S_ISDIR(s.st_mode) and s.st_mode & 0o7000 == 0o2000 and \
            s.st_gid == self.private_root_stats[str(BASE)]['fixed_privacy_identity']['gid'] and \
            s.st_dev == self.private_root_stats[str(BASE)]['fixed_privacy_identity']['dev']
        require(not s.st_mode & 0o7000 or inherited_setgid, 'special_permission_bits')
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
            raw = b''.join(pieces)
            self.private_ancestor(p)
            if str(p) in self.passive_stats:
                require(self.passive_stats[str(p)] == stamp(before), 'baseline_file_identity_changed')
            self.passive_stats[str(p)] = stamp(before)
            self.passive_hashes[str(p)] = sha(raw)
            self.reference_hits[str(p)] = any(str(x).encode() in raw for x in self.selected)
            return raw, stamp(before)
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

    def pin_fact(self, pin):
        # Only an already-byte-checked, stable baseline file can use this cache.
        path = pin['path']
        if path not in self.passive_stats:
            self.pinned(pin)
        require(self.passive_stats[path]['size'] == pin['bytes']
                and self.passive_hashes[path] == pin['sha256'], 'cached_pin_changed')
        require(stamp(P(path).lstat()) == self.passive_stats[path], 'cached_file_stat_changed')
        if 'stat' in pin:
            require(pin['stat'] == self.passive_stats[path], 'cached_pinned_stat_changed')

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
        self.privacy_gate()
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
        self.privacy_gate()
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

    def tree(self, path, expected_head, hash_regular_bytes=True):
        require(type(hash_regular_bytes) is bool, 'private_tracked_byte_mode_required')
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
        stat_inventory = []
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
                self.symlink_stats[str(p)] = {'stat':stamp(before),'link':os.readlink(p)}
            elif hash_regular_bytes:
                data, got = self.read(p)
                require(tracked_mode_equivalent(stat.S_IMODE(before.st_mode), mode,
                                                self.private_ancestor(p)),
                        'tracked_permission_mode_changed')
                require(got == stamp(before), 'tracked_identity_changed')
            else:
                # Snapshot exact physical metadata now; regular bytes remain unread
                # until this same row's full pre-remove SHA1-vs-Git-blob check.
                unused, observed = self.path(p)
                require(stamp(observed) == stamp(before), 'tracked_metadata_identity_changed')
                require(before.st_nlink == 1 and before.st_size <= LIMITS['one_file'],
                        'tracked_metadata_link_or_size_limit')
                require(tracked_mode_equivalent(stat.S_IMODE(before.st_mode), mode,
                                                self.private_ancestor(p)),
                        'tracked_permission_mode_changed')
                require(stamp(p.lstat()) == stamp(before), 'tracked_metadata_identity_changed')
                witness = {**stamp(before), 'allocated_bytes': before.st_blocks*512}
                if str(p) in self.initial_tracked_metadata_stats:
                    require(self.initial_tracked_metadata_stats[str(p)] == witness,
                            'initial_tracked_metadata_changed')
                self.initial_tracked_metadata_stats[str(p)] = witness
            if mode == '120000' or hash_regular_bytes:
                actual_oid = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                require(actual_oid == oid, 'tracked_source_bytes_changed')
                total += len(data)
                inventory.append([mode, oid, str(rel), sha(data)])
            else:
                total += before.st_size
            allocated += before.st_blocks*512
            stat_inventory.append([mode, oid, str(rel),
                                   {**stamp(before), 'allocated_bytes': before.st_blocks*512}])
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
        self.privacy_gate()
        return {'head': expected_head, 'tree': self.text_git(path, 'rev-parse', 'HEAD^{tree}'),
                'tracked_entries': len(rows), 'tracked_logical_bytes': total,
                'tracked_allocated_bytes_observed': allocated,
                'tracked_mode_blob_source_inventory_sha256': sha(canonical(inventory)) if hash_regular_bytes else None,
                'tracked_stat_inventory_sha256': sha(canonical(stat_inventory)),
                'regular_bytes_verified': hash_regular_bytes,
                'gitfile_sha256': sha(gd), 'directory_stat': stamp(path.lstat()),
                'retained_objects': len(ids), 'detached_clean_ignored0_untracked0': True}

    def walk(self, root):
        _, initial = self.path(root, directory=True)
        if str(root) in self.directory_stats:
            require(self.directory_stats[str(root)] == stamp(initial), 'baseline_root_directory_changed')
        self.directory_stats[str(root)] = stamp(initial)
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
                if stat.S_ISDIR(s.st_mode):
                    if str(p) in self.directory_stats:
                        require(self.directory_stats[str(p)] == stamp(s), 'baseline_directory_changed')
                    self.directory_stats[str(p)] = stamp(s)
                elif stat.S_ISLNK(s.st_mode):
                    observed = {'stat':stamp(s),'link':os.readlink(p)}
                    if str(p) in self.symlink_stats:
                        require(self.symlink_stats[str(p)] == observed, 'baseline_symlink_changed')
                    self.symlink_stats[str(p)] = observed
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
        if self.raw_namespace is None:
            self.raw_namespace = sorted(parent_raw_names)
        require(sorted(parent_raw_names) == self.raw_namespace, 'raw_namespace_changed')
        sidecar=exact_original_raw_lane_sidecar(self.left,self.selected)
        self.read_bytes+=sidecar['bytes']
        require(self.read_bytes<=LIMITS['total_file_bytes'],'cumulative_original_top_sidecar_read_limit')
        require(P(sidecar['path']).name in parent_raw_names,'original_top_sidecar_namespace_retained')
        previous=self.facts.get('original_top_regular_sidecar')
        require(previous is None or previous==sidecar,'original_top_sidecar_baseline_changed')
        self.facts['original_top_regular_sidecar']=sidecar
        self.passive_stats[sidecar['path']]=sidecar['stat']
        self.passive_hashes[sidecar['path']]=sidecar['sha256']
        self.reference_hits[sidecar['path']]=False
        results = {}
        for root in routes:
            actual = self.raw_inventory(root)
            results[root] = sha(canonical(actual))
        for pin in self.plan['original_raw_file_pins']:
            require(pin['receipt_key'] in RECEIPTS and
                    any(inside(pin['path'], P(root)) for root in routes),
                    'original_raw_pin_outside_receipt_routes')
            self.pin_fact(pin)
        require(self.plan['original_raw_files_complete_review']['complete'] is True,
                'original_raw_file_pin_coverage_missing')
        # All current LANL raw links are checked, including unrelated retained runs.
        for name in sorted(parent_raw_names):
            root = RAW/name
            if root==P(sidecar['path']):
                require(stamp(root.lstat())==sidecar['stat'],'original_top_sidecar_still_exact')
                continue
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

    def process_references(self, continuity_rows=None):
        pids = sorted(p for p in P('/proc').iterdir() if p.name.isdecimal())
        require(len(pids) <= LIMITS['processes'], 'process_count_limit')
        explicit = {int(x['pid']):x for x in self.plan['relevant_privileged_consumers']}
        require(len(explicit) == len(self.plan['relevant_privileged_consumers']),
                'duplicate_relevant_privileged_consumer')
        for item in explicit.values():
            require(item['identified_as_owned_consumer'] is True and item['review_basis']
                    and item['parent_review_identity_sha256'] == self.plan['parent_review_pin']['identity_sha256'],
                    'privileged_consumer_identification_missing')
            self.pin_fact(item['identification_file_pin'])
        snapshots = {}
        for proc in pids:
            self.left()
            pid = int(proc.name)
            owner = None
            try:
                owner = proc.stat().st_uid
                with (proc/'status').open('rb') as f:
                    status = f.read(LIMITS['one_proc_bytes']+1)
                require(len(status) <= LIMITS['one_proc_bytes'], 'process_status_limit')
            except FileNotFoundError:
                require(not proc.exists(), 'process_status_missing')
                continue
            except PermissionError:
                # No invented security clearance for unrelated foreign host daemons.
                require(owner != UID and pid not in explicit, 'relevant_process_status_inaccessible')
                continue
            self.read_bytes += len(status)
            require(self.read_bytes <= LIMITS['total_file_bytes'], 'cumulative_process_read_limit')
            fields = {}
            for line in status.decode().splitlines():
                if ':' in line:
                    k,v = line.split(':',1); fields[k] = v.strip()
            snapshots[pid] = {'path':proc,'fields':fields,
                              'uids':[int(x) for x in fields['Uid'].split()],
                              'ppid':int(fields['PPid'])}
        owned = {pid for pid,item in snapshots.items() if UID in item['uids']}
        def owned_descendant(pid):
            seen = set()
            current = snapshots[pid]['ppid']
            while current in snapshots and current not in seen:
                if current in owned:
                    return True
                seen.add(current)
                require(len(seen) <= LIMITS['processes'], 'process_ancestry_limit')
                current = snapshots[current]['ppid']
            return False
        identification_pin = self.plan['account_service_identification_pin']
        # Ordinary original file pin: the unchanged parent configuration digest binds it.
        self.pin_fact(identification_pin)
        def charge_service_bytes(count):
            self.read_bytes += count
            require(self.read_bytes <= LIMITS['total_file_bytes'], 'cumulative_account_service_read_limit')
        excluded = []
        terminal_zombies = []
        relevant = 0
        identified = 0
        for pid,item in snapshots.items():
            if pid not in owned and pid not in explicit and not owned_descendant(pid):
                continue
            relevant += 1
            proc,fields = item['path'],item['fields']
            before = self.proc_read(proc/'stat', LIMITS['one_proc_bytes'])
            if before is None:
                continue
            start = before[before.rfind(b')')+2:].split()[19]
            if pid in explicit:
                require(int(start) == explicit[pid]['start_ticks']
                        and explicit[pid]['uid'] in item['uids'], 'identified_consumer_PID_changed')
                identified += 1
            if pid == 1654291:
                portal_pin = self.plan['portal_service_review_pin']
                self.pin_fact(portal_pin)
                def charge_portal_metadata(entries, checks, unused_fds):
                    require(unused_fds == 0, 'portal_unexpected_process_FD_debit')
                    self.walk_entries += entries; self.stat_checks += checks
                    require(self.walk_entries <= LIMITS['walk_entries']
                            and self.stat_checks <= LIMITS['stat_checks'], 'portal_metadata_limit')
                    self.left()
                audit = exact_portal_autounmount_identification(portal_pin, ROWS, list(self.args.select),
                    list(self.facts['removed_rows']), self.plan['parent_review_pin']['identity_sha256'],
                    PORTAL_HELPER_SHA, self.left, charge_service_bytes, charge_portal_metadata,
                    continuity_rows=continuity_rows)
                require(int(start) == audit['start_ticks'], 'portal_snapshot_PID_changed')
                excluded.append(audit)
                self.facts['latest_exact_portal_service_classification'] = audit
                relevant -= 1
                continue
            if pid == 359656:
                audit = exact_account_pam_service_identification(identification_pin,
                    self.plan['parent_review_pin']['identity_sha256'], self.left, charge_service_bytes)
                excluded.append(audit)
                self.facts.setdefault('exact_account_service_classification_checks', []).append({
                    'checked_at':now(), 'pid':359656, 'start_ticks':40749693,
                    'classification':'excluded_exact_system_service', 'check_sha256':sha(canonical(audit))})
                self.facts['latest_exact_account_service_classification'] = audit
                relevant -= 1
                continue
            if fields.get('State','').split()[:1] == ['Z']:
                # Linux v6.8 do_exit clears task mm/files/fs before EXIT_ZOMBIE.
                # A zombie leader with other threads is not covered by this branch.
                before_values = before[before.rfind(b')')+2:].split()
                require(before_values[0] == b'Z' and int(before_values[1]) == item['ppid']
                        and int(fields['Pid']) == pid and int(fields['Threads']) == 1,
                        'terminal_zombie_initial_public_identity_changed')
                status = self.proc_read(proc/'status', LIMITS['one_proc_bytes'])
                require(status is not None, 'terminal_zombie_status_disappeared')
                terminal_fields = {}
                for line in status.decode().splitlines():
                    if ':' in line:
                        key,value = line.split(':',1)
                        require(key not in terminal_fields, 'terminal_zombie_duplicate_status')
                        terminal_fields[key] = value.strip()
                terminal_uids = [int(value) for value in terminal_fields['Uid'].split()]
                require(terminal_fields['State'].split()[:1] == ['Z']
                        and int(terminal_fields['Pid']) == pid
                        and int(terminal_fields['PPid']) == item['ppid']
                        and terminal_uids == item['uids'] and int(terminal_fields['Threads']) == 1,
                        'terminal_zombie_fresh_public_identity_changed')
                after = self.proc_read(proc/'stat', LIMITS['one_proc_bytes'])
                require(after is not None, 'terminal_zombie_final_stat_disappeared')
                after_values = after[after.rfind(b')')+2:].split()
                require(after_values[0] == b'Z' and after_values[19] == start
                        and int(after_values[1]) == item['ppid'],
                        'terminal_zombie_final_state_PID_or_parent_changed')
                terminal_zombies.append({'pid':pid, 'start_ticks':int(start),
                    'ppid':item['ppid'], 'uids':terminal_uids, 'state':'Z', 'threads':1,
                    'captured_status_and_fresh_before_after_stat_Z':True,
                    'fresh_public_status_pin':{'bytes':len(status),'sha256':sha(status)},
                    'protected_references':{key:'UNOBSERVED' for key in ('fd','cwd','root','exe','maps')},
                    'kernel_terminal_resource_release_basis':
                        'https://github.com/torvalds/linux/blob/v6.8/kernel/exit.c#L858-L891',
                    'kernel_terminal_mm_files_fs_invariant_is_explicit_assumption':True,
                    'other_threads_or_live_consumers_exempted':False,
                    'global_reference_free_or_cleanup_clearance_claimed':False})
                continue
            try:
                links = [proc/'cwd',proc/'root',proc/'exe']
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
                    require(not any_inside(target,self.selected), 'live_process_source_dependency')
                    require(not inside(target.removesuffix(' (deleted)'),R14_PATH), 'live_final14_source_process')
                maps = self.proc_read(proc/'maps', LIMITS['one_proc_bytes'])
                cmd = self.proc_read(proc/'cmdline', LIMITS['one_proc_bytes'])
                if maps is None or cmd is None:
                    continue
                for line in maps.decode(errors='strict').splitlines():
                    pieces = line.split(None,5)
                    if len(pieces)==6:
                        require(not any_inside(pieces[5],self.selected), 'mapped_source_dependency')
                require(not any(str(p).encode() in cmd for p in self.selected),
                        'live_or_queued_helper_source_dependency')
                require(str(R14_PATH).encode() not in cmd, 'active_final14_command')
                after = self.proc_read(proc/'stat', LIMITS['one_proc_bytes'])
                if after is not None:
                    require(after[after.rfind(b')')+2:].split()[19]==start, 'process_PID_reused')
            except FileNotFoundError:
                require(not proc.exists(), 'relevant_process_field_disappeared')
        require(set(explicit) <= set(snapshots), 'identified_consumer_missing_from_process_snapshot')
        return {'owned_or_owned_descendant_processes_checked':relevant,
                'explicit_privileged_consumer_evidence_checked':identified,
                'process_links_checked':self.proc_fds,
                'foreign_unidentified_daemons_not_invented_as_consumers':True,
                'inaccessible_ordinary_owned_or_identified_consumer_refuses':True,
                'excluded_exact_system_services':excluded,
                'stable_single_thread_terminal_zombie_audits':terminal_zombies,
                'exact_service_unobserved_references_are_not_reference_free':True,
                'global_privileged_security_clearance_claimed':False,
                'raw_process_args_maps_auth_environment_not_serialized':True}

    def aliases_and_sources(self):
        require(self.plan['pending_alias_coverage_review']['complete'] is True and
                self.plan['pending_alias_coverage_review']['no_queued_source_consumers'] is True,
                'pending_alias_coverage_missing')
        history = {x['path']: x for x in self.plan['historical_reference_files']}
        require(len(history) == len(self.plan['historical_reference_files']), 'history_pin_duplicate')
        for pin in history.values():
            self.pin_fact(pin)
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
                if str(p) not in self.passive_stats:
                    self.read(p)
                require(stamp(p.lstat()) == self.passive_stats[str(p)], 'baseline_metadata_changed')
                if self.reference_hits[str(p)]:
                    require(str(p) in history and self.passive_hashes[str(p)] == history[str(p)]['sha256'],
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
            self.pin_fact(pin)

    def stable_inventory(self):
        self.privacy_gate()
        def removed(path):
            return any(inside(path,BASE/name) for name in self.facts['removed_rows'])
        for path,expected in self.initial_tracked_metadata_stats.items():
            if removed(path):
                continue
            self.left(); self.stat_checks += 1
            require(self.stat_checks <= LIMITS['stat_checks'], 'stable_stat_check_limit')
            s = P(path).lstat()
            require({**stamp(s), 'allocated_bytes': s.st_blocks*512} == expected,
                    'initial_tracked_metadata_inventory_changed')
        for path,expected in self.passive_stats.items():
            if removed(path):
                continue
            self.left(); self.stat_checks += 1
            require(self.stat_checks <= LIMITS['stat_checks'], 'stable_stat_check_limit')
            require(stamp(P(path).lstat()) == expected, 'baseline_file_inventory_changed')
        for path,expected in self.directory_stats.items():
            if removed(path):
                continue
            self.left(); self.stat_checks += 1
            require(self.stat_checks <= LIMITS['stat_checks'], 'stable_stat_check_limit')
            # Directory identity/ctime/mtime/size detects added or removed children.
            require(stamp(P(path).lstat()) == expected, 'baseline_directory_inventory_changed')
        for path,expected in self.symlink_stats.items():
            if removed(path):
                continue
            self.left(); self.stat_checks += 1
            require(self.stat_checks <= LIMITS['stat_checks'], 'stable_stat_check_limit')
            p = P(path)
            require(stamp(p.lstat()) == expected['stat'] and os.readlink(p) == expected['link'],
                    'baseline_symlink_inventory_changed')
            if inside(path,RAW):
                require(not any_inside(str(p.resolve(strict=True)),self.selected),
                        'raw_link_live_source_dependency')
        names = sorted(p.name for p in RAW.iterdir() if p.name.startswith(('lanl-','lanl17-')))
        require(names == self.raw_namespace, 'raw_namespace_changed')
        self.privacy_gate()
        return {'stat_checks':self.stat_checks,'unchanged_files':len(self.passive_stats),
                'unchanged_directories':len(self.directory_stats),
                'unchanged_symlinks':len(self.symlink_stats)}

    def pre_remove_gate(self, name):
        self.privacy_gate()
        leases = self.leases()
        self.retain_git(); self.protect(); self.stable_inventory()
        current = self.tree(BASE/name,ROWS[name]['head'],hash_regular_bytes=True)
        baseline = self.baseline[name]
        require(self.args.remove is True and baseline['regular_bytes_verified'] is False
                and baseline['tracked_mode_blob_source_inventory_sha256'] is None
                and current['regular_bytes_verified'] is True
                and re.fullmatch('[0-9a-f]{64}',current['tracked_mode_blob_source_inventory_sha256']),
                'full_pre_remove_regular_byte_check_required')
        byte_result_fields = ('regular_bytes_verified', 'tracked_mode_blob_source_inventory_sha256')
        require({k:v for k,v in current.items() if k not in byte_result_fields}
                == {k:v for k,v in baseline.items() if k not in byte_result_fields},
                'pre_remove_checkout_changed')
        self.facts['pre_remove_full_byte_checks'][name] = current
        later = self.leases()
        require({k:v['sha256'] for k,v in later.items()}=={k:v['sha256'] for k,v in leases.items()},
                'released_lease_generation_changed_during_check')
        self.retain_git()
        self.privacy_gate()
        return current

    def gate(self, compare=False):
        self.left()
        self.privacy_gate()
        leases = self.leases()
        sources = self.retain_git()
        self.protect()
        trees = {p.name: self.tree(p, ROWS[p.name]['head'],hash_regular_bytes=not self.args.remove)
                 for p in self.selected if p.name not in self.facts['removed_rows']}
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
        private_roots = self.privacy_gate()
        return {'leases': leases, 'sources': sources, 'trees': trees,
                'effective_private_ancestor_roots': private_roots,
                'raw_tree_count': len(raw), 'raw_tree_inventory_sha256': sha(canonical(raw)),
                'aliases': aliases, 'processes': processes}

    def perform(self):
        require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
                and os.getuid() == os.geteuid() == UID
                and pwd.getpwuid(UID).pw_name == ACCOUNT, 'wrong_host_account')
        self.privacy_gate()
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
        # Exclude only explicit back-links to this review, not their other facts/pins.
        # The sealed review can then bind configuration without a digest cycle.
        review_links = []
        for key in ('control_siblings_complete_review', 'pending_alias_coverage_review',
                    'receipt_source_proofs_complete_review', 'original_raw_files_complete_review'):
            coverage = dict(config[key])
            review_links.append(coverage.pop('parent_review_identity_sha256'))
            config[key] = coverage
        consumers = []
        for item in config['relevant_privileged_consumers']:
            consumer = dict(item)
            review_links.append(consumer.pop('parent_review_identity_sha256'))
            consumers.append(consumer)
        config['relevant_privileged_consumers'] = consumers
        require(review['format'] == 'swdb.consumed-detached-source-parent-review.v1'
                and review['accepted_for_exact_subset'] is True
                and review['reviewed_configuration_sha256'] == sha(canonical(config))
                and review['final14_completed_and_released'] is True,
                'concrete_parent_configuration_or_final14_review_missing')
        require(all(link == review['identity_sha256'] for link in review_links),
                'excluded_parent_review_link_not_bound')
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
            self.pre_remove_gate(name)
            require(sha(self.read(self.args.plan, LIMITS['plan_bytes'])[0]) == self.args.plan_sha256
                    and sha(self.read(P(__file__).absolute(), LIMITS['plan_bytes'])[0]) == self.own_sha,
                    'final_plan_or_own_source_changed')
            self.leases()
            self.process_references([name])
            # Sole destructive operation; exact audited enum path, no force/prune/GC/branch deletion.
            self.current_removal = {'row': name, 'started_at': now()}
            self.git(PRIMARY, 'worktree', 'remove', str(BASE/name))
            require(not os.path.lexists(BASE/name), 'worktree_remove_incomplete')
            self.facts['removed_rows'].append(name)
            self.current_removal = None
            self.retain_git()
            self.protect()
        self.leases()
        self.retain_git()
        self.protect()
        self.stable_inventory()
        # One final exact byte pass over preserved originals, not N rehashes.
        require(self.receipts_and_raw()==self.raw_before, 'final_preserved_raw_bytes_changed')
        self.aliases_and_sources()
        for pin in self.plan['protected_file_pins']:
            self.pinned(pin)
        self.process_references()
        require(sha(self.read(self.args.plan, LIMITS['plan_bytes'])[0]) == self.args.plan_sha256
                and sha(self.read(P(__file__).absolute(), LIMITS['plan_bytes'])[0]) == self.own_sha,
                'end_plan_or_source_changed')
        self.facts['admitted'] = True
        self.facts['free_after_bytes'] = {p: os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ('/data1','/data')}
        self.facts['actual_data1_available_delta_bytes'] = self.facts['free_after_bytes']['/data1']-self.facts['free_before_bytes']['/data1']
        self.facts['capacity_admission'] = False

    def publish(self):
        self.facts['effective_private_ancestor_roots'] = self.privacy_gate()
        self.facts['privacy_after_receipt_write_check'] = 'Source-enforced fixed root identity/mode check; receipt carries its pre-seal snapshots.'
        self.facts['finished_at'] = now()
        self.facts['bytes_read'] = self.read_bytes
        self.facts['walk_entries_checked'] = self.walk_entries
        self.facts['stable_stat_checks'] = self.stat_checks
        self.facts['full_raw_byte_passes'] = 2 if self.facts['admitted'] else 'incomplete'
        self.facts['per_remove_full_remaining_catalog_rehash'] = False
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
        self.privacy_gate()
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

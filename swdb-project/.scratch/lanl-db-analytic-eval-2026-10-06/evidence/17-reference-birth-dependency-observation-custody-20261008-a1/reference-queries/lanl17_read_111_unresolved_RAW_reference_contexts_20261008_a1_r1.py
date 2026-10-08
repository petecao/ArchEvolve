#!/usr/bin/env python3
"""SOURCE-ONLY 2026-10-08 ET: fixed 111-file, read-only stdin query.

Parent reviews this exact source before any use. Hashes every original body;
projects reference metadata only. No selected-control import, subprocess,
Git, mutation, evaluation, queued-consumer attestation or clearance.
"""
import argparse
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

UID = 114316761
RAW = Path('/data/yanruj/EvolveSWDB_runs')
ONE_FILE = 512 * 1024 * 1024
TOTAL_BYTES = 16 * 1024 * 1024 * 1024
OUTPUT_BYTES = 32 * 1024 * 1024
MAX_CONTEXTS = 200000
MAX_VALUE = 8192
MAX_LINE = 4096
MAX_ALIAS_USES = 256
SECONDS = 600
EXPECTED_INPUT_BYTES = 240313888
EXPECTED_FILE_COUNT = 111
INPUT_PACK_PIN = {'path': '/private/tmp/lanl17-all18-local-literal-historical-reference-candidates-20261008-a1-r1.json', 'bytes': 3292991, 'sha256': 'a28ceb16234634cc8ee74eef0fdb5b3e9fb5f01aad90390ca188a2102bbcf31e', 'original_failed_O_pin': {'bytes': 21616756, 'path': '/private/tmp/lanl17-detached-passive-observer-originals-20261008-a3/observer.stdout', 'sha256': '93c08ff387147c8709d53e8cc39569afcaeac2e5cb667602a6859e2eee6e63e5'}}
ROW_PATHS = {'ArchEvolve-lanl-allocator-a2-20261006': '/data1/yanruj/ArchEvolve-lanl-allocator-a2-20261006', 'ArchEvolve-lanl-bulk-services-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-bulk-services-20261006-a1', 'ArchEvolve-lanl-bulk-total-services-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-bulk-total-services-20261006-a1', 'ArchEvolve-lanl-clock-a2-20261006': '/data1/yanruj/ArchEvolve-lanl-clock-a2-20261006', 'ArchEvolve-lanl-count-20261006': '/data1/yanruj/ArchEvolve-lanl-count-20261006', 'ArchEvolve-lanl-estimates-20261006': '/data1/yanruj/ArchEvolve-lanl-estimates-20261006', 'ArchEvolve-lanl-estimation-role-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a1', 'ArchEvolve-lanl-estimation-role-20261006-a2': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a2', 'ArchEvolve-lanl-float-memory-services-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-float-memory-services-20261006-a1', 'ArchEvolve-lanl-functional-evaluation-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-functional-evaluation-20261006-a1', 'ArchEvolve-lanl-functional-object-counts-20261006-a2': '/data1/yanruj/ArchEvolve-lanl-functional-object-counts-20261006-a2', 'ArchEvolve-lanl-functional-strict-20261006': '/data1/yanruj/ArchEvolve-lanl-functional-strict-20261006', 'ArchEvolve-lanl-independent-services-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-independent-services-20261006-a1', 'ArchEvolve-lanl-memory-a1-20261006': '/data1/yanruj/ArchEvolve-lanl-memory-a1-20261006', 'ArchEvolve-lanl-native-object-counts-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-native-object-counts-20261006-a1', 'ArchEvolve-lanl-openmp-projections-20261006-a1': '/data1/yanruj/ArchEvolve-lanl-openmp-projections-20261006-a1', 'ArchEvolve-lanl-prospective-inputs-20261006-a2': '/data1/yanruj/ArchEvolve-lanl-prospective-inputs-20261006-a2', 'ArchEvolve-lanl-root-projection-20261006': '/data1/yanruj/ArchEvolve-lanl-root-projection-20261006'}
INPUTS = [
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-allocator-counts-20261006-a2/runner.py",
    "bytes": 3066,
    "sha256": "0c27e8a413eeed578e3172415c483a3e317d0fbf3d9a9c608ba42c2524a514f4",
    "original_stat": {
      "ctime_ns": 1791329487881583288,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14162775,
      "mode": 33204,
      "mtime_ns": 1791329487881583288,
      "nlink": 1,
      "size": 3066,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-allocator-a2-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-allocator-elapsed-20261006-a1/runner.py",
    "bytes": 3777,
    "sha256": "176800f45b63ed6b57feb750181299cce50a9f9442a49def41169774720beb82",
    "original_stat": {
      "ctime_ns": 1791330039218203468,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14163857,
      "mode": 33204,
      "mtime_ns": 1791330039218203468,
      "nlink": 1,
      "size": 3777,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-allocator-a2-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-allocator-extra-count-20261006-a1/runner.py",
    "bytes": 4765,
    "sha256": "9dae599f2fee708f33fdb78b062cb82e742f0b933368ce4dfe60cb65e6997586",
    "original_stat": {
      "ctime_ns": 1791342093235099150,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14181040,
      "mode": 33204,
      "mtime_ns": 1791342093235099150,
      "nlink": 1,
      "size": 4765,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-allocator-extra-elapsed-20261006-a1/runner.py",
    "bytes": 4769,
    "sha256": "8dce79a91c7256c38f9dca0fa8b26e7f6fdbe6f00eaca05aa59f78bdd8b727c0",
    "original_stat": {
      "ctime_ns": 1791342708215565937,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14182201,
      "mode": 33204,
      "mtime_ns": 1791342708215565937,
      "nlink": 1,
      "size": 4769,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bound-estimates-20261006-a1/05-compact-reports.json",
    "bytes": 6932285,
    "sha256": "020aa6857591d1f14ac949fa171ddad70f17e469bd0d350a176ac94b891c6181",
    "original_stat": {
      "ctime_ns": 1791324084531889047,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14158696,
      "mode": 33204,
      "mtime_ns": 1791324084531889047,
      "nlink": 1,
      "size": 6932285,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bound-estimates-20261006-a1/bc-estimate.json",
    "bytes": 6885788,
    "sha256": "288dfd4223ff5d5e0b3c9db6c5517b820ef920f009a950970b20d052d280879e",
    "original_stat": {
      "ctime_ns": 1791324035403381309,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14158689,
      "mode": 33204,
      "mtime_ns": 1791324035403381309,
      "nlink": 1,
      "size": 6885788,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bound-estimates-20261006-a1/bfs-estimate.json",
    "bytes": 5809193,
    "sha256": "f54057cd145c357c56be8b8edaa4291b1e0666855469f29ee06ed03cea83f107",
    "original_stat": {
      "ctime_ns": 1791323906900053786,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14158682,
      "mode": 33204,
      "mtime_ns": 1791323906900053786,
      "nlink": 1,
      "size": 5809193,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bound-estimates-20261006-a1/characterization.json",
    "bytes": 21909,
    "sha256": "895dd962955e1f49e03fb0fe32344e5f19afd86c88692886a45581d881327caf",
    "original_stat": {
      "ctime_ns": 1791323666164569036,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14158661,
      "mode": 33204,
      "mtime_ns": 1791323666164569036,
      "nlink": 1,
      "size": 21909,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimates-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bound-estimates-20261006-a1/job.sh",
    "bytes": 5860,
    "sha256": "b8f590019ff572cfcfb8d1aca123a9babd6547cff016465dc0bc6aa8f543afdc",
    "original_stat": {
      "ctime_ns": 1791323570115578500,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157771,
      "mode": 33261,
      "mtime_ns": 1791323570114578489,
      "nlink": 1,
      "size": 5860,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimates-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bound-estimates-20261006-a1/fixture-counted/optimized.json",
    "bytes": 10024,
    "sha256": "4b98500c4a699760076de1fdf76785e6c2301d5ad3236849ac5e8e023729d228",
    "original_stat": {
      "ctime_ns": 1791323651940422314,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14158667,
      "mode": 33204,
      "mtime_ns": 1791323651940422314,
      "nlink": 1,
      "size": 10024,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimates-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bound-estimates-20261006-a1/fixture-counted/source.json",
    "bytes": 2087,
    "sha256": "05ae2e0220e1d9027e761ce1fee4e9455aa1543afb69b98a9f9028087ecd861a",
    "original_stat": {
      "ctime_ns": 1791323651957422490,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14158669,
      "mode": 33204,
      "mtime_ns": 1791323651957422490,
      "nlink": 1,
      "size": 2087,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimates-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bulk-count-20261006-a1/runner.py",
    "bytes": 4344,
    "sha256": "3713b18ae2784afcd23c477025b9866948d5fa7198d248d147e405fac973c875",
    "original_stat": {
      "ctime_ns": 1791335069501481629,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14171194,
      "mode": 33204,
      "mtime_ns": 1791335069501481629,
      "nlink": 1,
      "size": 4344,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-bulk-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bulk-count-20261006-a2/runner.py",
    "bytes": 4325,
    "sha256": "39c6c61328ff6cfc42ae436a799c9c833d6d647a1196ae02b802fcb3347f745e",
    "original_stat": {
      "ctime_ns": 1791335273618617760,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14172560,
      "mode": 33204,
      "mtime_ns": 1791335273618617760,
      "nlink": 1,
      "size": 4325,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-bulk-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bulk-elapsed-20261006-a2/runner.py",
    "bytes": 4327,
    "sha256": "9647a7815f5a825857381a6c37e459b2269eca21b002ba7ea3885826f0fcd557",
    "original_stat": {
      "ctime_ns": 1791336019713407936,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14173481,
      "mode": 33204,
      "mtime_ns": 1791336019713407936,
      "nlink": 1,
      "size": 4327,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-bulk-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bulk-total-count-20261006-a1/runner.py",
    "bytes": 4777,
    "sha256": "8789833badce21aa846419cf6f575b5b298d7c7db5d7395b199917ea600b9c46",
    "original_stat": {
      "ctime_ns": 1791337260898426162,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14174279,
      "mode": 33204,
      "mtime_ns": 1791337260898426162,
      "nlink": 1,
      "size": 4777,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-bulk-total-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-bulk-total-elapsed-20261006-a1/runner.py",
    "bytes": 4779,
    "sha256": "d2dbabf3bf62cf5bddeff7decd91dcdd50445e9a9cb9c60e5fb0acd2e397e195",
    "original_stat": {
      "ctime_ns": 1791337825279365759,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14175139,
      "mode": 33204,
      "mtime_ns": 1791337825279365759,
      "nlink": 1,
      "size": 4779,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-bulk-total-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-count-equivalence-20261006-a1/job.sh",
    "bytes": 1301,
    "sha256": "f29947be9c7c8a2fbceb0cab6a47c89b5f075a47216ad863b1d68dcc93b401f4",
    "original_stat": {
      "ctime_ns": 1791322060927073145,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065675,
      "mode": 33204,
      "mtime_ns": 1791322060927073145,
      "nlink": 1,
      "size": 1301,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-count-equivalence-20261006-a2/job.sh",
    "bytes": 1301,
    "sha256": "fee17f90515816c727b0e64b51b1704c488d6e2fb624695f4d28117b68267c18",
    "original_stat": {
      "ctime_ns": 1791323115144893353,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157299,
      "mode": 33261,
      "mtime_ns": 1791323115144893353,
      "nlink": 1,
      "size": 1301,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc/characterization.json",
    "bytes": 17057373,
    "sha256": "4e2ebed56006d9e32813e71265c1aa03357a5cdabfbe45e6d4f18575e2c93cea",
    "original_stat": {
      "ctime_ns": 1791322065925124487,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065125,
      "mode": 33204,
      "mtime_ns": 1791322065925124487,
      "nlink": 1,
      "size": 17057373,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc/host-end.txt",
    "bytes": 3508,
    "sha256": "b793b64a2424b3d4cd82d237b0001896ed3b4c7f8bd9bc461c27c76cd854db40",
    "original_stat": {
      "ctime_ns": 1791322084968320121,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065997,
      "mode": 33204,
      "mtime_ns": 1791322084968320121,
      "nlink": 1,
      "size": 3508,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc/job.sh",
    "bytes": 1538,
    "sha256": "f5f2610772da00bcf42b4d22eff26d780a286b05b98c47113365a52a7e00cbaf",
    "original_stat": {
      "ctime_ns": 1791321848400891501,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065082,
      "mode": 33204,
      "mtime_ns": 1791321848400891501,
      "nlink": 1,
      "size": 1538,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc/counted/optimized.json",
    "bytes": 2402422,
    "sha256": "467eb12c2272bb0f817191247b16f595132bf0155d41c05a09404474807538b1",
    "original_stat": {
      "ctime_ns": 1791321867093083262,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065633,
      "mode": 33204,
      "mtime_ns": 1791321867093083262,
      "nlink": 1,
      "size": 2402422,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc/counted/regions.json",
    "bytes": 2185,
    "sha256": "d0db4e1c2c8277a379b5b08fe89e58792a8830df2a29e1c950361d96a73c6a82",
    "original_stat": {
      "ctime_ns": 1791321857984989820,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065622,
      "mode": 33204,
      "mtime_ns": 1791321857984989820,
      "nlink": 1,
      "size": 2185,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc/counted/source.json",
    "bytes": 4069914,
    "sha256": "03707e7b173ba4014d2f71732c8d08cbe7c514ef53ac8ef0220cd209b8f56255",
    "original_stat": {
      "ctime_ns": 1791321871993133535,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065636,
      "mode": 33204,
      "mtime_ns": 1791321871993133535,
      "nlink": 1,
      "size": 4069914,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bfs/characterization.json",
    "bytes": 14191743,
    "sha256": "8936544b49da8d62064ba812b1a99a6bde19df53d5fd47310f0dd01d02468352",
    "original_stat": {
      "ctime_ns": 1791321909902522528,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065088,
      "mode": 33204,
      "mtime_ns": 1791321909902522528,
      "nlink": 1,
      "size": 14191743,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bfs/job.sh",
    "bytes": 1536,
    "sha256": "5d27237c56b4787ecd8d1b1d96c24abeec7c035b9d627da4c10e409705448d12",
    "original_stat": {
      "ctime_ns": 1791321848306890537,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14064495,
      "mode": 33204,
      "mtime_ns": 1791321848306890537,
      "nlink": 1,
      "size": 1536,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bfs/counted/optimized.json",
    "bytes": 2030850,
    "sha256": "872806f32c9ce2d48056414f5886f483c0a9e7fa99ea8797ae0e291186931011",
    "original_stat": {
      "ctime_ns": 1791321865151063338,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065631,
      "mode": 33204,
      "mtime_ns": 1791321865151063338,
      "nlink": 1,
      "size": 2030850,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bfs/counted/regions.json",
    "bytes": 3161,
    "sha256": "21161762fd7d51088bc6221f4b58a8ee701a0b1bcac9df24abde9fbe3c36ccd2",
    "original_stat": {
      "ctime_ns": 1791321857944989410,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065617,
      "mode": 33204,
      "mtime_ns": 1791321857944989410,
      "nlink": 1,
      "size": 3161,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bfs/counted/source.json",
    "bytes": 3092421,
    "sha256": "a79c4fc327693af145e653237f7626bfaad8f3f7e1b92d55ac171f42620e5214",
    "original_stat": {
      "ctime_ns": 1791321868073093316,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14065635,
      "mode": 33204,
      "mtime_ns": 1791321868073093316,
      "nlink": 1,
      "size": 3092421,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bc/characterization.json",
    "bytes": 17268162,
    "sha256": "3a36e568b689fa5dc046a730b78cda37b7de95e917f0d6070387202171edd9cf",
    "original_stat": {
      "ctime_ns": 1791323206535833521,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14156771,
      "mode": 33204,
      "mtime_ns": 1791323206535833521,
      "nlink": 1,
      "size": 17268162,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bc/job.sh",
    "bytes": 1541,
    "sha256": "635f672ca8e041b1797a983f109a8ca558da1a1aaf1a9ed286d7942a485bbff4",
    "original_stat": {
      "ctime_ns": 1791322969473395816,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14156727,
      "mode": 33204,
      "mtime_ns": 1791322969473395816,
      "nlink": 1,
      "size": 1541,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bc/counted/optimized.json",
    "bytes": 2463718,
    "sha256": "f7ee9f2352f22545d2c5d7e7cc00fdf30c8c69b864a3e4881c9d933bff24676a",
    "original_stat": {
      "ctime_ns": 1791322998629695447,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157277,
      "mode": 33204,
      "mtime_ns": 1791322998629695447,
      "nlink": 1,
      "size": 2463718,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bc/counted/regions.json",
    "bytes": 2185,
    "sha256": "d0db4e1c2c8277a379b5b08fe89e58792a8830df2a29e1c950361d96a73c6a82",
    "original_stat": {
      "ctime_ns": 1791322990022606989,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157261,
      "mode": 33204,
      "mtime_ns": 1791322990022606989,
      "nlink": 1,
      "size": 2185,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bc/counted/source.json",
    "bytes": 4162542,
    "sha256": "d9041452c21a1d9057c1a3eca29fc8e4855cb1255792360c665382cefbf38a2d",
    "original_stat": {
      "ctime_ns": 1791323003471745212,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157281,
      "mode": 33204,
      "mtime_ns": 1791323003471745212,
      "nlink": 1,
      "size": 4162542,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bfs/characterization.json",
    "bytes": 14381108,
    "sha256": "a0f6dbe625c69b3aabfad7520c9b288f71a239473555572e40cab5d8fb73da57",
    "original_stat": {
      "ctime_ns": 1791323047614198962,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14066442,
      "mode": 33204,
      "mtime_ns": 1791323047614198962,
      "nlink": 1,
      "size": 14381108,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bfs/job.sh",
    "bytes": 1539,
    "sha256": "38b3c6acb297ec8b9efa09df63d572224ee99719c6c27e09f107ead39de163e4",
    "original_stat": {
      "ctime_ns": 1791322969367394727,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14066437,
      "mode": 33204,
      "mtime_ns": 1791322969367394727,
      "nlink": 1,
      "size": 1539,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bfs/counted/optimized.json",
    "bytes": 2085784,
    "sha256": "3f4b260348354e7ab0159bcd203c2dca3f2e6e1d8c83180f215503ad67762d75",
    "original_stat": {
      "ctime_ns": 1791322997089679619,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157275,
      "mode": 33204,
      "mtime_ns": 1791322997089679619,
      "nlink": 1,
      "size": 2085784,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bfs/counted/regions.json",
    "bytes": 3161,
    "sha256": "21161762fd7d51088bc6221f4b58a8ee701a0b1bcac9df24abde9fbe3c36ccd2",
    "original_stat": {
      "ctime_ns": 1791322990155608356,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157266,
      "mode": 33204,
      "mtime_ns": 1791322990155608356,
      "nlink": 1,
      "size": 3161,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bfs/counted/source.json",
    "bytes": 3175233,
    "sha256": "77bf1ed3aa9ba3c1d86fca790074b6f91223c43f9275129ef997ed8ac2627ba7",
    "original_stat": {
      "ctime_ns": 1791322999974709270,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14157279,
      "mode": 33204,
      "mtime_ns": 1791322999974709270,
      "nlink": 1,
      "size": 3175233,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-count-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/runner.py",
    "bytes": 4419,
    "sha256": "f7b0297720088df2d21bed067254932a782ed492c2713fab0e0e4ce604dd0605",
    "original_stat": {
      "ctime_ns": 1791333249123407085,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14167722,
      "mode": 33204,
      "mtime_ns": 1791333249123407085,
      "nlink": 1,
      "size": 4419,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bc/characterization.json",
    "bytes": 25377935,
    "sha256": "641c80c687d6580a44f7cebdf50b4062be8b077a9c5e91072dc4d776322605d5",
    "original_stat": {
      "ctime_ns": 1791333654421665325,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169717,
      "mode": 33204,
      "mtime_ns": 1791333654421665325,
      "nlink": 1,
      "size": 25377935,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bc/counted/optimized.json",
    "bytes": 3553395,
    "sha256": "fcf2e092e70d55b97d887ab178e8e9e2b191374f25496528b9cc43e4f035d5cc",
    "original_stat": {
      "ctime_ns": 1791333434262353900,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169726,
      "mode": 33204,
      "mtime_ns": 1791333434262353900,
      "nlink": 1,
      "size": 3553395,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bc/counted/regions.json",
    "bytes": 2365,
    "sha256": "2984f52cdb983676a82ee58d384a9fc937b4b17cffa85440abf1edbf5ee393b9",
    "original_stat": {
      "ctime_ns": 1791333425630263195,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169720,
      "mode": 33204,
      "mtime_ns": 1791333425630263195,
      "nlink": 1,
      "size": 2365,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bc/counted/source.json",
    "bytes": 6202015,
    "sha256": "9e0d8ab4cae63793c3de0272a0ffbba31a37905278368ad6b5c42212346cbc20",
    "original_stat": {
      "ctime_ns": 1791333439288406711,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169728,
      "mode": 33204,
      "mtime_ns": 1791333439288406711,
      "nlink": 1,
      "size": 6202015,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bfs/characterization.json",
    "bytes": 21419440,
    "sha256": "464bd34630c5c57bfc6ff86f24ca7d7dd072a819deaab9cd86c3fa5961f3423b",
    "original_stat": {
      "ctime_ns": 1791333380176785470,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169684,
      "mode": 33204,
      "mtime_ns": 1791333380176785470,
      "nlink": 1,
      "size": 21419440,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bfs/counted/optimized.json",
    "bytes": 3053741,
    "sha256": "ae607bba8def6476b494cb1595d81c25474718a7487afe88549006daa1ab316c",
    "original_stat": {
      "ctime_ns": 1791333293200870847,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169705,
      "mode": 33204,
      "mtime_ns": 1791333293200870847,
      "nlink": 1,
      "size": 3053741,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bfs/counted/regions.json",
    "bytes": 3341,
    "sha256": "df2f3e5c8b3618913648995a880d245c2088bf0ddd473feb469b72899e6c4122",
    "original_stat": {
      "ctime_ns": 1791333286187797070,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169687,
      "mode": 33204,
      "mtime_ns": 1791333286187797070,
      "nlink": 1,
      "size": 3341,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bfs/counted/source.json",
    "bytes": 4811381,
    "sha256": "ea94d499f9b0fe360b7e56ff833c908a28f5fa2724ba05d11b41adf773b1c77f",
    "original_stat": {
      "ctime_ns": 1791333296243902858,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169707,
      "mode": 33204,
      "mtime_ns": 1791333296243902858,
      "nlink": 1,
      "size": 4811381,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bc/characterization.json",
    "bytes": 25470789,
    "sha256": "8d248a730ab379bd2da17badf9bfb7c891aae451b3e0f2d8d1f76a69ad46b7ce",
    "original_stat": {
      "ctime_ns": 1791334327484711053,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169760,
      "mode": 33204,
      "mtime_ns": 1791334327484711053,
      "nlink": 1,
      "size": 25470789,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bc/counted/optimized.json",
    "bytes": 3553395,
    "sha256": "fcf2e092e70d55b97d887ab178e8e9e2b191374f25496528b9cc43e4f035d5cc",
    "original_stat": {
      "ctime_ns": 1791333962738896378,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169769,
      "mode": 33204,
      "mtime_ns": 1791333962738896378,
      "nlink": 1,
      "size": 3553395,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bc/counted/regions.json",
    "bytes": 2365,
    "sha256": "2984f52cdb983676a82ee58d384a9fc937b4b17cffa85440abf1edbf5ee393b9",
    "original_stat": {
      "ctime_ns": 1791333954020805103,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169763,
      "mode": 33204,
      "mtime_ns": 1791333954020805103,
      "nlink": 1,
      "size": 2365,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bc/counted/source.json",
    "bytes": 6202015,
    "sha256": "9e0d8ab4cae63793c3de0272a0ffbba31a37905278368ad6b5c42212346cbc20",
    "original_stat": {
      "ctime_ns": 1791333967821949594,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169771,
      "mode": 33204,
      "mtime_ns": 1791333967821949594,
      "nlink": 1,
      "size": 6202015,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bfs/characterization.json",
    "bytes": 21515196,
    "sha256": "13a2acfefce2e688fd16c008cb1233ba555844988bbbec0b09140f35ad4cb209",
    "original_stat": {
      "ctime_ns": 1791333909242336212,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169739,
      "mode": 33204,
      "mtime_ns": 1791333909242336212,
      "nlink": 1,
      "size": 21515196,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bfs/counted/optimized.json",
    "bytes": 3053741,
    "sha256": "ae607bba8def6476b494cb1595d81c25474718a7487afe88549006daa1ab316c",
    "original_stat": {
      "ctime_ns": 1791333784954034054,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169748,
      "mode": 33204,
      "mtime_ns": 1791333784954034054,
      "nlink": 1,
      "size": 3053741,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bfs/counted/regions.json",
    "bytes": 3341,
    "sha256": "df2f3e5c8b3618913648995a880d245c2088bf0ddd473feb469b72899e6c4122",
    "original_stat": {
      "ctime_ns": 1791333777942960568,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169742,
      "mode": 33204,
      "mtime_ns": 1791333777942960568,
      "nlink": 1,
      "size": 3341,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bfs/counted/source.json",
    "bytes": 4811381,
    "sha256": "ea94d499f9b0fe360b7e56ff833c908a28f5fa2724ba05d11b41adf773b1c77f",
    "original_stat": {
      "ctime_ns": 1791333788015066137,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169750,
      "mode": 33204,
      "mtime_ns": 1791333788015066137,
      "nlink": 1,
      "size": 4811381,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-float-memory-count-20261006-a1/runner.py",
    "bytes": 4760,
    "sha256": "0ff2731f0e3d0b1063e952caf782332d92edadceb995716547061a3f4e15700a",
    "original_stat": {
      "ctime_ns": 1791343637860397197,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14183383,
      "mode": 33204,
      "mtime_ns": 1791343637860397197,
      "nlink": 1,
      "size": 4760,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-float-memory-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-float-memory-elapsed-20261006-a1/runner.py",
    "bytes": 4764,
    "sha256": "aaf4bc1f775c25601473f464c0602582c4b6aa11dd15bdc6309bca9f98a2031e",
    "original_stat": {
      "ctime_ns": 1791344108574409556,
      "dev": 2065,
      "gid": 114316761,
      "ino": 9345438,
      "mode": 33204,
      "mtime_ns": 1791344108574409556,
      "nlink": 1,
      "size": 4764,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-float-memory-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-call-projections-20261006-a1/bc.g16/projection/static.json",
    "bytes": 48116,
    "sha256": "3e6b2f92c5661a8b4ffd4ecdb41cc10eab98b363e7a7a11d6f7a5529a66861e2",
    "original_stat": {
      "ctime_ns": 1791334975030492130,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14171170,
      "mode": 33204,
      "mtime_ns": 1791334975030492130,
      "nlink": 1,
      "size": 48116,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-call-projections-20261006-a1/bfs.g16/projection/static.json",
    "bytes": 37713,
    "sha256": "75818150d970e41ef36270af4f6e8c367e29bced6a78bedc48c4aeef6e05afa7",
    "original_stat": {
      "ctime_ns": 1791334962576361643,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14171162,
      "mode": 33204,
      "mtime_ns": 1791334962576361643,
      "nlink": 1,
      "size": 37713,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-call-projections-20261006-a1/bfs.g17/projection/static.json",
    "bytes": 37713,
    "sha256": "75818150d970e41ef36270af4f6e8c367e29bced6a78bedc48c4aeef6e05afa7",
    "original_stat": {
      "ctime_ns": 1791334985801604976,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14171178,
      "mode": 33204,
      "mtime_ns": 1791334985801604976,
      "nlink": 1,
      "size": 37713,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-call-projections-20261006-a1/bc.g17/projection/static.json",
    "bytes": 48116,
    "sha256": "3e6b2f92c5661a8b4ffd4ecdb41cc10eab98b363e7a7a11d6f7a5529a66861e2",
    "original_stat": {
      "ctime_ns": 1791334998194734807,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14171186,
      "mode": 33204,
      "mtime_ns": 1791334998194734807,
      "nlink": 1,
      "size": 48116,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-call-projections-20261006-a1-control/runner.py",
    "bytes": 1782,
    "sha256": "cae656b772f37b1a626561fa838dab3cab12e4204ac1fa4a09faeb5974946601",
    "original_stat": {
      "ctime_ns": 1791334951478245355,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14171146,
      "mode": 33204,
      "mtime_ns": 1791334951478245355,
      "nlink": 1,
      "size": 1782,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-openmp-projections-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-count-20261006-a1/runner.py",
    "bytes": 4747,
    "sha256": "47680823270c07f2040ff70408989fd790bd5463ead8f78023a78dbafe2b0433",
    "original_stat": {
      "ctime_ns": 1791340353638880506,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14178601,
      "mode": 33204,
      "mtime_ns": 1791340353638880506,
      "nlink": 1,
      "size": 4747,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-count-20261006-a1/count/count-1.3/abi-projection/projection.json",
    "bytes": 42417,
    "sha256": "c7766e640c264891666c5d27982762ec836c1b721fc1c82f603cb27f162506a4",
    "original_stat": {
      "ctime_ns": 1791340470735107283,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14179321,
      "mode": 33204,
      "mtime_ns": 1791340470735107283,
      "nlink": 1,
      "size": 42417,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-elapsed-20261006-a1/runner.py",
    "bytes": 4751,
    "sha256": "eef0d59786b60066b4febb1655f6ab99e0973a1d81d0dfecf91c232fee5862f9",
    "original_stat": {
      "ctime_ns": 1791340708659599533,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14179373,
      "mode": 33204,
      "mtime_ns": 1791340708659599533,
      "nlink": 1,
      "size": 4751,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-elapsed-20261006-a1/elapsed/partial-trials.json",
    "bytes": 2083845,
    "sha256": "48c4bbb78dc46e73be10ce9754f8a59305510ce07e88d36aaab998fa2bb7803a",
    "original_stat": {
      "ctime_ns": 1791340986877513976,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14180139,
      "mode": 33204,
      "mtime_ns": 1791340986877513976,
      "nlink": 1,
      "size": 2083845,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-elapsed-20261006-a1/elapsed/receipt.json",
    "bytes": 2218202,
    "sha256": "4de0fb766dafdafe94f90e5458e33a4afd153f752747b880b7ec61a32b0b42b2",
    "original_stat": {
      "ctime_ns": 1791340986996515223,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14180161,
      "mode": 33204,
      "mtime_ns": 1791340986996515223,
      "nlink": 1,
      "size": 2218202,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-elapsed-20261006-a1/elapsed/count-1.3/abi-projection/projection.json",
    "bytes": 42541,
    "sha256": "19d18ae8e0e99600915b8ff3126cb913c3591bcf1df2c58486e254f3207cf79c",
    "original_stat": {
      "ctime_ns": 1791340823929806798,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14180093,
      "mode": 33204,
      "mtime_ns": 1791340823929806798,
      "nlink": 1,
      "size": 42541,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-independent-services-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-service-byte-read-20261006-a1/runner.py",
    "bytes": 3963,
    "sha256": "9f77a504326c9b8647b29a1159328b161a57fcd17c184766e2d2b241da60a1c4",
    "original_stat": {
      "ctime_ns": 1791332852247250792,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14166979,
      "mode": 33204,
      "mtime_ns": 1791332852247250792,
      "nlink": 1,
      "size": 3963,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-memory-a1-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-service-clock-20261006-a2/runner.py",
    "bytes": 3865,
    "sha256": "86fe58d56cc1dfea35e2d041e8952c01adb117087ebc6efad3ec08b203f2f104",
    "original_stat": {
      "ctime_ns": 1791330912600196392,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14164996,
      "mode": 33204,
      "mtime_ns": 1791330912600196392,
      "nlink": 1,
      "size": 3865,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-clock-a2-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-analytic-service-memory-20261006-a1/runner.py",
    "bytes": 3885,
    "sha256": "529cc86c298c21315f2499fc6b992d4888a9a35efcca4fcd0d1446b022c4033b",
    "original_stat": {
      "ctime_ns": 1791332238467916651,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14165757,
      "mode": 33204,
      "mtime_ns": 1791332238467916651,
      "nlink": 1,
      "size": 3885,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-memory-a1-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a1/runner.py",
    "bytes": 18069,
    "sha256": "05decc60933ca0e45b2dae7a8b4fb06d097086ef9fcd43041b84b582023b4378",
    "original_stat": {
      "ctime_ns": 1791339283722664825,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14176829,
      "mode": 33204,
      "mtime_ns": 1791339283722664825,
      "nlink": 1,
      "size": 18069,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a1-control/dispatcher.py",
    "bytes": 25314,
    "sha256": "7b15ea08da682de892525aeaed3320b302d925e8546866469aa13a05b339ffab",
    "original_stat": {
      "ctime_ns": 1791339280764633798,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14176821,
      "mode": 33204,
      "mtime_ns": 1791339280764633798,
      "nlink": 1,
      "size": 25314,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a2/runner.py",
    "bytes": 19963,
    "sha256": "2b29f6044402998925c16595d0097eecbb41bc1e4de3840504929d297c041e9f",
    "original_stat": {
      "ctime_ns": 1791339677871798009,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14177709,
      "mode": 33204,
      "mtime_ns": 1791339677871798009,
      "nlink": 1,
      "size": 19963,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a2-control/dispatcher.py",
    "bytes": 27934,
    "sha256": "76cc6d6f375e7c110f7630e689d45ae238ba4d0ced0d347c9f7c435d2b24aa86",
    "original_stat": {
      "ctime_ns": 1791339675479772931,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14177705,
      "mode": 33204,
      "mtime_ns": 1791339675479772931,
      "nlink": 1,
      "size": 27934,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a2-postfill-a1/runner.py",
    "bytes": 20043,
    "sha256": "029be60a4162e0ffe720b11587e023337125414830d64951ed480158fff0a194",
    "original_stat": {
      "ctime_ns": 1791341373299561544,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14180176,
      "mode": 33204,
      "mtime_ns": 1791341373299561544,
      "nlink": 1,
      "size": 20043,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a2-postfill-a1-control/dispatcher.py",
    "bytes": 25997,
    "sha256": "a9ef1c4e6040367596cc3b79b57ef7d3c119da730540ef0492095e377c99a9af",
    "original_stat": {
      "ctime_ns": 1791340831024881109,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14180109,
      "mode": 33204,
      "mtime_ns": 1791340831024881109,
      "nlink": 1,
      "size": 25997,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a2-postfill-a1-control/exporter-counters-a2.py",
    "bytes": 23691,
    "sha256": "b98637cd495cebcc5c2da0a806efe1a21f0141a8a2a47a551ea6cec67668c812",
    "original_stat": {
      "ctime_ns": 1791341979357907141,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14181035,
      "mode": 33188,
      "mtime_ns": 1791341979357907141,
      "nlink": 1,
      "size": 23691,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-estimation-role-20261006-a2-postfill-a1-control/exporter.py",
    "bytes": 23528,
    "sha256": "7f38c1e58c770fbd586ea3454fd36d89da2798c59ab12b883820bcddc8887a40",
    "original_stat": {
      "ctime_ns": 1791341711091098676,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14181029,
      "mode": 33204,
      "mtime_ns": 1791341711091098676,
      "nlink": 1,
      "size": 23528,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-estimation-role-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/command-repair.json",
    "bytes": 1908,
    "sha256": "03fbd4e6bfd215352ccc041e860868263d80f77a7b69eab8a9d20dd654d3a56b",
    "original_stat": {
      "ctime_ns": 1791328898832589833,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161567,
      "mode": 33204,
      "mtime_ns": 1791328898832589833,
      "nlink": 1,
      "size": 1908,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/runner.py",
    "bytes": 4496,
    "sha256": "9c293a9ba3baa4cabe92f76ef4d0e39eeae927b0431f7fdd58de9a2c0c832cb7",
    "original_stat": {
      "ctime_ns": 1791328898362585056,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14160936,
      "mode": 33204,
      "mtime_ns": 1791328898362585056,
      "nlink": 1,
      "size": 4496,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024-knob_out_of_range.legality.ii.json",
    "bytes": 1301,
    "sha256": "7496e5a7ef61dd87fe5ca67f82638dd9e894c6b8267b54aaaf11847b0c36abe1",
    "original_stat": {
      "ctime_ns": 1791328957627187441,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161732,
      "mode": 33204,
      "mtime_ns": 1791328957627187441,
      "nlink": 1,
      "size": 1301,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024-schedule_out_of_range.legality.ii.json",
    "bytes": 1309,
    "sha256": "6bd209ab54267d84cba58877d21b7aefd7317734028c75f89520d1df65b542c4",
    "original_stat": {
      "ctime_ns": 1791328959469206166,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161738,
      "mode": 33204,
      "mtime_ns": 1791328959469206166,
      "nlink": 1,
      "size": 1309,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.legality.ii.json",
    "bytes": 1265,
    "sha256": "e2206b77373c9cbfeb375dc7f3e76d645067d275825e30b2d9a4e617db320c4e",
    "original_stat": {
      "ctime_ns": 1791328951142121517,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161716,
      "mode": 33204,
      "mtime_ns": 1791328951142121517,
      "nlink": 1,
      "size": 1265,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384-knob_out_of_range.legality.ii.json",
    "bytes": 1304,
    "sha256": "2890fed07adbe8864e51c55caee6d02dfadfc689ab90ca6b34d2b8eb6630d542",
    "original_stat": {
      "ctime_ns": 1791328944201050960,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161673,
      "mode": 33204,
      "mtime_ns": 1791328944201050960,
      "nlink": 1,
      "size": 1304,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384-schedule_out_of_range.legality.ii.json",
    "bytes": 1312,
    "sha256": "aa08519c4c8b8b532484c3d5fd939a1d768eb673bdf73ab60a0823508a6ce918",
    "original_stat": {
      "ctime_ns": 1791328946024069491,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161679,
      "mode": 33204,
      "mtime_ns": 1791328946024069491,
      "nlink": 1,
      "size": 1312,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.legality.ii.json",
    "bytes": 1268,
    "sha256": "b0e07d3340f5c065101d0732fb52ebe1921b0b77cf7dd006c8cc5493c563631d",
    "original_stat": {
      "ctime_ns": 1791328938153989492,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161657,
      "mode": 33204,
      "mtime_ns": 1791328938153989492,
      "nlink": 1,
      "size": 1268,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/certification.json",
    "bytes": 325459,
    "sha256": "a9295188c39d01a82a348f619ee29f6dbf15d2bb42b86c52f43b6d336ef5e635",
    "original_stat": {
      "ctime_ns": 1791328964474257047,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14162404,
      "mode": 33204,
      "mtime_ns": 1791328964474257047,
      "nlink": 1,
      "size": 325459,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/converter.build.json",
    "bytes": 937,
    "sha256": "c168f87acf2432ae1f9ddb8c42f2e79ee278221b8576bd16b33a698d53d8cd9b",
    "original_stat": {
      "ctime_ns": 1791328937808985986,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161643,
      "mode": 33204,
      "mtime_ns": 1791328937808985986,
      "nlink": 1,
      "size": 937,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.v15/candidate-knob_out_of_range.o.build.json",
    "bytes": 1639,
    "sha256": "e54f7c3dc8735e994c02683c0f98a58b5b59a199984dd22f9c0125963e1a5606",
    "original_stat": {
      "ctime_ns": 1791328959295204398,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161730,
      "mode": 33204,
      "mtime_ns": 1791328959295204398,
      "nlink": 1,
      "size": 1639,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.v15/candidate-positive.o.build.json",
    "bytes": 1630,
    "sha256": "c858311b924354d24cc491183e69e3068171c2d337f98052ab241a968e16b962",
    "original_stat": {
      "ctime_ns": 1791328953034140750,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161715,
      "mode": 33204,
      "mtime_ns": 1791328953034140750,
      "nlink": 1,
      "size": 1630,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.v15/candidate-schedule_out_of_range.o.build.json",
    "bytes": 1643,
    "sha256": "f076b28df6f700166f7e6efde3fcb0bf58f76a3408cefa5bd55ffbbc0bbeea3a",
    "original_stat": {
      "ctime_ns": 1791328961117222920,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161736,
      "mode": 33204,
      "mtime_ns": 1791328961117222920,
      "nlink": 1,
      "size": 1643,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.v15/client-v15.o.build.json",
    "bytes": 1330,
    "sha256": "c5929189e796ef93edfa4994a2b13ad81efa761ace068302ef5cec7feaed4b2d",
    "original_stat": {
      "ctime_ns": 1791328953235142793,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161718,
      "mode": 33204,
      "mtime_ns": 1791328953235142793,
      "nlink": 1,
      "size": 1330,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.v15/evaluator-evaluator-v15.o.build.json",
    "bytes": 1375,
    "sha256": "291bd981e0015b9cc1e4d6ab118ffd78d292b87ea21e7c952e70dd6496058c37",
    "original_stat": {
      "ctime_ns": 1791328954783158530,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161720,
      "mode": 33204,
      "mtime_ns": 1791328954783158530,
      "nlink": 1,
      "size": 1375,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.v15/record-evaluator-v15.o.build.json",
    "bytes": 1369,
    "sha256": "51f66944025e9f1db4add839307d941b27e1f7e8b3113bbb33ffc0a52116306d",
    "original_stat": {
      "ctime_ns": 1791328955572166551,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161722,
      "mode": 33204,
      "mtime_ns": 1791328955572166551,
      "nlink": 1,
      "size": 1369,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-1024.v15/seams-evaluator-v15.o.build.json",
    "bytes": 1367,
    "sha256": "cdc9d59fb2cc5912b0548d057b22139eeb831c37cd696ddbefd08b968ee5e5c1",
    "original_stat": {
      "ctime_ns": 1791328957363184757,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161724,
      "mode": 33204,
      "mtime_ns": 1791328957363184757,
      "nlink": 1,
      "size": 1367,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.v15/candidate-knob_out_of_range.o.build.json",
    "bytes": 1641,
    "sha256": "0ddb069581c541794471077f14ba26a409ceca1d0612246ef230d680aefa616d",
    "original_stat": {
      "ctime_ns": 1791328945840067621,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161671,
      "mode": 33204,
      "mtime_ns": 1791328945840067621,
      "nlink": 1,
      "size": 1641,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.v15/candidate-positive.o.build.json",
    "bytes": 1632,
    "sha256": "fce0531e510880d35063a41e863de63b91a79ab3fb18443ad475fb4fd3476e0c",
    "original_stat": {
      "ctime_ns": 1791328939983008084,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161656,
      "mode": 33204,
      "mtime_ns": 1791328939983008084,
      "nlink": 1,
      "size": 1632,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.v15/candidate-schedule_out_of_range.o.build.json",
    "bytes": 1645,
    "sha256": "2c7cddb50911f5170ab49685f8acb64f486a2450c91a915f780dd091526ec69f",
    "original_stat": {
      "ctime_ns": 1791328947696086487,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161677,
      "mode": 33204,
      "mtime_ns": 1791328947696086487,
      "nlink": 1,
      "size": 1645,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.v15/client-v15.o.build.json",
    "bytes": 1332,
    "sha256": "2728b8d4415a539935c078d8338f3df20c060fbb403644bbcb20e8c04484bddc",
    "original_stat": {
      "ctime_ns": 1791328940209010381,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161659,
      "mode": 33204,
      "mtime_ns": 1791328940209010381,
      "nlink": 1,
      "size": 1332,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.v15/evaluator-evaluator-v15.o.build.json",
    "bytes": 1377,
    "sha256": "4785e257fe732df9379bd78af636079dcec19b943c21c3272aa0dc2002656051",
    "original_stat": {
      "ctime_ns": 1791328941748026025,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161661,
      "mode": 33204,
      "mtime_ns": 1791328941748026025,
      "nlink": 1,
      "size": 1377,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.v15/record-evaluator-v15.o.build.json",
    "bytes": 1371,
    "sha256": "3885194a73264e701c777fc0629ba8416f809a3c80aa54e3b6df005335e30d89",
    "original_stat": {
      "ctime_ns": 1791328942415032805,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161663,
      "mode": 33204,
      "mtime_ns": 1791328942415032805,
      "nlink": 1,
      "size": 1371,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-strict-20261006-a2/strict-certification/certify-899fdd1d9c134afc90ac4db802cf7ce1/bfs-16384.v15/seams-evaluator-v15.o.build.json",
    "bytes": 1369,
    "sha256": "1aee5d47076428a6bd346510b3b221ca9f929443ee565c74cf0065dfe117e94b",
    "original_stat": {
      "ctime_ns": 1791328943947048378,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14161665,
      "mode": 33204,
      "mtime_ns": 1791328943947048378,
      "nlink": 1,
      "size": 1369,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-strict-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-dx-object-counts-20261006-a1/runner.py",
    "bytes": 4155,
    "sha256": "ee64b13c24e47e2afe73e15f5c5767afd4e48c6626d5479ef594673d4d386a6a",
    "original_stat": {
      "ctime_ns": 1791333249125407106,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14167723,
      "mode": 33204,
      "mtime_ns": 1791333249125407106,
      "nlink": 1,
      "size": 4155,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-native-object-counts-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-dx-object-counts-20261006-a2/runner.py",
    "bytes": 4159,
    "sha256": "ce7e3ce4481a42b6b8fad456801c161f0c7817aadebc4e0b261c6be967d05cd3",
    "original_stat": {
      "ctime_ns": 1791334276589179218,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14169779,
      "mode": 33204,
      "mtime_ns": 1791334276589179218,
      "nlink": 1,
      "size": 4159,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-object-counts-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-functional-evaluation-20261006-a1/runner.py",
    "bytes": 6899,
    "sha256": "b2460c99255722e3d80fda1b0b6faec9d4ba47fef1a93dd3ed621b02e34c3963",
    "original_stat": {
      "ctime_ns": 1791339155278317490,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14176160,
      "mode": 33204,
      "mtime_ns": 1791339155278317490,
      "nlink": 1,
      "size": 6899,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-functional-evaluation-20261006-a1"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-native-root-projection-20261006-a1/compile-command.json",
    "bytes": 2033,
    "sha256": "37c4ed546cdb3818994c7621028897d74af66681138faf03e1cbfcef42b1542d",
    "original_stat": {
      "ctime_ns": 1791329406249751941,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14162763,
      "mode": 33204,
      "mtime_ns": 1791329406249751941,
      "nlink": 1,
      "size": 2033,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-root-projection-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl-native-root-projection-20261006-a1/runner.py",
    "bytes": 3766,
    "sha256": "62d92f79431761eba267ddf496699e57e87d94a4e535f39670afd0944c7c7b58",
    "original_stat": {
      "ctime_ns": 1791329405930748693,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14162759,
      "mode": 33204,
      "mtime_ns": 1791329405930748693,
      "nlink": 1,
      "size": 3766,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-root-projection-20261006"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2-control/runner.py",
    "bytes": 1774,
    "sha256": "2bcd8bce4e68f806264a677783239ec2e3713d253c49902e06eb785a6ae9f09b",
    "original_stat": {
      "ctime_ns": 1791335165541487009,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14171874,
      "mode": 33204,
      "mtime_ns": 1791335165541487009,
      "nlink": 1,
      "size": 1774,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-prospective-inputs-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  },
  {
    "path": "/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a2-control/validation-runner.py",
    "bytes": 3548,
    "sha256": "1ce73afe82bd285e0bf10f963ce599ab90949970866933eaca3b7d917cee8e37",
    "original_stat": {
      "ctime_ns": 1791337027052959225,
      "dev": 2065,
      "gid": 114316761,
      "ino": 14174267,
      "mode": 33204,
      "mtime_ns": 1791337027052959225,
      "nlink": 1,
      "size": 3548,
      "uid": 114316761
    },
    "original_candidate_reference_rows": [
      "ArchEvolve-lanl-prospective-inputs-20261006-a2"
    ],
    "original_reference_classification": "unclassified_literal_bytes"
  }
]

PATTERN = re.compile('|'.join(re.escape(v) for v in ROW_PATHS.values()) + r'(?![A-Za-z0-9_.-])')
PATH_TO_ROW = {v:k for k,v in ROW_PATHS.items()}

class Refused(Exception):
    pass

def require(value, code):
    if not value:
        raise Refused(code)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def stamp(s):
    return {k:getattr(s, 'st_'+k) for k in
        ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def check_time(deadline):
    require(time.monotonic() < deadline, 'query_deadline')

def checked_route(path):
    require(path.is_absolute() and str(path) == os.path.normpath(str(path))
            and path.is_relative_to(RAW) and '..' not in path.parts, 'fixed_route')
    route = []
    for node in reversed(path.parents):
        s = node.lstat()
        require(stat.S_ISDIR(s.st_mode) and not stat.S_ISLNK(s.st_mode), 'directory_type_or_symlink')
        if node == Path('/data/yanruj') or node.is_relative_to(Path('/data/yanruj')):
            require(s.st_uid == UID, 'directory_owner')
        else:
            require(s.st_uid == 0, 'system_ancestor_owner')
        route.append((str(node), s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid))
    return route

def read_original(pin, result, deadline):
    check_time(deadline)
    p = Path(pin['path'])
    before_route = checked_route(p)
    before = p.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid == UID and before.st_nlink == 1,
            'file_type_owner_or_links')
    require(0 <= before.st_size <= ONE_FILE and before.st_size == pin['bytes'], 'original_size')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(p, flags)
    parts = []
    h = hashlib.sha256()
    count = 0
    try:
        require(stamp(os.fstat(fd)) == stamp(before), 'open_identity_changed')
        while True:
            check_time(deadline)
            chunk = os.read(fd, min(1024*1024, ONE_FILE-count+1))
            if not chunk:
                break
            count += len(chunk)
            result['body_bytes_read'] += len(chunk)
            require(count <= ONE_FILE and result['body_bytes_read'] <= TOTAL_BYTES, 'body_read_budget')
            h.update(chunk)
            parts.append(chunk)
        end_fd = os.fstat(fd)
        after = p.lstat()
        require(stamp(end_fd) == stamp(before) == stamp(after), 'file_changed_during_read')
        require(checked_route(p) == before_route, 'directory_route_identity_changed')
    finally:
        os.close(fd)
    require(count == pin['bytes'] and h.hexdigest() == pin['sha256'], 'original_body_digest')
    return b''.join(parts), stamp(before), stamp(after)

def labels(s):
    return sorted({PATH_TO_ROW[m.group()] for m in PATTERN.finditer(s)})

def path_literals(value):
    # Emit only matched path substrings. A larger shell command/prompt/string body
    # is never reproduced merely because it contains a candidate directory.
    out = []
    for m in PATTERN.finditer(value):
        end = m.end()
        while end < len(value) and not value[end].isspace() and value[end] not in "\"'<>[]{}(),;":
            end += 1
        fragment = value[m.start():end]
        out.append({'row':PATH_TO_ROW[m.group()], 'path_string':fragment[:MAX_VALUE],
                    'path_string_cut_at_bound':len(fragment)>MAX_VALUE})
    return out

def value_projection(value):
    # Ordinary path or compiler symbol strings may be retained exactly. Larger
    # composite command/code text is path-projected, with its original hash.
    symbol = ('lambda_at_/data1/yanruj/' in value or '(lambda at /data1/yanruj/' in value)
    single = len(value.splitlines()) == 1 and not any(c.isspace() for c in value)
    plain_path = any(value.startswith(p) for p in ROW_PATHS.values()) and single
    return {'original_string_bytes':len(value.encode()), 'original_string_sha256':sha(value.encode()),
            'exact_path_or_symbol_value':value if len(value)<=MAX_VALUE and (plain_path or symbol) else None,
            'matched_path_literals':path_literals(value),
            'projection_kind':'exact_path_or_compiler_symbol' if len(value)<=MAX_VALUE and (plain_path or symbol)
                              else 'path_literals_only_from_compound_string'}

def json_category(keys, value):
    ks = [str(k).lower() for k in keys]
    if 'lambda_at_/data1/yanruj/' in value or '(lambda at /data1/yanruj/' in value:
        return 'compiler_symbol_or_region_identifier'
    if 'source_location' in ks or ('static_analysis' in ks and 'path' in ks):
        return 'IR_debug_or_source_location'
    if 'region_bindings' in ks:
        return 'registered_source_region_provenance'
    if any(k in ks for k in ('compiler_argv','wrapper_argv','projection_argv','argv','command','build_command')):
        return 'recorded_command_argv_not_queue_evidence'
    if any('preserv' in k or 'prior_attempt' in k for k in ks):
        return 'original_directory_preservation_mention'
    if any(k in ks for k in ('source','source_checkout','source_root','cwd','project')):
        return 'source_or_execution_provenance'
    return 'unclassified_scalar_reference'

def context_add(out, item, result, deadline):
    check_time(deadline)
    result['context_count'] += 1
    require(result['context_count'] <= MAX_CONTEXTS, 'projection_context_budget')
    encoded = json.dumps(item, ensure_ascii=True, separators=(',',':')).encode()
    result['projection_item_bytes'] += len(encoded)
    require(result['projection_item_bytes'] <= OUTPUT_BYTES, 'projection_byte_budget')
    out.append(item)

def json_contexts(body, result, deadline):
    def pairs(xs):
        d = {}
        for k,v in xs:
            require(k not in d, 'original_JSON_duplicate_key')
            d[k] = v
        return d
    def nonfinite(_):
        raise Refused('original_JSON_nonfinite')
    root = json.loads(body, object_pairs_hook=pairs, parse_constant=nonfinite)
    out = []
    todo = [([],root)]
    visited = 0
    while todo:
        keys, value = todo.pop()
        visited += 1
        if visited % 1024 == 0:
            check_time(deadline)
        if isinstance(value,dict):
            for key in value:
                if PATTERN.search(key):
                    context_add(out, {'JSON_field':keys+[key], 'JSON_context_kind':'dictionary_key',
                        'matched_rows':labels(key), 'mechanical_context_category':json_category(keys+[key],key),
                        'value':value_projection(key)}, result, deadline)
            todo.extend((keys+[k],v) for k,v in value.items())
        elif isinstance(value,list):
            todo.extend((keys+[i],v) for i,v in enumerate(value))
        elif isinstance(value,str) and PATTERN.search(value):
            context_add(out, {'JSON_field':keys, 'matched_rows':labels(value),
                'mechanical_context_category':json_category(keys,value),
                'value':value_projection(value)}, result, deadline)
    return out

def call_name(node):
    if isinstance(node,ast.Name):
        return node.id
    if isinstance(node,ast.Attribute):
        return call_name(node.value)+'.'+node.attr
    return type(node).__name__

def source_line(body_lines, line):
    value = body_lines[line-1]
    return {'line':line,'original_line_bytes':len(value.encode()),'original_line_sha256':sha(value.encode()),
            'concrete_code_line':value if len(value.encode())<=MAX_LINE else None,
            'line_exceeded_projection_bound':len(value.encode())>MAX_LINE,
            'matched_path_literals':path_literals(value)}

def python_contexts(text, result, deadline):
    tree = ast.parse(text)
    parents = {child:node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    lines = text.splitlines()
    out = []
    for node in ast.walk(tree):
        check_time(deadline)
        if not isinstance(node,ast.Constant) or not isinstance(node.value,str) or not PATTERN.search(node.value):
            continue
        chain = []
        parent = node
        while parent in parents:
            parent = parents[parent]
            chain.append(parent)
        calls = [p for p in chain if isinstance(p,ast.Call)]
        kw = next((p.arg for p in chain if isinstance(p,ast.keyword)),None)
        assignment = next((p for p in chain if isinstance(p,ast.Assign)),None)
        names = []
        if assignment is not None:
            names = [p.id for target in assignment.targets for p in ast.walk(target) if isinstance(p,ast.Name)]
        callee = call_name(calls[0].func) if calls else None
        if kw == 'cwd':
            category = 'script_runtime_working_directory_candidate'
        elif callee in ('open','os.open') or (callee and callee.endswith(('.read_bytes','.read_text'))):
            category = 'script_runtime_file_dereference_candidate'
        elif callee and callee.endswith(('.insert','.append')) and 'sys.path' in callee:
            category = 'script_runtime_import_search_path_candidate'
        elif callee in ('Path','P'):
            category = 'script_path_construction_not_alone_a_dereference'
        elif callee and any(x in callee for x in ('Popen','subprocess','check_output')):
            category = 'script_execution_argument_candidate'
        else:
            category = 'script_string_literal_reference'
        alias_uses = []
        if names:
            for use in ast.walk(tree):
                if isinstance(use,ast.Name) and isinstance(use.ctx,ast.Load) and use.id in names:
                    ancestor = use
                    while ancestor in parents and not isinstance(ancestor,(ast.Call,ast.keyword)):
                        ancestor = parents[ancestor]
                    alias_uses.append({'name':use.id,'line':use.lineno,'column':use.col_offset,
                        'nearest_call':call_name(ancestor.func) if isinstance(ancestor,ast.Call) else None,
                        'nearest_keyword':ancestor.arg if isinstance(ancestor,ast.keyword) else None})
                    if len(alias_uses)>=MAX_ALIAS_USES:
                        break
        context_add(out, {'AST':'Constant','line':node.lineno,'column':node.col_offset,
            'matched_rows':labels(node.value),'literal':value_projection(node.value),
            'nearest_callee':callee,'keyword':kw,'assigned_name_candidates':names,
            'mechanical_context_category':category,'source_line':source_line(lines,node.lineno),
            'assigned_name_syntactic_uses':alias_uses,
            'alias_uses_are_syntax_only_not_runtime_data_flow_or_queue_proof':True,
            'alias_use_list_reached_bound':len(alias_uses)>=MAX_ALIAS_USES}, result, deadline)
    return out

def line_contexts(text, suffix, result, deadline):
    out = []
    for number,line in enumerate(text.splitlines(),1):
        if not PATTERN.search(line):
            continue
        # .txt may be host/command metadata: do not reproduce unrelated argv,
        # environment, authentication or other private line contents.
        record = {'line':number,'original_line_bytes':len(line.encode()),'original_line_sha256':sha(line.encode()),
            'matched_rows':labels(line),'matched_path_literals':path_literals(line),
            'concrete_source_code_line':line if suffix in ('.py','.sh') and len(line.encode())<=MAX_LINE else None,
            'mechanical_context_category':'source_code_path_mention' if suffix in ('.py','.sh') else 'text_path_mention_only',
            'line_exceeded_projection_bound':len(line.encode())>MAX_LINE}
        context_add(out, record, result, deadline)
    return out

def emit(result):
    b = json.dumps(result, ensure_ascii=True, separators=(',',':')).encode()+b'\n'
    require(len(b)<=OUTPUT_BYTES, 'final_output_budget')
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-sha256',required=True)
    args = parser.parse_args()
    require(re.fullmatch('[0-9a-f]{64}',args.source_sha256) is not None,'parent_source_pin')
    require(sys.platform=='linux' and os.getuid()==UID,'Linux_account')
    require(len(INPUTS)==EXPECTED_FILE_COUNT and sum(p['bytes'] for p in INPUTS)==EXPECTED_INPUT_BYTES,
            'fixed_input_inventory')
    require(len({p['path'] for p in INPUTS})==EXPECTED_FILE_COUNT,'fixed_input_duplicate')
    deadline = time.monotonic()+SECONDS
    result = {'format':'swdb.fixed111.original_RAW_reference_context_query.v1','sealed':False,
        'started_utc':utc(),'finished_utc':None,'query_state':'started','failure':None,
        'parent_supplied_stdin_source_sha256':args.source_sha256,
        'stdin_source_pin_independently_rechecked_by_query':False,
        'source_transport_byte_verification_is_parent_custody':True,
        'input_pack_pin':INPUT_PACK_PIN,'fixed_original_input_bytes':EXPECTED_INPUT_BYTES,
        'limits':{'one_file_bytes':ONE_FILE,'total_body_read_bytes':TOTAL_BYTES,'output_bytes':OUTPUT_BYTES,
                  'seconds':SECONDS,'contexts':MAX_CONTEXTS,'string_value_bytes':MAX_VALUE,
                  'source_line_bytes':MAX_LINE,'syntactic_alias_uses_per_literal':MAX_ALIAS_USES},
        'body_bytes_read':0,'context_count':0,'projection_item_bytes':0,'file_observations':[],
        'selected_control_imports_or_calls':False,'filesystem_writes_or_Git_actions':False,
        'application_outcome_bodies_serialized':False,'scientific_actions_or_admission':False,
        'current_queue_history_classification_clearance_or_global_stability_generated':False}
    code = 0
    try:
        for pin in INPUTS:
            body,before,after = read_original(pin,result,deadline)
            record = {'original_file_pin':pin,'current_stat_before':before,'current_stat_after':after,
                'original_stat_equal_current':pin['original_stat']==before,
                'current_body_bytes':len(body),'current_body_sha256':sha(body),
                'projection':[],'projection_error':None}
            suffix = Path(pin['path']).suffix
            try:
                if suffix=='.json':
                    record['projection']=json_contexts(body,result,deadline)
                elif suffix=='.py':
                    text=body.decode('utf-8')
                    record['projection']=python_contexts(text,result,deadline)
                    record['matching_source_lines']=line_contexts(text,suffix,result,deadline)
                else:
                    record['projection']=line_contexts(body.decode('utf-8'),suffix,result,deadline)
            except (json.JSONDecodeError,UnicodeError,SyntaxError) as exc:
                record['projection_error']={'class':type(exc).__name__,'message_sha256':sha(str(exc).encode())}
            result['file_observations'].append(record)
            del body
        result['query_state']='fixed_file_metadata_query_finished'
    except BaseException as exc:
        code=1
        result['query_state']='stopped_with_partial_metadata'
        result['failure']={'class':type(exc).__name__,
            'code':str(exc) if isinstance(exc,Refused) else None,
            'message_sha256':sha(str(exc).encode())}
    result['finished_utc']=utc()
    try:
        emit(result)
    except Refused:
        # Never print a huge body or raw exception message when the output budget
        # is exceeded. Exact last processed pins remain as small factual metadata.
        compact={k:v for k,v in result.items() if k!='file_observations'}
        compact['query_state']='stopped_output_budget'
        compact['failure']={'class':'Refused','code':'final_output_budget'}
        compact['processed_file_pins']=[r['original_file_pin'] for r in result['file_observations']]
        emit(compact)
        code=1
    return code

if __name__=='__main__':
    sys.exit(main())

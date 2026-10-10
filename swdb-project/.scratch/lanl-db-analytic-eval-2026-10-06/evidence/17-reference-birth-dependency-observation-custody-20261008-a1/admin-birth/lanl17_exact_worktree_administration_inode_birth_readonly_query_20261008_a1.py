"""Fixed read-only Git-worktree administration inode-birth query; NOT RUN.

Only the 18 exact administration routes observed in the genuine checkout-birth
original and their anchors are walked. No checkout rewalk, ordinary file bodies,
Git command, control import, cleanup or process-role admission is performed.
"""
import ctypes
import datetime
import hashlib
import json
import os
import pathlib
import signal
import socket
import stat
import sys
import time

P = pathlib.Path
UID = 114316761
BASE = P('/data1/yanruj')
ADMIN_ROOT = BASE/'ArchEvolve'/'.git'/'worktrees'
ADMIN_ANCHORS = (P('/'), P('/data1'), BASE, BASE/'ArchEvolve',
                 BASE/'ArchEvolve'/'.git', ADMIN_ROOT)
CHECKOUT_BIRTH_ORIGINAL_PIN = {'path': '/private/tmp/lanl17-exact-checkout-inode-birth-query-original-20261008-a1.json', 'bytes': 14762700, 'sha256': 'e228811f4b119a7e0c97b666b7da249374f3637cef8b17c0b10b54c4ff422fb7', 'policy': 'Original UNSEALED genuine checkout-birth observation; no administration target walk there'}
ADMIN_ROUTES = {'ArchEvolve-lanl-allocator-a2-20261006': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-allocator-a2-20261006', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-allocator-a2-20261006', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-allocator-a2-20261006', 'original_pointer_file_pin': {'bytes': 86, 'sha256': '9626ee8cf9d39610c1c866ab9ffe4406b3eb0913c72d700d282b8d628826abe6', 'stat': {'blocks': 8, 'ctime_ns': 1791329486063564771, 'dev': 2097, 'gid': 114316761, 'ino': 60329743, 'mode': 33204, 'mtime_ns': 1791329486063564771, 'nlink': 1, 'size': 86, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[0].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-bulk-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-bulk-services-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-bulk-services-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-bulk-services-20261006-a1', 'original_pointer_file_pin': {'bytes': 90, 'sha256': 'dce4cfb852f67d543b28b923cd081fa6b934e845d11d7a3eb9688b789d60978f', 'stat': {'blocks': 8, 'ctime_ns': 1791335068456470687, 'dev': 2097, 'gid': 114316761, 'ino': 68310817, 'mode': 33204, 'mtime_ns': 1791335068456470687, 'nlink': 1, 'size': 90, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[1].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-bulk-total-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-bulk-total-services-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-bulk-total-services-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-bulk-total-services-20261006-a1', 'original_pointer_file_pin': {'bytes': 96, 'sha256': '0a7fdbf05859ab09efe4d84c7b7a860632a73ea1d4c8524661b84f6f8eda555a', 'stat': {'blocks': 8, 'ctime_ns': 1791337259122407440, 'dev': 2097, 'gid': 114316761, 'ino': 68963140, 'mode': 33204, 'mtime_ns': 1791337259122407440, 'nlink': 1, 'size': 96, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[2].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-clock-a2-20261006': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-clock-a2-20261006', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-clock-a2-20261006', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-clock-a2-20261006', 'original_pointer_file_pin': {'bytes': 82, 'sha256': '042d137a70a2f9f48013c51e9bd9c767306b144033ccb389f23fd0e357183e1a', 'stat': {'blocks': 8, 'ctime_ns': 1791330871700772045, 'dev': 2097, 'gid': 114316761, 'ino': 65051033, 'mode': 33204, 'mtime_ns': 1791330871700772045, 'nlink': 1, 'size': 82, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[3].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-float-memory-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-float-memory-services-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-float-memory-services-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-float-memory-services-20261006-a1', 'original_pointer_file_pin': {'bytes': 98, 'sha256': 'f698a65ae32d74240698fd4f25d8e3fda1c327dae593b28bf886f73fbc8e39a8', 'stat': {'blocks': 8, 'ctime_ns': 1791343636183379319, 'dev': 2097, 'gid': 114316761, 'ino': 69086370, 'mode': 33204, 'mtime_ns': 1791343636183379319, 'nlink': 1, 'size': 98, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[4].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-independent-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-independent-services-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-independent-services-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-independent-services-20261006-a1', 'original_pointer_file_pin': {'bytes': 97, 'sha256': '86a38a2283ec5fb83538b7924302caa07389480379e911a64a47e3708f85723c', 'stat': {'blocks': 8, 'ctime_ns': 1791340352458868143, 'dev': 2097, 'gid': 114316761, 'ino': 69082718, 'mode': 33204, 'mtime_ns': 1791340352458868143, 'nlink': 1, 'size': 97, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[5].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-memory-a1-20261006': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-memory-a1-20261006', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-memory-a1-20261006', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-memory-a1-20261006', 'original_pointer_file_pin': {'bytes': 83, 'sha256': 'ee2ab21ffe5fa99c179c9e108761e74e854d17b998bf1fcd24b99dac5988f530', 'stat': {'blocks': 8, 'ctime_ns': 1791332237198903545, 'dev': 2097, 'gid': 114316761, 'ino': 65575325, 'mode': 33204, 'mtime_ns': 1791332237198903545, 'nlink': 1, 'size': 83, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[6].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-estimation-role-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-estimation-role-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-estimation-role-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a1', 'original_pointer_file_pin': {'bytes': 92, 'sha256': '036c9397b3e41305271e30b6176d771ce4cc415a8a4f4fb7ac5721959ab6c9f1', 'stat': {'blocks': 8, 'ctime_ns': 1791339282290649804, 'dev': 2097, 'gid': 114316761, 'ino': 68977246, 'mode': 33204, 'mtime_ns': 1791339282290649804, 'nlink': 1, 'size': 92, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[7].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-estimation-role-20261006-a2': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-estimation-role-20261006-a2', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-estimation-role-20261006-a2', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a2', 'original_pointer_file_pin': {'bytes': 92, 'sha256': 'b96bd590a8fed55182c127ae9ac197430ccde176f6e1faf2d16a72313e22cabf', 'stat': {'blocks': 8, 'ctime_ns': 1791339676718785921, 'dev': 2097, 'gid': 114316761, 'ino': 69079266, 'mode': 33204, 'mtime_ns': 1791339676718785921, 'nlink': 1, 'size': 92, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[8].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-openmp-projections-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-openmp-projections-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-openmp-projections-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-openmp-projections-20261006-a1', 'original_pointer_file_pin': {'bytes': 95, 'sha256': '4b8b5299e3594358c7c881a163923b2dcbf9dcb504b9c83b8f53ee0e33d721b8', 'stat': {'blocks': 8, 'ctime_ns': 1791334950645236626, 'dev': 2097, 'gid': 114316761, 'ino': 68050305, 'mode': 33204, 'mtime_ns': 1791334950645236626, 'nlink': 1, 'size': 95, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[9].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-native-object-counts-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-native-object-counts-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-native-object-counts-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-native-object-counts-20261006-a1', 'original_pointer_file_pin': {'bytes': 97, 'sha256': 'fd7f7e497d68715834857a0fabbd0eb66b3915fd0508b435c3bce633edb0f9ae', 'stat': {'blocks': 8, 'ctime_ns': 1791333248482400339, 'dev': 2097, 'gid': 114316761, 'ino': 65837473, 'mode': 33204, 'mtime_ns': 1791333248482400339, 'nlink': 1, 'size': 97, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[10].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-count-20261006': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-count-20261006', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-count-20261006', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-count-20261006', 'original_pointer_file_pin': {'bytes': 79, 'sha256': '42946a42590c7d926d9a68a02e14ddb5af65a38b104c5d2d8e5aa4d7436f4bfa', 'stat': {'blocks': 8, 'ctime_ns': 1791321249126756662, 'dev': 2097, 'gid': 114316761, 'ino': 55604671, 'mode': 33204, 'mtime_ns': 1791321249126756662, 'nlink': 1, 'size': 79, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[11].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-estimates-20261006': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-estimates-20261006', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-estimates-20261006', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-estimates-20261006', 'original_pointer_file_pin': {'bytes': 83, 'sha256': '03b6752dfbbc6d52ac7934ab83ddc3634a87bcffaaaa700ae56d9d6af4bb4de6', 'stat': {'blocks': 8, 'ctime_ns': 1791323569112568158, 'dev': 2097, 'gid': 114316761, 'ino': 55612891, 'mode': 33204, 'mtime_ns': 1791323569112568158, 'nlink': 1, 'size': 83, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[12].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-functional-evaluation-20261006-a1': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-functional-evaluation-20261006-a1', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-functional-evaluation-20261006-a1', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-functional-evaluation-20261006-a1', 'original_pointer_file_pin': {'bytes': 98, 'sha256': '11f978a737741abbcbb274dab110675de0cd9cccd5acf547fa6b786a42ad558a', 'stat': {'blocks': 8, 'ctime_ns': 1791339153999304072, 'dev': 2097, 'gid': 114316761, 'ino': 68970244, 'mode': 33204, 'mtime_ns': 1791339153999304072, 'nlink': 1, 'size': 98, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[13].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-functional-object-counts-20261006-a2': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-functional-object-counts-20261006-a2', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-functional-object-counts-20261006-a2', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-functional-object-counts-20261006-a2', 'original_pointer_file_pin': {'bytes': 101, 'sha256': '4860a184553942d28d82cc1cb26976aea1f5f7a1efb786da189b535ed5d7ee8a', 'stat': {'blocks': 8, 'ctime_ns': 1791334275696169885, 'dev': 2097, 'gid': 114316761, 'ino': 66230689, 'mode': 33204, 'mtime_ns': 1791334275696169885, 'nlink': 1, 'size': 101, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[14].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-functional-strict-20261006': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-functional-strict-20261006', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-functional-strict-20261006', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-functional-strict-20261006', 'original_pointer_file_pin': {'bytes': 91, 'sha256': 'c38a6c034aaddbb0cd92daa53a703cadb5fa04d50500e00d78dcf2bfd0069c86', 'stat': {'blocks': 8, 'ctime_ns': 1791328845014042935, 'dev': 2097, 'gid': 114316761, 'ino': 57315654, 'mode': 33204, 'mtime_ns': 1791328845014042935, 'nlink': 1, 'size': 91, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[15].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-prospective-inputs-20261006-a2': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-prospective-inputs-20261006-a2', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-prospective-inputs-20261006-a2', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-prospective-inputs-20261006-a2', 'original_pointer_file_pin': {'bytes': 95, 'sha256': 'ce8de2e398c4fc1d92fac357a05402aa4bd1df2a6cd076d537d70aa5386b16ab', 'stat': {'blocks': 8, 'ctime_ns': 1791335164388474942, 'dev': 2097, 'gid': 114316761, 'ino': 68562737, 'mode': 33204, 'mtime_ns': 1791335164388474942, 'nlink': 1, 'size': 95, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[16].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}, 'ArchEvolve-lanl-root-projection-20261006': {'path': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-root-projection-20261006', 'original_pointer_route': '/data1/yanruj/ArchEvolve/.git/worktrees/ArchEvolve-lanl-root-projection-20261006', 'original_checkout_path': '/data1/yanruj/ArchEvolve-lanl-root-projection-20261006', 'original_pointer_file_pin': {'bytes': 89, 'sha256': 'f0dc8a10be2e4327bfdd928921e6b24245f8691f60086e35a61b240428c2e482', 'stat': {'blocks': 8, 'ctime_ns': 1791329404082729875, 'dev': 2097, 'gid': 114316761, 'ino': 59019139, 'mode': 33204, 'mtime_ns': 1791329404082729875, 'nlink': 1, 'size': 89, 'uid': 114316761}}, 'original_birth_receipt_jsonpath': '$.rows[17].git_indirection', 'original_target_birth_unwalked_in_checkout_query': True}}
CHILD = 1654291
PARENT = 1654279
START = 559081545
PSTART = 559081538
MOUNT = '/run/user/114316761/doc'
G5_SOURCE_SHA256 = 'a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb'
PUBLIC_ORIGINAL_SHA256 = '1ea76b7519827bae6f81902c2bebd6b16e22c303fcada24257bf1bab73174489'
CHILD_CMD_PIN = (100, '65b3170da324600f477de2acde6ae5f47d348a3a72e74d4b47d2612ec19f9999')
PARENT_CMD_PIN = (33, '407a0c7b9049543c6ad5bf73e3e7fbf431fec8908926f894aed0aa6e2d75903f')
ROWS = {'ArchEvolve-lanl-allocator-a2-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-allocator-a2-20261006', 'head': 'b9dabf361b429f0c07717f1891573f5d5f31b1ab', 'historical_allocated_bytes': 177709056, 'receipts': ['R1', 'R2']}, 'ArchEvolve-lanl-bulk-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-bulk-services-20261006-a1', 'head': 'aaf9a9d24a3b2f18af9a7ad8c445025fea366162', 'historical_allocated_bytes': 249249792, 'receipts': ['R3', 'R4']}, 'ArchEvolve-lanl-bulk-total-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-bulk-total-services-20261006-a1', 'head': '1703c98717ff303fdaa83b8044ac9b4060fedb78', 'historical_allocated_bytes': 275345408, 'receipts': ['R5']}, 'ArchEvolve-lanl-clock-a2-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-clock-a2-20261006', 'head': '05e1b7b05220c06fa1bea39af8881fdda38f818f', 'historical_allocated_bytes': 178987008, 'receipts': ['R6']}, 'ArchEvolve-lanl-float-memory-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-float-memory-services-20261006-a1', 'head': '3006d91e2d076db0104f3b7734131dec5f26caad', 'historical_allocated_bytes': 276357120, 'receipts': ['R7']}, 'ArchEvolve-lanl-independent-services-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-independent-services-20261006-a1', 'head': '1703c98717ff303fdaa83b8044ac9b4060fedb78', 'historical_allocated_bytes': 275345408, 'receipts': ['R8', 'R9']}, 'ArchEvolve-lanl-memory-a1-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-memory-a1-20261006', 'head': '8e54d74e64c08a29b20eec183b070f3e77a77e43', 'historical_allocated_bytes': 179073024, 'receipts': ['R10']}, 'ArchEvolve-lanl-estimation-role-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a1', 'head': 'a7a9b9e8b9d52245490b7dfd372f3be05f67ce27', 'historical_allocated_bytes': 179896320, 'receipts': ['R11']}, 'ArchEvolve-lanl-estimation-role-20261006-a2': {'path': '/data1/yanruj/ArchEvolve-lanl-estimation-role-20261006-a2', 'head': 'a7a9b9e8b9d52245490b7dfd372f3be05f67ce27', 'historical_allocated_bytes': 179896320, 'receipts': ['R12', 'R13']}, 'ArchEvolve-lanl-openmp-projections-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-openmp-projections-20261006-a1', 'head': '8949e10fc228bc1009de19fa9df6c9e1a61808ef', 'historical_allocated_bytes': 152952832, 'receipts': ['R14']}, 'ArchEvolve-lanl-native-object-counts-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-native-object-counts-20261006-a1', 'head': '502fea76159cb7b4c692291ee779dd0235b20c8b', 'historical_allocated_bytes': 153907200, 'receipts': ['R15']}, 'ArchEvolve-lanl-count-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-count-20261006', 'head': 'cda8f2db11996402bcb483bf98440eedc07feaa7', 'historical_allocated_bytes': 113459200, 'receipts': ['O1']}, 'ArchEvolve-lanl-estimates-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-estimates-20261006', 'head': 'b5acc909ef9df813352004e88633fac4db4b55e7', 'historical_allocated_bytes': 136187904, 'receipts': ['O2']}, 'ArchEvolve-lanl-functional-evaluation-20261006-a1': {'path': '/data1/yanruj/ArchEvolve-lanl-functional-evaluation-20261006-a1', 'head': 'bef54f9661d099dcf381538522bd4d9573d6fe0c', 'historical_allocated_bytes': 179683328, 'receipts': ['O3']}, 'ArchEvolve-lanl-functional-object-counts-20261006-a2': {'path': '/data1/yanruj/ArchEvolve-lanl-functional-object-counts-20261006-a2', 'head': '9ba9277b2b7cfed25569b4fa73aa683679a588e0', 'historical_allocated_bytes': 153993216, 'receipts': ['O4']}, 'ArchEvolve-lanl-functional-strict-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-functional-strict-20261006', 'head': 'dcb66fc4b9564dc742b310e036e6ee5495330df8', 'historical_allocated_bytes': 152883200, 'receipts': ['O5']}, 'ArchEvolve-lanl-prospective-inputs-20261006-a2': {'path': '/data1/yanruj/ArchEvolve-lanl-prospective-inputs-20261006-a2', 'head': 'c9be522053dffcd8e3308a7c723e2468b942e2a1', 'historical_allocated_bytes': 153923584, 'receipts': ['O6']}, 'ArchEvolve-lanl-root-projection-20261006': {'path': '/data1/yanruj/ArchEvolve-lanl-root-projection-20261006', 'head': '30f425b5275765c7ccdb5115ab8bb00f8b5f5e98', 'historical_allocated_bytes': 152977408, 'receipts': ['O7']}}
LIMITS = {'seconds': 600, 'work_seconds': 570, 'file_bytes_total': 8*1024*1024,
          'proc_file': 1024*1024, 'status': 32768, 'proc_stat': 16384,
          'cmdline': 4096, 'git_pointer': 4096, 'entries_total': 400000,
          'names_per_directory': 20000, 'directory_name_bytes': 64*1024*1024,
          'depth': 64, 'path_bytes': 4096,
          'failure_witnesses_total': 100000, 'object_metadata_bytes': 28*1024*1024,
          'failure_metadata_bytes': 2*1024*1024, 'output_bytes': 32*1024*1024}
OBJECT_ENCODING = {
    'format': 'ordered-array.v1',
    'object_fields': ['relative_path', 'original_stat', 'original_statx',
                      'directory_names_count_or_null', 'directory_names_digest_or_null',
                      'type_code'],
    'original_stat_fields': ['dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size',
                            'blocks', 'mtime_ns', 'ctime_ns'],
    'original_statx_fields': ['returned_mask', 'requested_mask', 'attributes',
                             'attributes_mask', 'mount_id_or_null',
                             'birth_supported', 'birth_seconds', 'birth_nanoseconds'],
    'type_codes': {'directory': 0, 'regular': 1, 'symlink_not_followed': 2,
                   'other_not_opened_for_body': 3},
    'first_pass_failure_fields': ['original_objects_index', 'concern_codes'],
    'concern_codes': {'birth_not_supported': 0, 'birth_nonpositive': 1,
        'birth_not_after_reported_helper_start': 2,
        'birth_within_boot_epoch_and_tick_resolution_margin': 3,
        'symlink_not_followed': 4, 'other_not_opened_for_body': 5,
        'regular_hardlink_aliases_not_enumerated': 6, 'inode_on_portal_mount_device': 7},
    'failure_originals_rule': 'index references the full retained row.original_objects array; the exact path/stat/statx birth are present there, not a digest-only witness',
    'absolute_path_rule': 'row.path + slash + relative_path; dot denotes row.path',
    'birth_class_rule': 'classify_birth uses the exact retained mask/sec/nsec and clock',
    'atime_excluded_because_read_only_queries_can_change_it': True,
    'metadata_digest': 'sha256 of each canonical encoded object, prefixed by 8-byte big-endian byte length, in byte-sorted depth-first order',
}

AT_EMPTY_PATH = 0x1000
AT_SYMLINK_NOFOLLOW = 0x100
STATX_BASIC_STATS = 0x7ff
STATX_BTIME = 0x800
STATX_MNT_ID = 0x1000
STATX_REQUIRED_BASIC = STATX_BASIC_STATS & ~0x20  # atime deliberately unbound

class Refused(Exception):
    pass

class LimitReached(Refused):
    pass

class StatxTimestamp(ctypes.Structure):
    _fields_ = [('tv_sec', ctypes.c_int64), ('tv_nsec', ctypes.c_uint32),
                ('reserved', ctypes.c_int32)]

class Statx(ctypes.Structure):
    # Linux v6.8 UAPI include/uapi/linux/stat.h, exact 0x100-byte ABI.
    _fields_ = [('mask', ctypes.c_uint32), ('blksize', ctypes.c_uint32),
                ('attributes', ctypes.c_uint64), ('nlink', ctypes.c_uint32),
                ('uid', ctypes.c_uint32), ('gid', ctypes.c_uint32),
                ('mode', ctypes.c_uint16), ('spare0', ctypes.c_uint16),
                ('ino', ctypes.c_uint64), ('size', ctypes.c_uint64),
                ('blocks', ctypes.c_uint64), ('attributes_mask', ctypes.c_uint64),
                ('atime', StatxTimestamp), ('btime', StatxTimestamp),
                ('ctime', StatxTimestamp), ('mtime', StatxTimestamp),
                ('rdev_major', ctypes.c_uint32), ('rdev_minor', ctypes.c_uint32),
                ('dev_major', ctypes.c_uint32), ('dev_minor', ctypes.c_uint32),
                ('mnt_id', ctypes.c_uint64), ('dio_mem_align', ctypes.c_uint32),
                ('dio_offset_align', ctypes.c_uint32),
                ('spare3', ctypes.c_uint64*12)]

def require(ok, code):
    if not ok:
        raise Refused(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()

def stamp(s):
    return {k: getattr(s, 'st_'+k) for k in
            ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'blocks',
             'mtime_ns', 'ctime_ns')}

class Query:
    def __init__(self):
        self.started = time.monotonic()
        self.bytes_read = 0
        self.entries = 0
        self.statx_calls = 0
        self.directory_name_bytes = 0
        self.failure_witnesses = 0
        self.object_metadata_bytes = 0
        self.failure_metadata_bytes = 0
        self.statx_fn = None

    def tick(self):
        if time.monotonic()-self.started >= LIMITS['work_seconds']:
            raise LimitReached('elapsed_work_limit')

    def entry(self):
        self.tick()
        self.entries += 1
        if self.entries > LIMITS['entries_total']:
            raise LimitReached('metadata_entry_limit')

    def witness(self, rows, value):
        self.failure_witnesses += 1
        if self.failure_witnesses > LIMITS['failure_witnesses_total']:
            raise LimitReached('failure_witness_limit')
        self.failure_metadata_bytes += len(canonical(value))+1
        if self.failure_metadata_bytes > LIMITS['failure_metadata_bytes']:
            raise LimitReached('failure_metadata_bytes_limit')
        rows.append(value)

    def read(self, path, cap):
        self.tick()
        require(cap <= LIMITS['proc_file'], 'individual_read_cap')
        remaining = LIMITS['file_bytes_total']-self.bytes_read
        if remaining < cap+1:
            raise LimitReached('cumulative_read_remaining')
        fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            before = stamp(os.fstat(fd))
            with os.fdopen(fd, 'rb', closefd=False) as f:
                raw = f.read(cap+1)
            self.bytes_read += len(raw)
            require(len(raw) <= cap, 'file_read_limit')
            require(before == stamp(os.fstat(fd)) == stamp(os.lstat(path)),
                    'read_identity_changed')
            return raw, before
        finally:
            os.close(fd)

    def install_statx(self):
        # No fallback birth from mtime/ctime or legacy stat emulation is accepted.
        require(ctypes.sizeof(StatxTimestamp) == 16 and ctypes.sizeof(Statx) == 256,
                'statx_abi_size')
        for field, offset in (('nlink', 0x10), ('ino', 0x20), ('atime', 0x40),
                              ('btime', 0x50), ('rdev_major', 0x80),
                              ('mnt_id', 0x90), ('spare3', 0xa0)):
            require(getattr(Statx, field).offset == offset, 'statx_abi_offset')
        self.libc = ctypes.CDLL(None, use_errno=True)
        self.statx_fn = self.libc.statx
        self.statx_fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                 ctypes.c_uint, ctypes.POINTER(Statx)]
        self.statx_fn.restype = ctypes.c_int

    def inode(self, fd):
        self.tick()
        s0 = stamp(os.fstat(fd))
        x = Statx()
        self.statx_calls += 1
        rc = self.statx_fn(fd, b'', AT_EMPTY_PATH|AT_SYMLINK_NOFOLLOW,
                           STATX_BASIC_STATS|STATX_BTIME|STATX_MNT_ID,
                           ctypes.byref(x))
        if rc != 0:
            raise OSError(ctypes.get_errno(), 'statx_failed')
        require(s0 == stamp(os.fstat(fd)), 'inode_changed_during_statx')
        require(x.mask & STATX_REQUIRED_BASIC == STATX_REQUIRED_BASIC,
                'statx_basic_fields_missing')
        require((x.dev_major, x.dev_minor) == (os.major(s0['dev']), os.minor(s0['dev']))
                and (x.ino, x.mode, x.uid, x.gid, x.nlink, x.size, x.blocks) ==
                tuple(s0[k] for k in ('ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'blocks')),
                'statx_fstat_mismatch')
        require(0 <= x.mtime.tv_nsec < 1000000000 and
                0 <= x.ctime.tv_nsec < 1000000000 and
                x.mtime.tv_sec*1000000000+x.mtime.tv_nsec == s0['mtime_ns'] and
                x.ctime.tv_sec*1000000000+x.ctime.tv_nsec == s0['ctime_ns'],
                'statx_time_fstat_mismatch')
        b = {'supported': bool(x.mask & STATX_BTIME),
             'seconds': x.btime.tv_sec, 'nanoseconds': x.btime.tv_nsec}
        require(not b['supported'] or 0 <= b['nanoseconds'] < 1000000000,
                'invalid_statx_birth_nsec')
        return {'stat': s0, 'statx': {'returned_mask': x.mask,
                'requested_mask': STATX_BASIC_STATS|STATX_BTIME|STATX_MNT_ID,
                'attributes': x.attributes, 'attributes_mask': x.attributes_mask,
                'mount_id': x.mnt_id if x.mask & STATX_MNT_ID else None,
                'birth': b}}

def public(q, pid):
    root = P('/proc')/str(pid)
    a, _ = q.read(root/'stat', LIMITS['proc_stat'])
    b, _ = q.read(root/'status', LIMITS['status'])
    final, _ = q.read(root/'stat', LIMITS['proc_stat'])
    def parse_stat(raw):
        tail = raw[raw.rfind(b')')+2:].split()
        require(len(tail) >= 20 and int(raw.split(b' ', 1)[0]) == pid,
                'public_stat_shape')
        return {'state': tail[0].decode('ascii'), 'ppid': int(tail[1]),
                'start_ticks': int(tail[19])}
    sa, sz = parse_stat(a), parse_stat(final)
    require(sa == sz, 'public_stat_interval_changed')
    fields = {line.split(':', 1)[0]: line.split(':', 1)[1].strip()
              for line in b.decode('ascii').splitlines() if ':' in line}
    require(fields['State'].split()[0] == sa['state'] and
            int(fields['PPid']) == sa['ppid'] and int(fields['Pid']) == pid,
            'public_status_stat_mismatch')
    return {'pid': pid, **sa, 'name': fields['Name'],
            'uids': list(map(int, fields['Uid'].split())),
            'gids': list(map(int, fields['Gid'].split())),
            'threads': int(fields['Threads']),
            'capability_hex': {k: fields[k] for k in
                               ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')},
            'stat_before_sha256': sha(a), 'stat_after_sha256': sha(final),
            'status_sha256': sha(b)}

def boot(q):
    raw, _ = q.read('/proc/stat', LIMITS['proc_file'])
    rows = [line.split() for line in raw.splitlines() if line.startswith(b'btime ')]
    require(len(rows) == 1 and len(rows[0]) == 2, 'boot_epoch_shape')
    epoch = int(rows[0][1])
    hz = os.sysconf('SC_CLK_TCK')
    require(epoch > 0 and isinstance(hz, int) and hz > 0, 'boot_clock_invalid')
    return {'boot_epoch_seconds': epoch, 'clock_ticks_per_second': hz,
            'proc_stat_sha256': sha(raw), 'proc_stat_bytes': len(raw)}

def mount(q):
    raw, _ = q.read(P('/proc')/str(PARENT)/'mountinfo', LIMITS['proc_file'])
    rows = []
    for line in raw.decode('ascii').splitlines():
        left, right = line.split(' - ', 1)
        a, b = left.split(), right.split()
        if a[4] == MOUNT:
            rows.append({'mount_id': int(a[0]), 'parent_mount_id': int(a[1]),
                         'device': a[2], 'root': a[3], 'mount_point': a[4],
                         'mount_options': a[5], 'optional_fields': a[6:],
                         'filesystem': b[0], 'source': b[1], 'super_options': b[2]})
    require(len(rows) == 1, 'exact_portal_mount_missing_or_ambiguous')
    r = rows[0]
    require(r['device'] == '0:48' and r['root'] == '/' and
            r['filesystem'] == 'fuse.portal' and r['source'] == 'portal' and
            f'user_id={UID}' in r['super_options'].split(',') and
            f'group_id={UID}' in r['super_options'].split(','), 'portal_mount_role_changed')
    return {'exact_route': r, 'whole_mountinfo_sha256': sha(raw),
            'whole_mountinfo_bytes': len(raw),
            'other_mount_rows_not_serialized': True}

def identity(q):
    c, p = public(q, CHILD), public(q, PARENT)
    require(c['start_ticks'] == START and c['ppid'] == PARENT and
            c['uids'] == [UID, 0, 0, 0] and c['name'] == 'fusermount3' and
            c['threads'] == 1 and c['state'] not in ('Z', 'X', 'x'), 'child_role_identity')
    require(p['start_ticks'] == PSTART and p['uids'] == [UID]*4 and
            p['name'] == 'xdg-document-po' and p['state'] not in ('Z', 'X', 'x'),
            'parent_role_identity')
    pins = {}
    for pid, expected in ((CHILD, CHILD_CMD_PIN), (PARENT, PARENT_CMD_PIN)):
        raw, _ = q.read(P('/proc')/str(pid)/'cmdline', LIMITS['cmdline'])
        require((len(raw), sha(raw)) == expected, 'fixed_public_cmdline_changed')
        pins[str(pid)] = {'bytes': len(raw), 'sha256': sha(raw)}
    # No protected child cwd/root/exe/fd/maps/syscall/wchan read is attempted.
    target = os.readlink(P('/proc')/str(PARENT)/'exe')
    require(target == '/usr/libexec/xdg-document-portal', 'parent_exe_route_changed')
    q.bytes_read += len(os.fsencode(target))
    require(q.bytes_read <= LIMITS['file_bytes_total'], 'parent_exe_link_read_bytes')
    route = mount(q)
    namespace_links = {}
    for who, path in (('query', P('/proc/self/ns/mnt')),
                      ('parent', P('/proc')/str(PARENT)/'ns/mnt')):
        link = os.readlink(path)
        require(link.startswith('mnt:[') and link.endswith(']') and
                len(os.fsencode(link)) <= 256, 'public_mount_namespace_link_shape')
        q.bytes_read += len(os.fsencode(link))
        require(q.bytes_read <= LIMITS['file_bytes_total'], 'public_link_cumulative_bytes')
        namespace_links[who] = link
    final_c, final_p = public(q, CHILD), public(q, PARENT)
    for original, final in ((c, final_c), (p, final_p)):
        require(all(original[k] == final[k] for k in
                ('pid', 'start_ticks', 'ppid', 'name', 'uids', 'gids', 'threads', 'capability_hex')),
                'identity_changed_after_command_and_mount_reads')
    return {'child': c, 'parent': p, 'public_identity_final_anchors':
            {'child': final_c, 'parent': final_p}, 'command_file_pins_only': pins,
            'parent_exe_route': target, 'portal_mount': route,
            'public_mount_namespace_links': namespace_links,
            'query_and_parent_mount_namespace_equal': namespace_links['query'] == namespace_links['parent'],
            'protected_child_fields': {k: 'UNOBSERVED' for k in
                ('cwd', 'root', 'exe', 'fd', 'maps', 'syscall', 'wait_channel')},
            'parent_references_remain_ordinary_checked_elsewhere': True}

def identity_key(value):
    return {who: {key: value[who][key] for key in
            ('pid', 'start_ticks', 'ppid', 'name', 'uids', 'gids', 'threads', 'capability_hex')}
            for who in ('child', 'parent')} | {
            'commands': value['command_file_pins_only'],
            'parent_exe_route': value['parent_exe_route'],
            'mount': value['portal_mount']['exact_route'],
            'mount_namespace_links': value['public_mount_namespace_links']}

def names(q, fd):
    q.tick()
    result = []
    os.lseek(fd, 0, os.SEEK_SET)  # Reset only this read-only descriptor's directory cursor.
    with os.scandir(fd) as it:
        for entry in it:
            q.tick()
            name = entry.name
            require(name not in ('.', '..') and '/' not in name and '\x00' not in name,
                    'directory_name_shape')
            q.directory_name_bytes += len(os.fsencode(name))+1
            if q.directory_name_bytes > LIMITS['directory_name_bytes']:
                raise LimitReached('directory_name_bytes_limit')
            result.append(name)
            if len(result) > LIMITS['names_per_directory']:
                raise LimitReached('directory_name_limit')
    return sorted(result, key=os.fsencode)

def open_directory_chain(path):
    require(path.is_absolute() and '..' not in path.parts, 'fixed_directory_path')
    fd = os.open('/', os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    anchors = [('/', stamp(os.fstat(fd)))]
    try:
        current = P('/')
        for part in path.parts[1:]:
            before = os.stat(part, dir_fd=fd, follow_symlinks=False)
            require(stat.S_ISDIR(before.st_mode), 'directory_chain_type')
            new = os.open(part, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,
                          dir_fd=fd)
            require(stamp(before) == stamp(os.fstat(new)) ==
                    stamp(os.stat(part, dir_fd=fd, follow_symlinks=False)),
                    'directory_chain_changed')
            os.close(fd)
            fd = new
            current /= part
            anchors.append((str(current), stamp(before)))
        return fd, anchors
    except BaseException:
        os.close(fd)
        raise

def check_chain(path, anchors):
    fd, after = open_directory_chain(path)
    try:
        require(after == anchors, 'directory_ancestors_changed')
    finally:
        os.close(fd)

def type_name(mode):
    if stat.S_ISDIR(mode): return 'directory'
    if stat.S_ISREG(mode): return 'regular'
    if stat.S_ISLNK(mode): return 'symlink_not_followed'
    return 'other_not_opened_for_body'

def classify_birth(item, clock):
    b = item['statx']['birth']
    if not b['supported']: return 'birth_not_supported'
    ns = b['seconds']*1000000000+b['nanoseconds']
    if ns <= 0: return 'birth_nonpositive'
    # Exact rational comparison; integer btime boot epoch has only 1s resolution.
    hz = clock['clock_ticks_per_second']
    start_numerator = (clock['boot_epoch_seconds']*hz+START)*1000000000
    if ns*hz <= start_numerator: return 'birth_not_after_reported_helper_start'
    if ns*hz <= start_numerator+(hz+1)*1000000000:
        return 'birth_within_boot_epoch_and_tick_resolution_margin'
    return 'birth_after_reported_start_plus_resolution_margin'


def encode_object(item):
    x = item['statx']
    b = x['birth']
    return [item['relative_path'],
            [item['stat'][key] for key in OBJECT_ENCODING['original_stat_fields']],
            [x['returned_mask'], x['requested_mask'], x['attributes'],
             x['attributes_mask'], x['mount_id'], b['supported'],
             b['seconds'], b['nanoseconds']],
            item.get('directory_names_count'), item.get('directory_names_bytes_digest'),
            OBJECT_ENCODING['type_codes'][item['type']]]

def query_anchors(q):
    observed = []
    for path in ADMIN_ANCHORS:
        q.tick()
        fd, chain = open_directory_chain(path)
        try:
            item = q.inode(fd)
            require(stat.S_ISDIR(item['stat']['mode']), 'anchor_not_real_directory')
            expected_uid = UID if path == BASE or BASE in path.parents else 0
            require(item['stat']['uid'] == expected_uid and item['stat']['nlink'] > 0,
                    'anchor_owner_or_unlinked')
            if path == BASE:
                require(stat.S_IMODE(item['stat']['mode']) == 0o700, 'base_privacy')
            require(item['stat'] == chain[-1][1], 'anchor_chain_statx_identity')
            check_chain(path, chain)
            observed.append({'path': str(path), 'original_inode_metadata': item,
                             'not_a_removed_administration_object': True})
        finally:
            os.close(fd)
    return observed

def query_row(q, name, definition, clock, portal_device):
    root = P(definition['path'])
    require(root == ADMIN_ROOT/name and definition == ADMIN_ROUTES[name],
            'exact_original_administration_route')
    result = {'row': name, 'path': str(root), 'g5_definition': ROWS[name],
              'original_pointer_route': definition['original_pointer_route'],
              'fixed_administration_definition': definition,
              'historical_g5_head_and_allocation_not_revalidated': True,
              'counts': {}, 'observed_device_counts': {}, 'birth_class_counts': {},
              'minimum_positive_birth': None,
              'failure_witnesses': [],
              'original_objects': [], 'last_attempted_object': None,
              'first_pass_completed': False, 'second_pass_completed': False,
              'metadata_equal_between_passes': False,
              'not_a_cleanup_or_process_reference_clearance': True}
    first = {}
    second_seen = set()
    first_hash = hashlib.sha256()
    second_hash = hashlib.sha256()
    def observe(parent_fd, leaf, rel, depth, phase):
        q.entry()
        require(depth <= LIMITS['depth'] and len(os.fsencode(str(root/rel))) <=
                LIMITS['path_bytes'], 'walk_path_or_depth_limit')
        result['last_attempted_object'] = {'path': str(root/rel), 'phase': phase}
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        result['last_attempted_object']['original_lstat_before'] = stamp(before)
        directory = stat.S_ISDIR(before.st_mode)
        require(rel != '.' or directory, 'candidate_root_not_real_directory')
        flags = (os.O_RDONLY|os.O_DIRECTORY if directory else os.O_PATH)
        fd = os.open(leaf, flags|os.O_NOFOLLOW|os.O_CLOEXEC, dir_fd=parent_fd)
        try:
            require(stamp(before) == stamp(os.fstat(fd)), 'entry_replaced_before_statx')
            item = q.inode(fd)
            result['last_attempted_object']['original_statx_metadata'] = item
            require(item['stat'] == stamp(os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)),
                    'entry_replaced_after_statx')
            require(item['stat']['uid'] == UID and item['stat']['nlink'] > 0,
                    'entry_owner_or_unlinked')
            item['type'] = type_name(item['stat']['mode'])
            item['relative_path'] = rel
            item['birth_class'] = classify_birth(item, clock)
            listing = names(q, fd) if directory else None
            if listing is not None:
                item['directory_names_bytes_digest'] = sha(b'\x00'.join(os.fsencode(v) for v in listing))
                item['directory_names_count'] = len(listing)
            key = canonical(encode_object(item))
            if phase == 1:
                require(rel not in first, 'duplicate_walk_route')
                encoded = encode_object(item)
                q.object_metadata_bytes += len(canonical(encoded))+1
                if q.object_metadata_bytes > LIMITS['object_metadata_bytes']:
                    raise LimitReached('object_metadata_bytes_limit')
                first[rel] = item
                result['original_objects'].append(encoded)
                first_hash.update(len(key).to_bytes(8, 'big')+key)
                result['counts'][item['type']] = result['counts'].get(item['type'], 0)+1
                device = f"{os.major(item['stat']['dev'])}:{os.minor(item['stat']['dev'])}"
                result['observed_device_counts'][device] = result['observed_device_counts'].get(device, 0)+1
                kind = item['birth_class']
                result['birth_class_counts'][kind] = result['birth_class_counts'].get(kind, 0)+1
                b = item['statx']['birth']
                if b['supported'] and b['seconds']*1000000000+b['nanoseconds'] > 0:
                    old = result['minimum_positive_birth']
                    if old is None or (b['seconds'], b['nanoseconds']) < \
                            (old['statx']['birth']['seconds'], old['statx']['birth']['nanoseconds']):
                        result['minimum_positive_birth'] = item
                concerns = []
                if kind != 'birth_after_reported_start_plus_resolution_margin': concerns.append(kind)
                if item['type'] not in ('directory', 'regular'): concerns.append(item['type'])
                if item['type'] == 'regular' and item['stat']['nlink'] != 1:
                    concerns.append('regular_hardlink_aliases_not_enumerated')
                if f"{os.major(item['stat']['dev'])}:{os.minor(item['stat']['dev'])}" == portal_device:
                    concerns.append('inode_on_portal_mount_device')
                if concerns:
                    q.witness(result['failure_witnesses'], [len(result['original_objects'])-1,
                              [OBJECT_ENCODING['concern_codes'][code] for code in concerns]])
            else:
                second_seen.add(rel)
                second_hash.update(len(key).to_bytes(8, 'big')+key)
                if first.get(rel) != item:
                    q.witness(result['failure_witnesses'], {'path': str(root/rel),
                              'concerns': ['metadata_changed_or_new_between_passes'],
                              'first_original_inode_metadata': first.get(rel),
                              'second_original_inode_metadata': item})
            if directory:
                for child in listing:
                    observe(fd, child, child if rel == '.' else rel+'/'+child, depth+1, phase)
                require(names(q, fd) == listing and q.inode(fd) ==
                        {k: item[k] for k in ('stat', 'statx')}, 'directory_changed_during_children')
            require(stamp(os.fstat(fd)) == item['stat'] ==
                    stamp(os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)),
                    'entry_changed_before_close')
        finally:
            os.close(fd)
    base_fd = None
    try:
        base_fd, anchors = open_directory_chain(ADMIN_ROOT)
        bs = next(st for path, st in anchors if path == str(BASE))
        require(bs['uid'] == UID and stat.S_IMODE(bs['mode']) == 0o700, 'base_privacy')
        require(os.fstat(base_fd).st_uid == UID, 'administration_parent_owner')
        result['administration_directory_anchors_before'] = anchors
        observe(base_fd, name, '.', 0, 1)
        result['first_pass_completed'] = True
        check_chain(ADMIN_ROOT, anchors)
        observe(base_fd, name, '.', 0, 2)
        result['second_pass_completed'] = True
        for rel in sorted(set(first)-second_seen, key=os.fsencode):
            q.witness(result['failure_witnesses'], {'path': str(root/rel),
                      'concerns': ['missing_in_second_pass'],
                      'first_original_inode_metadata': first[rel]})
        check_chain(ADMIN_ROOT, anchors)
        result['canonical_nonsymlink_root_route'] = str(root)
        result['root_original_statx_metadata'] = first['.']
        result['metadata_equal_between_passes'] = (first_hash.digest() == second_hash.digest()
                                                   and set(first) == second_seen)
    except Exception as exc:
        result['error'] = {'type': type(exc).__name__,
                           'code': str(exc) if isinstance(exc, Refused) else None,
                           'errno': exc.errno if isinstance(exc, OSError) else None}
        if isinstance(exc, LimitReached):
            result['query_limit_reached'] = True
    finally:
        if base_fd is not None: os.close(base_fd)
        result['first_metadata_sha256'] = first_hash.hexdigest()
        result['second_metadata_sha256'] = second_hash.hexdigest()
        result['first_objects_observed'] = len(first)
        result['second_objects_observed'] = len(second_seen)
    return result

def main():
    q = Query()
    output = {'format': 'swdb.exact-portal-helper-worktree-administration-inode-birth-query.v1',
              'sealed': False, 'source_preparation_runtime_inputs_fixed': True,
              'g5_source_sha256': G5_SOURCE_SHA256,
              'prior_public_identity_file_sha256': PUBLIC_ORIGINAL_SHA256,
              'genuine_prior_checkout_birth_original_pin': CHECKOUT_BIRTH_ORIGINAL_PIN,
              'fixed_administration_parent': str(ADMIN_ROOT),
              'limits': LIMITS, 'object_encoding': OBJECT_ENCODING, 'rows': [],
              'ordinary_file_bodies_read': False,
              'symlink_targets_not_traversed': True,
              'checkout_objects_rewalked': False,
              'shared_git_objects_refs_and_other_administration_rows_not_traversed': True,
              'new_root_birth_alone_is_not_inherited_handle_evidence': True,
              'parent_consumer_exclusion': False, 'helper_role_exclusion': False,
              'cleanup_capacity_or_scientific_admission': False}
    old_alarm = None
    try:
        require(sys.platform == 'linux' and os.uname().machine == 'x86_64' and
                socket.gethostname().split('.')[0] == 'mbit10' and
                os.getuid() == os.geteuid() == UID and UID != 0 and
                sys.dont_write_bytecode and not sys.flags.optimize, 'native_execution_context')
        require(len(ROWS) == len(ADMIN_ROUTES) == 18 and set(ROWS) == set(ADMIN_ROUTES),
                'exact_eighteen_original_administration_routes')
        def expired(signum, frame): raise LimitReached('elapsed_alarm')
        old_alarm = signal.signal(signal.SIGALRM, expired)
        signal.alarm(LIMITS['seconds'])
        q.install_statx()
        output['clock_before'] = boot(q)
        output['public_identity_before'] = identity(q)
        hz = output['clock_before']['clock_ticks_per_second']
        output['reported_helper_start_epoch_rational'] = {
            'numerator': output['clock_before']['boot_epoch_seconds']*hz+START,
            'denominator': hz, 'boot_epoch_integer_seconds_resolution': 1,
            'tick_seconds_rational': [1, hz],
            'conservative_helper_birth_upper_bound_rational':
                {'numerator': output['clock_before']['boot_epoch_seconds']*hz+hz+START+1,
                 'denominator': hz},
            'wall_clock_history_correspondence_is_an_assumption_not_measured': True}
        output['administration_anchors_before'] = query_anchors(q)
        portal_device = output['public_identity_before']['portal_mount']['exact_route']['device']
        for name, definition in ADMIN_ROUTES.items():
            q.tick()
            row = query_row(q, name, definition, output['clock_before'], portal_device)
            output['rows'].append(row)
            if row.get('query_limit_reached'): break
        output['administration_anchors_after'] = query_anchors(q)
        output['administration_anchor_metadata_interval_equal'] = (
            output['administration_anchors_before'] == output['administration_anchors_after'])
        output['clock_after'] = boot(q)
        output['public_identity_after'] = identity(q)
        output['public_identity_interval_equal'] = identity_key(output['public_identity_before']) == \
                                                  identity_key(output['public_identity_after'])
        output['boot_clock_interval_equal'] = all(output['clock_before'][k] == output['clock_after'][k]
                for k in ('boot_epoch_seconds', 'clock_ticks_per_second'))
        output['all_eighteen_walks_completed_and_metadata_stable'] = (len(output['rows']) == 18 and
                all(r['first_pass_completed'] and r['second_pass_completed'] and
                    r['metadata_equal_between_passes'] and 'error' not in r for r in output['rows']) and
                output['public_identity_interval_equal'] and output['boot_clock_interval_equal'] and
                output['administration_anchor_metadata_interval_equal'])
    except Exception as exc:
        output['error'] = {'type': type(exc).__name__,
                           'code': str(exc) if isinstance(exc, Refused) else None,
                           'errno': exc.errno if isinstance(exc, OSError) else None}
    finally:
        output['checked_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        output['elapsed_seconds'] = time.monotonic()-q.started
        output['bytes_read'] = q.bytes_read
        output['metadata_entry_visits'] = q.entries
        output['statx_calls'] = q.statx_calls
        output['statx_return_buffer_bytes'] = q.statx_calls*256
        output['directory_name_bytes_enumerated'] = q.directory_name_bytes
        output['failure_witness_count'] = q.failure_witnesses
        output['object_metadata_bytes'] = q.object_metadata_bytes
        output['failure_metadata_bytes'] = q.failure_metadata_bytes
        raw = canonical(output)
        try:
            require(len(raw)+1 <= LIMITS['output_bytes'], 'bounded_original_output')
            view = memoryview(raw+b'\n')
            while view:
                written = os.write(1, view)
                require(written > 0, 'stdout_write_failed')
                view = view[written:]
        finally:
            if old_alarm is not None:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_alarm)
    return 0 if output.get('all_eighteen_walks_completed_and_metadata_stable') else 1

if __name__ == '__main__':
    sys.exit(main())

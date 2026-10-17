"""MAA diagnostic trace attribution boundaries. Updated: 2026-09-25."""

from swdb.dx100_coverage import observe


def test_only_in_roi_actual_parent_stores_and_range_sizes_count(tmp_path):
    log = tmp_path / "trace"
    log.write_text('''50: system.maa: R[0] executeInstruction: my_idx_j: 16384, tile size: 16384
110: system.maa: I[0] Start [INSTR[opcode(INDIR_ST_VECTOR) datatype(INT32) baseAddr(0x4000)]]
120: system.maa: I[0] recvData: 2 entries received for addr(0x8000), grow(x0) from T[0]!
121: system.maa: I[0] recvData: new_data[2] = SPD[0][0] = 7/7/0.0!
122: system.maa: I[0] recvData: new_data[2] = SPD[0][1] = 9/9/0.0!
125: system.maa: R[0] executeInstruction: my_idx_j: 16384, tile size: 16384
126: system.maa: R[0] executeInstruction: my_idx_j: 7, tile size: 7
130: system.maa: I[0] End [INSTR]
131: system.maa: S[0] End [INSTR]
132: system.maa: R[0] End [INSTR]
133: system.maa: A[0] End [INSTR]
190: system.maa: I[1] Start [INSTR[opcode(INDIR_ST_VECTOR) datatype(INT32) baseAddr(0x5000)]]
191: system.maa: I[1] recvData: 2 entries received for addr(0x9000), grow(x0) from T[0]!
192: system.maa: I[1] recvData: new_data[0] = SPD[0][0] = 3/3/0.0!
193: system.maa: I[1] recvData: new_data[0] = SPD[0][1] = 4/4/0.0!
201: system.maa: R[0] executeInstruction: my_idx_j: 3, tile size: 3
SWDB_BFS_PARENT_STORAGE address=4000 count=20 element_bytes=4
''')
    coverage = observe(log, {"simTicks": "100", "finalTick": "200"}, 16384)
    assert coverage["completed_trace_units"] == {"I": 1, "S": 1, "R": 1, "A": 1}
    assert coverage["full_tiles"]["count"] == 1
    assert coverage["tail_tiles"]["count"] == 1
    assert coverage["competing_parent_updates"]["count"] == 1
    assert coverage["competing_parent_updates"]["samples"][0]["physical_word_address"] == 0x8008
    original = log.read_text()
    log.write_text(original.replace('address=4000', 'address=8000'))
    assert observe(log, {"simTicks": "100", "finalTick": "200"}, 16384)["competing_parent_updates"]["state"] == "unobserved"
    log.write_text(original)
    # A graph/source annotation without the observed returned parent address
    # cannot turn generic repeated stores into parent-conflict evidence.
    log.write_text(log.read_text().replace("SWDB_BFS_PARENT_STORAGE", "unavailable"))
    assert observe(log, {"simTicks": "100", "finalTick": "200"}, 16384)["competing_parent_updates"]["state"] == "unobserved"


def test_missing_exact_tick_interval_cannot_count_any_acceleration(tmp_path):
    log = tmp_path / "trace"
    log.write_text("100: system.maa: I[0] End [INSTR]\n")
    assert observe(log, {"simTicks": "100"}, 1024)["completed_trace_units"] == {}

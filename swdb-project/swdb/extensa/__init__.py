# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/ (package marker; see PROVENANCE.md for every file)
"""Machinery ported from Extensa (MemAcc AgenticRefiner) for SWDB's Extensa mode.

Only decision D1's ported groups live here: loop accounting (`search`, `leakage`),
runtime-probe contract checks (`probes`), certification profiles (`profiles`) and
BFS-relevant synthesis (`synthesis`). The loop itself, the speed rule and every
performance number are SWDB's own (`swdb.campaign`, the evaluator).
"""

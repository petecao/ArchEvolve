#!/usr/bin/env python3
"""Ticket 06 spike (b), lever 2 (shape splitting), 2026-10-14 ET. THROWAWAY.

Enumerates every graph shape within the bounds (vertices 3, edges <= 3, frontier <= 2) and writes
SAW drivers with one llvm_verify per shape. A shape fixes the CSR offsets and the frontier (its
size and its vertices in queue order); values stay symbolic (units.saw, shape_inputs).

Count check (map 19 item 4): the enumeration must equal the closed form
    C(E + V, V) * sum_{k=0..F} V! / (V - k)!
(offsets: nondecreasing (o1, o2, o3) in [0, E]; frontier: ordered k-tuples of distinct vertices).
At V = 3, E = 3, F = 2: C(6, 3) * (1 + 3 + 6) = 20 * 10 = 200.

Usage:
  shapes.py count                       print the enumeration size and the closed form; exit 1 if they differ
  shapes.py driver UNIT FIRST LAST OUT  write a driver for shapes [FIRST, LAST) of UNIT (peter|maa)
  shapes.py driver UNIT ID ID+1 OUT --overrides EXPR   (EXPR: the override list, default ovs)
"""
import itertools
import math
import sys

V, E, F = 3, 3, 2


def shapes():
    out = []
    for k in range(F + 1):
        for frontier in itertools.permutations(range(V), k):
            for o1 in range(E + 1):
                for o2 in range(o1, E + 1):
                    for o3 in range(o2, E + 1):
                        out.append((k, frontier, (0, o1, o2, o3)))
    return out


def closed_form():
    return math.comb(E + V, V) * sum(math.perm(V, k) for k in range(F + 1))


def shape_id(s):
    k, frontier, offsets = s
    return 'nf%d_f%s_o%s' % (k, ''.join(map(str, frontier)) or '-', ''.join(map(str, offsets)))


def frontier_term(frontier):
    if not frontier:
        return '{{ [] : [0][32] }}'
    return '{{ [%s] : [%d][32] }}' % (', '.join(map(str, frontier)), len(frontier))


def driver(unit, first, last, overrides='ovs'):
    entry = {'peter': '_Z15swdb_unit_peterii', 'maa': '_Z13swdb_unit_maai'}[unit]
    lines = []
    for s in shapes()[first:last]:
        k, frontier, offsets = s
        sid = shape_id(s)
        lines.append('print "SHAPE_BEGIN %s";' % sid)
        lines.append('t_%s <- time (llvm_verify m "%s" %s true (%s_shape %d %s {{ [%s] : [4][32] }}) z3);'
                     % (sid, entry, overrides, unit, k, frontier_term(frontier), ', '.join(map(str, offsets))))
        lines.append('print "SHAPE_PROVEN %s";' % sid)
    return '\n'.join(lines) + '\n'


def main(argv):
    if argv[1] == 'count':
        n, c = len(shapes()), closed_form()
        print('shapes %d closed_form %d' % (n, c))
        return 0 if n == c else 1
    if argv[1] == 'ids':
        for i, s in enumerate(shapes()):
            print(i, shape_id(s))
        return 0
    if argv[1] == 'driver':
        unit, first, last, out = argv[2], int(argv[3]), int(argv[4]), argv[5]
        overrides = argv[7] if len(argv) > 7 and argv[6] == '--overrides' else 'ovs'
        assert len(shapes()) == closed_form()
        open(out, 'w').write(driver(unit, first, last, overrides))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))

"""SMASH finite bitmap/block-rank contract, not BMU RTL or memory ABI.

Levels are canonical compact bit lists, bottom first. Set parent bits own fixed
child blocks; unused edge bits must be zero. This helper explicitly requires
full logical NZA blocks. It does not classify FP payloads or compute a kernel.
"""
from copy import deepcopy


def integer(value, *, minimum=0, maximum=(1 << 64) - 1, name="integer"):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(name + ": bounded exact integer required")
    return value


def decode_layout(layout, *, max_bitmap_bits=65536):
    integer(max_bitmap_bits, minimum=1, name="bitmap storage bound")
    if type(layout) is not dict:
        raise ValueError("explicit encoded layout required")
    if not isinstance(layout.get("matrix"), str) or not layout["matrix"]:
        raise ValueError("matrix identity required")
    rows = integer(layout.get("rows"), minimum=1, name="rows")
    columns = integer(layout.get("columns"), minimum=1, name="columns")
    integer(layout.get("group"), maximum=(1 << 32) - 1, name="group")
    integer(layout.get("generation"), minimum=1, name="generation")
    if rows * columns >= 1 << 64:
        raise ValueError("matrix extent overflows declared address domain")
    ratios, levels = layout.get("ratios"), layout.get("levels")
    if type(ratios) is not list or not 1 <= len(ratios) <= 8:
        raise ValueError("finite declared hierarchy required")
    if type(levels) is not list or len(levels) != len(ratios):
        raise ValueError("every declared bitmap level required")
    for ratio in ratios:
        integer(ratio, minimum=1, maximum=2048, name="compression ratio")
    if (rows * columns) % ratios[0]:
        raise ValueError("partial NZA block padding ABI unbound")
    if (
        sum(len(bits) for bits in levels if type(bits) is list)
        > max_bitmap_bits
    ):
        raise ValueError("bitmap storage bound exceeded")
    for bits in levels:
        if type(bits) is not list:
            raise ValueError("typed bitmap list required")
        for bit in bits:
            integer(bit, maximum=1, name="bitmap bit")
    logical_lengths = [(rows * columns) // ratios[0]]
    for ratio in ratios[1:]:
        logical_lengths.append((logical_lengths[-1] + ratio - 1) // ratio)
    top = len(levels) - 1
    if len(levels[top]) != logical_lengths[top]:
        raise ValueError("top-level bitmap extent drift")
    offsets = [0] * len(levels)
    block_indices = []

    def visit(level, logical_index):
        if logical_index >= logical_lengths[level]:
            raise ValueError("set padding bit beyond logical extent")
        if level == 0:
            block_indices.append(logical_index)
            return
        size = ratios[level]
        start = offsets[level - 1]
        end = start + size
        if end > len(levels[level - 1]):
            raise ValueError("missing selected child bitmap block")
        bits = levels[level - 1][start:end]
        offsets[level - 1] = end
        if not any(bits):
            raise ValueError("set parent with empty child block")
        for i, bit in enumerate(bits):
            if bit:
                visit(level - 1, logical_index * size + i)

    for i, bit in enumerate(levels[top]):
        if bit:
            visit(top, i)
    for level in range(top):
        if offsets[level] != len(levels[level]):
            raise ValueError("orphaned or extra compressed bitmap bytes")
    nza_elements = integer(
        layout.get("nza_elements"), name="logical NZA elements"
    )
    if nza_elements != len(block_indices) * ratios[0]:
        raise ValueError("NZA rank/declared logical length mismatch")
    result = []
    for rank, block in enumerate(block_indices):
        flat = block * ratios[0]
        result.append(
            {
                "matrix": layout["matrix"],
                "group": layout["group"],
                "generation": layout["generation"],
                "block_index": block,
                "block_rank": rank,
                "row": flat // columns,
                "column": flat % columns,
                "flat_start": flat,
                "logical_elements": ratios[0],
                "nza_start": rank * ratios[0],
                "nza_end": (rank + 1) * ratios[0],
                "per_lane_nonzero": None,
            }
        )
    return result


class GroupScanner:
    """Abstract PBMAP advances; RDIND observes the same current index.

    EOF is a helper API convention. No hardware EOF instruction, physical word
    encoding, group context ownership or transport bit order is inferred here.
    """

    def __init__(self, layout, *, max_bitmap_bits=65536):
        self.blocks = decode_layout(layout, max_bitmap_bits=max_bitmap_bits)
        self.group = layout["group"]
        self.generation = layout["generation"]
        self.cursor = 0
        self.current = None

    def _binding(self, group, generation):
        integer(group, maximum=(1 << 32) - 1, name="actual group")
        integer(generation, minimum=1, name="actual generation")
        if group != self.group or generation != self.generation:
            raise ValueError("group/matrix generation drift")

    def pbmap(self, *, group, generation):
        self._binding(group, generation)
        if self.cursor == len(self.blocks):
            self.current = None
            return False
        self.current = self.blocks[self.cursor]
        self.cursor += 1
        return True

    def rdind(self, *, group, generation):
        self._binding(group, generation)
        if self.current is None:
            raise ValueError("no current selected block")
        return deepcopy(self.current)

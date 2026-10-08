"""Untimed, finite association contracts; not a production simulator or RTL."""
from dataclasses import dataclass


class ContractError(ValueError):
    pass


def uint(value, maximum=(1 << 64) - 1):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ContractError("exact unsigned integer required")
    return value


@dataclass(frozen=True)
class Request:
    ordinal: int
    address: int
    generation: int


def gather(base, indices, *, width, generation):
    """Synthetic address generation, with no translation/coherence claim."""
    uint(base)
    uint(generation)
    if width not in (4, 8) or type(width) is not int or base % width:
        raise ContractError("word geometry")
    return [
        Request(i, uint(base + uint(index) * width), generation)
        for i, index in enumerate(indices)
    ]


class MapleQueue:
    """Reservation/response/consume abstraction of paper section 3.4."""

    def __init__(self, capacity, generation):
        if uint(capacity) == 0:
            raise ContractError("capacity")
        self.capacity = capacity
        self.generation = uint(generation)
        self.next_token = 0
        self.slots = {}
        self.order = []

    def reserve(self, request):
        if request.generation != self.generation:
            raise ContractError("generation")
        if len(self.slots) == self.capacity:
            return None  # backpressure: no state change or dropped request
        token = self.next_token
        self.next_token += 1
        self.slots[token] = [request, None]
        self.order.append(token)
        return token

    def respond(self, token, bits, generation):
        uint(bits)
        if generation != self.generation or token not in self.slots:
            raise ContractError("stale/foreign response")
        if self.slots[token][1] is not None:
            raise ContractError("duplicate response")
        self.slots[token][1] = bits

    def consume(self):
        if not self.order or self.slots[self.order[0]][1] is None:
            return None
        token = self.order.pop(0)
        request, bits = self.slots.pop(token)
        return request.ordinal, bits

    def drained(self):
        return not self.slots


class DxLines:
    """Line/offset grouping abstraction; choices below are explicit policies.

    Issue order is caller-provided, not a claim about real DRAM scheduling.
    This fixture retains all credits until write ACK (conservative abstraction).
    """

    def __init__(self, *, line_capacity, offset_capacity, width, generation):
        if uint(line_capacity) == 0 or uint(offset_capacity) == 0:
            raise ContractError("capacity")
        if width not in (4, 8) or type(width) is not int:
            raise ContractError("width")
        self.line_capacity = line_capacity
        self.offset_capacity = offset_capacity
        self.width = width
        self.generation = uint(generation)
        self.rows = {}
        self.ordinals = set()
        self.issued = set()
        self.returned = set()
        self.acked = set()
        self.closed = False

    def admit(self, request):
        if self.closed or request.generation != self.generation:
            raise ContractError("admission lifecycle")
        uint(request.ordinal)
        uint(request.address)
        if request.address % self.width or request.ordinal in self.ordinals:
            raise ContractError("address/ordinal")
        line = request.address // 64 * 64
        if line in self.issued:
            raise ContractError(
                "no appending after this abstract line is issued"
            )
        if len(self.ordinals) == self.offset_capacity:
            return False
        if line not in self.rows and len(self.rows) == self.line_capacity:
            return False
        self.rows.setdefault(line, []).append(request)
        self.ordinals.add(request.ordinal)
        return True

    def close(self, expected_ordinals):
        expected = list(expected_ordinals)
        for value in expected:
            uint(value)
        if (
            len(set(expected)) != len(expected)
            or set(expected) != self.ordinals
        ):
            raise ContractError("missing/extra/duplicate source coverage")
        self.closed = True

    def issue(self, line):
        if not self.closed or line not in self.rows or line in self.issued:
            raise ContractError("issue lifecycle")
        self.issued.add(line)
        return tuple(r.ordinal for r in self.rows[line])

    def respond(self, line, words, generation):
        if (
            generation != self.generation
            or line not in self.issued
            or line in self.returned
        ):
            raise ContractError("response identity")
        if len(words) != 64 // self.width:
            raise ContractError("line payload")
        for bits in words:
            uint(bits, (1 << (8 * self.width)) - 1)
        self.returned.add(line)
        return [
            (r.ordinal, words[(r.address - line) // self.width])
            for r in self.rows[line]
        ]

    def ack(self, line, generation):
        if (
            generation != self.generation
            or line not in self.returned
            or line in self.acked
        ):
            raise ContractError("write ACK identity")
        self.acked.add(line)

    def finished(self):
        return self.closed and self.acked == set(self.rows)

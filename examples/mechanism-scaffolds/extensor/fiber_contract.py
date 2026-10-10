"""Finite coordinate/position contract from ExTensor Fig. 6, not RTL/timing.

Strict unique coordinates are an explicit canonical input restriction here.
The paper does not give a duplicate-coordinate ABI. Payloads remain raw bits;
this contract does not compute products or reorder floating-point reductions.
"""
from collections import deque
from copy import deepcopy


def uint(value, limit, name):
    if type(value) is not int or not 0 <= value < limit:
        raise ValueError(name + ": expected bounded exact integer")
    return value


def validate_fiber(fiber, *, extent, storage_words, max_coordinates):
    uint(extent, 1 << 64, "extent")
    uint(storage_words, 1 << 64, "storage_words")
    uint(max_coordinates, 1 << 64, "max_coordinates")
    if not extent or not storage_words or not max_coordinates:
        raise ValueError("positive declared bounds required")
    if not isinstance(fiber, dict):
        raise ValueError("fiber object required")
    if not isinstance(fiber.get("tensor"), str) or not fiber["tensor"]:
        raise ValueError("explicit tensor owner required")
    if fiber.get("payload_type") != "float64_bits":
        raise ValueError(
            "only opaque evaluated float64 bit payloads supported"
        )
    uint(fiber.get("generation"), 1 << 64, "generation")
    if not fiber["generation"]:
        raise ValueError("fresh generation required")
    uint(fiber.get("level"), 1 << 32, "level")
    parent = fiber.get("parent")
    if type(parent) is not list:
        raise ValueError("explicit parent coordinate path required")
    for coordinate in parent:
        uint(coordinate, 1 << 64, "parent coordinate")
    rows = fiber.get("rows")
    if type(rows) is not list or len(rows) > max_coordinates:
        raise ValueError("finite coordinate capacity exceeded")
    previous = -1
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "coordinate",
            "position",
            "bits",
        }:
            raise ValueError(
                "complete coordinate/position/bits descriptor required"
            )
        coordinate = uint(row["coordinate"], extent, "coordinate")
        uint(row["position"], storage_words, "position")
        uint(row["bits"], 1 << 64, "payload bits")
        if coordinate <= previous:
            raise ValueError(
                "strict increasing canonical coordinates required"
            )
        previous = coordinate
    return deepcopy(fiber)


class Intersection:
    """Two finite streams, bounded output FIFO, explicit drained EOS.

    Positions and both tensor owners survive every match. A full output queue
    cannot consume a matching pair. These are abstract implementation obligations,
    not a paper-specified callback or credit ABI.
    """

    def __init__(
        self,
        left,
        right,
        *,
        extent,
        storage_words,
        max_coordinates,
        output_capacity
    ):
        uint(output_capacity, 1 << 32, "output_capacity")
        if not output_capacity:
            raise ValueError("positive output capacity required")
        self.left = validate_fiber(
            left,
            extent=extent,
            storage_words=storage_words,
            max_coordinates=max_coordinates,
        )
        self.right = validate_fiber(
            right,
            extent=extent,
            storage_words=storage_words,
            max_coordinates=max_coordinates,
        )
        if self.left["generation"] != self.right["generation"]:
            raise ValueError("mixed generation")
        if self.left["level"] != self.right["level"]:
            raise ValueError(
                "intersection requires the declared same dimension"
            )
        self.capacity = output_capacity
        self.pending = deque()
        self.i = self.j = 0
        self.eos = False

    def step(self):
        if self.eos:
            return "EOS"
        left, right = self.left["rows"], self.right["rows"]
        if self.i == len(left) or self.j == len(right):
            # Fig. 6 flush: trailing unmatched data cannot create a match.
            self.i, self.j = len(left), len(right)
            self.eos = True
            return "EOS"
        a, b = left[self.i], right[self.j]
        if a["coordinate"] < b["coordinate"]:
            self.i += 1
            return "DROP_LEFT"
        if a["coordinate"] > b["coordinate"]:
            self.j += 1
            return "DROP_RIGHT"
        if len(self.pending) == self.capacity:
            return "BLOCKED"
        self.pending.append(
            {
                "coordinate": a["coordinate"],
                "generation": self.left["generation"],
                "level": self.left["level"],
                "left": {
                    "tensor": self.left["tensor"],
                    "parent": deepcopy(self.left["parent"]),
                    "ordinal": self.i,
                    "position": a["position"],
                    "bits": a["bits"],
                },
                "right": {
                    "tensor": self.right["tensor"],
                    "parent": deepcopy(self.right["parent"]),
                    "ordinal": self.j,
                    "position": b["position"],
                    "bits": b["bits"],
                },
            }
        )
        self.i += 1
        self.j += 1
        return "MATCH"

    def take(self):
        if not self.pending:
            raise ValueError("no delivered pair available")
        return self.pending.popleft()

    @property
    def complete(self):
        return self.eos and not self.pending

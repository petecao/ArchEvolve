"""Finite Fifer §5 contract. Abstract lifecycle, not CGRA RTL or timing.

Each stage here has one input/output queue and processes one opaque token.
Hardware SIMD widths, configuration ABI and memory protection are not inferred.
"""
from collections import deque
from copy import deepcopy
from dataclasses import dataclass


def positive(value, name):
    if type(value) is not int or not 0 < value < 1 << 32:
        raise ValueError(name + ": positive exact integer required")
    return value


@dataclass(frozen=True)
class Value:
    bits: int
    control: bool = False

    def __post_init__(self):
        if type(self.bits) is not int or not 0 <= self.bits < 1 << 64:
            raise ValueError("opaque bounded payload bits required")
        if type(self.control) is not bool:
            raise ValueError("typed control bit required")


class Queue:
    def __init__(self, capacity):
        self.capacity = positive(capacity, "queue capacity")
        self.values = deque()
        self.reserved = 0

    @property
    def free(self):
        return self.capacity - len(self.values) - self.reserved

    def put(self, value):
        if type(value) is not Value or not self.free:
            raise ValueError("typed value and output capacity required")
        self.values.append(value)

    def take(self):
        if not self.values:
            raise ValueError("empty input queue")
        return self.values.popleft()


@dataclass
class Stage:
    name: str
    input: Queue
    output: Queue
    state: dict

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("explicit stage identity required")
        if type(self.input) is not Queue or type(self.output) is not Queue:
            raise ValueError("explicit queue endpoints required")
        if self.input is self.output or type(self.state) is not dict:
            raise ValueError(
                "distinct endpoints and explicit saved state required"
            )
        self.state = deepcopy(self.state)

    @property
    def ready(self):
        return bool(self.input.values) and self.output.free > 0


class PE:
    def __init__(self, stages, active):
        if type(stages) is not list or not stages:
            raise ValueError("finite stages required")
        if any(type(s) is not Stage for s in stages):
            raise ValueError("typed stage definitions required")
        self.stages = {s.name: s for s in stages}
        if len(self.stages) != len(stages) or active not in self.stages:
            raise ValueError(
                "unique stage identities and selected stage required"
            )
        self.active = active
        self.pending = None
        self.loaded = self.saved = False
        self.fabric = {}
        self.history = []

    def choose(self):
        # Ties use declared order solely for deterministic abstract tests.
        # The paper specifies most work, but not its tie-breaking implementation.
        current = self.stages[self.active]
        if self.pending is None and current.ready:
            return current.name
        ready = [s for s in self.stages.values() if s.ready]
        return (
            max(ready, key=lambda s: len(s.input.values)).name
            if ready
            else None
        )

    def begin(self):
        stage = self.stages[self.active]
        if self.pending is not None or not stage.ready:
            raise ValueError("stage blocked or fabric draining")
        value = stage.input.take()
        stage.output.reserved += 1
        token = object()
        self.fabric[token] = (stage.name, value)
        return token

    def finish(self, token, value):
        if token not in self.fabric or type(value) is not Value:
            raise ValueError(
                "actual in-flight token and typed output required"
            )
        name, _ = self.fabric.pop(token)
        stage = self.stages[name]
        stage.output.reserved -= 1
        stage.output.put(value)

    def request_switch(self, target):
        if self.pending is not None or target == self.active:
            raise ValueError("new single pending configuration required")
        if target not in self.stages or not self.stages[target].ready:
            raise ValueError("selected target must be eligible")
        if self.stages[self.active].ready:
            raise ValueError("paper policy retains unblocked current stage")
        self.pending = target
        self.loaded = self.saved = False

    def configuration_loaded(self, target):
        if target != self.pending or self.pending is None:
            raise ValueError("only pending inactive configuration may load")
        self.loaded = True

    def state_saved(self, name, state):
        if self.pending is None or name != self.active or self.fabric:
            raise ValueError("save final old state after fabric drain")
        if type(state) is not dict:
            raise ValueError("explicit stage state required")
        self.stages[name].state = deepcopy(state)
        self.saved = True

    def activate(self):
        if (
            self.pending is None
            or self.fabric
            or not self.loaded
            or not self.saved
        ):
            raise ValueError(
                "configuration load, fabric drain and old state required"
            )
        self.history.append((self.active, self.pending))
        self.active, self.pending = self.pending, None
        self.loaded = self.saved = False
        return deepcopy(self.stages[self.active].state)


class DRM:
    """Independent, initialization-bound DRM with in-order result delivery.

    Synthetic requests are opaque already-computed addresses. No memory accesses
    are performed. Fabric reconfiguration does not change this DRM's endpoints.
    """

    def __init__(self, owner, generation, output, slots):
        if not isinstance(owner, str) or not owner:
            raise ValueError("explicit DRM owner required")
        self.owner = owner
        self.generation = positive(generation, "generation")
        if type(output) is not Queue:
            raise ValueError("fixed DRM output endpoint required")
        self.output = output
        self.slots = positive(slots, "DRM slots")
        self.order = deque()
        self.requests = {}

    def issue(self, address, *, owner, generation):
        if (
            owner != self.owner
            or type(generation) is not int
            or generation != self.generation
        ):
            raise ValueError("DRM owner/generation drift")
        if type(address) is not int or not 0 <= address < 1 << 64:
            raise ValueError("actual finite address required")
        if len(self.order) == self.slots:
            raise ValueError("bounded DRM request storage full")
        token = object()
        self.order.append(token)
        self.requests[token] = {"address": address, "value": None}
        return token

    def response(self, token, value):
        if token not in self.requests or type(value) is not Value:
            raise ValueError("unknown request or malformed returned bits")
        if self.requests[token]["value"] is not None:
            raise ValueError("duplicate response")
        self.requests[token]["value"] = value

    def deliver(self):
        if not self.order:
            return False
        token = self.order[0]
        value = self.requests[token]["value"]
        if value is None or not self.output.free:
            return False
        self.output.put(value)
        self.order.popleft()
        del self.requests[token]
        return True

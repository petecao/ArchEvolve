"""Finite Flat-HTA line/branch contract from MICRO2019 §§3.1-4.4.

Raw key/value words are opaque uint64 patterns. Hash-line receipts are supplied;
this module does not implement or certify actual CRC32/ISA/atomic hardware.
"""
from copy import deepcopy


def integer(value, lower=0, upper=(1 << 64) - 1):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError("bounded exact integer required")
    return value


class FlatTable:
    def __init__(
        self,
        *,
        name,
        generation,
        table_id,
        key_words,
        line_count,
        hash_lines,
        sentinels
    ):
        if not isinstance(name, str) or not name:
            raise ValueError("explicit table identity required")
        integer(generation, 1)
        integer(table_id, 0, 3)
        integer(key_words, 1, 4)
        integer(line_count, 2, 65536)
        if line_count & (line_count - 1):
            raise ValueError("power-of-two line count required")
        self.name, self.generation, self.table_id = name, generation, table_id
        self.key_words, self.line_count = key_words, line_count
        self.slots_per_line = 64 // (8 * (key_words + 1))
        if type(hash_lines) is not dict:
            raise ValueError("explicit bounded hash-line receipts required")
        self.hash_lines = {}
        for key, line in hash_lines.items():
            self._key(key)
            self.hash_lines[key] = integer(line, 0, line_count - 1)
        if type(sentinels) is not dict or set(sentinels) != {
            "invalid_zero",
            "deleted_zero",
            "invalid_other",
            "deleted_other",
        }:
            raise ValueError(
                "four distinct source-format sentinel receipts required"
            )
        for key in sentinels.values():
            self._key(key)
            if key not in self.hash_lines:
                raise ValueError("missing sentinel hash receipt")
        if len(set(sentinels.values())) != 4:
            raise ValueError("sentinels must be distinct")
        for kind in ["invalid", "deleted"]:
            if self.hash_lines[sentinels[kind + "_zero"]] == 0:
                raise ValueError("line0 sentinel must hash to another line")
            if self.hash_lines[sentinels[kind + "_other"]] != 0:
                raise ValueError("other-line sentinel must hash to line0")
        self.sentinels = deepcopy(sentinels)
        self.lines = [
            [
                {"key": self._sentinel(i, "invalid"), "value": None}
                for _ in range(self.slots_per_line)
            ]
            for i in range(line_count)
        ]

    def _key(self, key):
        if type(key) is not tuple or len(key) != self.key_words:
            raise ValueError("fixed declared raw key-word tuple required")
        for word in key:
            integer(word)
        return key

    def line(self, key):
        self._key(key)
        if key not in self.hash_lines:
            raise ValueError("missing actual hash-line receipt")
        return self.hash_lines[key]

    def _sentinel(self, line, kind):
        return self.sentinels[kind + ("_zero" if line == 0 else "_other")]

    def _hit(self, line, key):
        return next(
            (
                i
                for i, pair in enumerate(self.lines[line])
                if pair["key"] == key
            ),
            None,
        )

    def _space(self, line, *, include_deleted):
        permitted = {self._sentinel(line, "invalid")}
        if include_deleted:
            permitted.add(self._sentinel(line, "deleted"))
        return next(
            (
                i
                for i, pair in enumerate(self.lines[line])
                if pair["key"] in permitted
            ),
            None,
        )

    def lookup(self, key):
        line = self.line(key)
        hit = self._hit(line, key)
        if hit is not None:
            return {
                "branch": "taken",
                "resolved": True,
                "found": True,
                "value": self.lines[line][hit]["value"],
            }
        if self._space(line, include_deleted=False) is not None:
            return {
                "branch": "taken",
                "resolved": True,
                "found": False,
                "value": None,
            }
        return {
            "branch": "fallthrough",
            "resolved": False,
            "found": None,
            "value": None,
        }

    def update(self, key, value):
        line = self.line(key)
        integer(value)
        slot = self._hit(line, key)
        if slot is None:
            slot = self._space(line, include_deleted=True)
        if slot is None:
            return {"branch": "fallthrough", "victim": None}
        self.lines[line][slot] = {"key": key, "value": value}
        return {"branch": "taken", "victim": None}

    def swap(self, key, value, *, victim_slot):
        # Explicit selected victim is a test/integration obligation. The paper
        # uses random selection; no random implementation is inferred here.
        self.line(key)
        integer(value)
        result = self.update(key, value)
        if result["branch"] == "taken":
            return result
        slot = integer(victim_slot, 0, self.slots_per_line - 1)
        line = self.line(key)
        victim = deepcopy(self.lines[line][slot])
        self.lines[line][slot] = {"key": key, "value": value}
        return {"branch": "fallthrough", "victim": victim}

    def delete(self, key):
        line = self.line(key)
        slot = self._hit(line, key)
        if slot is None:
            return {"branch": "fallthrough"}
        self.lines[line][slot] = {
            "key": self._sentinel(line, "deleted"),
            "value": None,
        }
        return {"branch": "taken"}


class ExclusiveMap:
    """Single-threaded consumer contract for HTA + software overflow.

    The paper describes stale software removal after full-line swap. This helper
    also requires removal on deleted-slot reuse and delete, so its exclusivity
    invariant holds over arbitrary mixed operations. That extra bookkeeping is
    an explicit integration obligation, not a certified original ISA wrapper.
    Concurrent use requires the paper's lock/recheck/atomic protocol separately.
    """

    def __init__(self, hardware):
        if type(hardware) is not FlatTable:
            raise ValueError("exact declared table required")
        self.hardware = hardware
        self.overflow = {}

    def lookup(self, key):
        result = self.hardware.lookup(key)
        if result["branch"] == "taken":
            return result["value"] if result["found"] else None
        return self.overflow.get(key)

    def put(self, key, value, *, victim_slot=0):
        result = self.hardware.swap(key, value, victim_slot=victim_slot)
        if result["victim"] is not None:
            victim = result["victim"]
            self.overflow[victim["key"]] = victim["value"]
        # This is necessary even if insertion reused a deleted slot and the
        # hardware branch was taken. Skip means resolved, not no software copy.
        self.overflow.pop(key, None)
        self.assert_exclusive()
        return result

    def delete(self, key):
        result = self.hardware.delete(key)
        self.overflow.pop(key, None)
        self.assert_exclusive()
        return result

    def assert_exclusive(self):
        keys = []
        for line, pairs in enumerate(self.hardware.lines):
            for pair in pairs:
                if pair["key"] in {
                    self.hardware._sentinel(line, "invalid"),
                    self.hardware._sentinel(line, "deleted"),
                }:
                    continue
                if self.hardware.line(pair["key"]) != line:
                    raise ValueError("key stored in wrong source-bound line")
                keys.append(pair["key"])
        if len(keys) != len(set(keys)) or set(keys) & set(self.overflow):
            raise ValueError(
                "duplicate key ownership across hardware/software"
            )
        for key in self.overflow:
            self.hardware.line(key)

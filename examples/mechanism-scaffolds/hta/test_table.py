import copy
import unittest

from table_contract import (
    ExclusiveMap,
    FlatTable,
)


def table():
    keys = [(i, 0) for i in range(1, 8)]
    sentinels = {
        "invalid_zero": (100, 0),
        "deleted_zero": (101, 0),
        "invalid_other": (102, 0),
        "deleted_other": (103, 0),
    }
    receipts = dict.fromkeys(keys, 0)
    receipts.update(
        {
            sentinels["invalid_zero"]: 1,
            sentinels["deleted_zero"]: 1,
            sentinels["invalid_other"]: 0,
            sentinels["deleted_other"]: 0,
        }
    )
    return FlatTable(
        name="fixture",
        generation=1,
        table_id=0,
        key_words=2,
        line_count=2,
        hash_lines=receipts,
        sentinels=sentinels,
    )


class TableTests(unittest.TestCase):
    def test_resolved_missing_is_not_a_returned_zero(self):
        h = table()
        self.assertEqual(
            h.lookup((1, 0)),
            {
                "branch": "taken",
                "resolved": True,
                "found": False,
                "value": None,
            },
        )
        h.update((1, 0), 0)
        self.assertEqual(h.lookup((1, 0))["value"], 0)
        self.assertTrue(h.lookup((1, 0))["found"])

    def test_full_update_no_mutation_and_swap_victim_ownership(self):
        h = table()
        h.update((1, 0), 11)
        h.update((2, 0), 22)
        before = copy.deepcopy(h.lines)
        self.assertEqual(h.update((3, 0), 33)["branch"], "fallthrough")
        self.assertEqual(h.lines, before)
        result = h.swap((3, 0), 33, victim_slot=1)
        self.assertEqual(result["victim"], {"key": (2, 0), "value": 22})
        self.assertEqual(result["branch"], "fallthrough")
        self.assertEqual(h.lookup((3, 0))["value"], 33)
        self.assertEqual(h.lookup((2, 0))["branch"], "fallthrough")

    def test_tombstone_does_not_hide_live_software_key(self):
        m = ExclusiveMap(table())
        for key, value in [(1, 11), (2, 22), (3, 33)]:
            m.put((key, 0), value)
        self.assertEqual(m.overflow, {(1, 0): 11})
        m.delete((2, 0))
        self.assertEqual(m.hardware.lookup((1, 0))["branch"], "fallthrough")
        self.assertEqual(m.lookup((1, 0)), 11)

    def test_deleted_slot_reuse_requires_software_duplicate_cleanup(self):
        # Counterexample to the naive consumer rule "taken means skip all SW".
        h = table()
        m = ExclusiveMap(h)
        for key, value in [(1, 11), (2, 22), (3, 33)]:
            m.put((key, 0), value)
        m.delete((2, 0))
        self.assertEqual(h.update((1, 0), 111)["branch"], "taken")
        with self.assertRaises(ValueError):
            m.assert_exclusive()  # Naive raw operation leaves stale SW key1.
        h.delete((1, 0))
        self.assertEqual(
            m.lookup((1, 0)), 11
        )  # Deleted key reappears: stale copy.
        # Corrected declared consumer cleans ownership on every insertion/deletion.
        m = ExclusiveMap(table())
        for key, value in [(1, 11), (2, 22), (3, 33)]:
            m.put((key, 0), value)
        m.delete((2, 0))
        self.assertEqual(m.put((1, 0), 111)["branch"], "taken")
        self.assertNotIn((1, 0), m.overflow)
        self.assertEqual(m.lookup((1, 0)), 111)
        m.delete((1, 0))
        self.assertIsNone(m.lookup((1, 0)))

    def test_existing_key_update_is_single_owner_and_sentinel_values_are_legal(
        self,
    ):
        m = ExclusiveMap(table())
        m.put((1, 0), 11)
        m.put((1, 0), 12)
        self.assertEqual(m.lookup((1, 0)), 12)
        # Sentinel raw bits are ordinary legal keys in the line they hash to.
        key = m.hardware.sentinels["invalid_other"]
        m.put(key, 55)
        self.assertEqual(m.lookup(key), 55)
        m.assert_exclusive()

    def test_untyped_bits_missing_hash_and_bad_victim_reject(self):
        h = table()
        for key in [(True, 0), (1.0, 0), (1,), (1 << 64, 0), (99, 0)]:
            with self.assertRaises(ValueError):
                h.lookup(key)
        for value in [True, -1, 1 << 64, 1.0]:
            with self.assertRaises(ValueError):
                h.update((1, 0), value)
        h.update((1, 0), 11)
        h.update((2, 0), 22)
        before = copy.deepcopy(h.lines)
        with self.assertRaises(ValueError):
            h.swap((3, 0), 33, victim_slot=True)
        self.assertEqual(h.lines, before)

    def test_invalid_slot_hash_and_descriptor_geometry_reject(self):
        h = table()
        params = {
            "name": "bad",
            "generation": 1,
            "table_id": 0,
            "key_words": 2,
            "line_count": 2,
            "hash_lines": h.hash_lines,
            "sentinels": h.sentinels,
        }
        for field, value in [
            ("line_count", 3),
            ("table_id", True),
            ("generation", False),
            ("key_words", 5),
        ]:
            bad = dict(params)
            bad[field] = value
            with self.assertRaises(ValueError):
                FlatTable(**bad)
        bad = copy.deepcopy(params)
        bad["hash_lines"][h.sentinels["invalid_zero"]] = 0
        with self.assertRaises(ValueError):
            FlatTable(**bad)


if __name__ == "__main__":
    unittest.main()

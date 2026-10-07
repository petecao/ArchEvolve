import copy
import unittest

from fiber_contract import (
    Intersection,
    validate_fiber,
)


def fiber(name, coordinates, parent):
    return {
        "tensor": name,
        "generation": 1,
        "level": 2,
        "parent": parent,
        "payload_type": "float64_bits",
        "rows": [
            {
                "coordinate": c,
                "position": i + 2,
                "bits": 0x3FF0000000000000 + i,
            }
            for i, c in enumerate(coordinates)
        ],
    }


def machine(a, b, capacity=1):
    return Intersection(
        a,
        b,
        extent=16,
        storage_words=32,
        max_coordinates=16,
        output_capacity=capacity,
    )


class FiberTests(unittest.TestCase):
    def test_pairs_preserve_owners_positions_and_raw_bits(self):
        a, b = fiber("A", [0, 1, 3, 5, 7, 9], [2]), fiber("B", [1, 5], [6])
        m, result = machine(a, b), []
        while not m.eos:
            m.step()
            if m.pending:
                result.append(m.take())
        self.assertEqual([r["coordinate"] for r in result], [1, 5])
        self.assertEqual(
            result[1]["left"],
            {
                "tensor": "A",
                "parent": [2],
                "ordinal": 3,
                "position": 5,
                "bits": 0x3FF0000000000003,
            },
        )
        self.assertEqual(result[1]["right"]["parent"], [6])
        self.assertEqual(result[1]["right"]["ordinal"], 1)
        self.assertTrue(m.complete)
        self.assertEqual(a["rows"][3]["coordinate"], 5)

    def test_backpressure_does_not_drop_matching_pair(self):
        m = machine(fiber("A", [1, 5], []), fiber("B", [1, 5], []))
        self.assertEqual(m.step(), "MATCH")
        before = (m.i, m.j, copy.deepcopy(list(m.pending)))
        self.assertEqual(m.step(), "BLOCKED")
        self.assertEqual((m.i, m.j, list(m.pending)), before)
        self.assertEqual(m.take()["coordinate"], 1)
        self.assertEqual(m.step(), "MATCH")
        self.assertEqual(m.step(), "EOS")
        self.assertFalse(m.complete)
        self.assertEqual(m.take()["coordinate"], 5)
        self.assertTrue(m.complete)

    def test_empty_or_disjoint_fiber_flush_has_no_false_payload(self):
        for coordinates in ([], [3, 4, 5]):
            m = machine(fiber("A", [0, 1, 9], []), fiber("B", coordinates, []))
            for _ in range(20):
                if m.step() == "EOS":
                    break
            self.assertTrue(m.complete)
            self.assertFalse(m.pending)

    def test_unsorted_and_duplicate_coordinates_reject(self):
        for coordinates in ([5, 1], [1, 1]):
            with self.assertRaises(ValueError):
                machine(fiber("A", coordinates, []), fiber("B", [1], []))

    def test_bounds_capacity_and_exact_bit_types_reject(self):
        good = fiber("A", [1], [])
        cases = [
            ("coordinate", 16),
            ("coordinate", False),
            ("position", 32),
            ("position", -1),
            ("bits", 1 << 64),
            ("bits", -1),
            ("bits", 1.0),
            ("bits", True),
        ]
        for field, value in cases:
            bad = copy.deepcopy(good)
            bad["rows"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(
                ValueError
            ):
                validate_fiber(
                    bad, extent=16, storage_words=32, max_coordinates=16
                )
        with self.assertRaises(ValueError):
            validate_fiber(
                fiber("A", [1, 2], []),
                extent=16,
                storage_words=32,
                max_coordinates=1,
            )
        with self.assertRaises(ValueError):
            machine(good, fiber("B", [1], []), capacity=0)

    def test_generation_dimension_and_missing_owner_reject(self):
        a, b = fiber("A", [1], [0]), fiber("B", [1], [0])
        for key, value in [
            ("generation", 2),
            ("generation", False),
            ("level", 3),
            ("tensor", ""),
            ("payload_type", "float32"),
            ("parent", None),
        ]:
            bad = copy.deepcopy(b)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                machine(a, bad)
        # Distinct tensor parents are legitimate; they must be retained, not merged.
        b["parent"] = [9]
        m = machine(a, b)
        self.assertEqual(m.step(), "MATCH")
        self.assertNotEqual(m.take()["left"]["parent"], b["parent"])


if __name__ == "__main__":
    unittest.main()

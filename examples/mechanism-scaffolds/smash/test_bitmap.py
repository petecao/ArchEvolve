import copy
import unittest

from bitmap_contract import (
    GroupScanner,
    decode_layout,
)


def layout():
    return {
        "matrix": "A",
        "rows": 4,
        "columns": 8,
        "group": 0,
        "generation": 1,
        "ratios": [2, 2, 2],
        "levels": [[0, 1, 1, 1, 1, 0], [1, 0, 1, 0, 0, 1], [1, 1, 0, 1]],
        "nza_elements": 8,
    }


class BitmapTests(unittest.TestCase):
    def test_multilevel_compact_blocks_rank_and_positions(self):
        blocks = decode_layout(layout())
        self.assertEqual([b["block_index"] for b in blocks], [1, 4, 5, 14])
        self.assertEqual(
            [(b["row"], b["column"]) for b in blocks],
            [(0, 2), (1, 0), (1, 2), (3, 4)],
        )
        self.assertEqual([b["nza_start"] for b in blocks], [0, 2, 4, 6])
        self.assertEqual(blocks[-1]["nza_end"], 8)
        self.assertTrue(all(b["per_lane_nonzero"] is None for b in blocks))

    def test_rdind_stable_group_zero_and_end_not_stale_index(self):
        scanner = GroupScanner(layout())
        with self.assertRaises(ValueError):
            scanner.rdind(group=0, generation=1)
        for expected in [1, 4, 5, 14]:
            self.assertTrue(scanner.pbmap(group=0, generation=1))
            a = scanner.rdind(group=0, generation=1)
            b = scanner.rdind(group=0, generation=1)
            self.assertEqual(a, b)
            self.assertEqual(a["block_index"], expected)
            a["matrix"] = "forged"
            self.assertEqual(
                scanner.rdind(group=0, generation=1)["matrix"], "A"
            )
        self.assertFalse(scanner.pbmap(group=0, generation=1))
        with self.assertRaises(ValueError):
            scanner.rdind(group=0, generation=1)

    def test_edge_child_padding_and_matrix_end(self):
        d = {
            "matrix": "edge",
            "rows": 3,
            "columns": 4,
            "group": 2,
            "generation": 1,
            "ratios": [2, 4],
            "levels": [[0, 1, 0, 0], [0, 1]],
            "nza_elements": 2,
        }
        b = decode_layout(d)[0]
        self.assertEqual((b["flat_start"], b["row"], b["column"]), (10, 2, 2))
        d["levels"][0][2] = 1
        d["nza_elements"] = 4
        with self.assertRaises(ValueError):
            decode_layout(d)
        d = layout()
        d["columns"] = 7
        d["ratios"][0] = 3
        with self.assertRaisesRegex(ValueError, "partial NZA"):
            decode_layout(d)

    def test_missing_extra_and_false_parent_blocks_reject(self):
        for action in ["missing", "extra", "empty", "top_short"]:
            d = layout()
            if action == "missing":
                d["levels"][0].pop()
            elif action == "extra":
                d["levels"][0].append(0)
            elif action == "empty":
                d["levels"][1][:2] = [0, 0]
            else:
                d["levels"][2].pop()
            with self.subTest(action=action), self.assertRaises(ValueError):
                decode_layout(d)

    def test_nza_rank_length_and_bitmap_capacity_reject(self):
        for count in [7, 9, False]:
            d = layout()
            d["nza_elements"] = count
            with self.assertRaises(ValueError):
                decode_layout(d)
        with self.assertRaises(ValueError):
            decode_layout(layout(), max_bitmap_bits=15)

    def test_typed_bits_ratio_and_context_drift_reject(self):
        for bit in [True, -1, 2, 1.0]:
            d = layout()
            d["levels"][0][0] = bit
            with self.assertRaises(ValueError):
                decode_layout(d)
        for ratio in [0, True, 2049]:
            d = layout()
            d["ratios"][1] = ratio
            with self.assertRaises(ValueError):
                decode_layout(d)
        scanner = GroupScanner(layout())
        for group, generation in [(False, 1), (1, 1), (0, 2), (0, True)]:
            with self.assertRaises(ValueError):
                scanner.pbmap(group=group, generation=generation)
        d = layout()
        d["rows"] = 1 << 63
        with self.assertRaises(ValueError):
            decode_layout(d)

    def test_empty_matrix_data_and_single_level(self):
        d = layout()
        d["levels"] = [[], [], [0, 0, 0, 0]]
        d["nza_elements"] = 0
        self.assertEqual(decode_layout(d), [])
        s = GroupScanner(d)
        self.assertFalse(s.pbmap(group=0, generation=1))
        d = layout()
        d["ratios"] = [2]
        d["levels"] = [[int(i in {1, 4, 5, 14}) for i in range(16)]]
        self.assertEqual(
            [b["block_index"] for b in decode_layout(d)], [1, 4, 5, 14]
        )


if __name__ == "__main__":
    unittest.main()

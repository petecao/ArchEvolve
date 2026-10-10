import unittest

from phase_contract import BulkPhase


def phase(**changes):
    args = dict(
        relaxed_atomic=True,
        no_intervening_reads=True,
        contiguous_physical=True,
        bins_proven=True,
    )
    args.update(changes)
    return BulkPhase(**args)


class Phases(unittest.TestCase):
    def test_replay_flush_visibility(self):
        p = phase()
        p.enable_batching()
        p.record_batched_bin(3)
        p.disable_batching()
        with self.assertRaises(ValueError):
            p.read()
        with self.assertRaises(ValueError):
            p.private_flush_complete()
        p.replay_complete(3)
        with self.assertRaises(ValueError):
            p.sync()
        p.private_flush_complete()
        p.sync()
        self.assertIn("MERGE", p.read())

    def test_read_paging_and_duplicate_completion(self):
        p = phase()
        p.enable_batching()
        p.record_batched_bin(1)
        with self.assertRaises(ValueError):
            p.read()
        with self.assertRaises(ValueError):
            p.page_out()
        p.disable_batching()
        p.replay_complete(1)
        with self.assertRaises(ValueError):
            p.replay_complete(1)
        with self.assertRaises(ValueError):
            p.record_batched_bin(2)

    def test_not_bfs_old_parent_or_ordered_fp(self):
        for args in [
            dict(needs_old_value=True),
            dict(ordered_fp_bits=True),
            dict(relaxed_atomic=False),
            dict(contiguous_physical=False),
            dict(mixed_conventional_atomics=True),
        ]:
            with self.assertRaises(ValueError):
                phase(**args)

    def test_explicit_geometry_and_proof_state(self):
        with self.assertRaises(ValueError):
            phase(bins_proven=1)
        p = phase()
        p.enable_batching()
        with self.assertRaises(ValueError):
            p.record_batched_bin(False)
        p.disable_batching()
        p.private_flush_complete()
        p.sync()
        self.assertIn("PROOF", p.page_out())


if __name__ == "__main__":
    unittest.main()

import unittest
from dataclasses import replace

from queue_contract import (
    QRM,
    Blocked,
)


class Queues(unittest.TestCase):
    def test_committed_only_and_producer_recovery(self):
        q = QRM()
        q.configure(0, 2, 1, 2)
        old = q.issue_enqueue(0, 1, 0x1234)
        with self.assertRaises(Blocked):
            q.issue_dequeue(0, 2)
        q.squash_producer(0, 1)
        new = q.issue_enqueue(0, 1, 0x5678)
        with self.assertRaises(ValueError):
            q.commit_enqueue(old)
        with self.assertRaises(ValueError):
            q.commit_enqueue(replace(new))
        q.commit_enqueue(new)
        ticket, value = q.issue_dequeue(0, 2)
        self.assertEqual(value["bits"], 0x5678)
        q.commit_dequeue(ticket)

    def test_full_until_consumer_commit_and_rollback(self):
        q = QRM()
        q.configure(0, 1, 1, 2)
        enq = q.issue_enqueue(0, 1, 7)
        q.commit_enqueue(enq)
        deq, _ = q.issue_dequeue(0, 2)
        with self.assertRaises(Blocked):
            q.issue_enqueue(0, 1, 8)
        q.squash_consumer(0, 2)
        with self.assertRaises(ValueError):
            q.commit_dequeue(deq)
        deq, value = q.issue_dequeue(0, 2)
        self.assertEqual(value["bits"], 7)
        q.commit_dequeue(deq)
        q.issue_enqueue(0, 1, 8)

    def test_fifo_peek_and_control_distinction(self):
        q = QRM()
        q.configure(0, 3, 1, 2)
        tokens = [
            q.issue_enqueue(0, 1, value, control)
            for value, control in [(11, False), (22, True)]
        ]
        for token in tokens:
            q.commit_enqueue(token)
        self.assertEqual(q.peek_data(0, 2), 11)
        ticket, value = q.issue_dequeue(0, 2)
        q.commit_dequeue(ticket)
        self.assertEqual(value["kind"], "data")
        ticket, value = q.issue_dequeue(0, 2)
        self.assertEqual(value["kind"], "control")
        q.commit_dequeue(ticket)

    def test_aggregate_capacity_mapping_and_ownership(self):
        q = QRM(physical_budget=3)
        q.configure(0, 2, 1, 2)
        with self.assertRaises(ValueError):
            q.configure(1, 2, 3, 4)
        q.issue_enqueue(0, 1, 7)
        with self.assertRaises(ValueError):
            q.configure(0, 1, 1, 2)
        with self.assertRaises(ValueError):
            q.issue_enqueue(0, 9, 7)
        with self.assertRaises(ValueError):
            q.issue_enqueue(0, 1, False)
        with self.assertRaises(ValueError):
            q.issue_dequeue(0, 9)
        with self.assertRaises(ValueError):
            q.issue_enqueue(False, 1, 7)
        with self.assertRaises(ValueError):
            q.issue_enqueue(0, True, 7)


if __name__ == "__main__":
    unittest.main()

import unittest

from stage_contract import (
    DRM,
    PE,
    Queue,
    Stage,
    Value,
)


def stage(name, work=0, out_capacity=4):
    input_queue = Queue(8)
    for i in range(work):
        input_queue.put(Value(i))
    return Stage(name, input_queue, Queue(out_capacity), {"iteration": 0})


class FiferTests(unittest.TestCase):
    def test_stay_on_unblocked_stage_then_choose_most_work(self):
        a, b, c = stage("A", 1), stage("B", 3), stage("C", 2)
        pe = PE([a, b, c], "A")
        self.assertEqual(pe.choose(), "A")
        token = pe.begin()
        self.assertEqual(pe.choose(), "B")
        pe.request_switch("B")
        pe.configuration_loaded("B")
        with self.assertRaises(ValueError):
            pe.activate()
        with self.assertRaises(ValueError):
            pe.begin()
        with self.assertRaises(ValueError):
            pe.state_saved("A", {"iteration": 1})
        pe.finish(token, Value(10))
        with self.assertRaises(ValueError):
            pe.activate()
        pe.state_saved("A", {"iteration": 1})
        self.assertEqual(pe.activate(), {"iteration": 0})
        self.assertEqual(a.state, {"iteration": 1})
        self.assertEqual(a.output.take(), Value(10))

    def test_ready_requires_space_including_inflight_reservations(self):
        a, b = stage("A", 2, 1), stage("B", 1)
        pe = PE([a, b], "A")
        token = pe.begin()
        self.assertFalse(a.ready)
        self.assertEqual(len(a.input.values), 1)
        with self.assertRaises(ValueError):
            pe.begin()
        pe.request_switch("B")
        pe.finish(token, Value(7))
        self.assertFalse(a.ready)
        pe.state_saved("A", {})
        with self.assertRaises(ValueError):
            pe.activate()
        pe.configuration_loaded("B")
        pe.activate()
        self.assertEqual(a.output.take(), Value(7))
        self.assertTrue(a.ready)

    def test_state_and_queues_survive_return_to_stage(self):
        a, b = stage("A", 1), stage("B", 1)
        pe = PE([a, b], "A")
        t = pe.begin()
        pe.finish(t, Value(0xABC, True))
        pe.request_switch("B")
        pe.configuration_loaded("B")
        state = {"iteration": 4}
        pe.state_saved("A", state)
        state["iteration"] = 99
        pe.activate()
        t = pe.begin()
        pe.finish(t, Value(0xDEF))
        a.input.put(Value(5))
        pe.request_switch("A")
        pe.state_saved("B", {"iteration": 1})
        pe.configuration_loaded("A")
        self.assertEqual(pe.activate(), {"iteration": 4})
        self.assertEqual(a.output.take(), Value(0xABC, True))
        self.assertEqual(b.output.take(), Value(0xDEF))
        with self.assertRaises(ValueError):
            pe.finish(t, Value(3))

    def test_drm_out_of_order_response_ordered_delivery_across_switch(self):
        a, b = stage("A", 1), stage("B", 1)
        pe = PE([a, b], "A")
        output = Queue(2)
        drm = DRM("PE0-neighbors", 1, output, 2)
        first = drm.issue(0x1000, owner=drm.owner, generation=1)
        second = drm.issue(0x1008, owner=drm.owner, generation=1)
        drm.response(second, Value(22))
        self.assertFalse(drm.deliver())
        token = pe.begin()
        pe.finish(token, Value(1))
        pe.request_switch("B")
        pe.configuration_loaded("B")
        pe.state_saved("A", {})
        pe.activate()  # Independent DRM outstanding requests need not drain.
        self.assertEqual(len(drm.order), 2)
        drm.response(first, Value(11))
        self.assertTrue(drm.deliver())
        self.assertTrue(drm.deliver())
        self.assertEqual([output.take().bits, output.take().bits], [11, 22])

    def test_drm_capacity_backpressure_stale_and_duplicate_responses(self):
        output = Queue(1)
        output.put(Value(9))
        drm = DRM("owner", 1, output, 1)
        token = drm.issue(0x80, owner="owner", generation=1)
        for owner, generation in [("other", 1), ("owner", 2), ("owner", True)]:
            with self.assertRaises(ValueError):
                drm.issue(0x80, owner=owner, generation=generation)
        with self.assertRaises(ValueError):
            drm.issue(0x88, owner="owner", generation=1)
        with self.assertRaises(ValueError):
            drm.response(object(), Value(1))
        drm.response(token, Value(5))
        with self.assertRaises(ValueError):
            drm.response(token, Value(5))
        self.assertFalse(drm.deliver())
        self.assertEqual(len(drm.order), 1)
        output.take()
        self.assertTrue(drm.deliver())
        with self.assertRaises(ValueError):
            drm.response(token, Value(5))

    def test_unready_target_wrong_config_and_control_types_reject(self):
        a, b = stage("A"), stage("B")
        pe = PE([a, b], "A")
        self.assertIsNone(pe.choose())
        with self.assertRaises(ValueError):
            pe.request_switch("B")
        with self.assertRaises(ValueError):
            pe.configuration_loaded("B")
        for bits, control in [(True, False), (1 << 64, False), (1, 1)]:
            with self.assertRaises(ValueError):
                Value(bits, control)
        with self.assertRaises(ValueError):
            Queue(False)


if __name__ == "__main__":
    unittest.main()

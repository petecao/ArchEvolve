# No-guest gzip transport configuration. Created 2026-09-26 ET.
import m5
from m5.objects import Root

root = Root(full_system=False)
m5.instantiate()
first = m5.simulate(1)
assert int(m5.curTick()) == 1
assert first.getCause() == "simulate() limit reached"
m5.trace.output("post-switch.log")
second = m5.simulate(1)
assert int(m5.curTick()) == 2
assert second.getCause() == "simulate() limit reached"
print("GZIP_TRANSPORT_NO_GUEST_OK ticks=2", flush=True)

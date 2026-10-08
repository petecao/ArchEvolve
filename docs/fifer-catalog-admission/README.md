# Fifer temporal stages and ordered memory delivery

Fifer (MICRO 2021) partitions irregular programs into regular compiled stages
that execute on a reconfigurable fabric. SRAM-backed queues decouple the stages.
A PE keeps its current stage while input and output space are available; when
blocked, it selects an eligible stage with the greatest input work. Switching
stops new old-stage inputs, drains in-flight fabric work, saves final stage state
and loads the next inactive configuration. Activation requires both drain and
configuration completion. Configuration load may overlap drain.

Independent dereference/scan modules (DRMs) keep working across fabric stage
switches. Requests may complete out of order, but results enter their owned
output queue in request order. Output backpressure retains the pending result.
Queue control bits preserve stage/control boundaries. Fifer uses statically
partitioned circular SRAM queues, not Pipette's physical-register-file queues.

Revision 0.1.14 adds explicit `fifer_drm_dereference` and `fifer_drm_scan`
mapping references, six located primary claims and eight mechanisms. Payload,
address width, range endpoint/stride encoding, low-level request association,
translation/protection and host completion remain unknown. A generic gather,
Pipette ABI or numerical-order capability is not inherited.

The [portable lifecycle helper](../../examples/mechanism-scaffolds/fifer/stage_contract.py)
models finite one-input/one-output stages with output reservations, drain/save/
load switching and independent in-order DRM delivery. Opaque tokens, stable
scheduler ties and payload containers are prototype conventions, not paper
hardware interfaces. It performs no memory access, scalar arithmetic or timing.

```sh
python3 -m unittest discover -s examples/mechanism-scaffolds/fifer -p 'test_*.py'
```

The reference 16 KB queue SRAM is a total per PE, not a capacity per queue.
Two-cycle activation excludes variable loading and draining. A future
implementation must bind compiled stage state, queue allocation, request/output
ownership, physical memory and whole-program completion under the workload's
original numerical oracle.

The [primary binding](primary-binding.json) identifies the cached proceedings
edition, DOI and section locators. The corpus PDF is not duplicated here.
Sections 4 and 5.1–5.5 support the stage/DRM lifecycle and remaining obligations.

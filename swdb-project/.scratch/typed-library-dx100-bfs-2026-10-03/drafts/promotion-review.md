# DX100 promotion review packet

Prepared: 2026-10-03 ET

Current local source commit: `f62401c` on `yanrujhou_main`. This packet is ready for Yan-Ru review; it records no promotion approval.

Normative library content is separate from certification and review records. Functional certification is simulated pre-check evidence. L3/L5 remain Eric-owned visibility assumptions; a real parent-gather companion and completion/execution witnesses still gate timed gem5 runs.

Final candidate receipt: `certification.123997581679463790ac7e9b00f3ed2b`. Ten matrix cells pass; all sixteen controls compile and fail the named checks. Candidate tree: `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`.

| Entry | Current content SHA256 | Derived status | Current certification receipts |
|---|---|---|---|
| `contract.bfs_read_offload` | `867fac18c28938268242e7d4b60049f3c3e97113512a761cc8a763735a77db51` | certified / experimental | `certification.592389e74eb348a5a13af90099eadd6e`, `certification.123997581679463790ac7e9b00f3ed2b`, `certification.778091a729fb4e85a677d96b161f688a` |
| `intrinsic.dxc_alu_scalar` | `12129d01a66be3089c2cff9b7b8444bcd039e31bed34c7b7022e20858961d5dd` | certified / experimental | `certification.f6494a61d8bb4c96899e45f29463a074` |
| `intrinsic.dxc_const_i32` | `d321f3c5d234afa7a41121f923a6e0a0edef51015c4f7ebe3cbe463c0a92950f` | certified / experimental | `certification.3ce440da9ced4acb8315447ef9fd1fba` |
| `intrinsic.dxc_gather` | `f1a54734b19e5223a1b2b11b91d177913ecda7296ce45592acb91412b4c6609d` | certified / experimental | `certification.68d181644cfb4ea38b10543fbea8ad7b` |
| `intrinsic.dxc_range_loop` | `dd2abc9caac3f39254ffa28d254b8308b95f73b496b1fb9a40bb8f570da54f57` | certified / experimental | `certification.d2f2df28e392444ebcff99ebca5b7bee` |
| `intrinsic.dxc_session_begin` | `69f444bf9d4800ebb4b1b29d45496b3cc2f0f49ea404bba4a65ec5343439de91` | certified / experimental | `certification.fe7b205ea86d4bb3b8ca4fde2df05c0d` |
| `intrinsic.dxc_stream_load` | `2deb4038416c9950ab524497a10071c69b5b295f87659d43d0ec24a8313fe79c` | certified / experimental | `certification.a660bf4c01ea415396d29caa4a925088` |
| `intrinsic.dxc_thread_context` | `9a25951c2ee114ff9e1c5265c2da5452bf3f8c5f850c36afeb157b00be0e8e88` | certified / experimental | `certification.0f0445fceae549398e79522fb4263ce5` |
| `intrinsic.dxc_tile_pointer` | `c276531e321c1fdfd12f6730d91e1351e5a864a0214931452e29bae78b10d20e` | certified / experimental | `certification.afefcbfc52d4457fb638061eb5ac7f8f` |
| `intrinsic.dxc_tile_size` | `8072dc02828ab0b865a11bd063b96b7412de71f435a450c1cb156e793f957c06` | certified / experimental | `certification.92223db31dc24d6d95f481f77a0f3423` |
| `intrinsic.dxc_wait` | `e349a9c69489091c35d5cb3654cae16b0b5361f8706fd4c4f21052756cc815de` | certified / experimental | `certification.a246311c98194743b142f3dac3868cae` |
| `lowering.dxc_alu_scalar.dx100-mmio.1.0-e4fc4af` | `5a2a27f42df1cc3d3eca23f5d67de01cb5b2c5c03e1b083926a4324988f09e92` | certified / experimental | `certification.f6494a61d8bb4c96899e45f29463a074` |
| `lowering.dxc_const_i32.dx100-mmio.1.0-e4fc4af` | `dabed65442efa3adc53b64711216da7852cdca9c0adaae64ed5fc0f404b449ee` | certified / experimental | `certification.3ce440da9ced4acb8315447ef9fd1fba` |
| `lowering.dxc_gather.dx100-mmio.1.0-e4fc4af` | `4a81c74e19f3f8ff0d714bcd11b1439d8a7f76d277f6de149f4d898b0c789559` | certified / experimental | `certification.68d181644cfb4ea38b10543fbea8ad7b` |
| `lowering.dxc_range_loop.dx100-mmio.1.0-e4fc4af` | `75b19f47333b0a7f46137c88c2733119d4d7e092161c29ff9645b2f1153a8ae9` | certified / experimental | `certification.d2f2df28e392444ebcff99ebca5b7bee` |
| `lowering.dxc_session_begin.dx100-mmio.1.0-e4fc4af` | `ba2ff29a24c9bc8829479b1e1187e56aaa21cf7fb53a416b4daaadb5763f204b` | certified / experimental | `certification.fe7b205ea86d4bb3b8ca4fde2df05c0d` |
| `lowering.dxc_stream_load.dx100-mmio.1.0-e4fc4af` | `ccd753348b4fa7ffa5a40cf0cefce35ebd9e17fd36b775fc0e4233b0c41861fa` | certified / experimental | `certification.a660bf4c01ea415396d29caa4a925088` |
| `lowering.dxc_thread_context.dx100-mmio.1.0-e4fc4af` | `3523e09c1bd53321f2530daf4a3415b0203f9f8614ad811149075ff5623c9b49` | certified / experimental | `certification.0f0445fceae549398e79522fb4263ce5` |
| `lowering.dxc_tile_pointer.dx100-mmio.1.0-e4fc4af` | `caaa665c9970763bc4f5a17484fa3e17cbe2b109a7a7a2fddfef89a6e2ed32ea` | certified / experimental | `certification.afefcbfc52d4457fb638061eb5ac7f8f` |
| `lowering.dxc_tile_size.dx100-mmio.1.0-e4fc4af` | `59b213f5dbdfb10b7f2b23f22179b2eeca7d6af046fa1132dbb36fb6990497f4` | certified / experimental | `certification.92223db31dc24d6d95f481f77a0f3423` |
| `lowering.dxc_wait.dx100-mmio.1.0-e4fc4af` | `39232bc2edfa22ab000c9b7b26284c36cd7973534379dd2cff97104b0d1c14aa` | certified / experimental | `certification.a246311c98194743b142f3dac3868cae` |

After explicit promotion approval, invoke `swdb promote ENTRY_ID --reviewer "Yan-Ru Jhou"` for each listed entry. Commit the resulting review records and sync them through Git before real ArchEvolve submit.

Review artifacts: `library/dx100/peter-section5.patch`, `library/rewrite_contracts/bfs_read_offload.yaml`, `library/dx100/dxc_lowering.hpp`, and the listed certification records. Raw Mac certification logs remain under `/private/tmp/swdb-typed-library-certification-20261003`; remote measurements have not started.

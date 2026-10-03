# DX100 promotion review packet

Prepared: 2026-10-03 ET

Source review base: `ed8c233` on `yanrujhou_main`, with the reviewed certification and admission fixes in this batch. This packet records no promotion approval.

Normative library content is separate from certification and review records. Functional certification is simulated pre-check evidence. L3/L5 remain Eric-owned visibility assumptions; a real parent-gather companion and completion/execution witnesses still gate timed gem5 runs.

Fresh candidate receipt: `certification.1e4397e31d594245bc10bd80ff2107f5`. Ten matrix cells pass; all sixteen controls compile and fail the named checks. Candidate tree: `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`.

Pinned differential driver SHA256: `5a30fd75e7a23db709eb7e112d9202f46037cadc8b8c9d667ac472fd77f5e976`. Every receipt binds the complete referenced normative dependency closure and checks it before and after execution. Lowering certification compiles each declared lowering, driver, reference and build definition; unsupported inputs fail before evidence publication.

| Entry | Current content SHA256 | Derived status | Fresh certification receipts |
|---|---|---|---|
| `contract.bfs_read_offload` | `867fac18c28938268242e7d4b60049f3c3e97113512a761cc8a763735a77db51` | certified / experimental | `certification.1e4397e31d594245bc10bd80ff2107f5` |
| `intrinsic.dxc_alu_scalar` | `12129d01a66be3089c2cff9b7b8444bcd039e31bed34c7b7022e20858961d5dd` | certified / experimental | `certification.fc8bcfd86d8c4e21bc66be6dc044535e` |
| `intrinsic.dxc_const_i32` | `d321f3c5d234afa7a41121f923a6e0a0edef51015c4f7ebe3cbe463c0a92950f` | certified / experimental | `certification.0de8b857162d4dc4b4d72336781db02e` |
| `intrinsic.dxc_gather` | `f1a54734b19e5223a1b2b11b91d177913ecda7296ce45592acb91412b4c6609d` | certified / experimental | `certification.11e7041c95624345ac35316a1a4bcafb` |
| `intrinsic.dxc_range_loop` | `dd2abc9caac3f39254ffa28d254b8308b95f73b496b1fb9a40bb8f570da54f57` | certified / experimental | `certification.bc94a00c855042d08cfd383cfe2f1670` |
| `intrinsic.dxc_session_begin` | `69f444bf9d4800ebb4b1b29d45496b3cc2f0f49ea404bba4a65ec5343439de91` | certified / experimental | `certification.9ce48662688647ccb09eca6271349f75` |
| `intrinsic.dxc_stream_load` | `2deb4038416c9950ab524497a10071c69b5b295f87659d43d0ec24a8313fe79c` | certified / experimental | `certification.d7adaf7c83724487b59392be50bb49fd` |
| `intrinsic.dxc_thread_context` | `9a25951c2ee114ff9e1c5265c2da5452bf3f8c5f850c36afeb157b00be0e8e88` | certified / experimental | `certification.fc354b152c9042819e609056da8e43c4` |
| `intrinsic.dxc_tile_pointer` | `c276531e321c1fdfd12f6730d91e1351e5a864a0214931452e29bae78b10d20e` | certified / experimental | `certification.f5e5e20bb3ad4e1c9c1721884a609965` |
| `intrinsic.dxc_tile_size` | `8072dc02828ab0b865a11bd063b96b7412de71f435a450c1cb156e793f957c06` | certified / experimental | `certification.21b2df44e91b48de806573ad68c25718` |
| `intrinsic.dxc_wait` | `e349a9c69489091c35d5cb3654cae16b0b5361f8706fd4c4f21052756cc815de` | certified / experimental | `certification.aea67a73afc7444095e975dad79d9fb5` |
| `lowering.dxc_alu_scalar.dx100-mmio.1.0-e4fc4af` | `16c16390e9fb10b2a9a33db7c5ea629cfe778297730717d4db9e66dc79e9b064` | certified / experimental | `certification.fc8bcfd86d8c4e21bc66be6dc044535e` |
| `lowering.dxc_const_i32.dx100-mmio.1.0-e4fc4af` | `e4916a2ec1bbb672ce27b6c4ef52a10a38e19458c914d09bb9e0c0969eea5bcf` | certified / experimental | `certification.0de8b857162d4dc4b4d72336781db02e` |
| `lowering.dxc_gather.dx100-mmio.1.0-e4fc4af` | `3ad324abd6d51613450786e617deafad181831cb82be867ae479968374a2a8f9` | certified / experimental | `certification.11e7041c95624345ac35316a1a4bcafb` |
| `lowering.dxc_range_loop.dx100-mmio.1.0-e4fc4af` | `683c4ecb61a61ea24de68930b11b40bc8a987465d3ec39cf6e1330af6b2a3831` | certified / experimental | `certification.bc94a00c855042d08cfd383cfe2f1670` |
| `lowering.dxc_session_begin.dx100-mmio.1.0-e4fc4af` | `8584f0c4b2358692e6f76be3d653ee461baa8addaab8a9fd15788a3382984569` | certified / experimental | `certification.9ce48662688647ccb09eca6271349f75` |
| `lowering.dxc_stream_load.dx100-mmio.1.0-e4fc4af` | `bfd124d6ce44b13ab96c3f4bb1d8b640aca4ade018ef007138004abc9b5f5f53` | certified / experimental | `certification.d7adaf7c83724487b59392be50bb49fd` |
| `lowering.dxc_thread_context.dx100-mmio.1.0-e4fc4af` | `3dd51312fd5d6bc55939b475163bb881ccfc0b68335b060d24a16d12b48dff3e` | certified / experimental | `certification.fc354b152c9042819e609056da8e43c4` |
| `lowering.dxc_tile_pointer.dx100-mmio.1.0-e4fc4af` | `842531eb06ab38e5c79eecceaf36b536d690d2c2be580f94949b727429c8b7dc` | certified / experimental | `certification.f5e5e20bb3ad4e1c9c1721884a609965` |
| `lowering.dxc_tile_size.dx100-mmio.1.0-e4fc4af` | `91a183168d5adb02cf9ee7eefbbeb396615dec36d4b8ec0ebce88c0c42c5b323` | certified / experimental | `certification.21b2df44e91b48de806573ad68c25718` |
| `lowering.dxc_wait.dx100-mmio.1.0-e4fc4af` | `d0cda6d52b5a86f3d53f8c4af12be8a8eac3c64fdcd37244ed35d70735acaae2` | certified / experimental | `certification.aea67a73afc7444095e975dad79d9fb5` |

After explicit promotion approval, invoke `swdb promote ENTRY_ID --reviewer "Yan-Ru Jhou"` for each listed entry. Fixture receipts and unrelated reviewers cannot grant shared admission. Commit the resulting review records and sync them through Git before real ArchEvolve submit.

Review artifacts: `library/dx100/peter-section5.patch`, `library/rewrite_contracts/bfs_read_offload.yaml`, `library/dx100/dxc_lowering.hpp`, and the listed certification records. Raw Mac certification logs remain under `/private/tmp/swdb-typed-library-certification-20261003`; remote measurements have not started.

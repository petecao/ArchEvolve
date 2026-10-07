# SMASH bitmap block-index assistance

SMASH (MICRO 2019) uses hierarchical bitmaps to locate represented matrix
blocks efficiently. The bitmap-management unit (BMU) traverses set bits depth
first and combines per-level indices into an original matrix block row/column.
Groups retain separate bitmap SRAM, configuration and output registers.
`PBMAP` advances the scan; `RDIND` reads the current block coordinates. The CPU
separately maintains NZA block rank, loads operands and performs arithmetic.

Revision 0.1.15 adds the explicit assist-only `smash_bitmap_block_index`
mapping, six located primary claims and six mechanism annotations. A
represented NZA block can contain zero-valued lanes: block presence supplies
no per-lane nonzero predicate. This record grants no generic gather return,
arithmetic datatype, coordinate width or ordered FP capability. SMASH is an
older MICRO 2019 implementation reference.

The [portable bitmap helper](../../examples/mechanism-scaffolds/smash/bitmap_contract.py)
checks a normalized finite bit-list hierarchy, compact child-block ownership,
original block geometry and NZA rank. It rejects orphan child blocks, extent
padding bits and incomplete logical NZA blocks. Partial higher-level groups
require zero unused bits. Group/generation identity is retained, and repeated
`rdind` reads preserve the current descriptor.

The normalized representation is not actual bitmap byte packing or BMU RTL.
Its finite bounds and end-of-stream return are helper conventions, not hardware
EOF, width or completion claims. It reads no matrix payload and computes no
arithmetic. Actual ratio units, SRAM footprints, buffer transport, coordinate
ABI, address translation/protection and kernel completion require separate proof.

```sh
python3 -m unittest discover -s examples/mechanism-scaffolds/smash -p 'test_*.py'
```

The [primary binding](primary-binding.json) identifies the cached 15-page
proceedings edition by hash and DOI without duplicating the corpus PDF. Catalog
locators cover sections 4.1–4.3 and 5, physical PDF pages 5–8, Table 1 and
Algorithms 1–2. The 256-byte bitmap buffers are an examined reference, not a
universal selected capacity.

The [public implementation binding](public-source/README.md) identifies the
official software snapshot and separates native CTZ indexing from external SIM
instrumentation. It documents the reviewed zero-CTZ guard and remaining consumer,
initialization and BMU-handler obligations without changing the paper capability.

The [block-lane consumer witness](consumer-fixture.md) compares the printed
Algorithm 1 indexing expression with a declared flat-block layout. Its corrected
coordinate calculation is a conditional consumer obligation, not an authenticated
public implementation repair. Run it together with the HTA witness from the root:

```sh
python3 examples/mechanism-scaffolds/run_consumer_fixtures.py --output-dir /tmp/new-consumer-fixtures
```

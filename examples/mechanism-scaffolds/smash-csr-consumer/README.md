# SMASH CSR admission and consumer boundary

An opt-in CSR structural admission entry and a separate one-comparison public consumer repair. Catalog capabilities are unchanged. No upstream source tree is redistributed.

Supply the exact private bitmap header from the earlier source-repair batch and the exact public consumer named in its source receipt. Outputs must be fresh private directories.

```sh
python3 examples/mechanism-scaffolds/smash-csr-consumer/smash_public_csr_input_admission_2026_10_07/materialize.py --parent EXACT_BITMAP_H --geometry EXACT_GEOMETRY_H --output NEW_CSR_PACKAGE
python3 examples/mechanism-scaffolds/smash-csr-consumer/smash_public_consumer_row_boundary_2026_10_07/materialize.py --source EXACT_PUBLIC_SPMV_C --output NEW_CONSUMER_PACKAGE
```

CSR callers include construct_csr_admitted.h after the original types/constructor and supply trusted row/column/value prefix counts and original declared nnz. Structural and unsupported bitmap-domain ordering failures reject before constructor mutation. Positive-size empty matrices are supported; zero-size matrices reject. This does not make the original parser retain trustworthy lengths or initialize values/NZA.

The consumer changes only j > columns to j >= columns, preventing the next vector access at the exact row boundary. Integer/symbolic fixtures establish this control path, not numerical kernel correctness. Assignment versus accumulation, indexer completion and NZA initialization remain separate.

Source-bound fixture extractors and executed receipts are included. CSR README/materializer are the exact dc18cdec tested revision; later unsealed packaging edits are excluded. Extracted third-party bodies stay in private outputs.

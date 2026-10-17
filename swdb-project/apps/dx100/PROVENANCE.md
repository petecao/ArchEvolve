# DX100 source snapshot

Date: 2026-09-25

Unmodified source subset from https://github.com/arkhadem/DX100 at commit
`e4fc4afdf894f295442cef3604667a469fab8e62`. Copied from the locally inspected
checkout at that exact HEAD. `SHA256SUMS` identifies every copied file.

The original paths of the GAPBS source, API, and gem5 headers are retained.
The full simulator, generated m5 objects, and external runtime are not vendored.
`-DFUNC` without `-DMAA` selects the scalar top-down native BFS path while using
the artifact API setup. This is not evidence of accelerator execution or
correctness. Native evaluation and simulated evaluation require separate records.

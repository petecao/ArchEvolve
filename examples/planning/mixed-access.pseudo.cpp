// Synthetic illustration of selected target loads, not a runnable benchmark.
// Bounds, array lifetime, index-production cost and CPU effects need a real harness.
// B/D loads and index arithmetic remain host responsibilities in this sketch.
#error "Illustrative source for capability planning only"
for (int i = 0; i < n; ++i) {
    int a = A[B[i]];
    int c = C[D[2 * i + 1]];
    float x = X[i];
    float y = Y[i + 2];
    consume_on_cpu(a, c, x, y);
}

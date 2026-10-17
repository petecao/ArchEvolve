// Evaluator-owned compiled BFS structural verifier: swdb.bfs.structural.compiled.v2.
// Created 2026-10-04 ET (ticket 63, decision of ticket 61 option 1).
//
// Exactly the criterion of swdb.bfs_native.verify_parents (swdb.bfs.structural.v1),
// in the same check order and with the same first-failure reasons, over a registered
// GAPBS SG file (mmap, read-only) and a little-endian int32 parent vector file:
//   1. source in [0, n)                        "source outside graph"
//   2. parent vector has exactly n entries     "parent vector length differs from vertex count"
//   3. every parent in [-1, n)                 "parent[v] is not an integer in [-1, n)"
//   4. parent[source] == source                "source must be its own parent"
//   5. BFS depths from source over the outgoing CSR; then, per vertex v in order:
//      unreachable v has parent -1; reachable v != source has a parent p >= 0,
//      the edge p -> v exists, and depth[p] + 1 == depth[v].
// Output (stdout): one JSON object, {"passed":true,"reason":null,"reachable_vertices":N}
// or {"passed":false,"reason":"..."}; exit 0 for either verdict. Exit 3 means the
// verifier could not run (malformed or oversized SG input, I/O failure): no verdict.
//
// Limits (memory-bounded, sized for scale 22): n <= 2^23 vertices, m <= 2^28 directed
// edges, SG file <= 3 GiB. Heap use is about 9 bytes per vertex (depth, queue,
// parent-edge flags); the SG file and the parent vector are mapped read-only.
// Build: -std=c++11 -O2 (no -ffast-math; integer-only code).
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

namespace {

const uint64_t kMaxVertices = uint64_t(1) << 23;
const uint64_t kMaxEdges = uint64_t(1) << 28;
const uint64_t kMaxSgBytes = uint64_t(3) << 30;

struct Infrastructure : std::runtime_error {
  explicit Infrastructure(const std::string& m) : std::runtime_error(m) {}
};

void require(bool ok, const char* message) {
  if (!ok) throw Infrastructure(message);
}

struct Mapping {
  int fd = -1;
  void* data = MAP_FAILED;
  size_t size = 0;
  ~Mapping() {
    if (data != MAP_FAILED && size) munmap(data, size);
    if (fd >= 0) close(fd);
  }
  // Opens a regular file; maps it only when its size passes `expected` (or any size
  // within `limit` when expected is UINT64_MAX). Returns false when the size differs
  // from `expected`, without mapping.
  bool open_file(const char* path, uint64_t limit, uint64_t expected) {
    fd = open(path, O_RDONLY | O_NOFOLLOW);
    require(fd >= 0, "cannot open input");
    struct stat st;
    require(fstat(fd, &st) == 0 && S_ISREG(st.st_mode), "input must be a regular file");
    if (expected != UINT64_MAX && uint64_t(st.st_size) != expected) return false;
    require(uint64_t(st.st_size) <= limit, "input exceeds the verifier's 3 GiB limit");
    size = size_t(st.st_size);
    require(size > 0, "input is empty");
    data = mmap(nullptr, size, PROT_READ, MAP_PRIVATE, fd, 0);
    require(data != MAP_FAILED, "cannot map input");
    return true;
  }
};

uint64_t read_le(const unsigned char* p, unsigned width) {
  uint64_t value = 0;
  for (unsigned b = 0; b < width; ++b) value |= uint64_t(p[b]) << (8 * b);
  return value;
}

struct Csr {
  uint64_t n = 0, m = 0;
  unsigned width = 0;
  const unsigned char* offsets = nullptr;     // (n+1) * width bytes
  const unsigned char* neighbors = nullptr;   // m * 4 bytes
  uint64_t offset(uint64_t u) const { return read_le(offsets + u * width, width); }
  int64_t neighbor(uint64_t e) const {
    return int64_t(int32_t(uint32_t(read_le(neighbors + e * 4, 4))));
  }
};

// Header, exact size, limits, monotone in-range offsets and in-range neighbors.
// Full SG equivalence (sortedness, symmetry, inverse) was proven at registration by
// tools/bfs_native/sg_identity.cc; the evaluator binds this file to that registration
// by its SHA-256 before every trial. These checks only keep every read in bounds.
Csr parse_sg(const Mapping& sg, unsigned width) {
  require(width == 4 || width == 8, "offset width must be four or eight");
  const unsigned char* data = static_cast<const unsigned char*>(sg.data);
  require(sg.size >= 1 + 2 * width && data[0] <= 1, "invalid SG header");
  bool directed = data[0] == 1;
  uint64_t m = read_le(data + 1, width), n = read_le(data + 1 + width, width);
  uint64_t sign = uint64_t(1) << (8 * width - 1);
  require(!(m & sign) && !(n & sign), "negative SG dimension");
  require(n >= 1 && n <= kMaxVertices, "SG vertex count outside the verifier limit (1..2^23)");
  require(m <= kMaxEdges, "SG directed edge count exceeds the verifier limit (2^28)");
  uint64_t block = (n + 1) * width + m * 4;
  require(1 + 2 * uint64_t(width) + block * (directed ? 2 : 1) == sg.size, "truncated or trailing SG data");
  Csr csr;
  csr.n = n; csr.m = m; csr.width = width;
  csr.offsets = data + 1 + 2 * width;
  csr.neighbors = csr.offsets + (n + 1) * width;
  require(csr.offset(0) == 0 && csr.offset(n) == m, "invalid SG CSR endpoints");
  uint64_t previous = 0;
  for (uint64_t u = 1; u <= n; ++u) {
    uint64_t current = csr.offset(u);
    require(current >= previous && current <= m, "invalid SG CSR offsets");
    previous = current;
  }
  for (uint64_t e = 0; e < m; ++e) {
    int64_t v = csr.neighbor(e);
    require(v >= 0 && uint64_t(v) < n, "SG neighbor outside graph");
  }
  return csr;
}

void verdict_fail(const std::string& reason) {
  std::string out = "{\"passed\":false,\"reason\":\"";
  for (char c : reason) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  out += "\"}\n";
  std::fputs(out.c_str(), stdout);
}

int verify(const Csr& g, int64_t source, const char* parents_path) {
  const int64_t n = int64_t(g.n);
  if (source < 0 || source >= n) { verdict_fail("source outside graph"); return 0; }
  Mapping parents_file;
  if (!parents_file.open_file(parents_path, UINT64_MAX, uint64_t(n) * 4)) {
    verdict_fail("parent vector length differs from vertex count");
    return 0;
  }
  const unsigned char* raw = static_cast<const unsigned char*>(parents_file.data);
  std::vector<int32_t> parent(static_cast<size_t>(n));
  for (int64_t v = 0; v < n; ++v) {
    int64_t p = int64_t(int32_t(uint32_t(read_le(raw + v * 4, 4))));
    if (p < -1 || p >= n) {
      verdict_fail("parent[" + std::to_string(v) + "] is not an integer in [-1, n)");
      return 0;
    }
    parent[size_t(v)] = int32_t(p);
  }
  if (parent[size_t(source)] != source) { verdict_fail("source must be its own parent"); return 0; }
  std::vector<int32_t> depth(static_cast<size_t>(n), -1);
  std::vector<int32_t> queue(static_cast<size_t>(n));
  size_t head = 0, tail = 0;
  depth[size_t(source)] = 0;
  queue[tail++] = int32_t(source);
  while (head < tail) {
    int64_t u = queue[head++];
    for (uint64_t e = g.offset(uint64_t(u)), end = g.offset(uint64_t(u) + 1); e < end; ++e) {
      int64_t v = g.neighbor(e);
      if (depth[size_t(v)] == -1) {
        depth[size_t(v)] = depth[size_t(u)] + 1;
        queue[tail++] = int32_t(v);
      }
    }
  }
  std::vector<unsigned char> parent_edge(static_cast<size_t>(n), 0);
  for (int64_t u = 0; u < n; ++u) {
    for (uint64_t e = g.offset(uint64_t(u)), end = g.offset(uint64_t(u) + 1); e < end; ++e) {
      int64_t v = g.neighbor(e);
      if (parent[size_t(v)] == u) parent_edge[size_t(v)] = 1;
    }
  }
  int64_t reachable = 0;
  for (int64_t v = 0; v < n; ++v) {
    int32_t d = depth[size_t(v)];
    int32_t p = parent[size_t(v)];
    if (d == -1) {
      if (p != -1) { verdict_fail("unreachable vertex " + std::to_string(v) + " has a parent"); return 0; }
    } else {
      ++reachable;
      if (v != source) {
        if (p < 0) { verdict_fail("reachable vertex " + std::to_string(v) + " has no parent"); return 0; }
        if (!parent_edge[size_t(v)]) { verdict_fail("parent edge absent for vertex " + std::to_string(v)); return 0; }
        if (depth[size_t(p)] + 1 != d) { verdict_fail("parent depth is wrong for vertex " + std::to_string(v)); return 0; }
      }
    }
  }
  std::printf("{\"passed\":true,\"reason\":null,\"reachable_vertices\":%lld}\n", static_cast<long long>(reachable));
  return 0;
}

int64_t parse_integer(const char* text) {
  require(text && *text, "empty integer argument");
  errno = 0;
  char* end = nullptr;
  long long value = std::strtoll(text, &end, 10);
  require(errno == 0 && end && *end == '\0', "invalid integer argument");
  return int64_t(value);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    require(argc == 5, "usage: bfs_verify SG_FILE OFFSET_BYTES SOURCE PARENTS_FILE");
    int64_t width = parse_integer(argv[2]);
    int64_t source = parse_integer(argv[3]);
    Mapping sg;
    sg.open_file(argv[1], kMaxSgBytes, UINT64_MAX);
    Csr g = parse_sg(sg, unsigned(width == 4 || width == 8 ? width : 0));
    int code = verify(g, source, argv[4]);
    std::fflush(stdout);
    require(!std::ferror(stdout), "verdict write failed");
    return code;
  } catch (const std::exception& error) {
    std::fprintf(stderr, "SWDB verifier failure: %s\n", error.what());
    return 3;
  }
}

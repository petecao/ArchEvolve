// Exact, bounded-memory GAPBS SG validation and canonical JSON streaming.
// Updated 2026-09-25. No graph-sized heap allocation; mapped input is read-only.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

static void require(bool ok, const char* message) {
  if (!ok) throw std::runtime_error(message);
}

struct Graph {
  const unsigned char* data;
  size_t size;
  unsigned width;
  uint64_t n, m, header, block;
  bool directed;
  uint64_t integer(uint64_t pos, unsigned bytes) const {
    require(pos <= size && bytes <= size - pos, "truncated SG integer");
    uint64_t result = 0;
    for (unsigned b = 0; b < bytes; ++b) result |= uint64_t(data[pos+b]) << (8*b);
    require(!(result & (uint64_t(1) << (8*bytes-1))), "negative SG integer");
    return result;
  }
  uint64_t offset(uint64_t base, uint64_t u) const { return integer(base + u*width, width); }
  uint64_t neighbor(uint64_t base, uint64_t e) const {
    return integer(base + (n+1)*width + e*4, 4);
  }
  bool contains(uint64_t base, uint64_t u, uint64_t v) const {
    uint64_t lo = offset(base, u), hi = offset(base, u+1);
    while (lo < hi) {
      uint64_t mid = lo + (hi-lo)/2;
      if (neighbor(base, mid) < v) lo = mid+1; else hi = mid;
    }
    return lo < offset(base, u+1) && neighbor(base, lo) == v;
  }
  void validate_csr(uint64_t base) const {
    require(offset(base, 0) == 0 && offset(base, n) == m, "invalid SG CSR endpoints");
    for (uint64_t u = 0; u < n; ++u) {
      uint64_t begin = offset(base, u), end = offset(base, u+1);
      require(begin <= end && end <= m, "invalid SG CSR offsets");
      uint64_t previous = 0;
      for (uint64_t e = begin; e < end; ++e) {
        uint64_t v = neighbor(base, e);
        require(v < n && v != u, "SG neighbor is outside graph or a self loop");
        require(e == begin || previous < v, "SG adjacency must already be sorted and deduplicated");
        previous = v;
      }
    }
  }
  void run() {
    require(size >= 1 + 2*width && data[0] <= 1, "invalid SG header");
    directed = data[0]; header = 1 + 2*width;
    m = integer(1, width); n = integer(1+width, width);
    require(n > 0 && n <= uint64_t(std::numeric_limits<int32_t>::max()), "invalid SG vertex count");
    // n is bounded by the on-disk int32 vertex ID. Check every multiplication.
    require(m <= (std::numeric_limits<uint64_t>::max() - (n+1)*width)/4,
            "SG dimensions overflow");
    block = (n+1)*width + m*4;
    require(block <= (size-header)/(directed ? 2 : 1)
            && header + block*(directed ? 2 : 1) == size, "truncated or trailing SG data");
    validate_csr(header);
    if (directed) validate_csr(header+block);
    uint64_t opposite = directed ? header+block : header;
    uint64_t minimum = m, maximum = 0, isolated = 0;
    // Distinct rows and equal edge counts make this membership check exact:
    // outgoing is a subset of transpose(opposite), both containing m edges.
    for (uint64_t u = 0; u < n; ++u) {
      uint64_t begin = offset(header, u), end = offset(header, u+1), degree = end-begin;
      minimum = std::min(minimum, degree); maximum = std::max(maximum, degree);
      if (!degree && offset(opposite, u) == offset(opposite, u+1)) ++isolated;
      for (uint64_t e = begin; e < end; ++e) {
        require(contains(opposite, neighbor(header, e), u),
                directed ? "SG inverse adjacency does not match outgoing edges" : "undirected SG adjacency is not symmetric");
      }
    }
    std::fputs("{\"adjacency\":[", stdout);
    for (uint64_t u = 0; u < n; ++u) {
      if (u) std::fputc(',', stdout);
      std::fputc('[', stdout);
      uint64_t begin = offset(header, u), end = offset(header, u+1);
      for (uint64_t e = begin; e < end; ++e) {
        if (e != begin) std::fputc(',', stdout);
        std::fprintf(stdout, "%llu", static_cast<unsigned long long>(neighbor(header, e)));
      }
      std::fputc(']', stdout);
    }
    std::fprintf(stdout, "],\"directed\":%s,\"format\":\"swdb.bfs.adjacency.v1\",\"num_vertices\":%llu}",
                 directed ? "true" : "false", static_cast<unsigned long long>(n));
    require(!std::ferror(stdout), "canonical stream write failed");
    std::fprintf(stderr, "{\"num_vertices\":%llu,\"num_directed_edges\":%llu,\"directed\":%s,\"isolated_vertices\":%llu,\"minimum_out_degree\":%llu,\"maximum_out_degree\":%llu}\n",
                 static_cast<unsigned long long>(n), static_cast<unsigned long long>(m), directed ? "true" : "false",
                 static_cast<unsigned long long>(isolated), static_cast<unsigned long long>(minimum), static_cast<unsigned long long>(maximum));
  }
};

int main(int argc, char** argv) {
  int fd = -1; void* mapping = MAP_FAILED; size_t size = 0;
  try {
    require(argc == 3, "usage: sg_identity FILE OFFSET_BYTES");
    unsigned width = unsigned(std::strtoul(argv[2], nullptr, 10));
    require(width == 4 || width == 8, "offset width must be four or eight");
    fd = open(argv[1], O_RDONLY | O_NOFOLLOW);
    require(fd >= 0, "cannot open SG input");
    struct stat st; require(fstat(fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_size > 0, "SG input must be a nonempty regular file");
    require(uint64_t(st.st_size) <= std::numeric_limits<size_t>::max(), "SG input exceeds address space");
    size = size_t(st.st_size);
    mapping = mmap(nullptr, size, PROT_READ, MAP_PRIVATE, fd, 0);
    require(mapping != MAP_FAILED, "cannot map SG input");
    Graph g{static_cast<const unsigned char*>(mapping), size, width}; g.run();
    munmap(mapping, size); close(fd); return 0;
  } catch (const std::exception& exc) {
    std::fprintf(stderr, "SG validation failed: %s\n", exc.what());
    if (mapping != MAP_FAILED) munmap(mapping, size);
    if (fd >= 0) close(fd);
    return 1;
  }
}

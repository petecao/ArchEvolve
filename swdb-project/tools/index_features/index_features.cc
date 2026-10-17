// index_features: exact index-stream features of a gapbs graph.
// Created 2026-09-22 (Eastern). See README.md in this folder for the contract.
//
// Builds the graph with gapbs's own Builder (so it is exactly the graph the
// kernel sees), walks the neighbor-ID ("index") stream in the visit order of
// the chosen --order, and prints one JSON object. Serial; no OpenMP needed.
//
// Build (from the repo root):
//   c++ -std=c++11 -O3 -Wall -I apps/gapbs/src
//       tools/index_features/index_features.cc -o index_features
// Build with the same C++ standard library as the kernel binary: gapbs's
// Kronecker generator relabels vertices with std::shuffle, whose output
// differs between libstdc++ and libc++ (see README.md).

#include <unistd.h>

#include <algorithm>
#include <cerrno>
#include <cinttypes>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

#include "benchmark.h"
#include "builder.h"
#include "command_line.h"
#include "graph.h"
#include "pvector.h"

namespace {

const int kToolVersion = 1;
const char kLineMapping[] =
    "line = floor(index*element_bytes/line_bytes), array assumed line-aligned";

void Die(const std::string &msg) {
  std::fflush(stdout);
  std::cout.flush();
  std::fprintf(stderr, "index_features: error: %s\n", msg.c_str());
  std::exit(2);
}

void PrintUsage(FILE *f) {
  std::fprintf(f,
      "usage: index_features [--order ORDER] [--element-bytes N] "
      "[--line-bytes N] [--out PATH|-] -- <gapbs graph args>\n"
      "  --order          in_neighbors_by_vertex (default) | "
      "out_neighbors_by_vertex\n"
      "  --element-bytes  bytes per element of the target array (default 4)\n"
      "  --line-bytes     cache-line size in bytes (default 64)\n"
      "  --out            JSON output file, or - for stdout (default -)\n"
      "  gapbs graph args: -g <scale> | -u <scale> | -f <file>, "
      "[-k <degree>] [-s] [-m]\n"
      "example: index_features --order in_neighbors_by_vertex -- -g 16 -k 16\n");
}

bool ParsePositiveInt(const char *s, int64_t max_value, int64_t *out) {
  if (s == nullptr || *s == '\0')
    return false;
  errno = 0;
  char *end = nullptr;
  long long v = std::strtoll(s, &end, 10);
  if (errno != 0 || end == s || *end != '\0' || v < 1 || v > max_value)
    return false;
  *out = static_cast<int64_t>(v);
  return true;
}

// gapbs's CLBase ignores unknown options and uses atoi(); this subclass makes
// bad graph arguments fatal instead of silently producing some other graph.
class CLIndexFeatures : public CLBase {
 public:
  CLIndexFeatures(int argc, char **argv) : CLBase(argc, argv, "index_features"),
                                          bad_(false) {}

  void HandleArg(signed char opt, char *opt_arg) override {
    int64_t v = 0;
    switch (opt) {
      case 'g':
      case 'u':
        if (!ParsePositiveInt(opt_arg, 30, &v)) {
          bad_ = true;
          bad_msg_ = std::string("-") + static_cast<char>(opt) +
                     " needs an integer scale in [1, 30], got '" +
                     (opt_arg ? opt_arg : "") + "'";
          return;
        }
        break;
      case 'k':
        if (!ParsePositiveInt(opt_arg, 1 << 20, &v)) {
          bad_ = true;
          bad_msg_ = std::string("-k needs a positive integer degree, got '") +
                     (opt_arg ? opt_arg : "") + "'";
          return;
        }
        break;
      case 'h':
        bad_ = true;
        bad_msg_ = "-h is not supported after --; use index_features --help";
        return;
      case '?':
      case ':':
        bad_ = true;
        bad_msg_ = "unknown or incomplete gapbs graph option after --";
        return;
      default:
        break;
    }
    CLBase::HandleArg(opt, opt_arg);
  }

  bool bad() const { return bad_; }
  const std::string &bad_msg() const { return bad_msg_; }

 private:
  bool bad_;
  std::string bad_msg_;
};

// gapbs prints timing and diagnostics to stdout; while it runs, stdout is
// pointed at stderr so the JSON on stdout (with --out -) stays clean.
class StdoutToStderr {
 public:
  StdoutToStderr() {
    std::fflush(stdout);
    std::cout.flush();
    saved_ = dup(STDOUT_FILENO);
    if (saved_ < 0 || dup2(STDERR_FILENO, STDOUT_FILENO) < 0)
      Die("cannot redirect stdout during graph build");
  }
  ~StdoutToStderr() {
    std::fflush(stdout);
    std::cout.flush();
    dup2(saved_, STDOUT_FILENO);
    close(saved_);
  }

 private:
  int saved_;
};

// Fenwick tree over stream positions 1..n; each entry is 0 or 1 (a "mark" on
// the latest position of each distinct value), so int32 counts suffice.
class Fenwick {
 public:
  explicit Fenwick(int64_t n) : n_(n), t_(static_cast<size_t>(n + 1), 0) {}
  void Add(int64_t i, int32_t delta) {  // i is 1-based
    for (; i <= n_; i += i & (-i))
      t_[static_cast<size_t>(i)] += delta;
  }
  int64_t Prefix(int64_t i) const {  // sum of entries 1..i
    int64_t s = 0;
    for (; i > 0; i -= i & (-i))
      s += t_[static_cast<size_t>(i)];
    return s;
  }
  void Clear() { std::fill(t_.begin(), t_.end(), 0); }

 private:
  int64_t n_;
  std::vector<int32_t> t_;
};

int BucketOf(int64_t d) {  // 0 -> 0; d >= 1 -> bit length of d
  int b = 0;
  while (d > 0) {
    ++b;
    d >>= 1;
  }
  return b;
}

struct ReuseResult {
  int64_t cold = 0;                 // first accesses (= distinct values)
  std::vector<int64_t> buckets;     // log2 buckets of reuse distance
};

// Exact reuse distance (distinct values strictly between consecutive accesses
// to the same value) for the stream value(i[0]), ..., value(i[L-1]).
// Marks sit on the latest position of each value seen so far; since nothing
// is marked at or after the current position k, the marks in (p, k) are
// total_marks - Prefix(p).
template <typename WalkT, typename MapT>
ReuseResult ReuseHistogram(WalkT walk, MapT value_of, int64_t num_values,
                           int64_t length, Fenwick *bit) {
  ReuseResult r;
  std::vector<int64_t> last(static_cast<size_t>(num_values), -1);
  bit->Clear();
  int64_t k = 0;         // 0-based position in the stream
  int64_t marks = 0;
  walk([&](int64_t index) {
    int64_t x = value_of(index);
    int64_t p = last[static_cast<size_t>(x)];
    if (p < 0) {
      ++r.cold;
      ++marks;
    } else {
      int64_t d = marks - bit->Prefix(p + 1);
      int b = BucketOf(d);
      if (static_cast<size_t>(b) >= r.buckets.size())
        r.buckets.resize(static_cast<size_t>(b) + 1, 0);
      ++r.buckets[static_cast<size_t>(b)];
      bit->Add(p + 1, -1);
    }
    bit->Add(k + 1, 1);
    last[static_cast<size_t>(x)] = k;
    ++k;
  });
  if (k != length)
    Die("internal error: stream length changed between passes");
  return r;
}

// Shortest of %.15g / %.16g / %.17g that reads back as the same double.
std::string Ratio(double x) {
  char buf[64];
  for (int prec = 15; prec <= 17; ++prec) {
    std::snprintf(buf, sizeof(buf), "%.*g", prec, x);
    if (std::strtod(buf, nullptr) == x)
      break;
  }
  std::string s(buf);
  if (s.find_first_of(".eEn") == std::string::npos)
    s += ".0";
  return s;
}

std::string Int(int64_t x) {
  char buf[32];
  std::snprintf(buf, sizeof(buf), "%" PRId64, x);
  return std::string(buf);
}

std::string BucketsJson(const std::vector<int64_t> &buckets) {
  std::string s = "[";
  for (size_t b = 0; b < buckets.size(); ++b) {
    int64_t lo = (b == 0) ? 0 : (int64_t(1) << (b - 1));
    int64_t hi = (b == 0) ? 0 : (int64_t(1) << b) - 1;
    if (b > 0)
      s += ", ";
    s += "{\"bucket\": " + Int(static_cast<int64_t>(b)) + ", \"lo\": " +
         Int(lo) + ", \"hi\": " + Int(hi) + ", \"count\": " +
         Int(buckets[b]) + "}";
  }
  return s + "]";
}

}  // namespace


int main(int argc, char *argv[]) {
  std::string order = "in_neighbors_by_vertex";
  int64_t element_bytes = 4;
  int64_t line_bytes = 64;
  std::string out_path = "-";

  int i = 1;
  bool saw_sep = false;
  for (; i < argc; ++i) {
    std::string a = argv[i];
    if (a == "--") {
      saw_sep = true;
      ++i;
      break;
    }
    if (a == "--help" || a == "-h") {
      PrintUsage(stdout);
      return 0;
    }
    if (a == "--order" || a == "--element-bytes" || a == "--line-bytes" ||
        a == "--out") {
      if (i + 1 >= argc)
        Die(a + " needs a value");
      const char *val = argv[++i];
      if (a == "--order") {
        order = val;
      } else if (a == "--element-bytes") {
        if (!ParsePositiveInt(val, 1 << 20, &element_bytes))
          Die(std::string("--element-bytes needs a positive integer, got '") +
              val + "'");
      } else if (a == "--line-bytes") {
        if (!ParsePositiveInt(val, 1 << 20, &line_bytes))
          Die(std::string("--line-bytes needs a positive integer, got '") +
              val + "'");
      } else {
        out_path = val;
        if (out_path.empty())
          Die("--out needs a path or -");
      }
      continue;
    }
    Die("unknown option '" + a + "' (tool options come before --)");
  }
  if (!saw_sep)
    Die("missing '--' before the gapbs graph arguments");
  bool use_in;
  if (order == "in_neighbors_by_vertex")
    use_in = true;
  else if (order == "out_neighbors_by_vertex")
    use_in = false;
  else
    Die("--order must be in_neighbors_by_vertex or out_neighbors_by_vertex, "
        "got '" + order + "'");

  // gapbs argv: program name + everything after "--".
  std::vector<char *> gargv;
  gargv.push_back(argv[0]);
  for (; i < argc; ++i)
    gargv.push_back(argv[i]);
  gargv.push_back(nullptr);
  int gargc = static_cast<int>(gargv.size()) - 1;

  CLIndexFeatures cli(gargc, gargv.data());
  Graph g;
  {
    StdoutToStderr redirect;
    bool ok = cli.ParseArgs();
    if (cli.bad())
      Die(cli.bad_msg());
    if (!ok)
      Die("no graph input after -- (use -g, -u, or -f)");
    if (optind < gargc)
      Die(std::string("unexpected argument after --: '") + gargv[optind] + "'");
    Builder b(cli);
    g = b.MakeGraph();
  }

  const int64_t n = g.num_nodes();
  if (n < 1)
    Die("graph has no vertices");

  // Walk the index stream in visit order: for u = 0..N-1, for v in list(u).
  auto walk = [&](const std::function<void(int64_t)> &visit) {
    for (NodeID u = 0; u < n; ++u) {
      if (use_in) {
        for (NodeID v : g.in_neigh(u))
          visit(v);
      } else {
        for (NodeID v : g.out_neigh(u))
          visit(v);
      }
    }
  };
  auto line_of = [&](int64_t x) { return x * element_bytes / line_bytes; };

  // Pass 1: length, sequential and same-line steps.
  int64_t length = 0, seq_steps = 0, same_line_steps = 0;
  {
    int64_t prev = -1;
    walk([&](int64_t x) {
      if (length > 0) {
        if (x == prev + 1)
          ++seq_steps;
        if (line_of(x) == line_of(prev))
          ++same_line_steps;
      }
      prev = x;
      ++length;
    });
  }

  // Passes 2 and 3: reuse distances over indices and over lines. One Fenwick
  // tree (L * 4 bytes) and one last-position table (<= N * 8 bytes) at a time.
  Fenwick bit(length);
  ReuseResult elem = ReuseHistogram(walk, [](int64_t x) { return x; }, n,
                                    length, &bit);
  const int64_t num_lines = line_of(n - 1) + 1;
  ReuseResult line = ReuseHistogram(walk, line_of, num_lines, length, &bit);

  // Degree skew over the degrees the ranged step walks.
  std::vector<int64_t> deg(static_cast<size_t>(n));
  for (NodeID u = 0; u < n; ++u)
    deg[static_cast<size_t>(u)] = use_in ? g.in_degree(u) : g.out_degree(u);
  std::sort(deg.begin(), deg.end());
  int64_t sum = 0, dmax = deg.back();
  long double sumsq = 0;
  for (int64_t d : deg) {
    sum += d;
    sumsq += static_cast<long double>(d) * d;
  }
  if (sum != length)
    Die("internal error: degree sum != stream length");
  // G = sum_i (2i - N - 1) d_(i) / (N * sum d), i = 1..N ascending.
  // |numerator| <= N * sum; computed in long double, exact for the magnitudes
  // of any graph that fits in memory (64-bit mantissa).
  long double gnum = 0;
  for (int64_t idx = 0; idx < n; ++idx)
    gnum += static_cast<long double>(2 * (idx + 1) - n - 1) *
            deg[static_cast<size_t>(idx)];
  double gini = (sum == 0) ? 0.0
      : static_cast<double>(gnum / (static_cast<long double>(n) * sum));
  long double mean = static_cast<long double>(sum) / n;
  long double var = sumsq / n - mean * mean;
  if (var < 0)
    var = 0;
  double cv = (sum == 0) ? 0.0 : static_cast<double>(std::sqrt(var) / mean);
  std::vector<int64_t>().swap(deg);

  const int64_t distinct = elem.cold;
  double dup = (length == 0) ? 0.0
      : static_cast<double>(length - distinct) / static_cast<double>(length);
  double seq = (length < 2) ? 0.0
      : static_cast<double>(seq_steps) / static_cast<double>(length - 1);
  double same = (length < 2) ? 0.0
      : static_cast<double>(same_line_steps) / static_cast<double>(length - 1);

  std::string j = "{";
  j += "\"tool\": \"index_features\", ";
  j += "\"tool_version\": " + Int(kToolVersion) + ", ";
  j += "\"order\": \"" + order + "\", ";
  j += "\"element_bytes\": " + Int(element_bytes) + ", ";
  j += "\"line_bytes\": " + Int(line_bytes) + ", ";
  j += std::string("\"line_mapping\": \"") + kLineMapping + "\", ";
  j += "\"graph\": {\"num_nodes\": " + Int(n) + ", \"num_edges_directed\": " +
       Int(g.num_edges_directed()) + ", \"directed\": " +
       (g.directed() ? "true" : "false") + "}, ";
  j += "\"stream_length\": " + Int(length) + ", ";
  j += "\"distinct_indices\": " + Int(distinct) + ", ";
  j += "\"duplicate_ratio\": " + Ratio(dup) + ", ";
  j += "\"sequential_fraction\": " + Ratio(seq) + ", ";
  j += "\"same_line_fraction\": " + Ratio(same) + ", ";
  j += "\"reuse_distance_histogram\": {\"unit\": \"elements\", \"cold\": " +
       Int(elem.cold) + ", \"buckets\": " + BucketsJson(elem.buckets) + "}, ";
  j += "\"line_reuse_distance_histogram\": {\"unit\": \"lines\", "
       "\"distinct\": " + Int(line.cold) + ", \"cold\": " + Int(line.cold) +
       ", \"buckets\": " + BucketsJson(line.buckets) + "}, ";
  j += std::string("\"degree\": {\"which\": \"") + (use_in ? "in" : "out") +
       "\", \"mean\": " + Ratio(static_cast<double>(mean)) + ", \"max\": " +
       Int(dmax) + ", \"gini\": " + Ratio(gini) + ", \"cv\": " + Ratio(cv) +
       "}";
  j += "}\n";

  // The output file is opened only now, so a failed run leaves no JSON file.
  FILE *out = stdout;
  if (out_path != "-") {
    out = std::fopen(out_path.c_str(), "w");
    if (out == nullptr)
      Die("cannot open --out file '" + out_path + "': " + std::strerror(errno));
  }
  if (std::fputs(j.c_str(), out) < 0 || std::fflush(out) != 0)
    Die("cannot write JSON output");
  if (out != stdout && std::fclose(out) != 0)
    Die("cannot close --out file '" + out_path + "'");
  return 0;
}

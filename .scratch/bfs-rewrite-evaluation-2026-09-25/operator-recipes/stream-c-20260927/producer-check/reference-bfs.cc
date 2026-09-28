// Copyright (c) 2015, The Regents of the University of California (Regents)
// See LICENSE.txt for license details

#include <iostream>
#include <vector>

#include "benchmark.h"
#include "bitmap.h"
#include "builder.h"
#include "command_line.h"
#include "graph.h"
#include "platform_atomics.h"
#include "pvector.h"
#include "sliding_queue.h"
#include "timer.h"

#ifdef MAA
#include <climits>
#include <cstdlib>
#include <omp.h>
#include <MAA_utility.hpp>
#endif


/*
GAP Benchmark Suite
Kernel: Breadth-First Search (BFS)
Author: Scott Beamer

Will return parent array for a BFS traversal from a source vertex

This BFS implementation makes use of the Direction-Optimizing approach [1].
It uses the alpha and beta parameters to determine whether to switch search
directions. For representing the frontier, it uses a SlidingQueue for the
top-down approach and a Bitmap for the bottom-up approach. To reduce
false-sharing for the top-down approach, thread-local QueueBuffer's are used.

To save time computing the number of edges exiting the frontier, this
implementation precomputes the degrees in bulk at the beginning by storing
them in the parent array as negative numbers. Thus, the encoding of parent is:
  parent[x] < 0 implies x is unvisited and parent[x] = -out_degree(x)
  parent[x] >= 0 implies x been visited

[1] Scott Beamer, Krste Asanović, and David Patterson. "Direction-Optimizing
    Breadth-First Search." International Conference on High Performance
    Computing, Networking, Storage and Analysis (SC), Salt Lake City, Utah,
    November 2012.
*/


using namespace std;

int64_t BUStep(const Graph &g, pvector<NodeID> &parent, Bitmap &front,
               Bitmap &next) {
  int64_t awake_count = 0;
  next.reset();
  #pragma omp parallel for reduction(+ : awake_count) schedule(dynamic, 1024)
  for (NodeID u=0; u < g.num_nodes(); u++) {
    if (parent[u] < 0) {
      for (NodeID v : g.in_neigh(u)) {
        if (front.get_bit(v)) {
          parent[u] = v;
          awake_count++;
          next.set_bit(u);
          break;
        }
      }
    }
  }
  return awake_count;
}


int64_t TDStep(const Graph &g, pvector<NodeID> &parent,
               SlidingQueue<NodeID> &queue) {
  int64_t scout_count = 0;
  #pragma omp parallel
  {
    QueueBuffer<NodeID> lqueue(queue);
    #pragma omp for reduction(+ : scout_count) nowait
    for (auto q_iter = queue.begin(); q_iter < queue.end(); q_iter++) {
      NodeID u = *q_iter;
      for (NodeID v : g.out_neigh(u)) {
        NodeID curr_val = parent[v];
        if (curr_val < 0) {
          if (compare_and_swap(parent[v], curr_val, u)) {
            lqueue.push_back(v);
            scout_count += -curr_val;
          }
        }
      }
    }
    lqueue.flush();
  }
  return scout_count;
}


#ifdef MAA
static_assert(TILE_SIZE >= 1024 && (TILE_SIZE & (TILE_SIZE - 1)) == 0,
              "DX100 top-down step expects a power-of-two tile of at least 1024");

// Per-guest-thread DX100 scratchpad tiles and scalar registers. They are
// allocated by DX100Prepare inside the timed DOBFS call, never at startup.
static int dx100_tiles[NUM_CORES][NUM_TILES_PER_CORE];
static int dx100_regs[NUM_CORES][NUM_REGS_PER_CORE];

// Complete-call DX100 setup: checked 32-bit CSR offsets, MAA initialization,
// and serialized slot allocation. Returns false (CPU policy only) when any
// precondition fails; offsets are never truncated.
static bool DX100Prepare(const Graph &g, pvector<int32_t> &offsets32) {
  if (omp_get_max_threads() != NUM_CORES)
    return false;
  const int64_t n = g.num_nodes();
  if (n <= 0 || n >= INT_MAX || g.num_edges_directed() > INT_MAX)
    return false;
  pvector<SGOffset> offsets = g.VertexOffsets();
  if (offsets[0] != 0 || offsets[n] < 0 || offsets[n] > INT_MAX)
    return false;
  offsets32.resize(n + 1);
  #pragma omp parallel for
  for (int64_t i = 0; i <= n; i++)
    offsets32[i] = static_cast<int32_t>(offsets[i]);
  alloc_MAA();
  init_MAA();
  int allocated = 0;
  #pragma omp parallel num_threads(NUM_CORES)
  {
    #pragma omp critical
    {
      const int tid = omp_get_thread_num();
      for (int k = 0; k < NUM_TILES_PER_CORE; k++)
        dx100_tiles[tid][k] = get_new_tile<int>();
      for (int k = 0; k < NUM_REGS_PER_CORE; k++)
        dx100_regs[tid][k] = get_new_reg<int>();
      allocated++;
    }
  }
  return allocated == NUM_CORES;
}

// DX100 top-down step adapted from the pinned author TDStepMAA to upstream
// GAPBS: public accessors, frontier-relative indices, checked 32-bit offsets.
static int64_t TDStepDX100(const Graph &g, int32_t *offsets, NodeID *neighbors,
                           pvector<NodeID> &parent, SlidingQueue<NodeID> &queue) {
  NodeID *frontier = queue.begin();
  const int len = static_cast<int>(queue.size());
  NodeID *parents = parent.data();
  const int64_t n = g.num_nodes();
  int64_t scout_count = 0;
  clear_mem_region();
  add_mem_region(frontier, frontier + len);
  add_mem_region(offsets, offsets + n + 1);
  add_mem_region(neighbors, neighbors + offsets[n]);
  add_mem_region(parents, parents + n);
  #pragma omp parallel num_threads(NUM_CORES) reduction(+ : scout_count)
  {
    if (omp_get_num_threads() != NUM_CORES)
      std::abort();
    const int tid = omp_get_thread_num();
    const int tile0 = dx100_tiles[tid][0], tile1 = dx100_tiles[tid][1];
    const int tile2 = dx100_tiles[tid][2], tile3 = dx100_tiles[tid][3];
    const int tile4 = dx100_tiles[tid][4], tile5 = dx100_tiles[tid][5];
    const int tile6 = dx100_tiles[tid][6], tile7 = dx100_tiles[tid][7];
    const int reg0 = dx100_regs[tid][0], reg1 = dx100_regs[tid][1];
    const int regOne = dx100_regs[tid][2], regZero = dx100_regs[tid][3];
    const int last_i_reg = dx100_regs[tid][6], last_j_reg = dx100_regs[tid][7];
    QueueBuffer<NodeID> lqueue(queue);
    maa_const<int>(1, regOne);
    maa_const<int>(0, regZero);
    uint32_t *tile0Ptr = get_cacheable_tile_pointer<uint32_t>(tile0);
    uint32_t *tile4Ptr = get_cacheable_tile_pointer<uint32_t>(tile4);
    int *tile5Ptr = get_cacheable_tile_pointer<int>(tile5);
    int idx = 0;
    while (idx < len) {
      const int remaining = len - idx;
      int tile_size = -1;
      for (int size = TILE_SIZE; size >= 1024; size /= 2) {
        if (remaining > NUM_CORES * size) {
          tile_size = size;
          break;
        }
      }
      if (tile_size != -1) {
        const int min = idx + tid * tile_size;
        const int max = min + tile_size;
        maa_const<int>(min, reg0);
        maa_const<int>(max, reg1);
        // tile0 = u = frontier[min..max)
        maa_stream_load<int>(frontier, reg0, reg1, regOne, tile0);
        // tile1 = offsets[u], tile2 = offsets[u + 1]
        maa_indirect_load<int>(offsets, tile0, tile1);
        maa_indirect_load<int>(offsets + 1, tile0, tile2);
        maa_const<int>(0, last_i_reg);
        maa_const<int>(-1, last_j_reg);
        int produced = 0;
        do {
          // tile6 = i (position within this tile), tile7 = j (edge index)
          maa_range_loop<int>(last_i_reg, last_j_reg, tile1, tile2, regOne, tile6, tile7);
          // tile0 = v = neighbors[j]; tile3 = u = frontier[min + i]
          maa_indirect_load<int>(neighbors, tile7, tile0);
          maa_indirect_load<int>(frontier + min, tile6, tile3);
          wait_ready(tile7);
          produced = get_tile_size(tile7);
          if (produced == 0)
            break;
          #pragma omp critical
          {
            // tile7 = parent[v]; tile4 = parent[v] < 0
            maa_indirect_load<int>(parents, tile0, tile7);
            maa_alu_scalar<int>(tile7, regZero, tile4, Operation_t::LT_OP);
            // where tile4: tile5 = old parent[v]; parent[v] = u
            maa_indirect_store_vector<int>(parents, tile0, tile3, tile4, tile5);
            wait_ready(tile5);
          }
          for (int k = 0; k < produced; k++) {
            if (tile4Ptr[k] && tile5Ptr[k] < 0) {
              lqueue.push_back(static_cast<NodeID>(tile0Ptr[k]));
              scout_count += -static_cast<int64_t>(tile5Ptr[k]);
            }
          }
        } while (produced > 0);
        idx += NUM_CORES * tile_size;
      } else {
        // Scalar tail: at most NUM_CORES * 1024 frontier entries.
        #pragma omp barrier
        #pragma omp for schedule(dynamic, 64)
        for (int i = idx; i < len; i++) {
          const NodeID u = frontier[i];
          for (int32_t j = offsets[u]; j < offsets[u + 1]; j++) {
            const NodeID v = neighbors[j];
            const NodeID curr_val = parents[v];
            if (curr_val < 0 && compare_and_swap(parents[v], curr_val, u)) {
              lqueue.push_back(v);
              scout_count += -curr_val;
            }
          }
        }
        idx = len;
      }
    }
    lqueue.flush();
  }
  clear_mem_region();
  return scout_count;
}
#endif


void QueueToBitmap(const SlidingQueue<NodeID> &queue, Bitmap &bm) {
  #pragma omp parallel for
  for (auto q_iter = queue.begin(); q_iter < queue.end(); q_iter++) {
    NodeID u = *q_iter;
    bm.set_bit_atomic(u);
  }
}

void BitmapToQueue(const Graph &g, const Bitmap &bm,
                   SlidingQueue<NodeID> &queue) {
  #pragma omp parallel
  {
    QueueBuffer<NodeID> lqueue(queue);
    #pragma omp for nowait
    for (NodeID n=0; n < g.num_nodes(); n++)
      if (bm.get_bit(n))
        lqueue.push_back(n);
    lqueue.flush();
  }
  queue.slide_window();
}

pvector<NodeID> InitParent(const Graph &g) {
  pvector<NodeID> parent(g.num_nodes());
  #pragma omp parallel for
  for (NodeID n=0; n < g.num_nodes(); n++)
    parent[n] = g.out_degree(n) != 0 ? -g.out_degree(n) : -1;
  return parent;
}

pvector<NodeID> DOBFS(const Graph &g, NodeID source, bool logging_enabled = false,
                      int alpha = 15, int beta = 18) {
  if (logging_enabled)
    PrintStep("Source", static_cast<int64_t>(source));
  Timer t;
  t.Start();
  pvector<NodeID> parent = InitParent(g);
  t.Stop();
  if (logging_enabled)
    PrintStep("i", t.Seconds());
  parent[source] = source;
  SlidingQueue<NodeID> queue(g.num_nodes());
  queue.push_back(source);
  queue.slide_window();
  Bitmap curr(g.num_nodes());
  curr.reset();
  Bitmap front(g.num_nodes());
  front.reset();
#ifdef MAA
  pvector<int32_t> offsets32;
  const bool dx100 = DX100Prepare(g, offsets32);
  NodeID *neighbors = dx100 ? g.out_neigh(0).begin() : nullptr;
#endif
  int64_t edges_to_check = g.num_edges_directed();
  int64_t scout_count = g.out_degree(source);
  while (!queue.empty()) {
#ifdef MAA
    if (dx100 && queue.size() > static_cast<size_t>(NUM_CORES) * 1024) {
      t.Start();
      edges_to_check -= scout_count;
      scout_count = TDStepDX100(g, offsets32.data(), neighbors, parent, queue);
      queue.slide_window();
      t.Stop();
      if (logging_enabled)
        PrintStep("td-dx100", t.Seconds(), queue.size());
      continue;
    }
#endif
    if (scout_count > edges_to_check / alpha) {
      int64_t awake_count, old_awake_count;
      TIME_OP(t, QueueToBitmap(queue, front));
      if (logging_enabled)
        PrintStep("e", t.Seconds());
      awake_count = queue.size();
      queue.slide_window();
      do {
        t.Start();
        old_awake_count = awake_count;
        awake_count = BUStep(g, parent, front, curr);
        front.swap(curr);
        t.Stop();
        if (logging_enabled)
          PrintStep("bu", t.Seconds(), awake_count);
      } while ((awake_count >= old_awake_count) ||
               (awake_count > g.num_nodes() / beta));
      TIME_OP(t, BitmapToQueue(g, front, queue));
      if (logging_enabled)
        PrintStep("c", t.Seconds());
      scout_count = 1;
    } else {
      t.Start();
      edges_to_check -= scout_count;
      scout_count = TDStep(g, parent, queue);
      queue.slide_window();
      t.Stop();
      if (logging_enabled)
        PrintStep("td", t.Seconds(), queue.size());
    }
  }
  #pragma omp parallel for
  for (NodeID n = 0; n < g.num_nodes(); n++)
    if (parent[n] < -1)
      parent[n] = -1;
  return parent;
}


void PrintBFSStats(const Graph &g, const pvector<NodeID> &bfs_tree) {
  int64_t tree_size = 0;
  int64_t n_edges = 0;
  for (NodeID n : g.vertices()) {
    if (bfs_tree[n] >= 0) {
      n_edges += g.out_degree(n);
      tree_size++;
    }
  }
  cout << "BFS Tree has " << tree_size << " nodes and ";
  cout << n_edges << " edges" << endl;
}


// BFS verifier does a serial BFS from same source and asserts:
// - parent[source] = source
// - parent[v] = u  =>  depth[v] = depth[u] + 1 (except for source)
// - parent[v] = u  => there is edge from u to v
// - all vertices reachable from source have a parent
bool BFSVerifier(const Graph &g, NodeID source,
                 const pvector<NodeID> &parent) {
  pvector<int> depth(g.num_nodes(), -1);
  depth[source] = 0;
  vector<NodeID> to_visit;
  to_visit.reserve(g.num_nodes());
  to_visit.push_back(source);
  for (auto it = to_visit.begin(); it != to_visit.end(); it++) {
    NodeID u = *it;
    for (NodeID v : g.out_neigh(u)) {
      if (depth[v] == -1) {
        depth[v] = depth[u] + 1;
        to_visit.push_back(v);
      }
    }
  }
  for (NodeID u : g.vertices()) {
    if ((depth[u] != -1) && (parent[u] != -1)) {
      if (u == source) {
        if (!((parent[u] == u) && (depth[u] == 0))) {
          cout << "Source wrong" << endl;
          return false;
        }
        continue;
      }
      bool parent_found = false;
      for (NodeID v : g.in_neigh(u)) {
        if (v == parent[u]) {
          if (depth[v] != depth[u] - 1) {
            cout << "Wrong depths for " << u << " & " << v << endl;
            return false;
          }
          parent_found = true;
          break;
        }
      }
      if (!parent_found) {
        cout << "Couldn't find edge from " << parent[u] << " to " << u << endl;
        return false;
      }
    } else if (depth[u] != parent[u]) {
      cout << "Reachability mismatch" << endl;
      return false;
    }
  }
  return true;
}


int main(int argc, char* argv[]) {
  CLApp cli(argc, argv, "breadth-first search");
  if (!cli.ParseArgs())
    return -1;
  Builder b(cli);
  Graph g = b.MakeGraph();
  SourcePicker<Graph> sp(g, cli.start_vertex());
  auto BFSBound = [&sp,&cli] (const Graph &g) {
    return DOBFS(g, sp.PickNext(), cli.logging_en());
  };
  SourcePicker<Graph> vsp(g, cli.start_vertex());
  auto VerifierBound = [&vsp] (const Graph &g, const pvector<NodeID> &parent) {
    return BFSVerifier(g, vsp.PickNext(), parent);
  };
  BenchmarkKernel(cli, g, BFSBound, PrintBFSStats, VerifierBound);
  return 0;
}

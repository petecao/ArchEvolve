// Native-CPU certification seams and faults (certify 1.4). Created: 2026-10-05 ET (ticket 75).
// Agent-decided under Yan-Ru's 2026-10-05 delegation; revisable.
//
// `swdb certify` compiles this file into a separate trusted object, once with no fault (positive
// matrix) and once per control with exactly one -DSWDB_NATIVE_FAULT_<ID>. That macro reaches only
// this translation unit; the candidate object, built once per build configuration from the native
// candidate prelude, is linked unchanged against each of these objects.
//
// Each fault emulates one way a rewrite under contract.bfs_tdstep_frontier_staging can be wrong,
// at a seam every conforming candidate must pass through, so it never searches the candidate's
// spelling:
//
//   claim_without_write   (clause C2) the first successful claim of the run returns true but
//                         leaves parent[v] unchanged, as a claim primitive that compares without
//                         writing would. A rewrite that kept the post-claim store `parent[v] = u`
//                         masks it; one that removed the store (as C2 permits only because the
//                         claim writes) leaves v without a parent, which the verifier rejects.
//   partial_batch_dropped (clause S1) in every step whose window holds more than BATCH positions,
//                         the trailing (size mod BATCH) positions are never expanded: the step is
//                         handed a window shortened by that tail, and before the next step the tail
//                         is skipped, exactly as a staged loop that expands its full batches and
//                         drops the final partial batch behaves. It acts on the step's inputs, so it
//                         tests that the checks catch the bug class, whatever the candidate.
//   stale_row_offset      (clause S2) in the first step, the first window vertex u is
//                         expanded over the row of vertex u + 1 (its staged bounds come from the
//                         wrong vertex) while it still claims as u; the bounds are restored before
//                         the next step.
//   forged_frontier       (clause C1, obligation once_enqueue) the first push of the run is pushed
//                         twice (the native form of ticket 67's version 2).
#include <atomic>
#include <cstddef>
#include <cstdint>

#if (defined(SWDB_NATIVE_FAULT_CLAIM_WITHOUT_WRITE) + defined(SWDB_NATIVE_FAULT_PARTIAL_BATCH_DROPPED) + \
     defined(SWDB_NATIVE_FAULT_STALE_ROW_OFFSET) + defined(SWDB_NATIVE_FAULT_FORGED_FRONTIER)) > 1
#error "select at most one native certification fault"
#endif
#ifndef SWDB_NATIVE_FAULT_BATCH
#define SWDB_NATIVE_FAULT_BATCH 16
#endif

void swdb_cert_record_frontier(const int32_t *window, size_t count);

namespace swdb_fault {
std::atomic<unsigned long long> &claims() { static std::atomic<unsigned long long> v(0); return v; }
std::atomic<unsigned long long> &pushes() { static std::atomic<unsigned long long> v(0); return v; }
std::atomic<bool> &claim_lost_once() { static std::atomic<bool> v(false); return v; }
std::atomic<bool> &pushed_twice_once() { static std::atomic<bool> v(false); return v; }
// The frontier hook runs on the master thread between steps, never concurrently with a step.
size_t &hidden_tail() { static size_t v = 0; return v; }
bool &stale_applied() { static bool v = false; return v; }
bool &stale_pending() { static bool v = false; return v; }
int32_t *&stale_base() { static int32_t *v = nullptr; return v; }
size_t &stale_index() { static size_t v = 0; return v; }
int32_t (&stale_saved())[2] { static int32_t v[2] = {0, 0}; return v; }
}  // namespace swdb_fault

unsigned long long swdb_seam_claims() { return swdb_fault::claims().load(); }
unsigned long long swdb_seam_pushes() { return swdb_fault::pushes().load(); }
void swdb_seam_count_claim() { swdb_fault::claims().fetch_add(1); }
void swdb_seam_count_push() { swdb_fault::pushes().fetch_add(1); }

bool swdb_seam_claim_lost() {
#if defined(SWDB_NATIVE_FAULT_CLAIM_WITHOUT_WRITE)
  return !swdb_fault::claim_lost_once().exchange(true);
#else
  return false;
#endif
}

bool swdb_seam_push_twice() {
#if defined(SWDB_NATIVE_FAULT_FORGED_FRONTIER)
  return !swdb_fault::pushed_twice_once().exchange(true);
#else
  return false;
#endif
}

void swdb_seam_frontier(size_t *out_start, size_t *out_end, size_t shared_in, const int32_t *shared,
                        int32_t *offsets, size_t offsets_count) {
  (void)shared_in;
  (void)offsets;
  (void)offsets_count;
  // 1. Undo the previous step's input fault.
#if defined(SWDB_NATIVE_FAULT_PARTIAL_BATCH_DROPPED)
  if (swdb_fault::hidden_tail()) {
    *out_start += swdb_fault::hidden_tail();  // the dropped tail is never expanded
    swdb_fault::hidden_tail() = 0;
  }
#endif
#if defined(SWDB_NATIVE_FAULT_STALE_ROW_OFFSET)
  if (swdb_fault::stale_pending()) {
    swdb_fault::stale_base()[swdb_fault::stale_index()] = swdb_fault::stale_saved()[0];
    swdb_fault::stale_base()[swdb_fault::stale_index() + 1] = swdb_fault::stale_saved()[1];
    swdb_fault::stale_pending() = false;
  }
#endif
  // 2. Record the window this step is handed (vertex IDs; judged out of process).
  swdb_cert_record_frontier(shared + *out_start, *out_end - *out_start);
  // 3. This step's input fault.
#if defined(SWDB_NATIVE_FAULT_PARTIAL_BATCH_DROPPED)
  // Only a true partial batch: full batches before it are expanded (ticket 75 review).
  const size_t size = *out_end - *out_start;
  swdb_fault::hidden_tail() = size > size_t(SWDB_NATIVE_FAULT_BATCH) ? size % size_t(SWDB_NATIVE_FAULT_BATCH) : 0;
  *out_end -= swdb_fault::hidden_tail();
#endif
#if defined(SWDB_NATIVE_FAULT_STALE_ROW_OFFSET)
  if (!swdb_fault::stale_applied() && *out_end > *out_start) {
    const int32_t u = shared[*out_start];
    if (u >= 0 && size_t(u) + 2 < offsets_count) {
      const int32_t next_begin = offsets[u + 1], next_end = offsets[u + 2];
      swdb_fault::stale_base() = offsets;
      swdb_fault::stale_index() = size_t(u);
      swdb_fault::stale_saved()[0] = offsets[u];
      swdb_fault::stale_saved()[1] = offsets[u + 1];
      offsets[u] = next_begin;  // u's row bounds now come from vertex u + 1
      offsets[u + 1] = next_end;
      swdb_fault::stale_pending() = true;
    }
    swdb_fault::stale_applied() = true;
  }
#endif
}

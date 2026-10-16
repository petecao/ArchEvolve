"""Prospective lexical-array refinement of the exact default QueueBuffer lifetime.

This is not a malloc/new/delete implementation. No allocator/source proof is
accepted. The original out-slot freeze is kept unchanged. All sizes except the
source's default local buffer capacity remain symbolic.
"""
import argparse
import hashlib
import json
from pathlib import Path
from outslot_lowering import canonical_generated_text

HERE = Path(__file__).resolve().parent
PINS = {
    "gapbs_models.h": "e2248bbe1e7dd47c6a46f8645aca9f065900c7205b066fbd5956b2c7c5fcf95c",
    "tdstep_standin.c": "3af025040802b2c018a7a192738c276863f7c489e4c3ce238443b9f2a3f6bcfa",
    "bfs_unit.h": "52d40d00b0a7462eed164deec3a8958a855de5763e7f20fefb8e2f257f09bd34",
    "dxc_summaries.h": "c70a4644a4cd27feabcacd3633a1135bcb46a8f36d86a08b2fee4a469a868c71",
    "abi-map.json": "e6dca1c772e1ba7d0e54fe43e95c203e4c72302e72b439f48ee86c5b9cb673e7",
}
UNIT_PIN = "3c5867a2b8919806f681603836bd0cff448f21634485abf84e49ed71f25515ef"


def once(value, old, new):
    if value.count(old) != 1: raise ValueError("unsupported source/context: " + old[:100])
    return value.replace(old, new, 1)


def build(source, unit):
    raw = {name: (source / name).read_bytes() for name in PINS}
    for name, pin in PINS.items():
        if hashlib.sha256(raw[name]).hexdigest() != pin:
            raise ValueError("unsupported changed source: " + name)
    unit_raw = unit.read_bytes()
    if hashlib.sha256(unit_raw).hexdigest() != UNIT_PIN:
        raise ValueError("unsupported changed source unit")
    original = {name: data.decode("utf-8", errors="strict") for name, data in raw.items()}
    files = {name: original[name] for name in PINS if name.endswith((".h", ".c"))}
    g = files["gapbs_models.h"]
    g = once(g, "Threads = 1. Members with a body here are proven in the same WP run.",
             "Threads = 1. All bodies here must be proved in a fresh WP component.")
    g = once(g, "// Body-less functions (compiler builtins, operator new[] / delete[], std::copy) are\n// standard-library summaries: Extern contracts, each an assumption entry (map 16 item 7).",
             "// Body-less atomic/copy interfaces retain Extern summary assumptions.\n// Private binding is an ordinary body; retirement is a caller-scope obligation.")
    begin = g.index("/* operator new NodeID[n]")
    end = g.index("/*@ requires \\valid(swdb_out); requires \\separated(swdb_out, first", begin)
    replacement = r'''/* Private storage for the source's one default QueueBuffer lifetime.
   Caller creates one uninitialized typed automatic object. This adapter only
   binds its address; it does not initialize payload or implement an allocator.
   Source refinement, lifetime and actual initialization-map gates remain open. */
#define SWDB_LQUEUE_CAPACITY 16384
typedef NodeID swdb_private_NodeID_array[SWDB_LQUEUE_CAPACITY];
/*@
  predicate gapbs_buffer_domain{L}(struct QueueBuffer_NodeID *self) =
    \valid(self) &&
    \initialized(&self->sq) && \initialized(&self->local_size) &&
    \initialized(&self->in) && \initialized(&self->local_queue) &&
    gapbs_queue_domain(self->sq) &&
    self->local_size == SWDB_LQUEUE_CAPACITY && self->in <= self->local_size &&
    gapbs_nodeid_span(self->local_queue, self->local_size) &&
    \separated(self, self->sq,
      self->local_queue + (0 .. self->local_size - 1),
      self->sq->shared + (0 .. self->sq->shared_max_size - 1));
*/
/*@ requires \valid(storage) && \valid(swdb_out);
    requires n == SWDB_LQUEUE_CAPACITY;
    requires gapbs_nodeid_span(&(*storage)[0], n);
    requires \separated(storage, swdb_out);
    assigns *swdb_out;
    ensures *swdb_out == &(*storage)[0];
    ensures \initialized(swdb_out); */
void swdb_bind_private_NodeID_array(swdb_private_NodeID_array *storage, size_t n, NodeID **swdb_out) {
  (void)n;
  *swdb_out = &(*storage)[0];
}

'''
    removed = g[begin:end]
    g = g[:begin] + replacement + g[end:]
    g = once(g, "requires 1 <= given_size <= SWDB_LQUEUE_CAPACITY;",
             "requires given_size == SWDB_LQUEUE_CAPACITY;\n    requires \\valid(storage) && gapbs_nodeid_span(&(*storage)[0], given_size);")
    g = once(g, "requires \\separated(self, master, swdb_lqueue_storage + (0 .. SWDB_LQUEUE_CAPACITY - 1),",
             "requires \\separated(self, master, storage,")
    g = once(g, "ensures self->local_queue == &swdb_lqueue_storage[0];",
             "ensures self->local_queue == &(*storage)[0];")
    g = once(g, "struct SlidingQueue_NodeID *master, size_t given_size) {",
             "struct SlidingQueue_NodeID *master, size_t given_size, swdb_private_NodeID_array *storage) {")
    g = once(g, "swdb_new_NodeID_array_out(self->local_size, &swdb_ret_alloc);",
             "swdb_bind_private_NodeID_array(storage, self->local_size, &swdb_ret_alloc);")
    g = once(g, "swdb_delete_NodeID_array(self->local_queue);",
             "/* Lexical destruction marker: every admitted caller ends the array's\n     block immediately after this call. No deallocation claim for this body. */\n  (void)self;")
    if "swdb_lqueue_storage" in g or "swdb_new_NodeID_array" in g or "swdb_delete_NodeID_array" in g:
        raise ValueError("old allocator surrogate remains")
    files["gapbs_models.h"] = g
    td = files["tdstep_standin.c"]
    td = once(td, "    struct QueueBuffer_NodeID lqueue;",
              "    swdb_private_NodeID_array swdb_local_storage; /* no initializer */\n    struct QueueBuffer_NodeID lqueue;")
    td = once(td, "QueueBuffer_NodeID_QueueBuffer(&lqueue, queue, 16384);",
              "QueueBuffer_NodeID_QueueBuffer(&lqueue, queue, 16384, &swdb_local_storage);")
    # This exact statement/scope adjacency is a mandatory lifetime gate. No
    # source operation can observe the interval before actual block retirement.
    if td.count("QueueBuffer_NodeID_destroy(&lqueue);\n  }\n  /* #ifdef GEM5") != 1:
        raise ValueError("unsupported destruction/lifetime boundary")
    td = once(td, r"\base_addr(parent->start_), \base_addr(queue->shared), \base_addr(&swdb_lqueue_storage[0]),",
              r"\base_addr(parent->start_), \base_addr(queue->shared),")
    td = once(td, "      \\base_addr(dxc_tile_data[t]) != \\base_addr(&swdb_lqueue_storage[0]) &&\n", "")
    td = once(td, "      swdb_lqueue_storage[0 .. SWDB_LQUEUE_CAPACITY - 1],\n", "")
    files["tdstep_standin.c"] = td
    bfs = files["bfs_unit.h"]
    bfs = once(bfs, "  // QueueBuffer storage, and the four interface objects.",
               "  // Four interface objects. Private QueueBuffer storage is created later.")
    # Remove only the artificial global's argument/inequalities. Distinctness
    # of every preexisting source object remains pairwise complete.
    old_pred = bfs[bfs.index("  predicate bfs_distinct_blocks"):bfs.index("*/", bfs.index("  predicate bfs_distinct_blocks"))]
    names = ("o", "n", "p", "q", "g", "vo", "pa", "qu")
    pairs = [f"{a} != {b}" for i, a in enumerate(names) for b in names[i + 1:]]
    new_pred = "  predicate bfs_distinct_blocks(" + ", ".join("char *" + n for n in names) + ") =\n    " + " &&\n    ".join(pairs) + ";\n"
    bfs = once(bfs, old_pred, new_pred)
    files["bfs_unit.h"] = bfs
    for name, value in files.items():
        if "swdb_lqueue_storage" in value: raise ValueError("global surrogate remains in " + name)
        files[name] = "// Prospective lexical private-array refinement; source/formal acceptance pending.\n" + value
    old_post = original["tdstep_standin.c"].split("    ensures visited_parent_unchanged:", 1)[1].split("void TDStep(", 1)[0]
    new_post = files["tdstep_standin.c"].split("    ensures visited_parent_unchanged:", 1)[1].split("void TDStep(", 1)[0]
    if old_post != new_post: raise ValueError("TD functional postcondition drift")
    operations = {
        "positive": "QueueBuffer_NodeID_push_back(&buffer, 17);\n  *out = buffer.local_queue[0];",
        "missing-store": "*out = buffer.local_queue[0];",
        "wrong-cell": "QueueBuffer_NodeID_push_back(&buffer, 17);\n  *out = buffer.local_queue[1];",
        "uninitialized-scalar": "NodeID uninitialized;\n  *out = uninitialized;",
        "copy-positive": "size_t prior = queue->shared_in;\n  QueueBuffer_NodeID_push_back(&buffer, 17);\n  QueueBuffer_NodeID_flush(&buffer);\n  *out = queue->shared[prior];",
        "history-positive": "QueueBuffer_NodeID_push_back(&buffer, 17);\n  QueueBuffer_NodeID_flush(&buffer);\n  *out = buffer.local_queue[0];",
    }
    for name, operation in operations.items():
        flushes = name in ("copy-positive", "history-positive")
        pre = "\n    requires queue->shared_in < queue->shared_max_size;" if flushes else ""
        frame = "*out, queue->shared_in, queue->shared[queue->shared_in]" if flushes else "*out"
        post = "\n    ensures *out == 17;" if "positive" in name else ""
        files["sites/" + name + ".c"] = (
            '// Prospective same-allocation-path control. Never execute undefined negatives.\n'
            '#include "gapbs_models.h"\n\n'
            '/*@ requires gapbs_queue_domain(queue) && \\valid(out);'
            '\n    requires \\separated(out, queue, queue->shared + (0 .. queue->shared_max_size - 1));'
            + pre + '\n    assigns ' + frame + ';' + post + ' */\n'
            'void swdb_allocation_site(struct SlidingQueue_NodeID *queue, NodeID *out) {\n'
            '  swdb_private_NodeID_array storage; /* no initializer: exact same producer */\n'
            '  struct QueueBuffer_NodeID buffer;\n'
            '  QueueBuffer_NodeID_QueueBuffer(&buffer, queue, 16384, &storage);\n  '
            + operation + '\n  QueueBuffer_NodeID_destroy(&buffer);\n}\n')
    site_domain = ('/*@ requires gapbs_queue_domain(queue) && \\valid(out);\n'
                   '    requires \\separated(out, queue, queue->shared + (0 .. queue->shared_max_size - 1));\n'
                   '    assigns *out;')
    control_functions = {name: ["swdb_allocation_site"] for name in operations}
    for positive in (False, True):
        name = "reentry-positive" if positive else "reentry-missing-store"
        store = "QueueBuffer_NodeID_push_back(&buffer, 17);" if positive else "if (lifetime == 0) QueueBuffer_NodeID_push_back(&buffer, 17);"
        operations[name] = "two loop lifetimes: " + ("both store then read" if positive else "first stores; second omits store then reads")
        control_functions[name] = ["swdb_allocation_site"]
        files["sites/" + name + ".c"] = (
            '// Prospective same-path lexical retirement/reentry. Undefined negative is never executed.\n'
            '#include "gapbs_models.h"\n\n' + site_domain
            + ('\n    ensures *out == 17;' if positive else '') + ' */\n'
            'void swdb_allocation_site(struct SlidingQueue_NodeID *queue, NodeID *out) {\n'
            '  for (unsigned lifetime = 0; lifetime < 2; ++lifetime) {\n'
            '    swdb_private_NodeID_array storage; /* new uninitialized lifetime each iteration */\n'
            '    struct QueueBuffer_NodeID buffer;\n'
            '    QueueBuffer_NodeID_QueueBuffer(&buffer, queue, 16384, &storage);\n    '
            + store + '\n    *out = buffer.local_queue[0];\n'
            '    QueueBuffer_NodeID_destroy(&buffer);\n  }\n}\n')
        name = "modular-entry-positive" if positive else "modular-entry-missing-store"
        operations[name] = "two modular entries: " + ("both store then read" if positive else "first stores; second omits store then reads")
        control_functions[name] = ["swdb_lifetime_entry", "swdb_allocation_site"]
        store = "(void)write; QueueBuffer_NodeID_push_back(&buffer, 17);" if positive else "if (write) QueueBuffer_NodeID_push_back(&buffer, 17);"
        files["sites/" + name + ".c"] = (
            '// Prospective same-path repeated modular entry. Undefined negative is never executed.\n'
            '#include "gapbs_models.h"\n\n' + site_domain
            + ('\n    ensures *out == 17;' if positive else '\n    ensures write ==> *out == 17;') + ' */\n'
            'void swdb_lifetime_entry(struct SlidingQueue_NodeID *queue, bool write, NodeID *out) {\n'
            '  swdb_private_NodeID_array storage; /* new uninitialized function lifetime */\n'
            '  struct QueueBuffer_NodeID buffer;\n'
            '  QueueBuffer_NodeID_QueueBuffer(&buffer, queue, 16384, &storage);\n  '
            + store + '\n  *out = buffer.local_queue[0];\n'
            '  QueueBuffer_NodeID_destroy(&buffer);\n}\n\n' + site_domain
            + ('\n    ensures *out == 17;' if positive else '') + ' */\n'
            'void swdb_allocation_site(struct SlidingQueue_NodeID *queue, NodeID *out) {\n'
            '  NodeID first;\n  swdb_lifetime_entry(queue, true, &first);\n'
            '  swdb_lifetime_entry(queue, false, out);\n}\n')
    files = {name: canonical_generated_text(value) for name, value in files.items()}
    def contract(text, name):
        pos = text.index("void " + name + "(")
        begin = text.rfind("/*@", 0, pos)
        return text[begin + 3:text.index("*/", begin)].strip()
    original_g = original["gapbs_models.h"]
    original_td = original["tdstep_standin.c"]
    new_td = files["tdstep_standin.c"]
    def subsection(text, first, last):
        begin = text.index(first)
        return text[begin:text.index(last, begin)]
    manifest = {
        "method": "t07-lexical-private-array-prospective-v3-canonical", "parent_outslot_source_pins": PINS,
        "actual_unit_sha256": UNIT_PIN, "removed_static_allocator_source": removed,
        "introduced_private_binding_source": replacement,
        "helper_bodies": 20, "original_helper_bodies_retained": 19, "new_binding_bodies": 1,
        "default_local_capacity": 16384, "incoming_SlidingQueue_capacity": "symbolic num_nodes; unchanged",
        "exact_source_producers": {
            "repository": "arkhadem/DX100", "commit": "e4fc4afdf894f295442cef3604667a469fab8e62",
            "sliding_queue.h": {"sha256": "3d5a1d3cff924737c2fc7c6b4fcbb859270f1fcc626c25aac4c780b7b6f4c02c",
                                "git_blob_sha1": "fed319ea556423c55db8d995a97ea21a0f950da8", "allocation_lines": [98, 101], "destruction_lines": [104, 105]},
            "actual_project_unit": {"sha256": UNIT_PIN, "construction_line": 21, "push_lines": [53, 63], "flush_line": 67, "scope_exit_line": 68},
        },
        "contract_changes": {
            name: {"old": contract(original_g, name), "new": contract(files["gapbs_models.h"], name)}
            for name in ("QueueBuffer_NodeID_QueueBuffer", "QueueBuffer_NodeID_destroy", "QueueBuffer_NodeID_flush", "QueueBuffer_NodeID_push_back")
        },
        "entry_frame_change": {
            "old": subsection(original_td, "    assigns parent->start_", "    ensures visited_parent_unchanged:"),
            "new": subsection(new_td, "    assigns parent->start_", "    ensures visited_parent_unchanged:"),
        },
        "entry_separation_change": {
            "old": subsection(original_td, "    requires separation:", "    requires context:"),
            "new": subsection(new_td, "    requires separation:", "    requires context:"),
        },
        "device_separation_change": {
            "old": subsection(original_td, "    requires spd:", "    requires dx100_idle:"),
            "new": subsection(new_td, "    requires spd:", "    requires dx100_idle:"),
        },
        "old_global_frame_projection": "old artificial global buffer -> fresh caller-private automatic array; remove only artificial entry separation/frame, retain all preexisting source objects and internal payload helper frames",
        "destructor_projection": "no observable source state effect; actual private-array block retirement immediately follows marker at every admitted call site; not a generic delete or danglingness proof",
        "unit_postconditions_sha256": hashlib.sha256(old_post.encode()).hexdigest(),
        "source_qualification": "exact default successful-normal allocation, one 16384-element NodeID array, nonescape/address-insensitive single lifetime; generic n/new/delete/hooks/failure/exceptions unsupported",
        "physical_source_header_macro_include_closure_gate": "REFUSED_NOT_IMPLEMENTED; producer hash below is recorded source research, not the selected C++ build closure. This packet only qualifies hand-model feasibility.",
        "same_path_controls": {name: {"expected": "ordinary positive proof candidate" if "positive" in name else "source-read initializedness must remain non-valid; no proof accepted",
                                     "operation": operation, "root_functions": control_functions[name]} for name, operation in operations.items()},
        "output_pins": {n: hashlib.sha256(v.encode("utf-8")).hexdigest() for n, v in files.items()},
        "proof_acceptance": False, "allocator_correspondence": "PENDING_INIT_MAP_SAME_PATH_AND_SOURCE_REFINEMENT_GATES",
        "TD_or_counted_admissible": False,
    }
    return files, manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=HERE / "standin_outslot_canonical")
    p.add_argument("--unit", type=Path, default=HERE.parents[3] / "library/dx100/bfs_read_offload.inc")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--require-allocator-correspondence", action="store_true")
    a = p.parse_args()
    files, manifest = build(a.source, a.unit)
    if a.require_allocator_correspondence:
        raise ValueError("allocator correspondence pending: exact init-map and same-path formal negatives unrun")
    if a.output.exists(): raise ValueError("output must be absent")
    a.output.mkdir(parents=True)
    for name, value in files.items():
        (a.output / name).parent.mkdir(parents=True, exist_ok=True)
        (a.output / name).write_bytes(value.encode("utf-8"))
    (a.output / "private-array-map.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__": main()

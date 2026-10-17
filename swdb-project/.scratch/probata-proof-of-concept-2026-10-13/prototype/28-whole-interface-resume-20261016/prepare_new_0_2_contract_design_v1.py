"""2026-10-16 ET. Concrete per-call/model contract design, source only.

Not a published proof_semantics entry and not a verifier runner. Parent owns
isolated production model/entry assembly after source/frontend coordination.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys


def deny(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("contract preparation forbids " + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent


def pin(path):
    path = Path(path).resolve(strict=True);data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def prepare():
    path = HERE / "whole_interface_v3.py"
    api = {"__file__": str(path), "__name__": "contract_design_only"}
    exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), api)
    declarations = api["inventory"](HERE.parents[3])
    instances = json.loads((HERE / "source-dispatch-contracts-v2.json").read_bytes())["contracts"]
    # These relations are executed by the concrete model bodies. They are not
    # axioms or imported summaries that replace those bodies in CBMC.
    relations = {
        "alloc_MAA": "Set seven MMIO endpoints to source MEM_SIZE + exact tile/size/ready/RF/instruction spans; install six built-in regions and next_region=6. Preserve allocation counters, payload/size versions, pending commands and ordinary history.",
        "init_MAA": "Set global source allocation counters and next_region to their source initial values. Preserve MMIO allocation, registrations, payload, size versions, pending commands and ordinary history.",
        "add_mem_region": "At old next_region, apply the exact source overlap predicate and ID conversion; install [start,end), advance the int8 source counter. Region assignment later uses first containing ID and preserves F2 stall/lookup order.",
        "clear_mem_region": "Replace registrations with the six current source MMIO intervals; next_region=6. Do not reset payload, allocations, pending commands or memory history.",
        "get_cacheable_tile_pointer": "Return descriptor(kind=cacheable,tile=SPD_id,dtype=actual T,offset=0), denoting MMIO_base + SPD_id*TILE_SIZE*4. Grant no ownership, readiness, initializedness or size.",
        "get_noncacheable_tile_pointer": "Return descriptor(kind=noncacheable,tile=SPD_id,dtype=actual T,offset=0), denoting the source noncacheable base + SPD_id*TILE_SIZE*4. Grant no CPU-access policy or ownership/readiness/initializedness.",
        "get_data_type": "Return the exact source canonical-type mapping uint32/int32/float/uint64/int64/double→0..5; every other type→MAX6. No state changes.",
        "get_new_tile": "Return old global tile allocation counter; advance it by sizeof(T)/4 and assign every physical half to the owned thread. Odd 8-byte starts are allowed. Payload, size and pending state are not initialized or cleared.",
        "get_new_reg": "Both arities return old global RF allocation counter and advance it by sizeof(T)/4, assigning all physical halves. Arity0 preserves bytes/initializedness. Arity1 then performs the explicit-ID-stalling typed RF write of the exact input object-representation bits.",
        "get_reg": "After typed pair ownership/domain and pending-writer checks, read all bytes from the immutable shared RF image and require their initializedness. Return the exact T bit copy. No invented read stall or ownership grant.",
        "set_reg": "Stall source-matching pending explicit RF operands at the starting ID, then check complete physical-pair interference/ownership and replace exactly T's bytes with input bits. Preserve other bytes and ordinary-memory history.",
        "maa_const": "Perform the same source typed RF payload write, preserving its own source ordering premise; do not invent the set_reg source fence. Explicit-ID stalls and complete-pair checks remain concrete.",
        "wait_ready": "On conditional normal return cover globally counted source/destination commands naming this physical half, including either half of an 8-byte role. Settle their deferred dependency/action closure. A condition-only role does not count. No polling/liveness conclusion.",
        "get_tile_size": "Require the exact starting tile to be Finished, then return its initialized uint16 size version. No wait, cover, fresh-zero assumption or copy of first-half metadata to a second half.",
        "print_tile": "Read size without cover, then ordered typed CPU tile values with ordinary pending/ownership/initializedness guards; append bounded ordered typed observation events. Printed byte formatting is outside the chosen observation projection unless separately integrated.",
        "maa_alu_scalar": "After concrete stalls/role binding capture immutable source size/tile/RF/condition versions. At cover, for active lanes compute source typed binary(src,scalar); comparisons produce u32. Preserve every inactive byte and publish the captured size.",
        "maa_alu_vector": "Require source sizes/condition size agreement through deferred guards; capture both tile versions. At cover compute typed binary(src1,src2) for active lanes, with u32 comparisons, byte-preserving inactive outputs and captured output size.",
        "maa_alu_reduce": "Use the source operation/type initializer and fold each active source value as src OP accumulator, not accumulator OP src. Settle the captured masked fold into the typed RF result at cover; preserve input versions and source numeric guards.",
        "maa_stream_load": "Capture signed-int RF min/max/stride, condition and source issue history; deferred guards require nonempty nonnegative range, positive stride and source signed-overflow/page/count domain. Active lane k reads data[min+k*stride] at a permitted issue-to-cover history prefix; inactive bytes remain unchanged; publish the checked count.",
        "maa_stream_store": "Capture signed-int bounds/stride and source/condition versions. At cover execute the checked active data[min+k*stride]=src[k] actions under complete physical-line guards and arbitrary permitted action order; do not evaluate RF/index producers at issue.",
        "maa_indirect_load": "Capture u32 indices, source/condition size/value versions and ordinary-cell issue history. Retain uint32 multiplication/source offset correspondence, index bounds and first-ID/F2 guards. Active lanes read permitted history versions; preserve inactive bytes and publish captured size.",
        "maa_indirect_store_vector": "Capture indices/vector/conditions; complete stores to mapped cells under full-line guards. Optional output publishes progressively copied line old values for each action, including repeated aliases. Inactive output bytes/initializedness remain unchanged.",
        "maa_indirect_store_scalar": "Capture indices/typed RF scalar/conditions; complete the scalar stores under full-line guards. Optional old output observes the progressively updated line, with inactive-byte preservation and no forged memory-cell identity.",
        "maa_indirect_rmw_vector": "For each active action, compute typed ADD/MIN/MAX(old, captured_vector[k]) in a permitted action order; update the shared physical cell and optional progressive old-result output. Preserve repeated-alias dependence and source overflow/float rules.",
        "maa_indirect_rmw_scalar": "For each active action, compute typed ADD/MIN/MAX(old,captured RF scalar) with the same progressive alias/action-order and optional old-result semantics. Source numeric/initializedness guards remain concrete.",
        "maa_range_loop": "Force INT32 regardless of T. Capture continuation i/j, signed stride and equal-size min/max/condition versions; deferred RangeFuser-source loop emits checked (i,j) values, advances/resets continuation state and publishes both sizes/RF states at cover. This bounded domain requires the entire output to fit the two-element prefix below source capacity.",
    }
    setup = {"alloc_MAA", "init_MAA", "add_mem_region", "clear_mem_region"}
    rows = []
    for name in dict.fromkeys(row["name"] for row in declarations):
        source_rows = [row for row in declarations if row["name"] == name]
        recipes = [api["contract"](row) for row in source_rows]
        domains = list(dict.fromkeys(rule for recipe in recipes for rule in recipe["domains"]))
        if name in setup: domains += ["No unbound command; exact configured source MMIO geometry; source region/ID/capacity guards"]
        if name.startswith("get_new_"): domains += ["Check capacity and complete physical-pair ownership before source counter/value effects; never assume fresh-zero bytes"]
        if name in {"get_reg", "set_reg", "maa_const"}: domains += ["Exact T bit representation and complete RF pair domain/ownership; pending interference/stalls remain in model body"]
        if any("packet" in row for row in source_rows):
            domains += ["Bounded command/DAG/value-prefix/action/history capacities are asserted model-domain checks",
                "Apply source explicit-destination/global-region stalls before capturing immutable versions",
                "Operation and source undefinedness checks occur only on selected active values; no inactive-lane arithmetic or initializedness obligation"]
        if any(row.get("packet", {}).get("memory_access") for row in source_rows):
            domains += ["CPU/device projections share exact physical scalar cells; reject mixed-width/type or MMIO-overlapping ordinary views",
                "Conservative whole remaining object physical envelope; device writes include full cache-line conflict envelope"]
        rows.append({"call": name, "source_declarations": [{"declaration": row["declaration"], "arity": row["formal_arity"],
            "minimum_arity": row["minimum_arity"], "header": row["file"], "line": row["line"],
            "header_sha256": row["header_sha256"], "body_sha256": row["body_sha256"]} for row in source_rows],
            "typed_arity_instances": [row for row in instances if row["name"] == name],
            "contract": {"asserted_domain_checks": domains, "normal_return_state_value_relation": relations[name],
                "owned_rules": {"mmio": "The pinned source MMIO operations implement the stated model semantics on conditional normal return (explicit accepted TCB)",
                    "compiler": "Admitted original complete-TU/ABI/source-expression/CPU-pointer observation and transformation",
                    "numeric_runtime": "Explicit selected signed-shift/IEEE rounding/unordered minmax policies; source numeric guards remain checked"},
                "source_basis": [basis for recipe in recipes for basis in recipe["source_basis"]]},
            "execution": {"body": "Generated dws_<actual canonical c_name> wrapper over reviewed concrete state/value backends",
                "packet_family": next(("dxw_alu" if row["packet"]["opcode"]>=8 else "dxw_range" if row["packet"]["opcode"]==7 else "dxw_stream" if row["packet"]["opcode"]<=1 else "dxw_indirect" for row in source_rows if "packet" in row), None),
                "CBMC": "Keep and execute the concrete body; do not replace it with an imported nondeterministic return, havoc frame or assumed postcondition",
                "WP": "Do not promote this design to a WP summary until its corresponding concrete-body obligations and frame/return relation are separately admitted"}})
    assert len(rows)==26 and len({row["call"] for row in rows})==26
    assert sum(len(row["source_declarations"]) for row in rows)==27
    assert sum(len(row["typed_arity_instances"]) for row in rows)==132
    assert all(row["contract"]["normal_return_state_value_relation"] and row["contract"]["asserted_domain_checks"] for row in rows)
    result = {"date":"2026-10-16 ET","status":"CONCRETE NEW0.2 CONTRACT/MODEL DESIGN; not a published/accepted entry",
        "prospective_entry":{"id":"semantics.dx100_bfs_0_2","version":"0.2","sequence":2,
            "hardware_interface":{"id":"dx100-mmio","version":"1.0-e4fc4af","gem5_commit":"e4fc4afdf894f295442cef3604667a469fab8e62"},
            "old_0_1_bytes_preserved":True,"new_entry_only":True},
        "calls":rows,"counts":{"call_entries":26,"declarations":27,"exact_six_type_or_nontemplate_instances":132},
        "model_ABI":{"pointer":"struct dws_pointer {unsigned kind,object,tile,dtype;uint64_t offset;}",
            "calls":"dws_<bound source c_name>(unsigned owned_thread, exact scalar or dws_pointer source arguments...)",
            "CPU":"dws_cpu_load/store_{u32,i32,f32,u64,i64,f64}(owned_thread,pointer,index[,value])",
            "families":"11 dws_fixed_maa_* direct prepare→fixed family builder→bind routes; no callback ABI",
            "representation":"Exact memcpy scalar input/result bits; actual canonical typedef identities derive from admitted compiler observation, never the synthetic headers",
            "memory":"Same physical scalar cells and spans for CPU/device projections, full MMIO exclusion and source lifetime/provenance admission"},
        "CBMC_method":{"checks":"Every source/runtime/domain/hazard/undefinedness check is an ordinary named property; no source precondition is converted into an assumption",
            "choices":"Only internal semantic nondeterministic choices are range-restricted to the complete permitted finite choice set; never constrain choices to a desired output",
            "classification":"Capacity/unsupported/runtime-domain property failures report unsupported/unknown; proven model safety plus original assertions may prove the controlled source unit. Distinguish source/model premises in the formal frame.",
            "source_body":"Original source remains compiler-observed; owned per-call MMIO semantics are explicit. No optional hardware/body theorem blocker.",
            "anti_vacuity":"All called concrete functions remain reachable; check complete original assertions, source guards, model/ordinary-term inventory, unwind sufficiency, exact verdict/records and retained counterexample for negatives"},
        "predicted_public_fixtures":[
            {"fixture":"source_call_fixture_v2.cpp","scope":"All26 names/both overloads, uint32/int32 data, all11 families, CPU values and waits","prediction":"Positive: final ordinary data[0]=39,data[1]=41, return80, checked range continuation and size2; not observed"},
            {"fixture":"Same source with final assertion/return expected79","scope":"Source-derived negative","prediction":"Counterexample to original assertion, with source/model guards healthy; not observed"},
            {"fixture":"Six typed initialized RF/ALU/reduction callers","scope":"Exact uint32/int32/float/uint64/int64/double source instances","prediction":"Defined arithmetic/bit representations succeed; source overflow/division/shift/unsupported operations remain classified checks"},
            {"fixture":"64-bit role second-half wait and condition-only wait pair","scope":"Physical readiness/pair semantics","prediction":"Either counted half covers; condition-only wait does not cover and premature CPU observation fails"},
            {"fixture":"Same-thread/other-thread ordinary write between issue and cover","scope":"Shared physical cell history and complete CPU effects","prediction":"Same-thread conflicting write refuses; permitted other-thread history exposes all allowed prefixes, preserving source correlation"},
            {"fixture":"Partial same-type alias views and mixed-width/MMIO alias negatives","scope":"Cell identity/ownership/line envelopes","prediction":"Same scalar bytes reuse history; mixed views and MMIO crossings refuse; selected-element disjointness does not waive full-line conflict"}],
        "inputs":[pin(HERE/name) for name in ("whole_interface_v3.py","source_dispatch_v2.py","source_pointer_bridge_synthetic_v2.h",
            "source_direct_families_v2.h","source_routes_synthetic_v2.h","source-dispatch-preparation-v2.json","source_call_fixture_v2.cpp")],
        "public_admission":False,"actual_compiler_native_verifier_execution":False,"current_0_2":False,"full_ticket28":False}
    output=HERE/'new-0.2-contract-design-v1.json';output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return pin(output)


if __name__=="__main__":print(json.dumps(prepare(),sort_keys=True))

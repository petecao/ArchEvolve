"""Selected-TU single-activation controls; shared B/time/RSS guard required.

Only parsing/preprocessing and pure source observations. Never execute a program,
formal verifier, prover, provider, version/config probe, or initialize payload.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import time

GENERATOR = Path(__file__).resolve().parents[2] / "selected_source.py"
RETAINED = Path("/private/tmp/probata-t07-selected-source-controls-final2-20261016/selected")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--case", choices=("repeat", "conditional-flush", "early-return", "retained"), default="repeat")
    args = ap.parse_args()
    out = args.output.resolve()
    if out.exists() or out.is_relative_to(GENERATOR.parents[5]):
        raise ValueError("fresh external output required")
    out.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location("selected_source_activation", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = []

    def record(name, passed, **details):
        records.append(dict(name=name, passed=bool(passed), **details))
        module.write(out / "controls.json", dict(records=records,
            proof_acceptance=False, source_refinement_accepted=False,
            native_execution=False, lifetime_reset_qualified=False))
        if not passed:
            raise AssertionError(name)

    baseline = module.inspect_ast((RETAINED / "TDStep-ast.stdout").read_bytes(),
        (RETAINED / "QueueBuffer-ast.stdout").read_bytes(),
        RETAINED / "source/benchmarks/gapbs/src/bfs.cc")
    domain = baseline["single_activation_source_observation"]
    record("actual-selected-single-activation-structure",
           domain["declaration_outside_loops_and_conditionals"] is True and
           domain["declaration_first_in_parallel_body"] is True and
           domain["final_flush_direct_terminal_statement"] is True and
           domain["parallel_body_byte_range"] == [2695, 4988])
    record("runtime-and-refinement-qualification-still-refused",
           domain["runtime_threads_one_qualified"] is False and
           domain["interprocedural_reentrancy_qualified"] is False and
           domain["allocator_or_lifetime_refinement_accepted"] is False)
    if args.case == "retained":
        for name, directory in (("repeat", "single-activation-red2"),
                                ("conditional-flush", "single-activation-flush-red")):
            case = Path("/private/tmp/probata-t07-" + directory + "-20261016/repeated")
            try:
                module.inspect_ast((case / "TDStep-ast.stdout").read_bytes(),
                    (case / "QueueBuffer-ast.stdout").read_bytes(),
                    case / "source/benchmarks/gapbs/src/bfs.cc")
            except module.Refused as error:
                record("final-gate-refuses-actual-retained-" + name,
                       "single activation" in str(error), reason=str(error))
            else:
                record("final-gate-refuses-actual-retained-" + name, False)
        excluded = Path("/private/tmp/probata-t07-single-activation-exit-red-20261016/repeated/syntax.stderr")
        record("retained-early-return-is-excluded-OpenMP-source",
               "error: cannot return from OpenMP region" in excluded.read_text(),
               classification="compiler language exclusion, not feature RED or initialization evidence")
        return

    # Real selected TU rather than a manufactured AST serializer. This lexical
    # repetition retains the exact default allocation and the same push/flush
    # operations, but creates two lifetimes in one implicit task activation.
    repeated = out / "repeated"
    repeated.mkdir()
    (repeated / "tmp").mkdir()
    shutil.copytree(RETAINED / "source", repeated / "source")
    source = repeated / "source/benchmarks/gapbs/src/bfs.cc"
    original = source.read_bytes()
    if args.case == "repeat":
        before = b"  QueueBuffer<NodeID> lqueue(queue);"
        after = b"  for (int swdb_repeat = 0; swdb_repeat < 2; ++swdb_repeat) {\n" + before
        text = original.replace(before, after, 1)
        text = text.replace(b"  lqueue.flush();\n }", b"  lqueue.flush();\n  }\n }", 1)
    elif args.case == "conditional-flush":
        text = original.replace(b"  lqueue.flush();", b"  if (accelerate) lqueue.flush();", 1)
    else:
        text = original.replace(b"  lqueue.flush();", b"  if (accelerate) return;\n  lqueue.flush();", 1)
    record("actual-selected-source-" + args.case + "-mutation", text != original)
    source.write_bytes(text)
    try:
        module.compiler_observations(repeated, source, time.monotonic() + 90)
    except module.Refused as error:
        # Compile errors are not a GREEN source-domain refusal.
        if args.case == "early-return":
            record("compiler-excludes-return-from-OpenMP-source-domain",
                   str(error) == "full selected-TU compiler step refused: syntax" and
                   "error: cannot return from OpenMP region" in (repeated / "syntax.stderr").read_text(),
                   classification="excluded OpenMP source, not feature RED or initialization evidence")
            return
        record("real-compiler-" + args.case + "-refused",
               "activation" in str(error) or "loop ancestor" in str(error), reason=str(error))
    else:
        record("real-compiler-" + args.case + "-refused", False,
               reason="source gate accepted unsupported lifetime path")


if __name__ == "__main__":
    main()

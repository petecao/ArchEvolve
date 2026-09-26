"""Compile identified BFS candidates against a pinned executable model.

Updated: 2026-09-25. Primary candidates use the complete-call ROI.
"""

import json
from pathlib import Path
import re
import shutil
import subprocess

from swdb import artifacts, workflow
from swdb.bfs_native import StageFailure, Stopped, _protect_driver_macros
from swdb.cli import Failure
from swdb.dx100 import REVISION, _bounded_process, _file, _finish, _prepare, _request
from swdb.dx100_author import AUTHOR_ROI, HOOKS

ROI = "bfs.complete_call.v1"
SUPPRESSED = ["m5_reset_stats", "m5_dump_stats", "m5_work_begin", "m5_work_end", "m5_exit"]


def _protect_model_headers(candidate, model):
    """The current operation contract compiles against this pinned interface.

    Candidate application helpers remain editable, but a candidate copy of an
    interface input must not differ from the model copy selected by -I. Check
    all files, including .inc and extensionless headers, and basename shadows.
    """
    surfaces = (Path('include'), Path('util/m5/src'), Path('benchmarks/API'))
    names = {'m5ops.h', 'MAA_gem5.hpp', 'MAA.hpp'}
    for surface in surfaces:
        names.update(path.name for path in (model / surface).rglob('*') if path.is_file()
                     and not path.name.startswith('.')
                     and (not path.suffix or path.suffix in {'.h', '.hh', '.hpp', '.hxx', '.inc'}))
    for entry in candidate['artifact']['files']:
        relative = Path(artifacts.relative_path(entry['path']))
        if relative.name in names or any(relative.is_relative_to(surface) for surface in surfaces):
            pinned = model / relative
            if not pinned.is_file() or artifacts.file_hash(pinned) != entry['sha256']:
                raise Failure('candidate changes or shadows the pinned model interface input: ' + entry['path'])


def driver(source, model, function, diagnostic=None):
    prefix = "\n".join(f"#define {name}(...) ((void)0)" for name in SUPPRESSED)
    suffix = "\n".join(f"#undef {name}" for name in SUPPRESSED)
    instrumentation = (f"#define SWDB_REGION_COUNT {len(diagnostic['regions'])}\n#include "
        + json.dumps(diagnostic['runtime']['path'])) if diagnostic else ""
    return f'''// Trusted generated evaluator, 2026-09-25. Complete BFS call only.
#include <cstdint>
#include <cstdio>
#include <iostream>
#include {json.dumps(str(model / 'include/gem5/m5ops.h'))}
{instrumentation}
{prefix}
#define main swdb_gem5_original_main
#include {json.dumps(str(source))}
#undef main
{suffix}
int main(int argc, char **argv) {{
  CLApp cli(argc, argv, "SWDB complete-call BFS");
  if (!cli.ParseArgs()) return 2;
  Builder builder(cli);
  Graph graph = builder.MakeGraph();
  const int64_t source = cli.start_vertex();
  if (source < 0 || source >= graph.num_nodes()) return 3;
  m5_checkpoint(0, 0);
  std::cout << "ROI started: 4 configured threads" << std::endl;
  m5_work_begin(0, 0);
  m5_reset_stats(0, 0);
  {'::swdb_profile::start();' if diagnostic else ''}
  auto parent = {function}(graph, static_cast<NodeID>(source), cli.logging_en());
  {'::swdb_profile::stop();' if diagnostic else ''}
  m5_dump_stats(0, 0);
  m5_work_end(0, 0);
  std::printf("SWDB_BFS_PARENT_STORAGE address=%llx count=%llu element_bytes=4\\n",
      static_cast<unsigned long long>(reinterpret_cast<uintptr_t>(parent.data())),
      static_cast<unsigned long long>(parent.size()));
  std::cout << "ROI End!!!" << std::endl;
  m5_exit(0);
  {'::swdb_profile::write();' if diagnostic else ''}
  // Continuation sees precisely the parent object returned by the timed call.
  bool valid = parent.size() == static_cast<size_t>(graph.num_nodes());
  uint64_t digest = UINT64_C(14695981039346656037);
  for (size_t i = 0; i < parent.size(); ++i) {{
    const int64_t value = parent[i];
    if (value < -1 || value >= graph.num_nodes()) valid = false;
    uint32_t bits = static_cast<uint32_t>(value);
    for (unsigned b = 0; b < 4; ++b) {{
      digest ^= (bits >> (8 * b)) & 255u;
      digest *= UINT64_C(1099511628211);
    }}
  }}
  if (valid) valid = BFSVerifier(graph, static_cast<NodeID>(source), parent);
  std::printf("SWDB_BFS_RESULT source=%lld vertices=%lld parent_count=%llu parent_fnv1a64=%016llx\\n",
      static_cast<long long>(source), static_cast<long long>(graph.num_nodes()),
      static_cast<unsigned long long>(parent.size()), static_cast<unsigned long long>(digest));
  std::printf("Verification: %s\\n", valid ? "PASS" : "FAIL");
  std::fflush(stdout);
  return valid ? 0 : 4;
}}
'''


def compile_candidate(args):
    store, request, data = _request(args, "compile")
    session = None
    error = None
    try:
        session, target, model = _prepare(args, "compile", store, request, data)
        roi = request.get('roi')
        author_diagnostic = roi == AUTHOR_ROI
        if roi not in {ROI, AUTHOR_ROI} or (author_diagnostic and request.get('diagnostic_regions') is not True):
            raise Failure("author traversal ROI requires source diagnostics; primary candidates require complete-call ROI")
        function = request.get("function")
        if not isinstance(function, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", function):
            raise Failure("selected BFS function must be one C++ identifier")
        if type(request.get("accelerated")) is not bool:
            raise Failure("accelerated must be explicit boolean; it does not establish observed path coverage")
        if type(request.get("diagnostic_regions", False)) is not bool:
            raise Failure("diagnostic_regions must be a boolean")
        if "discovery" in request and not request.get("diagnostic_regions"):
            raise Failure("discovery settings require diagnostic_regions")
        candidate = store.get(request.get("candidate"), "candidate")
        if not candidate:
            raise Failure("candidate source is unavailable")
        original = store.get(candidate["source_snapshot"], "source_snapshot")
        implementation = store.get(candidate['implementation'], 'implementation')
        expected_function = original.get('context', {}).get('function', implementation.get('function'))
        if function != expected_function:
            raise Failure('selected BFS function differs from the identified source implementation')
        if original["application"] not in {"gapbs", "dx100-gapbs"}:
            raise Failure("candidate application has no supported trusted BFS driver")
        source_root = artifacts.verify(candidate["artifact"])
        artifacts.check_protections(source_root, candidate["protections"])
        if author_diagnostic:
            if (candidate.get('artifact_role') != 'source_baseline' or original['application'] != 'dx100-gapbs'
                    or function not in {'DOBFS', 'DOBFSMAA'} or request['accelerated'] != (function == 'DOBFSMAA')):
                raise Failure('author diagnostic requires the unchanged identified DX100 source baseline and selected author function')
            for entry in candidate['artifact']['files']:
                if Path(entry['path']).suffix in {'.h', '.hpp', '.cc', '.cpp', '.c', '.S'}:
                    _file({'path': str(model / artifacts.relative_path(entry['path'])), 'sha256': entry['sha256']},
                          'unchanged author diagnostic source')
        _protect_model_headers(candidate, model)
        source_path = "src/bfs.cc" if original["application"] == "gapbs" else "benchmarks/gapbs/src/bfs.cc"
        source = source_root / source_path
        if not source.is_file():
            raise Failure("candidate BFS translation unit is missing")
        driver_text = driver(source, model, function)
        _protect_driver_macros(candidate, source_root, extra_text=driver_text)
        model_build = store.get(request.get("build_evaluation"), "evaluation")
        if (not model_build or model_build.get("outcome", {}).get("state") != "complete"
                or model_build["outcome"]["stage"] != "build"
                or model_build["context"]["model"]["revision"] != REVISION
                or (not request.get("fixture") and model_build["evidence_kind"] != "execution")):
            raise Failure("candidate compilation requires a completed compatible model build")
        if not request.get("fixture"):
            _file({"path": model_build["build"]["receipt"], "sha256": model_build["build"]["receipt_sha256"]}, "model build receipt")
        if request.get("fixture"):
            compiler = _file(request.get("fixture_compiler"), "fixture compiler")
        else:
            if "fixture_compiler" in request:
                raise Failure("fixture compiler cannot produce real candidate evidence")
            compiler = Path(shutil.which("g++-13") or "")
            if not compiler.is_absolute():
                raise Failure("GCC 13 candidate compiler is unavailable")
        build_directory = (artifacts.external_directory('/data1/yanruj/EvolveSWDB_builds') / data['id']
                           if data['context']['host'] == 'mbit10' else session.folder / 'build')
        build_directory.mkdir(exist_ok=False)
        data['context']['build_directory'] = str(build_directory)
        driver_path = build_directory / ('author_roi.cc' if author_diagnostic else 'complete_call.cc')
        binary = build_directory / "bfs"
        m5_source = model / "util/m5/build/x86/abi/x86/m5op.S"
        if not m5_source.is_file():
            raise Failure("pinned model m5ops assembly is unavailable")
        flags = ["-std=c++11", "-O3", "-Wall", "-g", "-fopenmp", "-DGEM5", "-DNUM_CORES=4",
                 f"-DTILE_SIZE={target['configuration']['tile_elements']}"]
        if author_diagnostic:
            flags = ['-std=c++11', '-O3', '-Wall', '-g3', '-fopenmp', '-DGEM5']
            if request['accelerated']:
                flags += ['-DNUM_CORES=4', f"-DTILE_SIZE={target['configuration']['tile_elements']}"]
        if request["accelerated"]:
            flags += ["-DMAA"]
        includes = [model / "include", model / "util/m5/src", model / "benchmarks/API", source.parent]
        if request.get('diagnostic_regions'):
            from swdb.dx100_diagnostic import prepare
            diagnostic = prepare(session, request, candidate, source_root, source, compiler, flags, includes, build_directory)
            selected_driver = driver
            if author_diagnostic:
                from swdb.dx100_author import driver as selected_driver
                diagnostic['difference'] += '; author reset/dump hooks activate/deactivate guards while forwarding original ROI events'
            diagnostic['roi'] = roi
            driver_text = selected_driver(Path(diagnostic['instrumented_source']['path']), model, function, diagnostic)
            _protect_driver_macros(candidate, source_root, extra_text=driver_text)
            data['context']['diagnostic'] = diagnostic
        driver_path.write_text(driver_text)
        command = [str(compiler), *flags, *('-I' + str(path) for path in includes),
            str(driver_path), str(m5_source), "-o", str(binary)]
        data.update(candidate=candidate["id"], source_snapshot=candidate["source_snapshot"], implementation=candidate["implementation"])
        verifier = next((guard for guard in candidate["protections"] if guard["kind"] == "verifier"), None)
        if not verifier or verifier["path"] != source_path:
            raise Failure("candidate has no protected BFS verifier in its translation unit")
        data["context"].update(candidate_sha256=candidate["artifact"]["sha256"], roi=roi, application=original["application"],
            source_path=source_path, function=function, accelerated_requested=request["accelerated"],
            model_build=model_build["id"], suppressed_internal_events=[] if author_diagnostic else SUPPRESSED,
            driver={"path": str(driver_path), "sha256": artifacts.file_hash(driver_path)},
            timed_source={"path": str(source), "sha256": artifacts.file_hash(source)},
            verifier_source={"path": str(source), "sha256": artifacts.file_hash(source),
                "symbol": "BFSVerifier", "protected_text_sha256": artifacts.digest(verifier["text"]),
                "bounds_check": "trusted driver validates parent length and values before BFSVerifier"})
        data["build"] = {"compiler": str(compiler), "compiler_sha256": artifacts.file_hash(compiler), "flags": flags,
            "driver": data["context"]["driver"], "m5ops": {"path": str(m5_source), "sha256": artifacts.file_hash(m5_source)},
            "binary": str(binary), "source_artifact": candidate["artifact"]}
        if not request.get('fixture'):
            version = _bounded_process(session, 'candidate_compiler_identity', [str(compiler), '--version'], 30,
                request['budget']['memory_gib'], request['budget']['storage_gib'])
            data['build']['compiler_version'] = version.read_text(errors='replace').splitlines()[:2]
        else:
            data['build']['compiler_version'] = ['explicit fixture compiler']
        data['build']['adapter'] = 'dx100.author_roi_diagnostic.v1' if author_diagnostic else 'dx100.complete_call.v1'
        if author_diagnostic:
            data['context']['internal_event_hooks'] = HOOKS
        session.save()
        _bounded_process(session, "candidate_compile", command, request["budget"]["build_seconds"],
                         request["budget"]["memory_gib"], request["budget"]["storage_gib"])
        artifacts.verify(candidate["artifact"])
        if not binary.is_file():
            raise StageFailure("missing_observation", "compiler produced no candidate binary")
        data["build"]["binary_sha256"] = artifacts.file_hash(binary)
        data["raw_artifacts"].append({"kind": "candidate_build", "artifact": artifacts.identify(build_directory)})
        data["outcome"] = {"state": "complete", "stage": "candidate_build", "reason": "Identified candidate compiled; no simulated correctness or timing inferred."}
    except (Failure, StageFailure, Stopped, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        error = exc
    return _finish(args, data, session, error)

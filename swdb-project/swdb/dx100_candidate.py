"""Compile identified BFS candidates against a pinned executable model.

Updated: 2026-09-26. Primary candidates use the complete-call ROI.
2026-10-03 ET (ticket 39): the trusted driver, its original-graph oracle, the
translation unit, the protected verifier and the graph-verification contract
come from the candidate kernel's plug-in. The BFS driver and oracle below are the
BFS plug-in's; their text is unchanged.
"""

import json
from pathlib import Path
import re
import shutil
import subprocess

from swdb import artifacts, kernels, workflow
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


ORIGINAL_GRAPH_ORACLE = r'''
// This evaluator-owned parser precedes all candidate headers. Its private
// arrays never alias Graph storage and it uses no candidate graph accessors.
namespace swdb_original {
class Graph {
  uint64_t nodes_, arcs_;
  int32_t source_;
  std::vector<uint64_t> offsets_;
  std::vector<int32_t> neighbors_, depth_, queue_;
  std::vector<uint8_t> parent_edge_;
  static uint64_t integer(FILE *stream, unsigned width) {
    uint8_t bytes[8];
    if (std::fread(bytes, 1, width, stream) != width)
      throw std::runtime_error("truncated original serialized graph");
    uint64_t value = 0;
    for (unsigned i = 0; i < width; ++i) value |= uint64_t(bytes[i]) << (8*i);
    if (bytes[width-1] & 128) throw std::runtime_error("negative serialized count or offset");
    return value;
  }
public:
  Graph(int argc, char **argv, unsigned width) : nodes_(0), arcs_(0), source_(-1) {
    const char *path = nullptr, *selected_source = nullptr;
    for (int i = 1; i < argc; ++i) {
      if (std::strcmp(argv[i], "-f") == 0 || std::strcmp(argv[i], "-r") == 0) {
        const bool file = std::strcmp(argv[i], "-f") == 0;
        if (i+1 == argc || (file ? path != nullptr : selected_source != nullptr))
          throw std::runtime_error("original graph requires one -f and one -r argument");
        if (file) path = argv[++i]; else selected_source = argv[++i];
      }
    }
    if (!path || !selected_source || (width != 4 && width != 8))
      throw std::runtime_error("original graph requires explicit serialized input and source");
    char *end = nullptr;
    errno = 0;
    const long long selected = std::strtoll(selected_source, &end, 10);
    if (errno || end == selected_source || *end || selected < 0 || selected > INT32_MAX)
      throw std::runtime_error("invalid original graph source");
    source_ = static_cast<int32_t>(selected);
    struct Input {
      FILE *stream;
      explicit Input(const char *name) : stream(std::fopen(name, "rb")) {
        if (!stream) throw std::runtime_error("original serialized graph cannot be opened");
      }
      ~Input() { std::fclose(stream); }
    } input(path);
    FILE *stream = input.stream;
    if (std::fseek(stream, 0, SEEK_END) != 0) throw std::runtime_error("original graph is not seekable");
    const long length = std::ftell(stream);
    if (length < 0 || std::fseek(stream, 0, SEEK_SET) != 0)
      throw std::runtime_error("original graph length is unavailable");
    const int directed = std::fgetc(stream);
    if (directed != 0 && directed != 1) throw std::runtime_error("invalid original graph direction");
    arcs_ = integer(stream, width);
    nodes_ = integer(stream, width);
    const uint64_t limit = UINT64_C(2147483648);
    // CSR + fixed-size depth/queue/edge work arrays + conservative small-object
    // reserve. Check before any graph-sized allocation; no capacity growth.
    if (!nodes_ || nodes_ > INT32_MAX || arcs_ > limit/4 || nodes_ > limit/17 ||
        (nodes_+1)*8 + arcs_*4 + nodes_*9 + 65536 > limit)
      throw std::runtime_error("original graph oracle exceeds 2 GiB extra-allocation budget");
    if (uint64_t(source_) >= nodes_) throw std::runtime_error("original source is outside graph");
    const uint64_t expected = 1 + 2*width + (1+directed)*((nodes_+1)*width + arcs_*4);
    if (uint64_t(length) != expected) throw std::runtime_error("serialized graph size differs from declared CSR");
    offsets_.resize(nodes_+1);
    neighbors_.resize(arcs_);
    depth_.assign(nodes_, -1);
    queue_.resize(nodes_);
    parent_edge_.assign(nodes_, 0);
    for (uint64_t u = 0; u <= nodes_; ++u) {
      offsets_[u] = integer(stream, width);
      if (offsets_[u] > arcs_ || (u && offsets_[u] < offsets_[u-1]))
        throw std::runtime_error("invalid original CSR offsets");
    }
    if (offsets_[0] || offsets_[nodes_] != arcs_)
      throw std::runtime_error("original CSR does not span its declared neighbors");
    if (arcs_ && std::fread(neighbors_.data(), 4, arcs_, stream) != arcs_)
      throw std::runtime_error("truncated original CSR neighbors");
    // Decode in place, including on a big-endian host, without a second buffer.
    for (uint64_t u = 0; u < nodes_; ++u) {
      int32_t previous = -1;
      for (uint64_t e = offsets_[u]; e < offsets_[u+1]; ++e) {
        const unsigned char *bytes = reinterpret_cast<const unsigned char *>(&neighbors_[e]);
        const uint32_t value = uint32_t(bytes[0]) | uint32_t(bytes[1])<<8 |
            uint32_t(bytes[2])<<16 | uint32_t(bytes[3])<<24;
        if (value >= nodes_ || value == u || int64_t(value) <= previous)
          throw std::runtime_error("original CSR is not normalized adjacency");
        neighbors_[e] = static_cast<int32_t>(value);
        previous = neighbors_[e];
      }
    }
    // Registration checks the inverse CSR/symmetry. The independent oracle
    // needs only outgoing adjacency; the exact full file length is checked.
  }
  uint64_t nodes() const { return nodes_; }
  int32_t source() const { return source_; }
  bool verify(const int32_t *parent, uint64_t count) {
    if (!parent || count != nodes_) return false;
    for (uint64_t u = 0; u < nodes_; ++u)
      if (parent[u] < -1 || int64_t(parent[u]) >= int64_t(nodes_)) return false;
    if (parent[source_] != source_) return false;
    uint64_t begin = 0, end = 0;
    depth_[source_] = 0;
    queue_[end++] = source_;
    while (begin < end) {
      const int32_t u = queue_[begin++];
      for (uint64_t e = offsets_[u]; e < offsets_[u+1]; ++e) {
        const int32_t v = neighbors_[e];
        if (depth_[v] == -1) {
          depth_[v] = depth_[u]+1;
          queue_[end++] = v;
        }
      }
    }
    for (uint64_t u = 0; u < nodes_; ++u)
      for (uint64_t e = offsets_[u]; e < offsets_[u+1]; ++e)
        if (parent[neighbors_[e]] == int64_t(u)) parent_edge_[neighbors_[e]] = 1;
    for (uint64_t v = 0; v < nodes_; ++v) {
      if (depth_[v] == -1) { if (parent[v] != -1) return false; }
      else if (v != uint64_t(source_) && (parent[v] < 0 || !parent_edge_[v] ||
               depth_[parent[v]] != depth_[v]-1)) return false;
    }
    return true;
  }
};
} // namespace swdb_original
'''


def driver(source, model, function, diagnostic=None, *, sg_offset_bytes=8, trusted_graph=True):
    if type(sg_offset_bytes) is not int or sg_offset_bytes not in {4, 8}:
        raise ValueError('serialized graph offsets must be 4 or 8 bytes')
    prefix = "\n".join(f"#define {name}(...) ((void)0)" for name in SUPPRESSED)
    suffix = "\n".join(f"#undef {name}" for name in SUPPRESSED)
    instrumentation = (f"#define SWDB_REGION_COUNT {len(diagnostic['regions'])}\n#include "
        + json.dumps(diagnostic['runtime']['path'])) if diagnostic else ""
    return f'''// Trusted generated evaluator, 2026-09-26. Complete BFS call only.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cerrno>
#include <cstring>
#include <stdexcept>
#include <vector>
#include <iostream>
#include {json.dumps(str(model / 'include/gem5/m5ops.h'))}
{ORIGINAL_GRAPH_ORACLE if trusted_graph else ''}
{instrumentation}
{prefix}
#define main swdb_gem5_original_main
#include {json.dumps(str(source))}
#undef main
{suffix}
int main(int argc, char **argv) {{
  try {{
  {f'swdb_original::Graph oracle(argc, argv, {sg_offset_bytes});' if trusted_graph else ''}
  CLApp cli(argc, argv, "SWDB complete-call BFS");
  if (!cli.ParseArgs()) return 2;
  Builder builder(cli);
  Graph graph = builder.MakeGraph();
  const int64_t source = cli.start_vertex();
  if (source < 0 || source >= graph.num_nodes()) return 3;
  {'if (uint64_t(graph.num_nodes()) != oracle.nodes() || source != oracle.source()) return 3;' if trusted_graph else ''}
  const uint64_t original_nodes = {'oracle.nodes()' if trusted_graph else 'graph.num_nodes()'};
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
  const auto *parent_values = parent.data();
  const uint64_t parent_count = parent.size();
  bool valid = parent_count == original_nodes;
  uint64_t digest = UINT64_C(14695981039346656037);
  for (uint64_t i = 0; i < parent_count && i < original_nodes; ++i) {{
    const int64_t value = parent_values[i];
    if (value < -1 || value >= int64_t(original_nodes)) valid = false;
    uint32_t bits = static_cast<uint32_t>(value);
    for (unsigned b = 0; b < 4; ++b) {{
      digest ^= (bits >> (8 * b)) & 255u;
      digest *= UINT64_C(1099511628211);
    }}
  }}
  if (valid) valid = {'oracle.verify(parent_values, parent_count)' if trusted_graph else 'BFSVerifier(graph, static_cast<NodeID>(source), parent)'};
  std::printf("SWDB_BFS_RESULT source=%lld vertices=%lld parent_count=%llu parent_fnv1a64=%016llx\\n",
      static_cast<long long>(source), static_cast<long long>(original_nodes),
      static_cast<unsigned long long>(parent_count), static_cast<unsigned long long>(digest));
  std::printf("Verification: %s\\n", valid ? "PASS" : "FAIL");
  std::fflush(stdout);
  return valid ? 0 : 4;
  }} catch (const std::exception &error) {{
    std::fprintf(stderr, "Trusted BFS evaluator: %s\\n", error.what());
    return 5;
  }}
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
        if roi not in {plugin.gem5_roi for plugin in kernels.plugins() if plugin.gem5_roi} | {AUTHOR_ROI} or (author_diagnostic and request.get('diagnostic_regions') is not True):
            raise Failure("author traversal ROI requires source diagnostics; primary candidates require complete-call ROI")
        function = request.get("function")
        if not isinstance(function, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", function):
            raise Failure("selected kernel function must be one C++ identifier")
        if type(request.get("accelerated")) is not bool:
            raise Failure("accelerated must be explicit boolean; it does not establish observed path coverage")
        if type(request.get("diagnostic_regions", False)) is not bool:
            raise Failure("diagnostic_regions must be a boolean")
        if type(request.get('parent_gather_diagnostic', False)) is not bool:
            raise Failure('parent_gather_diagnostic must be a boolean')
        if request.get('parent_gather_diagnostic') and (request.get('diagnostic_regions') or not request['accelerated']):
            raise Failure('parent-gather diagnostic requires an accelerated primary build without region instrumentation')
        if "discovery" in request and not request.get("diagnostic_regions"):
            raise Failure("discovery settings require diagnostic_regions")
        candidate = store.get(request.get("candidate"), "candidate")
        if not candidate:
            raise Failure("candidate source is unavailable")
        data.update(candidate=candidate["id"], source_snapshot=candidate["source_snapshot"],
                    implementation=candidate["implementation"])
        if candidate.get("proposal"):
            data["proposal"] = candidate["proposal"]
        original = store.get(candidate["source_snapshot"], "source_snapshot")
        implementation = store.get(candidate['implementation'], 'implementation')
        plugin = kernels.require((implementation or {}).get('kernel'), 'gem5 candidate compilation')
        if not author_diagnostic and roi != plugin.gem5_roi:
            raise Failure(f"{plugin.name} primary candidates require the {plugin.gem5_roi} complete-call ROI")
        if author_diagnostic and plugin is not kernels.BFS:
            raise Failure("author traversal diagnostics exist only for the BFS reference")
        expected_function = original.get('context', {}).get('function', implementation.get('function'))
        if function != expected_function:
            raise Failure(f'selected {plugin.name} function differs from the identified source implementation')
        if original["application"] not in plugin.source_paths:
            raise Failure(f"candidate application has no supported trusted {plugin.name} driver")
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
        source_path = plugin.source_paths[original["application"]]
        source = source_root / source_path
        if not source.is_file():
            raise Failure(f"candidate {plugin.name} translation unit is missing")
        sg_offset_bytes = 8 if original['application'] == 'gapbs' else 4
        driver_text = plugin.gem5_driver(source, model, function, sg_offset_bytes=sg_offset_bytes,
                                         trusted_graph=not author_diagnostic)
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
        binary = build_directory / plugin.binary_stem
        # SCons' build-tree copy is a symlink by default. Bind the regular
        # pinned source so execute can apply its unchanged input-file guard.
        m5_source = model / "util/m5/src/abi/x86/m5op.S"
        if m5_source.is_symlink() or not m5_source.is_file():
            raise Failure("pinned model m5ops assembly is unavailable")
        flags = ["-std=c++11", "-O3", "-Wall", "-g", "-fopenmp", "-DGEM5", "-DNUM_CORES=4",
                 f"-DTILE_SIZE={target['configuration']['tile_elements']}"]
        if author_diagnostic:
            flags = ['-std=c++11', '-O3', '-Wall', '-g3', '-fopenmp', '-DGEM5']
            if request['accelerated']:
                flags += ['-DNUM_CORES=4', f"-DTILE_SIZE={target['configuration']['tile_elements']}"]
        if request["accelerated"]:
            flags += ["-DMAA"]
        if request.get('parent_gather_diagnostic'):
            flags += ['-DSWDB_DXC_DIAGNOSTIC']
        includes = [model / "include", model / "util/m5/src", model / "benchmarks/API", source.parent]
        if request.get('diagnostic_regions'):
            from swdb.dx100_diagnostic import prepare
            diagnostic = prepare(session, request, candidate, source_root, source, compiler, flags, includes, build_directory)
            selected_driver = plugin.gem5_driver
            if author_diagnostic:
                from swdb.dx100_author import driver as selected_driver
                diagnostic['difference'] += '; author reset/dump hooks activate/deactivate guards while forwarding original ROI events'
            diagnostic['roi'] = roi
            driver_text = selected_driver(Path(diagnostic['instrumented_source']['path']), model, function, diagnostic,
                **({} if author_diagnostic else {'sg_offset_bytes': sg_offset_bytes}))
            _protect_driver_macros(candidate, source_root, extra_text=driver_text)
            data['context']['diagnostic'] = diagnostic
        driver_path.write_text(driver_text)
        command = [str(compiler), *flags, *('-I' + str(path) for path in includes),
            str(driver_path), str(m5_source), "-o", str(binary)]
        verifier = next((guard for guard in candidate["protections"] if guard["kind"] == "verifier"), None)
        if not verifier or verifier["path"] != source_path:
            raise Failure(f"candidate has no protected {plugin.name} verifier in its translation unit")
        data["context"].update(candidate_sha256=candidate["artifact"]["sha256"], roi=roi, application=original["application"],
            source_path=source_path, function=function, accelerated_requested=request["accelerated"],
            model_build=model_build["id"], suppressed_internal_events=[] if author_diagnostic else SUPPRESSED,
            driver={"path": str(driver_path), "sha256": artifacts.file_hash(driver_path)},
            timed_source={"path": str(source), "sha256": artifacts.file_hash(source)},
            verifier_source={"path": str(source), "sha256": artifacts.file_hash(source),
                "symbol": plugin.verifier_symbol, "protected_text_sha256": artifacts.digest(verifier["text"]),
                "bounds_check": plugin.gem5_bounds_check})
        if request.get('parent_gather_diagnostic'):
            data['context']['parent_gather_diagnostic'] = {'label': 'parent-gather race probes',
                'define': 'SWDB_DXC_DIAGNOSTIC', 'source_artifact_sha256': candidate['artifact']['sha256'],
                'performance_evidence': False}
        if not author_diagnostic:
            data['context']['graph_verification'] = plugin.graph_verification_contract(original['application'])
            data['context'][plugin.protected_verifier_key] = data['context']['verifier_source']
            data['context']['verifier_source'] = {
                **data['context']['driver'],
                'symbol': plugin.gem5_oracle_symbol, 'bounds_check': plugin.gem5_oracle_bounds_check}
        data["build"] = {"compiler": str(compiler), "compiler_sha256": artifacts.file_hash(compiler), "flags": flags,
            "driver": data["context"]["driver"], "m5ops": {"path": str(m5_source), "sha256": artifacts.file_hash(m5_source)},
            "binary": str(binary), "source_artifact": candidate["artifact"]}
        if not request.get('fixture'):
            version = _bounded_process(session, 'candidate_compiler_identity', [str(compiler), '--version'], 30,
                request['budget']['memory_gib'], request['budget']['storage_gib'])
            data['build']['compiler_version'] = version.read_text(errors='replace').splitlines()[:2]
        else:
            data['build']['compiler_version'] = ['explicit fixture compiler']
        data['build']['adapter'] = 'dx100.author_roi_diagnostic.v1' if author_diagnostic else 'dx100.complete_call.v2'
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

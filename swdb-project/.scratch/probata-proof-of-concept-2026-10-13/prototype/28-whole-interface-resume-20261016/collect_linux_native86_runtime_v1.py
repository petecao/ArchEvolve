"""2026-10-16 ET. Read-only passive inventory, never a tool/loader probe.

Root explicitly authorized this stdin script on mbit10. No remote files, leases,
project imports, compiler/linker/native/version queries or child processes.
BASE_REQUEST_JSON is filled locally with prior compact static path/pin metadata.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
import time


BASE_REQUEST_JSON = "__BASE_REQUEST_JSON__"
LLVM = Path("/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64")


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("passive inventory forbids " + event)


def elf(path):
    """Bounded ELF64LE program-header/dynamic strings only; no loader calls."""
    with Path(path).open("rb") as stream:
        head = stream.read(64)
        if head[:4] != b"\x7fELF": return {"ELF": False}
        if head[4:6] != b"\x02\x01": return {"ELF": True, "selected_64LE": False}
        machine = struct.unpack_from("<H", head, 18)[0]
        start = struct.unpack_from("<Q", head, 32)[0]
        size, count = struct.unpack_from("<HH", head, 54)
        if (count and size < 56) or count > 4096: raise ValueError("ELF program header bound")
        loads, dynamic, interpreter = [], None, []
        for index in range(count):
            stream.seek(start + size * index);raw = stream.read(56)
            if len(raw) != 56: raise ValueError("truncated ELF program header")
            kind, flags, offset, address, physical, file_bytes, memory_bytes, align = struct.unpack("<IIQQQQQQ", raw)
            if kind == 1: loads.append((address, offset, file_bytes))
            if kind == 2: dynamic = (offset, file_bytes)
            if kind == 3:
                if file_bytes > 4096: raise ValueError("ELF interpreter bound")
                stream.seek(offset);interpreter.append(stream.read(file_bytes).rstrip(b"\0").decode())
        entries = []
        if dynamic:
            if dynamic[1] > 1048576: raise ValueError("ELF dynamic table bound")
            stream.seek(dynamic[0]);data = stream.read(dynamic[1])
            for index in range(0, len(data) - 15, 16):
                tag, value = struct.unpack_from("<qQ", data, index)
                if tag == 0: break
                entries.append((tag, value))
        table = next((value for tag, value in entries if tag == 5), None)
        length = next((value for tag, value in entries if tag == 10), 0)
        strings = b""
        if table is not None:
            if length > 67108864: raise ValueError("ELF string table bound: " + str(path))
            matches = [(offset + table - address) for address, offset, extent in loads if address <= table and table + length <= address + extent]
            if len(matches) != 1: raise ValueError("ELF virtual string table mapping")
            stream.seek(matches[0]);strings = stream.read(length)
        def string(offset):
            end = strings.find(b"\0", offset)
            if not 0 <= offset < len(strings) or end < 0: raise ValueError("ELF dynamic string bounds")
            return strings[offset:end].decode()
        return {"ELF": True, "selected_64LE": True, "machine": machine, "interpreter": interpreter,
                "needed": [string(value) for tag, value in entries if tag == 1],
                "rpath": [string(value) for tag, value in entries if tag == 15],
                "runpath": [string(value) for tag, value in entries if tag == 29]}


def collect(request):
    started = time.monotonic()
    physical, aliases, trees = {}, {}, {}
    def resolve(path):
        path = Path(path)
        if not path.is_absolute(): raise ValueError("absolute inventory path required")
        pending, current, budget = list(path.parts[1:]), Path("/"), 128
        while pending:
            budget -= 1
            if budget < 0: raise ValueError("inventory alias chain bound")
            current = Path(os.path.normpath(current / pending.pop(0)))
            if current.is_symlink():
                target = os.readlink(current)
                aliases[str(current)] = {"path": str(current), "target": target, "resolved": str(current.resolve(strict=True))}
                following = Path(target) if Path(target).is_absolute() else current.parent / target
                pending = list(following.parts[1:]) + pending
                current = Path("/")
        return current.resolve(strict=True)
    def pin(path):
        real = resolve(path)
        if not real.is_file() or real.is_symlink(): raise ValueError("regular physical inventory input required")
        before = real.stat()
        with real.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        after = real.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("input changed while hashing")
        row = {"path": str(real), "bytes": after.st_size, "sha256": digest}
        physical[str(real)] = row
        return row
    def tree(path):
        root = resolve(path)
        if str(root) in trees: return
        if not root.is_dir(): raise ValueError("physical inventory directory required")
        files = []
        linked_directories = []
        for child in sorted(root.rglob("*")):
            mode = child.lstat().st_mode
            if stat.S_ISDIR(mode): continue
            if stat.S_ISLNK(mode):
                target = resolve(child)
                files.append({"relative": str(child.relative_to(root)), "symlink": os.readlink(child), "resolved": str(target)})
                if target.is_dir(): linked_directories.append(target)
                else: pin(child)
            elif stat.S_ISREG(mode):
                row = pin(child); files.append({"relative": str(child.relative_to(root)), "bytes": row["bytes"], "sha256": row["sha256"]})
            else: raise ValueError("special passive runtime input")
        trees[str(root)] = {"path": str(root), "files": files}
        for target in linked_directories: tree(target)
    differences = []
    for expected in request["prior_physical_inputs"]:
        actual = pin(expected["path"])
        if (actual["bytes"], actual["sha256"]) != (expected["bytes"], expected["sha256"]):
            differences.append({"requested_path": expected["path"], "expected": expected, "actual": actual})
    for path in request["additional_paths"]: pin(path)
    for pattern in ("libc.*", "libm.*", "libpthread.*", "librt.*", "libdl.*", "libresolv.*", "libgcc_s.*", "libmvec.*"):
        for path in sorted(Path("/usr/lib/x86_64-linux-gnu").glob(pattern)):
            if path.is_file() or path.is_symlink(): pin(path)
    sanitizer = LLVM / "lib/clang/22/lib/x86_64-unknown-linux-gnu"
    tree(sanitizer)
    tree(LLVM / "lib/clang/22/share")
    tree("/usr/lib/gcc/x86_64-linux-gnu/13")
    tree("/etc/ld.so.conf.d")
    selected_libraries = []
    for path in sorted((LLVM / "lib").rglob("*")):
        if path.name.startswith(("libc++.", "libc++abi.", "libunwind.")) and (path.is_file() or path.is_symlink()):
            selected_libraries.append({"requested_path": str(path), "physical": pin(path)})
    if not any(row["requested_path"].endswith("libc++.so") for row in selected_libraries):
        raise ValueError("LLVM libc++ linker selection absent")
    if not any("libclang_rt.asan" in row["path"] for row in physical.values()):
        raise ValueError("Clang ASan runtime archive inventory absent")
    absence = []
    for path in ("/etc/ld.so.preload",):
        if os.path.lexists(path): raise ValueError("unadmitted system loader preload exists")
        absence.append(path)
    wrapper = "/data/yanruj/EvolveSWDB_runs/probata-source-gate-native-20261015-1102-node0/compiler-bin/clang++"
    wrapper_pin = pin(wrapper)
    if wrapper_pin["sha256"] != "3c053dce26cf5ef22656f1ec9efe0cdf2911a37d5a910261895ac9c42e128fe4":
        raise ValueError("actual selected wrapper differs")
    linker = pin("/usr/bin/ld")
    driver = pin(LLVM / "bin/clang++")
    library_dirs = sorted({str(Path(row["physical"]["path"]).parent) for row in selected_libraries if ".so" in row["requested_path"]})
    graph, unresolved, multiple = {}, [], []
    pending = list(physical)
    while pending:
        path = pending.pop()
        if path in graph: continue
        information = elf(path);edges = []
        graph[path] = {"elf": information, "edges": edges}
        if not information.get("selected_64LE"): continue
        for interpreter in information["interpreter"]:
            row = pin(interpreter);edges.append({"interpreter": interpreter, "selected_static_candidate": row["path"]});pending.append(row["path"])
        prior = request["prior_static_edges"].get(path)
        for needed in information["needed"]:
            if "/" in needed: raise ValueError("unreviewed ELF needed path")
            selected = next((edge["selected_static_candidate"] for edge in prior or [] if edge.get("needed") == needed), None)
            if selected is None:
                origin = str(Path(path).parent)
                runtime_paths = [value.replace("${ORIGIN}", origin).replace("$ORIGIN", origin)
                                 for item in information["runpath"] or information["rpath"] for value in item.split(":") if value]
                if any("$" in value for value in runtime_paths): raise ValueError("unreviewed ELF runtime path token")
                order = (runtime_paths if not information["runpath"] else []) + library_dirs + (
                    runtime_paths if information["runpath"] else []) + request["search_roots"]
                candidates = []
                for directory in order:
                    candidate = Path(directory) / needed
                    if candidate.is_file():
                        row = pin(candidate)
                        if row["path"] not in candidates: candidates.append(row["path"])
                if not candidates:
                    unresolved.append({"object": path, "needed": needed});continue
                if len(candidates) > 1: multiple.append({"object": path, "needed": needed, "candidates": candidates})
                selected = candidates[0]
            row = pin(selected);edges.append({"needed": needed, "selected_static_candidate": row["path"]});pending.append(row["path"])
    if unresolved: raise ValueError("unresolved static native runtime dependencies: " + json.dumps(unresolved))
    result = {"date": "2026-10-16 ET", "passive_only": True, "admitted": False,
              "pins": [physical[name] for name in sorted(physical)], "aliases": [aliases[name] for name in sorted(aliases)],
              "trees": [trees[name] for name in sorted(trees)], "absence": absence,
              "loader_environment": {"LD_LIBRARY_PATH": ":".join(library_dirs)},
              "selected_stdlib_files": selected_libraries, "compiler": {"command": [wrapper], "version": "22.1.8",
                  "wrapper": wrapper_pin, "driver": driver, "linker": linker},
              "wrapper_source": Path(wrapper).read_text(), "prior_pin_differences": differences,
              "selected_loader_environment": {key: os.environ.get(key) for key in ("LD_PRELOAD", "LD_AUDIT", "LD_LIBRARY_PATH",
                  "LIBRARY_PATH", "COMPILER_PATH", "GCC_EXEC_PREFIX", "CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH")},
              "source_request": request["source_metadata"], "wall_seconds": time.monotonic() - started,
              "static_elf_closure": graph, "multiple_static_candidates": multiple, "unresolved": unresolved,
              "scope": "Fresh physical files/trees/link chains only. Prior static ELF dependency candidates remain OS-loader TCB; no loaded-code observation, compiler/linker/version/native job, lane acquisition or proof."}
    # Recheck every already hashed physical input before returning compact data.
    for expected in list(result["pins"]):
        if pin(expected["path"]) != expected: raise ValueError("passive runtime input changed after capture")
    return result


if __name__ == "__main__":
    sys.addaudithook(no_child)
    print(json.dumps(collect(json.loads(BASE_REQUEST_JSON)), indent=2, sort_keys=True))

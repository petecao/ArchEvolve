"""2026-10-16 ET. Exact reviewed function definitions; inert until root admission."""
import contextlib,hashlib,json,os,pathlib,re,shlex,shutil,stat,subprocess,sys
from pathlib import Path

def pin(path):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def recheck(rows):
    for row in rows:
        if pin(row["path"]) != row:
            raise ValueError("physical input changed: " + row["path"])


def physical_runtime(policy, closed):
    python = closed.verify_python_metadata(policy["python_surface_binding"])
    for path, expected in policy["runtime_files"].items():
        if pin(path)["sha256"] != expected: raise ValueError("runtime file differs: " + path)
    headers = policy["linux_header_surfaces"]
    if set(headers) != {"libc++", "clang-resource"}: raise ValueError("two exact LLVM header surfaces required")
    for name, header in headers.items():
        root = Path(header["path"])
        if closed._resolution(root, []) != root or root.is_symlink() or not root.is_dir():
            raise ValueError("physical LLVM header root required")
        rows = []
        for path in sorted(root.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode): continue
            if not stat.S_ISREG(mode): raise ValueError("nonregular LLVM header input")
            row = pin(path); rows.append({"relative": str(path.relative_to(root)), "bytes": row["bytes"], "sha256": row["sha256"]})
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        if len(rows) != header["count"] or digest != header["inventory_sha256"]:
            raise ValueError("LLVM header membership/content differs: " + name)
    native = policy["native_runtime"]
    if native.get("admitted") is not True or not native.get("pins") or not native.get("trees"):
        raise ValueError("complete prospectively admitted native link/runtime closure required")
    recheck(native["pins"])
    for alias in native["aliases"]:
        path = Path(alias["path"])
        if not path.is_symlink() or os.readlink(path) != alias["target"] or str(path.resolve(strict=True)) != alias["resolved"]:
            raise ValueError("native runtime link chain differs")
    for absent in native["absence"]:
        if os.path.lexists(absent): raise ValueError("native runtime absence obligation changed")
    for tree in native["trees"]:
        root = Path(tree["path"])
        if root.is_symlink() or not root.is_dir(): raise ValueError("physical native runtime root required")
        found = []
        for path in sorted(root.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode): continue
            if stat.S_ISLNK(mode):
                found.append({"relative": str(path.relative_to(root)), "symlink": os.readlink(path), "resolved": str(path.resolve(strict=True))})
            elif stat.S_ISREG(mode):
                row = pin(path); found.append({"relative": str(path.relative_to(root)), "bytes": row["bytes"], "sha256": row["sha256"]})
            else: raise ValueError("special native runtime input")
        if found != tree["files"]: raise ValueError("native runtime membership/content differs")
    return {"python": python, "runtime_files": len(policy["runtime_files"]), "native_pins": len(native["pins"]),
            "native_roots": len(native["trees"]), "scope": "physical source/runtime identity; no proof or native result"}


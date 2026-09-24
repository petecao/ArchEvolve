"""Required ISA: what an implementation's intrinsics need, what its build flags enable, and
what a machine can run. Extensions use the `lscpu` flag names of vocabulary isa_extensions.

The build enables an extension through an explicit `-m<extension>` flag (GCC/Clang
spelling, e.g. `-msse4.1` for `sse4_1`) or a `-march` value in MARCH. An x86-64 build
always has SSE and SSE2 (the x86-64 baseline). Flags apply left to right: a later
`-march` replaces the set, `-mno-<extension>` removes an extension and every extension that
implies it. A `-march` value not in MARCH (including `native`, which depends on the build
host) is reported rather than guessed.
"""

import shlex

BASELINE = {"sse", "sse2"}

# what enabling one extension also enables (GCC: -mavx512f implies -mavx2, and so on)
IMPLIES = {
    "sse2": {"sse"}, "pni": {"sse2"}, "ssse3": {"pni"}, "sse4_1": {"ssse3"}, "sse4_2": {"sse4_1"},
    "avx": {"sse4_2"}, "avx2": {"avx"}, "fma": {"avx"},
    "avx512f": {"avx2"}, "avx512cd": {"avx512f"}, "avx512dq": {"avx512f"}, "avx512bw": {"avx512f"},
    "avx512vl": {"avx512f"},
}

# compiler spelling (after -m) -> lscpu name, where they differ
SPELLING = {"sse3": "pni", "sse4.1": "sse4_1", "sse4.2": "sse4_2"}

def flag_for(ext):
    """The -m flag that enables one extension (lscpu `sse4_1` is `-msse4.1`)."""
    return "-m" + next((spelled for spelled, name in SPELLING.items() if name == ext), ext)


_V2 = {"sse", "sse2", "pni", "ssse3", "sse4_1", "sse4_2"}
_V3 = _V2 | {"avx", "avx2", "fma"}
_V4 = _V3 | {"avx512f", "avx512cd", "avx512dq", "avx512bw", "avx512vl"}

# -march values whose extensions the tool knows (GCC's x86 -march documentation), limited to
# the extensions in vocabulary isa_extensions
MARCH = {
    "x86-64": set(BASELINE), "x86-64-v2": _V2, "x86-64-v3": _V3, "x86-64-v4": _V4,
    "core2": {"sse", "sse2", "pni", "ssse3"}, "nehalem": _V2, "westmere": _V2,
    "sandybridge": _V2 | {"avx"}, "ivybridge": _V2 | {"avx"},
    "haswell": _V3, "broadwell": _V3, "skylake": _V3, "alderlake": _V3,
    "skylake-avx512": _V4, "cascadelake": _V4, "cooperlake": _V4, "cannonlake": _V4,
    "icelake-client": _V4, "icelake-server": _V4, "tigerlake": _V4, "sapphirerapids": _V4,
    "znver1": _V3, "znver2": _V3, "znver3": _V3, "znver4": _V4, "znver5": _V4,
}


def closure(extensions):
    found, todo = set(), list(extensions)
    while todo:
        ext = todo.pop()
        if ext not in found:
            found.add(ext)
            todo.extend(IMPLIES.get(ext, ()))
    return found


def enabled(flags, known):
    """(extensions the flags enable, [problem]) for a build.flags string. `known` is the
    vocabulary isa_extensions; -m flags that name no extension (-mtune=, -mfpmath=) are ignored."""
    have, problems = set(BASELINE), []
    try:
        words = shlex.split(flags or "")
    except ValueError as exc:
        return have, [f"cannot split the build flags: {exc}"]
    for word in words:
        if word.startswith("-march="):
            value = word.split("=", 1)[1]
            if value in MARCH:
                have = BASELINE | closure(MARCH[value])
            elif value == "native":
                problems.append("-march=native depends on the build host, so the tool cannot tell which "
                                "extensions it enables; use a named -march value or explicit -m<extension> flags")
            else:
                problems.append(f"unknown -march value {value!r}: the tool does not know which extensions it "
                                "enables; use explicit -m<extension> flags or add it to swdb/isa.py")
        elif word.startswith("-mno-"):
            ext = SPELLING.get(word[5:], word[5:])
            if ext in known:
                have = {e for e in have if ext not in closure({e})}
        elif word.startswith("-m") and "=" not in word:
            ext = SPELLING.get(word[2:], word[2:])
            if ext in known:
                have |= closure({ext})
    return have, problems


def required(impl, store):
    """{extension: [intrinsic IDs that need it]} for an implementation's uses_intrinsics."""
    need = {}
    for iid in impl.get("uses_intrinsics", []):
        intrinsic = store.get(iid, "intrinsic")
        for ext in (intrinsic or {}).get("isa_extensions", []):
            need.setdefault(ext, []).append(iid)
    return need


def machine_lacks(machine, need):
    """Why a machine cannot run code that needs `need` ({extension: intrinsics}), or None."""
    if not need:
        return None
    flags = machine.get("cpu", {}).get("flags")
    names = ", ".join(sorted(need))
    if not flags:
        return (f"machine {machine['id']!r} lists no CPU flags, so it is not known to support {names}; "
                "recapture it with swdb capture-machine (format 0.3)")
    missing = sorted(set(need) - set(flags))
    if missing:
        users = sorted({i for ext in missing for i in need[ext]})
        return (f"machine {machine['id']!r} lacks {', '.join(missing)}, which the implementation's intrinsics "
                f"need ({', '.join(users)})")
    return None

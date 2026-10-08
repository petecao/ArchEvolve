"""Batch source repair: typed reader and finite upper-bitmap metadata storage."""
import argparse
import hashlib
import json
import re
from pathlib import Path

PARENT_SHA = "56d6a6925f1c614eb951ded0e3769681dd8d19d12088dd547064192feae93c39"


def fix_upper(text, level):
    start = text.index("void construct_bitmap" + str(level) + "(")
    brace = text.index("{", start)
    end = brace + 1
    depth = 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    original = text[start:end]
    body = original
    previous = level - 1
    guard = f"""
    /* Finite complete groups with a proved consistent packed width only. */
    if (sizeof(unsigned long) != 8 || format->bitmap{previous}_bits <= 0 ||
        format->bitmap{previous}_bits > INT_MAX - 63 ||
        format->compression_ratio{previous} <= 0 ||
        format->compression_ratio{previous} != format->compression_ratio{level} ||
        format->bitmap{previous}_bits % format->compression_ratio{level}) {{
        fputs("Unsupported SMASH packed bitmap geometry\\n", stderr);
        exit(98);
    }}
"""
    position = body.index("{") + 1
    body = body[:position] + guard + body[position:]
    allocation = f"new_bitmap{previous} = (unsigned long*)malloc(sizeof(unsigned long));"
    assert body.count(allocation) == 1
    body = body.replace(
        allocation,
        f"""new_bitmap{previous} = (unsigned long*)calloc(1, sizeof(unsigned long));
    uint64_t new_bitmap{previous}_capacity_words = 1;
    if (!new_bitmap{previous}) {{
        fputs("Bitvector allocation failure\\n", stderr);
        exit(99);
    }}""",
    )
    pattern = rf"if\(new_bitmap{previous}_blocks % 64 ==0\)\s*new_bitmap{previous} = \(unsigned long\*\)realloc\(new_bitmap{previous},new_bitmap{previous}_blocks\*sizeof\(unsigned long\)\);"
    replacement = f"""const uint64_t needed_words =
                    ((uint64_t)new_bitmap{previous}_blocks *
                     format->compression_ratio{previous} + 63) / 64;
                if (needed_words > new_bitmap{previous}_capacity_words) {{
                    unsigned long *grown = (unsigned long*)realloc(
                        new_bitmap{previous}, needed_words * sizeof(unsigned long));
                    if (!grown) {{
                        fputs("Bitvector allocation failure\\n", stderr);
                        exit(99);
                    }}
                    new_bitmap{previous} = grown;
                    for (uint64_t word = new_bitmap{previous}_capacity_words;
                         word < needed_words; ++word)
                        new_bitmap{previous}[word] = 0;
                    new_bitmap{previous}_capacity_words = needed_words;
                }}"""
    body, count = re.subn(pattern, lambda m: replacement, body)
    assert count == 1
    return text[:start] + body + text[end:]


def materialize(parent, helper, output):
    raw = parent.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_SHA:
        raise ValueError("exact batched setter/constructor parent required")
    if (
        hashlib.sha256(helper.read_bytes()).hexdigest()
        != "3d57d1b93c5625ec385916d25bc7799fb82b72f5f331b14718eeb4b5328fd41e"
    ):
        raise ValueError("constructor helper drift")
    text = raw.decode()
    a = text.index("inline int read_bit(")
    b = text.index("void print_bitmaps(", a)
    reader = text[a:b]
    assert (
        reader.count("int mask;") == 1
        and reader.count("0x0000000000000001 << mask") == 1
    )
    reader = reader.replace("int mask;", "uint64_t mask;").replace(
        "0x0000000000000001 << mask", "UINT64_C(1) << mask"
    )
    text = text[:a] + reader + text[b:]
    text = fix_upper(fix_upper(text, 1), 2)
    output.mkdir(parents=True, exist_ok=False)
    (output / "bitmap.h").write_text(text)
    (output / helper.name).write_bytes(helper.read_bytes())
    receipt = {
        "parent_sha256": PARENT_SHA,
        "files": {
            f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in output.iterdir()
        },
        "scope": "source software fixes only: earlier constructor, setter, typed indexer; new reader width and upper metadata capacity/init. Complete same-ratio geometry only. NZA values remain undefined. No fullkernel/numerical grant.",
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--helper", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(materialize(a.parent, a.helper, a.output), indent=2))

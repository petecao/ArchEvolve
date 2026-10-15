#!/usr/bin/env python3
"""Ticket 42 (updated 2026-10-15 ET): check that the proof keeps ticket 41's approved statement.

Usage: check_approved.py <dir holding Vocabulary.v and Composition.v>

Composition.v may differ from the approved file only inside three marked blocks:
  (* BEGIN t42 imports *) ... (* END t42 imports *)   -> removed (one block, optional)
  (* BEGIN t42 lemmas *)  ... (* END t42 lemmas *)    -> removed (one block, optional)
  (* BEGIN t42 proof *)   ... (* END t42 proof *)     -> replaced by the approved
      "  (* OPEN ... *)\nAdmitted.\n" body of parallel_composition (exactly one block)
Each block starts at the beginning of a line and ends with its END marker and a newline.
The reconstructed text must hash to ticket 41's approved sha256; Vocabulary.v must be
unchanged. Exit 0 = approved statement kept, 1 = refused.
"""
import hashlib, re, sys
from pathlib import Path

APPROVED = {
    "Vocabulary.v": "081b558de2d94a0b37200b094d39af38eddf51546686a575f97dac2e3a6a3a3d",
    "Composition.v": "ffb5bda714b9fce5a13927a4860f6c85438821cdcdf3b4f1560f26a91eefd4f4",
}
OPEN_BODY = ("  (* OPEN — ticket 42 proves this; it must prove exactly this approved text. *)\n"
             "Admitted.\n")
BLOCKS = {"imports": "", "lemmas": "", "proof": OPEN_BODY}


# Inside the blocks: nothing that adds a section hypothesis, an axiom, an admitted step, a
# closed/reopened section, or a changed checker option.  (Notation tricks are caught by the
# harness, which compares the elaborated statement with the approved one.)
FORBIDDEN = re.compile(r"\b(Variables?|Hypothes(is|es)|Context|Section|End|Axioms?|Parameters?|"
                       r"Conjecture|Admitted|admit|give_up|Unset|Set|Abort|Module|Load|Declare|"
                       r"Require|Extern|Universe|Polymorphic|Typing|Guard|Positivity)\b")
IMPORT_LINE = re.compile(r"^From Stdlib Require Import( (Lia|Bool|PeanoNat|Permutation|Wf_nat|"
                         r"Wellfounded|Sorted|ListDec|Decidable|Lists\.List|Compare_dec|"
                         r"Arith|Relations|Program\.Wf|Setoid|Morphisms))+\.$")


def strip_comments(s):
    out, depth, i = [], 0, 0
    while i < len(s):
        if s.startswith("(*", i):
            depth += 1; i += 2
        elif s.startswith("*)", i) and depth:
            depth -= 1; i += 2
        else:
            if not depth:
                out.append(s[i])
            i += 1
    return "".join(out)


def guard(name, body):
    lines = body.split("\n")[1:-2]  # drop the marker lines
    code = strip_comments("\n".join(lines))
    if name == "imports":
        for ln in code.split("\n"):
            if ln.strip() and not IMPORT_LINE.match(ln.strip()):
                raise SystemExit(f"refused: imports block line not on the Stdlib allowlist: {ln!r}")
        return
    m = FORBIDDEN.search(code)
    if m:
        raise SystemExit(f"refused: forbidden word {m.group(0)!r} in the t42 {name} block")


def reconstruct(text):
    for name, replacement in BLOCKS.items():
        pattern = re.compile(r"^\(\* BEGIN t42 %s \*\)\n.*?^\(\* END t42 %s \*\)\n" % (name, name),
                             re.S | re.M)
        for m in pattern.finditer(text):
            guard(name, m.group(0))
        found = pattern.findall(text)
        if len(found) > 1 or (name == "proof" and len(found) != 1 and "BEGIN t42" in text):
            raise SystemExit(f"refused: block {name!r} appears {len(found)} times")
        text = pattern.sub(lambda _m: replacement, text)
    if "t42 " in text and ("BEGIN t42" in text or "END t42" in text):
        raise SystemExit("refused: unmatched t42 marker")
    return text


def main():
    folder = Path(sys.argv[1])
    ok = True
    voc = hashlib.sha256((folder / "Vocabulary.v").read_bytes()).hexdigest()
    if voc != APPROVED["Vocabulary.v"]:
        print(f"REFUSED Vocabulary.v sha256 {voc} != approved"); ok = False
    text = (folder / "Composition.v").read_text()
    rec = hashlib.sha256(reconstruct(text).encode()).hexdigest()
    if rec != APPROVED["Composition.v"]:
        print(f"REFUSED Composition.v statement sha256 {rec} != approved "
              f"(edit outside the t42 blocks)"); ok = False
    if ok:
        print("approved statement kept: Vocabulary.v", voc, "; Composition.v statement", rec)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

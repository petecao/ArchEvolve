# Predicate grammar provenance

Date: 2026-10-03 ET

Grammar: MaizeHPC/MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76`, `AgenticRefiner/refiner/predicate_dsl/grammar.py`. License: Apache-2.0 WITH LLVM-exception. User authorized proceeding under this license on 2026-10-03; Peter confirmation remains pending. Only parser imports changed; no runtime probes, Z3 or SMT port.

Parser: Lark 1.3.1, MIT, vendored from its installed distribution. Imports are isolated under `swdb._vendor.lark`; license texts are in `licenses/`.

Ported files:

- swdb/predicate_grammar.py
- swdb/_vendor/lark/__init__.py
- swdb/_vendor/lark/__pyinstaller/__init__.py
- swdb/_vendor/lark/__pyinstaller/hook-lark.py
- swdb/_vendor/lark/ast_utils.py
- swdb/_vendor/lark/common.py
- swdb/_vendor/lark/exceptions.py
- swdb/_vendor/lark/grammar.py
- swdb/_vendor/lark/grammars/__init__.py
- swdb/_vendor/lark/indenter.py
- swdb/_vendor/lark/lark.py
- swdb/_vendor/lark/lexer.py
- swdb/_vendor/lark/load_grammar.py
- swdb/_vendor/lark/parse_tree_builder.py
- swdb/_vendor/lark/parser_frontends.py
- swdb/_vendor/lark/parsers/__init__.py
- swdb/_vendor/lark/parsers/cyk.py
- swdb/_vendor/lark/parsers/earley.py
- swdb/_vendor/lark/parsers/earley_common.py
- swdb/_vendor/lark/parsers/earley_forest.py
- swdb/_vendor/lark/parsers/grammar_analysis.py
- swdb/_vendor/lark/parsers/lalr_analysis.py
- swdb/_vendor/lark/parsers/lalr_interactive_parser.py
- swdb/_vendor/lark/parsers/lalr_parser.py
- swdb/_vendor/lark/parsers/lalr_parser_state.py
- swdb/_vendor/lark/parsers/xearley.py
- swdb/_vendor/lark/reconstruct.py
- swdb/_vendor/lark/tools/__init__.py
- swdb/_vendor/lark/tools/nearley.py
- swdb/_vendor/lark/tools/serialize.py
- swdb/_vendor/lark/tools/standalone.py
- swdb/_vendor/lark/tree.py
- swdb/_vendor/lark/tree_matcher.py
- swdb/_vendor/lark/tree_templates.py
- swdb/_vendor/lark/utils.py
- swdb/_vendor/lark/visitors.py

- swdb/_vendor/lark/grammars/common.lark
- swdb/_vendor/lark/grammars/lark.lark
- swdb/_vendor/lark/grammars/python.lark
- swdb/_vendor/lark/grammars/unicode.lark
- swdb/_vendor/lark/py.typed

All vendored Python and grammar data files carry MIT SPDX and Lark-version provenance headers. The full-package typing marker retains its marker role and carries the same attribution; [PEP 561](https://peps.python.org/pep-0561/#packaging-type-information) specifies the marker by its presence. The MemAcc grammar alone carries Apache-2.0 WITH LLVM-exception.

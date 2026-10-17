"""2026-10-16 ET. Bounded, child-free public scientific binding controls."""
import ast
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main():
    # Reuse the already reviewed retained-lowering harness, changing only the
    # public module/test seam and its larger real, compact evidence fixture.
    source = (HERE/'run_pure_closed_evidence.py').read_text()
    source = source.replace("'green-v8'}", "'green-v8','green-v9','green-v10'}")
    source = source.replace('t25-closed-source-evidence-', 't25-closed-scientific-binding-')
    source = source.replace('signal.alarm(60)', 'signal.alarm(120)')
    source = source.replace("if stage!='red':names+=['vector_reallocation_closed_evidence.py']",
        "names+=['vector_reallocation_closed_evidence.py']\n    if stage!='red':names+=['vector_reallocation_closed_binding.py']")
    source = source.replace("test=output/'test_closed_source_evidence.py';test.write_bytes((PROJECT/'tests/test_vector_reallocation_closed_evidence.py').read_bytes())",
        "test=output/'test_closed_scientific_binding.py';test.write_bytes((PROJECT/'tests/test_vector_reallocation_closed_binding.py').read_bytes())\n    fixture=PROJECT/'tests/fixtures/proof/vector_closed_scientific_bundle'\n    target=output/'fixtures/proof/vector_closed_scientific_bundle'\n    if fixture.exists():\n        for item in fixture.rglob('*'):\n            assert not item.is_symlink()\n            if item.is_file():\n                dest=target/item.relative_to(fixture);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(item.read_bytes())")
    source = source.replace('raw_bytes<4*1024**2', 'raw_bytes<128*1024**2')
    source = source.replace("'whole_alarm_seconds':60", "'whole_alarm_seconds':120")
    ast.parse(source)
    namespace = {'__file__': str(HERE/'run_pure_closed_evidence.py'), '__name__': '__main__'}
    exec(compile(source, '<reviewed-child-free-binding-harness>', 'exec'), namespace)


if __name__ == '__main__':
    main()

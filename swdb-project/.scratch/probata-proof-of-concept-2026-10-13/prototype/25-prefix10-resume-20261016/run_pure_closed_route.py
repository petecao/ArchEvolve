"""2026-10-16 ET. Same child-free harness for the explicit source route seam."""
from pathlib import Path


HERE = Path(__file__).resolve().parent
source = (HERE/'run_pure_closed_binding.py').read_text()
source = source.replace('t25-closed-scientific-binding-', 't25-closed-source-route-')
source = source.replace('test_vector_reallocation_closed_binding.py', 'test_vector_reallocation_closed_route.py')
source = source.replace("names+=['vector_reallocation_closed_binding.py']",
                        "names+=['vector_reallocation_closed_binding.py','vector_reallocation_closed_route.py']")
exec(compile(source, '<reviewed-child-free-route-harness>', 'exec'),
     {'__file__': str(HERE/'run_pure_closed_binding.py'), '__name__': '__main__'})

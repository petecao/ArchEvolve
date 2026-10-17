"""Shared standard-library public parser stand-in builders; created 2026-10-16 ET.

Uses the committed fixture/method lineup and the actual Clang translator.
No solver result is produced by this builder.
"""
import yaml

from conftest import FIXTURES, REPO
from swdb import c_lowering


def method_version(identity):
    """A contract_fixture method version with the real Mac lineup, sequence 2 (current: frozen, from the
    frozen contract fixture). fix-21 (2026-10-14 ET): the lineup is the committed draft's
    (library/methods/probata-draft-1.yaml), so the two never drift; the translator is this checkout's tool."""
    data = yaml.safe_load((FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml").read_text())
    data.update(id="method.wp-tracer-fixture", sequence=2,
                description="Fixture method version with the real WP lineup of the Mac (ticket 21 tests).")
    data["lineup"] = yaml.safe_load((REPO / "library" / "methods" / "probata-draft-1.yaml").read_text())["lineup"]
    next(row for row in data["lineup"] if row["tool"] == "frama-c-wp")["flags"] += ["-rte-initialized", "@all", "-wp-no-filter-init"]
    data["c_lowering"]["translators"] = [identity["c_lowering"]]
    return data



def public_parser_standin_seed(tmp_path):
    import json
    import shutil
    import sys
    import yaml
    from conftest import FIXTURES, make_records, run_swdb
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    methods = library / 'methods'; methods.mkdir(parents=True)
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    method = method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method,sort_keys=False))
    marker = tmp_path/'wp-launched'
    frama = tmp_path/'frama.py'
    frama.write_text('import sys\nfrom pathlib import Path\n'
        'if "-version" in sys.argv: print("33.0");sys.exit(0)\n'
        'if "-wp" in sys.argv:\n'
        f' Path({str(marker)!r}).write_text("parser-error stand-in; no solver")\n'
        ' print("[kernel] wp_input.c:3: User Error: scripted fault\\nFrama-C aborted: invalid user input.");sys.exit(1)\n')
    why3 = tmp_path/'why3.conf'
    names = {'alt-ergo':'Alt-Ergo','z3':'Z3','cvc5':'CVC5'}
    why3.write_text(''.join(f'[prover]\nname = "{names[row["tool"]]}"\nversion = "{row["version"]}"\n'
                           'command = "/usr/bin/false"\n' for row in method['lineup'] if row['tool'] in names))
    def prove(*args, ok=True):
        done = run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
            '--runs-dir',tmp_path/'runs','--format','json',*args,env={
                'SWDB_FRAMA_C':f'{sys.executable} {frama}','WHY3CONFIG':str(why3),
                'SWDB_VERIFIER_LOCK':str(tmp_path/'standin-only.lock')})
        if not ok:
            return done
        assert done.returncode == 0, done.stdout + done.stderr
        return yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    return library, prove, marker

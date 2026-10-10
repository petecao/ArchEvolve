from pathlib import Path
import ast,difflib,hashlib,os,re,subprocess
root=Path('/Users/yanrujhou/CLionProjects/ArchEvolve');tmp=Path('/private/tmp');R='5e12a9796432654d88def24ecea617d16ca605b2'
patch=(tmp/'lanl17-certification-classification-prospective-r2-20261008-a5.diff').read_text();lines=patch.splitlines(True);old={};new={};i=0
while i<len(lines):
 assert lines[i].startswith('--- a/');name=lines[i][6:].rstrip('\n');i+=1;assert lines[i]=='+++ b/'+name+'\n';i+=1
 base=subprocess.check_output(['git','show',R+':'+name],cwd=root).decode();original=base.splitlines(True);out=[];cursor=0
 while i<len(lines) and not lines[i].startswith('--- a/'):
  m=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n',lines[i]);assert m;i+=1;start=int(m[1])-1;out+=original[cursor:start];cursor=start
  while i<len(lines) and not lines[i].startswith(('@@ ','--- a/')):
   row=lines[i];i+=1
   if row[0] in ' -':assert original[cursor]==row[1:];cursor+=1
   if row[0] in ' +':out.append(row[1:])
 out+=original[cursor:];old[name]=base;new[name]=''.join(out);ast.parse(new[name])
def replace(name,a,b):
 assert new[name].count(a)==1,(name,a);new[name]=new[name].replace(a,b)
replace('swdb-project/swdb/campaign_targets.py','except (Failure, UsageError) as exc:\n                # 2026-10-08 ET: keep the interrupted iteration;', 'except (Failure, UsageError, OSError) as exc:\n                # 2026-10-08 ET: keep the interrupted iteration;')
replace('swdb-project/swdb/certification_native.py',"raise Failure('BFS frontier logging statement or correctness check differs from the protected text')", "raise common.CandidateFailure('BFS frontier logging statement or correctness check differs from the protected text')")
replace('swdb-project/swdb/certification_blinding.py','instrument = lambda text: common.candidate_check(plugin.certification_instrument, text, frontier_hook=False) + driver','instrument = lambda text: plugin.certification_instrument(text, frontier_hook=False) + driver')
replace('swdb-project/swdb/certification_blinding.py','instrumented = instrument(source)','instrumented = common.candidate_check(instrument, source)')
test='swdb-project/tests/test_extensa_targets.py'
replace(test,'["compiler", "trusted_build", "configuration"]','["compiler", "trusted_build", "configuration", "trusted_io"]')
replace(test,'        else:\n            raise UsageError("typed library is invalid: fixture")','        elif failure == "trusted_io":\n            raise FileNotFoundError("trusted certification driver is unavailable: fixture")\n        else:\n            raise UsageError("typed library is invalid: fixture")')
new[test]+='''

@pytest.mark.parametrize("version", ["1.4", "1.5"])
@pytest.mark.parametrize("source", ["bool BFSVerifier() {}", "ANCHOR\nbool BFSVerifier() {}\nANCHOR",
                                   "ANCHOR", "ANCHOR\nbool BFSVerifier() {}\nbool BFSVerifier() {}"])
def test_native_authored_frontier_refusals_are_candidate_failures(tmp_path, monkeypatch, version, source):
    from swdb import certification, certification_common as common, certification_native as native
    from swdb import certification_procedures as procedures

    # Reach the actual authored-source guard without graph generation or a compiler/build.
    monkeypatch.setattr(certification, "matrix_graphs", lambda *a: [])
    monkeypatch.setattr(native, "staging_tail_graph", lambda *a: None)
    (tmp_path / "bfs.cc").write_text(source)
    profile = {"data": {"matrix": {"sources": [0], "threads": [1]},
                        "rewrite_scope": {"file": "bfs.cc"}}, "harness_v14": {},
               "hook": {"anchor": "ANCHOR", "hook_v14": "HOOK"}}
    with pytest.raises(common.CandidateFailure) as refused:
        native.certify_native_v14(tmp_path, tmp_path, tmp_path, profile, None,
                                  procedure=procedures.procedure(procedures.NATIVE, version))
    assert refused.value.check == "certification_aborted"


@pytest.mark.parametrize("phase", ["positive", "trusted_control"])
def test_blinded_instrumentation_distinguishes_authored_and_trusted_control_failures(tmp_path, monkeypatch, phase):
    from types import SimpleNamespace
    from swdb import certification, certification_blinding as blinding, certification_common as common
    from swdb import certification_legality as legality
    from swdb.cli import Failure

    (tmp_path / "candidate.cc").write_text("positive")
    driver = tmp_path / "driver.cc"
    driver.write_text("trusted driver")
    calls = []

    def instrument(text, **kwargs):
        calls.append(text)
        if text == "trusted_bad" or phase == "positive":
            raise Failure("instrumentation lacks protected anchor: fixture")
        return "instrumented positive"

    class Build:
        def __init__(self, *args, **kwargs):
            pass

        def candidate_object(self, *args, **kwargs):
            return {"returncode": 0}

        def link(self, *args, **kwargs):
            return {"returncode": 0}

    monkeypatch.setattr(certification, "matrix_graphs", lambda *a: [("tiny", tmp_path / "tiny.sg")])
    monkeypatch.setattr(certification, "legality_checks", lambda *a, **kw: [])
    monkeypatch.setattr(legality, "applies", lambda *a: True)
    monkeypatch.setattr(legality, "CONTROLS", {"trusted_bad_control": set()})
    monkeypatch.setattr(legality, "control", lambda *a, **kw: {
        "source": "trusted_bad", "fault": None, "site": "candidate_tokens"})
    plugin = SimpleNamespace(certification_source="candidate.cc", binary_stem="fixture",
                             certification_instrument=instrument, certification_controls={},
                             control_source=lambda sources: sources[0])
    procedure = SimpleNamespace(legality="v1", driver_path=lambda *a, **kw: driver)
    with pytest.raises(Failure) as refused:
        blinding.certify_candidate(tmp_path, tmp_path, tmp_path, [1], 1, [0], plugin=plugin,
                                   contract={"fixture": True}, procedure=procedure, build_class=Build)
    assert isinstance(refused.value, common.CandidateRefusal) is (phase == "positive")
    assert calls == (["positive"] if phase == "positive" else ["positive", "trusted_bad"])
'''
# Source-only literals above must preserve intended escaped newlines in the proposed Python test.
new[test]=new[test].replace('"ANCHOR\nbool BFSVerifier() {}\nANCHOR"','"ANCHOR\\nbool BFSVerifier() {}\\nANCHOR"').replace('"ANCHOR\nbool BFSVerifier() {}\nbool BFSVerifier() {}"','"ANCHOR\\nbool BFSVerifier() {}\\nbool BFSVerifier() {}"')
for name,body in new.items():ast.parse(body)
raw=''.join(''.join(difflib.unified_diff(old[name].splitlines(True),new[name].splitlines(True),fromfile='a/'+name,tofile='b/'+name)) for name in new).encode()
path=tmp/'lanl17-certification-classification-prospective-r3-20261008-a5.diff';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(raw)
print(path,len(raw),hashlib.sha256(raw).hexdigest());print('Reconstructed and AST parsed:',len(new),'existing files. No repository writes, module imports or tests.')

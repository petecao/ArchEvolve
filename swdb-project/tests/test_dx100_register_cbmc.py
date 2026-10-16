"""2026-10-16 ET. Public adapter admission, no compiler/CBMC process probes."""
import argparse,os
from pathlib import Path
import pytest,yaml
from conftest import REPO
from swdb import cbmc_adapter
from swdb.library import Library
from testkit.dx100_register import register_semantics

def test_current_partial_register_fixture_refuses_all_cbmc_factory_routes_before_forwarding(tmp_path,monkeypatch):
 library=tmp_path/'library';(library/'proof_semantics').mkdir(parents=True)
 data=yaml.safe_load((REPO/'library/proof_semantics/dx100_bfs_0_1.yaml').read_text())
 register_semantics(data,library)
 (library/'proof_semantics/register.yaml').write_text(yaml.safe_dump(data,sort_keys=False))
 active=Library(library)
 marker=tmp_path/'must-not-probe-cbmc'
 probe=tmp_path/'cbmc';probe.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\nexit 99\n');probe.chmod(0o755)
 monkeypatch.setenv('SWDB_CBMC',str(probe))
 # Exercise the public production factory with real current library metadata.
 # No collaborator is replaced. This check precedes ordinary, script and
 # whole-function forwarding; it does not validate a proof unit or run a tool.
 for whole,script in [(None,None),('/unadmitted-whole-function',None),(None,Path('/unadmitted-script'))]:
  args=argparse.Namespace(whole_function=whole)
  with pytest.raises(cbmc_adapter.AdapterError,match='partial register fixture is admitted only through its WP route'):
   cbmc_adapter.CbmcAdapter.from_args(args,script,library=active,contract=None,method=None)
 assert not marker.exists()

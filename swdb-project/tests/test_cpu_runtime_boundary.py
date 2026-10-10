"""Portable runtime preflight evidence boundary; no native accuracy claim. 2026-10-07 ET."""
from pathlib import Path

from swdb import cpu_pairing


def test_unsupported_host_retains_counted_identity_without_runtime_admission(monkeypatch):
    monkeypatch.setattr(cpu_pairing.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(cpu_pairing.subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(AssertionError('unsupported host must not run ldd')))
    native={'loaded_libraries': {
        'libstdc++.so.6': {'sha256': 'a'*64, 'path': '/unavailable/libstdc++.so.6'},
        'libc.so.6': {'sha256': 'b'*64, 'path': '/unavailable/libc.so.6'}}, 'missing': []}
    result=cpu_pairing.runtime_admission({'observation_contract': {'native_runtime': native}}, Path('/unavailable/native'))
    assert result['scope']=='protected_binary_preflight'
    assert result['counted']=={'libstdc++.so.6': 'a'*64, 'libc.so.6': 'b'*64}
    assert result['resolved'] is None
    assert result['missing']==['actual_native_runtime_identity']
    assert result['accuracy_claim'] is False


def test_contract_fixture_runtime_cannot_claim_native_accuracy():
    native={'loaded_libraries': {}, 'missing': ['shared_cache_file_hash_unavailable']}
    result=cpu_pairing.runtime_admission({'observation_contract': {'native_runtime': native}}, Path('/unavailable/native'), fixture=True)
    assert result['scope']=='contract_fixture_only'
    assert result['counted']==native
    assert result['missing']==[] and result['accuracy_claim'] is False


def test_unavailable_runtime_query_withholds_relation_without_losing_counted_facts(monkeypatch):
    monkeypatch.setattr(cpu_pairing.platform,'system',lambda:'Linux')
    def timeout(*args,**kwargs):
        raise cpu_pairing.subprocess.TimeoutExpired('ldd',15)
    monkeypatch.setattr(cpu_pairing.subprocess,'run',timeout)
    native={'loaded_libraries':{'libc.so.6':{'sha256':'b'*64}},'missing':[]}
    result=cpu_pairing.runtime_admission({'observation_contract':{'native_runtime':native}},Path('/unavailable/native'))
    assert result['counted']=={'libc.so.6':'b'*64}
    assert result['resolved'] is None and result['missing']==['actual_native_runtime_identity']
    assert result['accuracy_claim'] is False

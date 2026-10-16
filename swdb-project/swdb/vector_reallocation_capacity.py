"""Pinned C++17 implementation capacity witness; created 2026-10-16 ET.

This qualifies the source implementation only. The new C-model capacity post
still requires proof, and every caller must derive its growth/no-growth branch.
"""
import hashlib
from pathlib import Path

HEADERS={
    '__vector/vector.h':'7e2a0317d9ed2be3427b5e5e04f18ea8e8553da397924080855bf191e90aed0e',
    '__memory/allocate_at_least.h':'5279f57d0e12aa6e4e781634e11a8173f791b59992e0319647ff831ae556a570',
}


def bind(provenance):
    if provenance.get('verdict')!='passed' or provenance.get('library',{}).get('id')!='libc++-22.1.8':
        raise ValueError('the exact-capacity source witness requires admitted libc++22.1.8')
    command=provenance.get('context',{}).get('command',[])
    frontend=provenance.get('effective',{}).get('frontend',[])
    for argv in (command,frontend):
        standards=[a for a in argv if a.startswith(('-std=','--std='))]
        if standards!=['-std=c++17'] or any(a.startswith(('-D','-U')) for a in argv):
            raise ValueError('the exact-capacity witness requires unmodified C++17 macro selection')
    sources=[]
    for suffix,digest in HEADERS.items():
        rows=[row for row in provenance.get('headers',[]) if row['path'].endswith('/'+suffix)]
        if len(rows)!=1 or rows[0]['sha256']!=digest:
            raise ValueError('the actual count/value capacity implementation changed: '+suffix)
        path=Path(rows[0]['path'])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('the actual capacity header bytes changed: '+suffix)
        sources.append({'header_suffix':suffix,'path':str(path),'sha256':digest})
    return {'id':'vector-cpp17-capacity-1','language':'C++17','library':'libc++-22.1.8',
            'scope':'implementation-specific count/value capacity; not a universal vector standard theorem',
            'sources':sources,'caller_premises_added':[],'model_postcondition_to_prove':'capacity == count',
            'semantic_support':'count/value uses __vallocate(n); pre-C++23 allocate_at_least returns requested n',
            'proof_status':'header correspondence only; model and caller branch proofs remain required'}

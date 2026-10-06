"""Explicit service interposer/allocator controls. Created: 2026-10-06 ET."""
import copy
import os

SCOPE={'format':'swdb.service-control-environment.v1','prefixes':['MALLOC_'],
    'exact_variables':['GLIBC_TUNABLES','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH','DYLD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES'],
    'absence_semantics':'null_or_absent_is_unset_under_declared_scope'}


def snapshot():
    values={key:value for key,value in os.environ.items() if key.startswith('MALLOC_')}
    values.update({key:os.environ.get(key) for key in SCOPE['exact_variables']})
    return {'control_environment':values,'control_environment_scope':copy.deepcopy(SCOPE)}


def valid(context):
    values=context.get('control_environment')
    return context.get('control_environment_scope')==SCOPE and isinstance(values,dict) and \
        set(SCOPE['exact_variables'])<=set(values) and all((key.startswith('MALLOC_') or key in SCOPE['exact_variables']) and \
        (value is None or isinstance(value,str)) for key,value in values.items())

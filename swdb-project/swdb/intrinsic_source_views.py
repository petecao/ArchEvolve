"""Outcome-free intrinsic variants bound to shipped code and selected macros. 2026-10-06 ET."""
import re
from swdb import artifacts,paths
from swdb.cli import Failure


def source_file(reference):
    roots={'library':paths.HOME/'library','project':paths.HOME,'repository':paths.HOME.parent}
    root=roots.get(reference.get('root'))
    if root is None:raise Failure('unsupported shipped source root')
    relative=reference.get('path','')
    file=(root/relative).resolve()
    if not relative or not file.is_relative_to(root.resolve()) or not file.is_file():
        raise Failure('shipped source must be an available safe relative path')
    if artifacts.file_hash(file)!=reference.get('sha256'):
        raise Failure('shipped source hash differs: '+relative)
    return file


def problems(intrinsic):
    view=intrinsic.get('source_view')
    if view is None:return []
    issues=[]
    try:
        file=source_file(view['source'])
        if not re.search(r'\b'+re.escape(intrinsic['name'])+r'\s*\(',file.read_text()):
            issues.append('source view does not declare its exact C symbol')
        if re.search(r'^\s*#\s*(?:line\b|[0-9]+)',file.read_text(),re.M):
            issues.append('source view refuses debug #line overrides')
    except (Failure,OSError) as exc:issues.append(str(exc))
    return issues


def effective_defines(flags):
    result={};items=iter(flags)
    for flag in items:
        if flag in ('-D','-U'):flag+=next(items,'')
        if flag.startswith('-D'):
            name,_,value=flag[2:].partition('=');result[name]=value or '1'
        elif flag.startswith('-U'):result.pop(flag[2:],None)
    return result


def require_compiled_view(intrinsic,flags):
    view=intrinsic.get('source_view')
    if view is None:raise Failure('functional command requires an immutable intrinsic source_view')
    issues=problems(intrinsic)
    if issues:raise Failure('intrinsic source_view: '+'; '.join(issues))
    macros=effective_defines(flags)
    for name in view['compile_defines']:
        if macros.get(name)!='1':raise Failure('compiled backend differs from intrinsic source_view define '+name)
    for name in view.get('compile_undefines',[]):
        if name in macros:raise Failure('compiled backend differs from intrinsic source_view undefined macro '+name)
    return {'intrinsic':intrinsic['id'],'intrinsic_sha256':artifacts.digest(intrinsic),
        'source_view_sha256':artifacts.digest(view),'source':view['source'],
        'backend':view['backend'],'compile_defines':macros,'evidence_scope':view['evidence_scope']}

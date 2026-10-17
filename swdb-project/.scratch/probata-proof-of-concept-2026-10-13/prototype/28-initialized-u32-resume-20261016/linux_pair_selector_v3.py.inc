# 2026-10-16 ET. Exact inherited root alias repair; producer stays absolute-only.
def normalize_compiler_selector(env,wanted):
 command=wanted['command']
 if not isinstance(command,list)or len(command)!=1 or not isinstance(command[0],str)or not pathlib.Path(command[0]).is_absolute():
  raise ValueError('compiler normalization requires one admitted absolute command')
 expected=wanted['command_executable']
 if pathlib.Path(command[0]).resolve()!=pathlib.Path(expected['path']).resolve():
  raise ValueError('compiler normalization command and pinned wrapper differ')
 try:selected=shlex.split(env.get('SWDB_CLANG',shlex.join(command)))
 except (ValueError,TypeError):raise ValueError('malformed inherited Clang selector')from None
 observed=None
 if selected!=command:
  if selected!=['clang++']:raise ValueError('inherited Clang selector is not the exact reviewed alias')
  executable=shutil.which('clang++',path=env.get('PATH'))
  if executable is None or pathlib.Path(executable).resolve()!=pathlib.Path(expected['path']).resolve():
   raise ValueError('reviewed Clang alias resolves to another physical wrapper')
  if not pathlib.Path(executable).is_file()or pin(executable)['sha256']!=expected['sha256']:
   raise ValueError('reviewed Clang alias wrapper bytes differ')
  observed=pin(executable)
 env['SWDB_CLANG']=shlex.join(command)
 return {'input_tokens':selected,'selected_absolute_tokens':list(command),'reviewed_alias_used':selected==['clang++'],
         'resolved_alias_wrapper':observed,'scope':'exact root-export alias normalized only after pinned path/bytes check; producer absolute-command requirement unchanged'}

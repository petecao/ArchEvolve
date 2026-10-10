"""NOT RUN: new sparse-retirement transition/sequence contracts only.

Future parent-authorized execution AST-lifts closed exact method/statement
slices from pinned sparse R1 and R2. All filesystem, native, plan, process and
publication boundaries are in-memory SYNTHETIC values. No production module,
main, import, native command, deletion, Git, proc, SSH or old test suite runs.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from types import SimpleNamespace
import unittest

SOURCES = {
    'original': ('/private/tmp/lanl_sparse_retire_consumed_source_guard_20261008_a1_r1.py',
                 165299, 'd108a7201161c6676941bccbc31292f9ac08c61835bbcd1bee0df2c01fe22e04'),
    'corrected': ('/private/tmp/lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py',
                  166145, '4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26'),
}
SYNTHETIC_UID = 17001
BASE_TEXT = '/SYNTHETIC/checkouts'
PRIMARY_TEXT = '/SYNTHETIC/primary'
ROW = 'row-a'
HEAD = 'a'*40
PIN_BYTES = b'SYNTHETIC_PIN'
PIN_SHA = hashlib.sha256(PIN_BYTES).hexdigest()
FIELDS = ('dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns')
PATTERN = b'/swdb-project/library/\n'
LIBRARY_BODY = b'SYNTHETIC_LIBRARY_BYTES\n'


class VirtualPath(PurePosixPath):
    model = None

    def lstat(self):
        return self.model.statistics[str(self)]


def source_ast(which):
    path, size, digest = SOURCES[which]
    with Path(path).open('rb') as source:
        body = source.read(256*1024+1)
    if len(body) != size or hashlib.sha256(body).hexdigest() != digest:
        raise AssertionError('pinned_source_bytes_changed')
    return ast.parse(body)


def environment(which):
    module = source_ast(which)
    guard = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'Guard')
    methods = {n.name: n for n in guard.body if isinstance(n, ast.FunctionDef)}
    names = ('Refused','require','sha','canonical','stamp','tracked_mode_equivalent')
    pure = [copy.deepcopy(n) for n in module.body
            if isinstance(n, (ast.FunctionDef,ast.ClassDef)) and n.name in names]
    if len(pure) != len(names):
        raise AssertionError('closed_pure_inventory')
    assignments = []
    for name in ('LIMITS','RETIREMENT_STAT_FIELDS','RETIREMENT_PATTERN'):
        assignments.append(copy.deepcopy(next(n for n in module.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))))
    selected = [copy.deepcopy(methods[n]) for n in ('library_snapshot','retained_poststate','completed_names','git')]
    original_perform = methods['perform']
    first = next(i for i,n in enumerate(original_perform.body) if isinstance(n,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id == 'first' for t in n.targets))
    end = next(i for i,n in enumerate(original_perform.body) if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant)
                       and t.slice.value == 'admitted' for t in n.targets))
    operation = copy.deepcopy(original_perform)
    operation.name = 'exact_operation_slice'
    operation.body = copy.deepcopy(original_perform.body[first:end])
    if ast.dump(ast.Module(body=operation.body,type_ignores=[]),include_attributes=False) != \
            ast.dump(ast.Module(body=original_perform.body[first:end],type_ignores=[]),include_attributes=False):
        raise AssertionError('exact_statement_slice')
    closed = ast.Module(body=pure+assignments+[ast.ClassDef(name='ExactMethods',bases=[],keywords=[],
        body=selected+[operation],decorator_list=[])],type_ignores=[])
    if any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(closed)):
        raise AssertionError('no_target_imports')
    context = {'__name__':'SYNTHETIC_closed_slice','hashlib':hashlib,'json':json,'stat':stat,
        'P':VirtualPath,'BASE':VirtualPath(BASE_TEXT),'PRIMARY':VirtualPath(PRIMARY_TEXT),
        'ROWS':{ROW:{'head':HEAD}},'UID':SYNTHETIC_UID,'now':lambda:'SYNTHETIC_TIME',
        '__file__':'/SYNTHETIC/source.py'}
    ast.fix_missing_locations(closed)
    # This definition lift happens ONLY in the later explicitly reviewed batch.
    exec(compile(closed,'<SYNTHETIC sparse exact slices>','exec'),context)
    return context, methods


def original_object(relative, inode, mode, size=0, names=()):
    kind = 0 if stat.S_ISDIR(mode) else 1
    full = [2097,inode,mode,SYNTHETIC_UID,17001,2 if kind == 0 else 1,size,8,100,200]
    sx = [8191,8191,0,0,136,True,1800000000,inode]
    ordered = sorted(names)
    digest = hashlib.sha256(b'\0'.join(x.encode() for x in ordered)).hexdigest() if kind == 0 else None
    return [relative,full,sx,len(ordered) if kind == 0 else None,digest,kind]


class PoststateWorld:
    """Synthetic external facts; production poststate comparisons remain exact."""
    def __init__(self, context):
        self.context = context
        self.args = SimpleNamespace(select=[ROW])
        self.selected = [VirtualPath(BASE_TEXT)/ROW]
        self.statistics = {}
        self.witnesses = {}
        self.names = {}
        self.bodies = {}
        self.events = []
        self.library_baselines = {}
        self.admin_baselines = {}
        self.facts = {'completed_retirements':[]}
        checkout = VirtualPath(BASE_TEXT)/ROW
        admin = VirtualPath(PRIMARY_TEXT)/'.git/worktrees'/ROW
        pointer = ('gitdir: '+str(admin)+'\n').encode()
        co = [original_object('.',1,stat.S_IFDIR|0o775,names=('.git','swdb-project')),
              original_object('.git',2,stat.S_IFREG|0o664,len(pointer)),
              original_object('swdb-project',3,stat.S_IFDIR|0o775,names=('library',)),
              original_object('swdb-project/library',4,stat.S_IFDIR|0o775,names=('item.txt',)),
              original_object('swdb-project/library/item.txt',5,stat.S_IFREG|0o664,len(LIBRARY_BODY))]
        ao = [original_object('.',11,stat.S_IFDIR|0o2777,names=('HEAD','index')),
              original_object('HEAD',12,stat.S_IFREG|0o664,4),
              original_object('index',13,stat.S_IFREG|0o664,9)]
        self.original_checkout = {ROW:{'root':str(checkout),'objects':{x[0]:copy.deepcopy(x) for x in co},
            'git_pointer':{'sha256':hashlib.sha256(pointer).hexdigest()}}}
        self.original_admin = {ROW:{'root':str(admin),'objects':{x[0]:copy.deepcopy(x) for x in ao}}}
        for root,objects in ((checkout,co),(admin,ao)):
            for obj in objects:
                self.add(root/obj[0],obj)
        self.bodies[str(checkout/'.git')] = pointer
        self.bodies[str(checkout/'swdb-project/library/item.txt')] = LIBRARY_BODY
        self.bodies[str(admin/'HEAD')] = b'HEAD'
        self.bodies[str(admin/'index')] = b'INDEX-new'
        self.admin_baselines[ROW] = {'HEAD':{'sha256':hashlib.sha256(b'HEAD').hexdigest(),
                                           'stat':context['stamp'](self.statistics[str(admin/'HEAD')])}}
        info = original_object('info',21,stat.S_IFDIR|0o2700,names=('sparse-checkout',))
        pattern = original_object('info/sparse-checkout',22,stat.S_IFREG|0o600,len(PATTERN))
        self.add(admin/'info',info); self.add(admin/'info/sparse-checkout',pattern)
        self.names[str(admin)] = ['HEAD','index','info']
        self.statistics[str(admin)].st_ctime_ns += 1
        self.witnesses[str(admin)][0][9] += 1
        self.bodies[str(admin/'info/sparse-checkout')] = PATTERN
        # Index replacement is the specifically permitted native outcome.
        self.statistics[str(admin/'index')].st_ino = 33
        self.witnesses[str(admin/'index')][0][1] = 33
        self.witnesses[str(admin/'index')][1][-1] = 33
        self.retirement_transition_witnesses = {ROW:{
            'new_info_inode':copy.deepcopy(self.witnesses[str(admin/'info')]),
            'new_pattern_inode':copy.deepcopy(self.witnesses[str(admin/'info/sparse-checkout')])}}
        VirtualPath.model = self
        self.library_baselines[ROW] = context['ExactMethods'].library_snapshot(self,ROW,True)

    def add(self,path,obj):
        full,sx = copy.deepcopy(obj[1]),copy.deepcopy(obj[2])
        self.statistics[str(path)] = SimpleNamespace(**{'st_'+k:v for k,v in zip(FIELDS,full)})
        self.witnesses[str(path)] = [full,sx]
        if obj[5] == 0:
            # Names are populated explicitly from the closed synthetic facts.
            self.names[str(path)] = []
            if obj[0] == '.':
                self.names[str(path)] = ['.git','swdb-project'] if '/checkouts/' in str(path) else ['HEAD','index']
            elif obj[0] == 'swdb-project': self.names[str(path)] = ['library']
            elif obj[0] == 'swdb-project/library': self.names[str(path)] = ['item.txt']
            elif obj[0] == 'info': self.names[str(path)] = ['sparse-checkout']

    def debit_metadata(self,**unused): pass
    def inode_witness(self,path): return copy.deepcopy(self.witnesses[str(path)])
    def directory_names(self,path,expected):
        if self.context['stamp'](self.statistics[str(path)]) != expected:
            raise AssertionError('synthetic_directory_stat_interval')
        return list(self.names[str(path)])
    def private_ancestor(self,path): return True
    def read(self,path,cap=None):
        return self.bodies[str(path)],self.context['stamp'](self.statistics[str(path)])
    def administration_read(self,path,cap=None): return self.read(path,cap)
    def git(self,path,*args):
        self.events.append(('git',str(path),args))
        if args[:3] == ('ls-tree','-r','-z'):
            oid = hashlib.sha1(b'blob '+str(len(LIBRARY_BODY)).encode()+b'\0'+LIBRARY_BODY).hexdigest()
            return ('100644 blob '+oid+'\tswdb-project/library/item.txt\0').encode()
        raise AssertionError('synthetic_poststate_Git_whitelist')
    def sparse_index(self,name): return {'SYNTHETIC_closed_expanded_index':name}
    def shared_administration(self): return {'SYNTHETIC_shared_originals_unchanged':True}
    def library_snapshot(self,name,full_bytes=False):
        return self.context['ExactMethods'].library_snapshot(self,name,full_bytes)

    def mutate_inode(self,relative,mode=None):
        path=str(VirtualPath(PRIMARY_TEXT)/'.git/worktrees'/ROW/relative)
        self.statistics[path].st_ino += 100
        self.witnesses[path][0][1] += 100
        self.witnesses[path][1][-1] += 100
        if mode is not None:
            self.statistics[path].st_mode = mode
            self.witnesses[path][0][2] = mode


class OperationWorld:
    def __init__(self,context,fail=None):
        self.context = context
        self.args = SimpleNamespace(select=['row-a','row-b'],retire=True,
            plan='/SYNTHETIC/plan.json',plan_sha256=PIN_SHA)
        self.facts = {'completed_retirements':[]}
        self.current_retirement = None
        self.retirement_transition_witnesses = {}
        self.retirement_poststates = {}
        self.library_baselines = {'row-a':{},'row-b':{}}
        self.plan = {'protected_file_pins':[]}
        self.own_sha = PIN_SHA
        self.raw_before = {'SYNTHETIC_RAW':'same'}
        self.events = []
        self.fail = fail

    def completed_names(self): return self.context['ExactMethods'].completed_names(self)
    def gate(self):
        self.events.append(('initial_metadata',tuple(self.completed_names())))
        return {'trees':{'row-a':{},'row-b':{}},'processes':{'performed':False}}
    def left(self): return 1000
    def pre_retire_gate(self,name): self.events.append(('full_byte_precheck',name))
    def read(self,path,cap=None): return PIN_BYTES,{}
    def leases(self): self.events.append(('leases',)); return {}
    def shared_administration(self,full_bytes=False): self.events.append(('shared',full_bytes)); return {}
    def process_references(self,scope=None):
        self.events.append(('fresh_references',None if scope is None else tuple(scope),tuple(self.completed_names())))
    def create_private_sparse_pattern(self,name):
        if self.current_retirement is None or self.current_retirement['stage'] != 'before_private_pattern':
            raise AssertionError('marker_required_before_new_admin')
        self.events.append(('private_pattern',name)); return {'SYNTHETIC_pattern':name}
    def private_pattern_transition(self,name,pin):
        self.events.append(('transition',name)); return {'SYNTHETIC_transition':name}
    def git(self,path,*args):
        name=path.name
        if args != ('read-tree','-m','-u','HEAD') or self.current_retirement['stage'] != 'native_read_tree_started' \
                or name not in self.retirement_transition_witnesses:
            raise AssertionError('one_exact_marked_native_operation')
        self.events.append(('native_read_tree',name))
        if self.fail == 'native': raise self.context['Refused']('SYNTHETIC_native_failure')
    def close_retirement(self,name):
        self.events.append(('poststate_proof_and_private_original',name))
        if self.fail == 'poststate': raise self.context['Refused']('SYNTHETIC_poststate_failure')
        self.retirement_poststates[name] = {'SYNTHETIC_poststate':name}
        return {'row':name,'private_original_poststate_pin':{'SYNTHETIC_pin':name}}
    def retain_git(self): self.events.append(('retained_Git',))
    def protect(self): self.events.append(('protected',))
    def stable_inventory(self): self.events.append(('stable',tuple(self.completed_names())))
    def receipts_and_raw(self): self.events.append(('final_full_RAW',)); return self.raw_before
    def aliases_and_sources(self): self.events.append(('final_aliases',))
    def pinned(self,pin,cap=None): self.events.append(('private_original_bytes',)); return b'SYNTHETIC'
    def library_snapshot(self,name,full_bytes=False): self.events.append(('library_full',name,full_bytes))
    def retained_poststate(self,name,full_bytes=False):
        self.events.append(('final_poststate',name,full_bytes)); return self.retirement_poststates[name]


class SparseRetirementContracts(unittest.TestCase):
    def poststate(self,which,mutation=None):
        context,unused = environment(which)
        model=PoststateWorld(context)
        if mutation: mutation(model)
        return context['ExactMethods'].retained_poststate(model,ROW,True),model

    def test_unchanged_transition_and_replaced_index_accept(self):
        result,model=self.poststate('corrected')
        self.assertEqual(result['git_admin']['index']['stat'][1],33)
        self.assertEqual(result['git_admin']['info']['stat'][1],21)
        self.assertEqual(result['git_admin']['info/sparse-checkout']['stat'][1],22)
        self.assertFalse(result['original_full_checkout_continuity_claimed'])

    def test_same_byte_pattern_swap_original_negative_corrected_refusal(self):
        result,unused=self.poststate('original',lambda m:m.mutate_inode('info/sparse-checkout'))
        self.assertEqual(result['git_admin']['info/sparse-checkout']['bytes_sha256'],hashlib.sha256(PATTERN).hexdigest())
        with self.assertRaisesRegex(Exception,'retirement_private_pattern_transition_inode_or_mode_changed'):
            self.poststate('corrected',lambda m:m.mutate_inode('info/sparse-checkout'))

    def test_same_name_info_swap_original_negative_corrected_refusal(self):
        result,unused=self.poststate('original',lambda m:m.mutate_inode('info'))
        self.assertEqual(result['git_admin']['info']['names'],['sparse-checkout'])
        with self.assertRaisesRegex(Exception,'retirement_private_pattern_transition_inode_or_mode_changed'):
            self.poststate('corrected',lambda m:m.mutate_inode('info'))

    def test_transition_permissions_refuse_even_with_same_bytes(self):
        for relative,mode in (('info',stat.S_IFDIR|0o775),('info/sparse-checkout',stat.S_IFREG|0o666)):
            with self.subTest(relative=relative):
                self.poststate('original',lambda m:m.mutate_inode(relative,mode))
                with self.assertRaisesRegex(Exception,'retirement_private_pattern_transition_inode_or_mode_changed'):
                    self.poststate('corrected',lambda m:m.mutate_inode(relative,mode))

    def test_library_actual_bytes_and_extra_admin_entry_refuse(self):
        def changed_library(m): m.bodies[str(VirtualPath(BASE_TEXT)/ROW/'swdb-project/library/item.txt')]=b'CHANGED_same_length____\n'
        with self.assertRaisesRegex(Exception,'retirement_library_Git_blob_or_mode_changed'):
            self.poststate('corrected',changed_library)
        def extra_lock(m): m.names[str(VirtualPath(PRIMARY_TEXT)/'.git/worktrees'/ROW)].append('index.lock')
        with self.assertRaisesRegex(Exception,'retirement_admin_root_children'):
            self.poststate('corrected',extra_lock)

    def test_exact_marked_sequence_checks_before_each_native_and_final(self):
        context,unused=environment('corrected'); model=OperationWorld(context)
        context['ExactMethods'].exact_operation_slice(model)
        self.assertEqual(model.completed_names(),['row-a','row-b'])
        self.assertIsNone(model.current_retirement)
        self.assertFalse(model.facts['initial_checks']['processes']['performed'])
        for name in ('row-a','row-b'):
            begin=model.events.index(('private_pattern',name))
            self.assertIn(('full_byte_precheck',name),model.events[:begin])
            self.assertEqual(model.events[begin-1][0:2],('fresh_references',(name,)))
            self.assertEqual(model.events[begin:begin+4], [('private_pattern',name),('transition',name),
                ('native_read_tree',name),('poststate_proof_and_private_original',name)])
        final=model.events.index(('final_full_RAW',))
        self.assertIn(('stable',('row-a','row-b')),model.events[:final])
        self.assertEqual([r for r in model.events if r[0]=='fresh_references'][-1],
            ('fresh_references',None,('row-a','row-b')))

    def test_native_and_postproof_failure_keep_uncertain_marker_without_completion(self):
        for stage in ('native','poststate'):
            with self.subTest(stage=stage):
                context,unused=environment('corrected'); model=OperationWorld(context,stage)
                with self.assertRaisesRegex(Exception,'SYNTHETIC_'+stage+'_failure'):
                    context['ExactMethods'].exact_operation_slice(model)
                self.assertEqual(model.completed_names(),[])
                self.assertEqual(model.current_retirement['row'],'row-a')
                self.assertIn(model.current_retirement['stage'],
                    ('native_read_tree_started','native_returned_poststate_pending'))
                self.assertIn('row-a',model.retirement_transition_witnesses)

    def test_native_Git_uses_original_objects_at_both_entry_points(self):
        context,methods=environment('corrected'); seen=[]
        model=SimpleNamespace(selected=[],current_retirement=None,completed_names=lambda:[],
            left=lambda:1000,privacy_gate=lambda:None,native_git=lambda:None)
        def native_run(argv,**kwargs):
            seen.append(argv); return SimpleNamespace(returncode=0,stdout=b'ORIGINAL',stderr=b'')
        context['subprocess']=SimpleNamespace(run=native_run,PIPE='SYNTHETIC_PIPE')
        self.assertEqual(context['ExactMethods'].git(model,VirtualPath(PRIMARY_TEXT),'rev-parse','HEAD'),b'ORIGINAL')
        self.assertEqual(seen[0][:2],['/usr/bin/git','--no-replace-objects'])
        # Exact source-only check for the otherwise unexecuted direct batch call.
        calls=[n for n in ast.walk(methods['tree']) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
               and n.func.value.id=='subprocess' and n.func.attr=='run']
        self.assertEqual(len(calls),1)
        self.assertEqual([n.value for n in calls[0].args[0].elts[:2]],
                         ['/usr/bin/git','--no-replace-objects'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

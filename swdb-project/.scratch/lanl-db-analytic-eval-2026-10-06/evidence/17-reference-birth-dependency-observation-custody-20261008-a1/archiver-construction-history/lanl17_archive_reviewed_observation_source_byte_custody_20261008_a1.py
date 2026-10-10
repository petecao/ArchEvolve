"""Fixed local byte-custody archiver. SOURCE PREPARATION 2026-10-08 ET; NOT RUN.

Only an explicitly parent-reviewed finite original list may be archived. No
selected source import, scientific command, SSH, Git mutation, issue or map edit.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import subprocess
import time
from zoneinfo import ZoneInfo

W = Path('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve')
PREFIX = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-reference-birth-dependency-observation-custody-20261008-a1'
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
MAX_ROWS = 192
MAX_ORIGINAL = 64 * 1024 * 1024
MAX_ORIGINAL_TOTAL = 512 * 1024 * 1024
MAX_STREAM_TOTAL = 2 * 1024 * 1024 * 1024
MAX_METADATA = 2 * 1024 * 1024
GZIP_THRESHOLD = 1024 * 1024
SECONDS = 1800
PLAIN_SUFFIXES = {'.py', '.md', '.diff', '.c', '.h', '.sh', '.txt', '.dsc'}
STAMP_KEYS = ('dev', 'ino', 'mode', 'nlink', 'uid', 'gid', 'size', 'mtime_ns', 'ctime_ns')

class Refused(Exception):
    pass

def require(ok, code):
    if not ok:
        raise Refused(code)

def stamp(s):
    return {key: getattr(s, 'st_' + key) for key in STAMP_KEYS}

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode()

def unique(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, 'duplicate_JSON_key')
        obj[key] = value
    return obj

def strict_json(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(Refused('nonfinite_JSON')))

def components(path):
    require(path.is_absolute() and str(path) == str(path.resolve(strict=True)),
            'noncanonical_or_redirected_path')
    for p in list(reversed(path.parents)) + [path]:
        require(not stat.S_ISLNK(p.lstat().st_mode), 'symlink_component')
    return path

class Archive:
    def __init__(self, args):
        self.args = args
        self.end = time.monotonic() + SECONDS
        self.charged = 0
        self.inputs = {}
        self.written = []
        self.created = False

    def tick(self):
        require(time.monotonic() < self.end, 'archive_deadline')

    def charge(self, n):
        self.tick()
        self.charged += n
        require(self.charged <= MAX_STREAM_TOTAL, 'stream_byte_limit')

    def open_original(self, path, cap):
        self.tick()
        path = components(Path(path))
        require(Path('/private/tmp') in path.parents, 'original_outside_private_tmp')
        s = stamp(path.lstat())
        require(stat.S_ISREG(s['mode']) and s['nlink'] == 1 and s['uid'] == os.getuid()
                and not s['mode'] & 0o7000 and 0 <= s['size'] <= cap,
                'original_type_owner_link_size')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        require(stamp(os.fstat(fd)) == s, 'original_changed_before_open')
        return path, fd, s

    def read_pin(self, path, cap, expected=None):
        path, fd, before = self.open_original(path, cap)
        h = hashlib.sha256()
        parts = []
        n = 0
        try:
            while True:
                self.tick()
                block = os.read(fd, min(1024 * 1024, cap - n + 1))
                if not block:
                    break
                self.charge(len(block)); n += len(block)
                require(n <= cap, 'original_returned_bytes_excess')
                h.update(block); parts.append(block)
            require(n == before['size'] and before == stamp(os.fstat(fd)) == stamp(path.lstat()),
                    'original_byte_identity_changed')
        finally:
            os.close(fd)
        pin = {'path': str(path), 'bytes': n, 'sha256': h.hexdigest(), 'stat': before}
        if expected is not None:
            require(n == expected['bytes'] and pin['sha256'] == expected['sha256'], 'original_pin_mismatch')
        self.inputs[str(path)] = pin
        return b''.join(parts), pin

    def hash_pin(self, path, expected):
        path, fd, before = self.open_original(path, MAX_ORIGINAL)
        h = hashlib.sha256(); n = 0
        try:
            while True:
                self.tick(); block = os.read(fd, min(1024 * 1024, MAX_ORIGINAL - n + 1))
                if not block: break
                self.charge(len(block)); n += len(block)
                require(n <= MAX_ORIGINAL, 'original_returned_bytes_excess'); h.update(block)
            require(n == before['size'] and before == stamp(os.fstat(fd)) == stamp(path.lstat()),
                    'original_changed_during_hash')
        finally:
            os.close(fd)
        require(n == expected['original_bytes'] and h.hexdigest() == expected['original_sha256'],
                'explicit_original_byte_pin_mismatch')
        self.inputs[str(path)] = {'path': str(path), 'bytes': n, 'sha256': h.hexdigest(), 'stat': before}

    def git(self, *args):
        self.tick()
        cmd = ['git', '--no-replace-objects', '-c', 'core.hooksPath=/dev/null',
               '-c', 'core.fsmonitor=false', '-c', 'diff.external=', '-C', str(W), *args]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=min(120, max(0.1, self.end-time.monotonic())),
            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_OPTIONAL_LOCKS': '0',
                 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'})
        require(result.returncode == 0 and len(result.stdout) <= MAX_METADATA
                and len(result.stderr) <= MAX_METADATA, 'read_only_Git_refused_or_output_limit')
        return result.stdout

    def source_state(self, initial=False):
        components(W)
        require(self.git('rev-parse', 'HEAD').decode().strip() == self.args.expected_head,
                'worktree_HEAD_not_expected')
        require(self.git('rev-parse', 'codex/lanl-ticket11-source-c').decode().strip() == C,
                'retained_C_ref_changed')
        require(not self.git('diff', '--no-ext-diff', '--name-only')
                and not self.git('diff', '--cached', '--no-ext-diff', '--name-only'),
                'prior_tracked_or_staged_changes')
        tree = self.git('ls-tree', '-r', '-z', self.args.expected_head)
        if initial:
            require(not self.git('status', '--porcelain', '-z', '--untracked-files=all'), 'initial_worktree_not_clean')
            self.original_tree = tree
            self.branch = self.git('branch', '--show-current').decode().strip()
        else:
            require(tree == self.original_tree and self.git('branch', '--show-current').decode().strip() == self.branch,
                    'prior_tree_modes_or_branch_changed')
        core = self.git('ls-tree', '-r', '-z', C, '--', 'swdb-project/swdb')
        current = self.git('ls-tree', '-r', '-z', self.args.expected_head, '--', 'swdb-project/swdb')
        require(core == current, 'C_core_namespace_changed')
        require(sum(bool(x) and x.split(b'\t',1)[1].endswith(b'.py') for x in core.split(b'\0')) == 185,
                'C_Python_module_count_not_185')
        records = self.git('ls-tree', '-r', '-z', self.args.expected_head, '--', 'swdb-project/records')
        count = sum(bool(x) and x.split(b'\t',1)[1].endswith((b'.yaml',b'.yml')) for x in records.split(b'\0'))
        require(count == 704, 'canonical_YAML_count_not_704')
        return {'HEAD': self.args.expected_head, 'branch': self.branch,
                'prior_tracked_entries': sum(bool(x) for x in tree.split(b'\0')),
                'prior_tree_bytes_sha256': hashlib.sha256(tree).hexdigest(),
                'C_ref': C, 'Python_module_count': 185, 'canonical_YAML_count': count,
                'F6_inherited_from_exact_C_namespace': F6}

    def validate_policy(self, row):
        policy = row['original_policy']
        if policy['kind'] != 'original_sealed_JSON':
            require(policy['kind'] in {'original_unsealed_JSON','opaque_exact_original_bytes'}, 'original_policy_kind')
            return
        raw, _ = self.read_pin(row['original_path'], MAX_ORIGINAL,
                               {'bytes':row['original_bytes'],'sha256':row['original_sha256']})
        obj = strict_json(raw)
        key = policy['identity_key']
        require(key == 'identity_sha256' and obj[key] == policy['identity_sha256'], 'original_seal_value_changed')
        flag = policy['canonical_ensure_ascii']
        require(isinstance(flag,bool) and ('canonical_ensure_ascii' in obj) == policy['flag_originally_present'],
                'original_seal_policy_presence_changed')
        require(obj.get('canonical_ensure_ascii', True) == flag, 'original_seal_policy_changed')
        expected = hashlib.sha256(json.dumps({k:v for k,v in obj.items() if k!=key},
            sort_keys=True,separators=(',',':'),ensure_ascii=flag,allow_nan=False).encode()).hexdigest()
        require(expected == obj[key], 'original_seal_failed')

    def fresh_file(self, relative):
        p = PurePosixPath(relative)
        require(not p.is_absolute() and '..' not in p.parts and str(p) == relative
                and p.parts and p.name not in {'README.md','manifest.json'}, 'stored_relative_path')
        target = self.dest / relative
        current = self.dest
        for part in p.parts[:-1]:
            current /= part
            if not current.exists(): os.mkdir(current,0o700)
            require(not current.is_symlink() and current.is_dir() and current.stat().st_uid == os.getuid()
                    and stat.S_IMODE(current.stat().st_mode) == 0o700, 'fresh_output_parent')
        fd = os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        self.written.append(PREFIX+'/'+relative)
        return target,fd

    def copy(self, row):
        path, fd, before = self.open_original(row['original_path'], MAX_ORIGINAL)
        target, outfd = self.fresh_file(row['stored_relative_path'])
        h=hashlib.sha256(); n=0
        try:
            with os.fdopen(outfd,'wb',closefd=False) as out:
                sink = gzip.GzipFile(filename='',mode='wb',fileobj=out,compresslevel=9,mtime=0) if row['storage_codec']=='gzip_mtime0' else out
                try:
                    while True:
                        self.tick(); block=os.read(fd,min(1024*1024,MAX_ORIGINAL-n+1))
                        if not block: break
                        self.charge(len(block));n+=len(block);require(n<=MAX_ORIGINAL,'copy_byte_limit')
                        h.update(block);sink.write(block)
                finally:
                    if sink is not out: sink.close()
                out.flush();os.fsync(outfd)
            require(before==stamp(os.fstat(fd))==stamp(path.lstat()),'original_changed_while_storing')
        finally:
            os.close(fd);os.close(outfd)
        require(n==row['original_bytes'] and h.hexdigest()==row['original_sha256'],'stored_source_byte_mismatch')
        stored=target.lstat();require(stat.S_ISREG(stored.st_mode) and stored.st_uid==os.getuid()
              and stored.st_nlink==1 and stat.S_IMODE(stored.st_mode)==0o600,'stored_file_type_owner_mode')
        sh=hashlib.sha256(); seen=0
        with target.open('rb') as f:
            while True:
                self.tick();part=f.read(1024*1024)
                if not part:break
                self.charge(len(part));seen+=len(part);sh.update(part)
        require(stamp(target.lstat())==stamp(stored),'stored_file_changed_during_hash')
        dh=hashlib.sha256(); dn=0
        with target.open('rb') as f:
            stream=gzip.GzipFile(fileobj=f,mode='rb') if row['storage_codec']=='gzip_mtime0' else f
            try:
                while True:
                    self.tick();part=stream.read(min(1024*1024,row['original_bytes']-dn+1))
                    if not part:break
                    self.charge(len(part));dn+=len(part);require(dn<=row['original_bytes'],'decompression_excess')
                    dh.update(part)
            finally:
                if stream is not f:stream.close()
        require(dn==row['original_bytes'] and dh.hexdigest()==row['original_sha256']
                and stamp(target.lstat())==stamp(stored),'stored_original_decode_mismatch')
        return {**row,'stored_bytes':seen,'stored_sha256':sh.hexdigest(),
                'stored_stat':stamp(stored),'decompressed_original_bytes':dn,
                'decompressed_original_sha256':dh.hexdigest(),'decompression_equals_original_byte_pin':True}

    def write_metadata(self, name, body):
        require(name in {'README.md','manifest.json'} and len(body)<=MAX_METADATA,'archive_metadata_limit')
        fd=os.open(self.dest/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        self.written.append(PREFIX+'/'+name)
        try:
            with os.fdopen(fd,'wb',closefd=False) as out:out.write(body);out.flush();os.fsync(fd)
        finally:os.close(fd)
        require((self.dest/name).read_bytes()==body,'archive_metadata_readback')

    def perform(self):
        self_raw,self_pin=self.read_pin(Path(__file__),MAX_METADATA)
        require(self_pin['sha256']==self.args.source_sha256,'archiver_self_source_pin')
        raw,invpin=self.read_pin(self.args.inventory,MAX_METADATA)
        require(invpin['sha256']==self.args.inventory_sha256,'inventory_file_pin')
        inv=strict_json(raw)
        require(inv['format']=='swdb.local-observation-source-byte-custody.explicit-inventory.v1'
                and inv['state']=='parent_reviewed_final_explicit_inventory'
                and inv['archive_relative_path']==PREFIX and not inv['pending_explicit_extensions']
                and not inv['missing_named_originals'],'final_explicit_inventory_required')
        rr,rpin=self.read_pin(self.args.parent_review,MAX_METADATA)
        require(rpin['sha256']==self.args.parent_review_sha256,'parent_review_file_pin')
        review=strict_json(rr)
        require(review['format']=='swdb.local-observation-byte-custody-parent-review.v1'
                and review['canonical_ensure_ascii'] is True
                and review['accepted_for_exact_byte_custody_archive'] is True
                and review['inventory_sha256']==invpin['sha256']
                and review['archiver_sha256']==self_pin['sha256']
                and review['expected_head']==self.args.expected_head,'parent_review_binding')
        require(hashlib.sha256(canonical({k:v for k,v in review.items() if k!='identity_sha256'})).hexdigest()==review['identity_sha256'],
                'parent_review_True_seal')
        rows=inv['rows'];require(isinstance(rows,list) and 1<=len(rows)<=MAX_ROWS,'finite_rows')
        require(len({r['original_path'] for r in rows})==len(rows)
                and len({r['stored_relative_path'] for r in rows})==len(rows),'duplicate_inventory_original_or_target')
        total=0
        for row in rows:
            require(type(row['original_bytes']) is int and 0<=row['original_bytes']<=MAX_ORIGINAL
                    and re.fullmatch('[0-9a-f]{64}',row['original_sha256']),'original_inventory_pin')
            total+=row['original_bytes'];require(total<=MAX_ORIGINAL_TOTAL,'original_inventory_total')
            plain=Path(row['original_path']).suffix in PLAIN_SUFFIXES or Path(row['original_path']).name=='tmux.conf'
            expected='gzip_mtime0' if row['original_bytes']>GZIP_THRESHOLD and not plain else 'plain'
            require(row['storage_codec']==expected and row['content_class']==('plain_source_or_document' if plain else 'bounded_metadata_original'),
                    'fixed_representation_policy')
            require((row['storage_codec']=='plain') or row['stored_relative_path'].endswith('.gz'),'gzip_suffix_required')
            self.hash_pin(row['original_path'],row);self.validate_policy(row)
        before=self.source_state(initial=True)
        require(before['prior_tracked_entries']==review['prior_tracked_entries'],'parent_prior_tree_count')
        self.dest=W/PREFIX
        components(self.dest.parent)
        require(not os.path.lexists(self.dest),'archive_prefix_already_exists')
        os.mkdir(self.dest,0o700);self.created=True
        originals=[self.copy(row) for row in rows]
        for p,pin in self.inputs.items():
            require(stamp(Path(p).lstat())==pin['stat'],'original_or_control_changed_before_publication')
        require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==self.args.source_sha256,'final_archiver_source_recheck')
        after=self.source_state()
        now=datetime.now(timezone.utc); eastern=now.astimezone(ZoneInfo('America/Detroit'))
        readme=(f'# Reference, inode-birth and dependency observation byte custody\n\nDate: {eastern:%Y-%m-%d %H:%M:%S} (ET). Created UTC: {now.isoformat()}.\n\n'
          'This is exact byte custody of explicitly reviewed metadata originals and source/documents. Original failure, partial/global-incomplete facts, original seals/unsealed policies, creation-time NOTRUN text and later actual observations remain distinct and unchanged.\n\n'
          +inv['snapshot_boundary']+'\n\n'
          'Large approved metadata originals use lossless gzip with mtime=0 and empty filename; each entry retains original and stored byte/SHA pins and full decompression equality. Python sources/documents/diffs remain plain byte-exact. No ordinary application outcome body, auth material or numerical scientific record is selected by the archiver.\n\n'
          'The fresh canonicalTrue manifest seals BYTE CUSTODY ONLY. It supplies no new current completeness, process-role exclusion, cleanup selection/capacity, campaign normality or scientific admission. No selected query/control main, test, SSH, provider, compiler, simulator, Git mutation, issue/status/map/progress edit or source permission action is performed. Later G/O preparations are retained only if explicitly present in the final parent-reviewed inventory.\n').encode()
        self.write_metadata('README.md',readme)
        manifest={'format':'swdb.local-reference-birth-dependency-observation.byte-custody.v1',
          'canonical_ensure_ascii':True,'created_utc':now.isoformat(),'created_ET':eastern.isoformat(),
          'parent_commit':self.args.expected_head,'archiver_source_pin':self_pin,'explicit_inventory_pin':invpin,
          'parent_review_pin':rpin,'prior_source_tree_before':before,'prior_source_tree_after':after,
          'original_count':len(originals),'original_bytes_total':total,'originals':originals,
          'README_bytes':len(readme),'README_sha256':hashlib.sha256(readme).hexdigest(),
          'source_and_original_policies_normalized_or_rewritten':False,
          'selected_mains_tests_SSH_scientific_or_Git_mutations_performed_by_archiver':False,
          'new_plan_process_role_cleanup_capacity_or_scientific_admission':False}
        manifest['identity_sha256']=hashlib.sha256(canonical(manifest)).hexdigest()
        body=json.dumps(manifest,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False).encode()+b'\n'
        self.write_metadata('manifest.json',body)
        final=self.source_state()
        require(final==after,'source_context_changed_after_metadata_publication')
        status=self.git('status','--porcelain','-z','--untracked-files=all').split(b'\0')
        actual=set()
        for item in status:
            if not item:continue
            require(item.startswith(b'?? '),'unexpected_tracked_edit_after_archive')
            actual.add(item[3:].decode())
        require(actual==set(self.written),'archive_not_exact_added_pathset')
        return {'archive':PREFIX,'originals':len(originals),'added_paths':len(self.written),
          'original_bytes':total,'stored_bytes':sum(r['stored_bytes'] for r in originals),
          'manifest_sha256':hashlib.sha256(body).hexdigest(),'manifest_identity_sha256':manifest['identity_sha256'],
          'prior_tree_preserved':True,'no_Git_stage_commit_push_or_selected_main':True}

def main():
    p=argparse.ArgumentParser(description='Local explicit byte-custody archive only; reviewed originals only.')
    for name in ('expected-head','inventory','inventory-sha256','parent-review','parent-review-sha256','source-sha256'):
        p.add_argument('--'+name,required=True)
    args=p.parse_args()
    require(re.fullmatch('[0-9a-f]{40}',args.expected_head),'dynamic_expected_HEAD40')
    for s in (args.inventory_sha256,args.parent_review_sha256,args.source_sha256):
        require(re.fullmatch('[0-9a-f]{64}',s),'exact_file_SHA64')
    worker=Archive(args)
    def expired(sig,frame):raise Refused('archive_alarm')
    old=signal.signal(signal.SIGALRM,expired);signal.alarm(SECONDS)
    try:
        result=worker.perform();print(json.dumps(result,sort_keys=True,ensure_ascii=True,allow_nan=False));return 0
    except Exception as e:
        print(json.dumps({'format':'swdb.local-byte-custody-partial-failure.v1',
            'class':type(e).__name__,'code':str(e) if isinstance(e,Refused) else 'original_error_text_not_emitted',
            'fresh_archive_directory_created':worker.created,'partial_paths_retained':worker.written,
            'charged_bytes':worker.charged},sort_keys=True),file=sys.stderr);return 1
    finally:signal.alarm(0);signal.signal(signal.SIGALRM,old)

if __name__=='__main__':
    raise SystemExit(main())

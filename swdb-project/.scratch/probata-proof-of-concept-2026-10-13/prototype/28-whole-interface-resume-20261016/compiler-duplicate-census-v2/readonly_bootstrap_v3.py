# 2026-10-16 ET. Inert root-selected stdin bootstrap; do not run while authoring.
import resource
import sys
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CPU, (100, 100))

def readonly_audit(event, args):
    if event == 'open':
        path, mode, flags = args
        if (isinstance(mode, str) and any(char in mode for char in 'wax+')) or flags & (1 | 2 | 64 | 512 | 1024):
            raise PermissionError('passive diagnostic forbids writable open')
    if event in {'os.system', 'os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir',
                 'os.chmod', 'os.chown', 'os.link', 'os.symlink', 'os.truncate', 'os.utime', 'os.chdir',
                 'os.putenv', 'os.unsetenv', 'ctypes.dlopen', 'resource.setrlimit'} or event.startswith(
                 ('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')):
        raise PermissionError('passive diagnostic mutation/child/network refused: ' + event)

sys.addaudithook(readonly_audit)
import hashlib
payload = sys.stdin.buffer.read(22966)
if len(payload) != 22965 or hashlib.sha256(payload).hexdigest() != 'd265c49485057cbd43cfd913cfc905683090866174b45d863f22121331d997b3':
    raise ValueError('exact original diagnostic stdin bytes required')
if len(sys.argv) != 2:
    raise ValueError('one exact original raw argument required')
sys.argv = ['-', sys.argv[1]]
exec(compile(payload, '<reviewed-complete-duplicate-census-stdin>', 'exec'), {'__name__': '__main__', '__builtins__': __builtins__})

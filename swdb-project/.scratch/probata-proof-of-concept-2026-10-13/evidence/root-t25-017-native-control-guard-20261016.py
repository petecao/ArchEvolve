"""2026-10-15 ET. One serial ticket25 control job; not formal admission."""
import dataclasses,json,os,sys
from pathlib import Path
REPO=Path('/private/tmp/probata-root-t25-controls-01771a83/swdb-project')
sys.path.insert(0,str(REPO))
from swdb.rss_watchdog import run
out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
cmd=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*sys.argv[2:],'--basetemp='+str(out/'pytest')]
(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
r=run(cmd,log=out/'controls.log',cwd=str(REPO),env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},cap_bytes=8589934592,timeout=180)
(out/'resources.json').write_text(json.dumps(dataclasses.asdict(r),indent=2)+'\n')
print(json.dumps(dataclasses.asdict(r)));print((out/'controls.log').read_text()[-6000:]);raise SystemExit(r.exit_code)

#!/usr/bin/env python3
"""Start or stop only this project's loopback workspace process."""
import json, os, signal, subprocess, sys, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local'
PID=LOCAL/'server.pid'
URL='http://127.0.0.1:4321/api/state'
def owned(pid):
    result=subprocess.run(['ps','-p',str(pid),'-o','command='],text=True,capture_output=True)
    return result.returncode==0 and str(ROOT/'server.py') in result.stdout

def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'start'
    if action not in ('start','stop'):raise SystemExit('Use start or stop.')
    LOCAL.mkdir(exist_ok=True,mode=0o700)
    pid=int(PID.read_text()) if PID.exists() else None
    if action=='stop':
        if pid and owned(pid):os.kill(pid,signal.SIGTERM);PID.unlink();print('Stopped Stagepay workspace. Local chain and records are kept.')
        else:print('No owned Stagepay workspace process is running.')
        return
    if pid and owned(pid):print('Stagepay already running: http://127.0.0.1:4321');return
    try:
        urllib.request.urlopen(URL,timeout=2).close()
    except OSError:pass
    else:raise SystemExit('Port 4321 already responds without an owned process marker. No changes made.')
    with (LOCAL/'server.log').open('ab') as log:
        os.chmod(LOCAL/'server.log',0o600)
        p=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    PID.write_text(str(p.pid));PID.chmod(0o600)
    for _ in range(40):
        if p.poll() is not None:raise SystemExit('Stagepay could not start. Check .local/server.log.')
        try:
            with urllib.request.urlopen(URL,timeout=1) as r:json.load(r)
            print('Stagepay running: http://127.0.0.1:4321');return
        except OSError:time.sleep(.1)
    raise SystemExit('Stagepay did not respond in time.')
if __name__=='__main__':main()

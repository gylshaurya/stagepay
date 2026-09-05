#!/usr/bin/env python3
"""Start an isolated Anvil chain and deploy Stagepay using its public demo accounts."""
import json, os, subprocess, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'
RPC = 'http://127.0.0.1:18545'
def rpc(method, params=None):
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or []}).encode()
    with urllib.request.urlopen(urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json'}),timeout=10) as r: data=json.load(r)
    if 'error' in data: raise RuntimeError(data['error']['message'])
    return data['result']
def main():
    LOCAL.mkdir(exist_ok=True,mode=0o700)
    marker=LOCAL/'anvil.pid'
    try:
        rpc('eth_chainId')
        if not marker.exists(): raise SystemExit('Port 18545 is occupied by an unowned service. No changes made.')
        cmd=subprocess.check_output(['ps','-p',marker.read_text().strip(),'-o','command='],text=True)
        if 'anvil' not in cmd or str(LOCAL/'anvil-state.json') not in cmd: raise SystemExit('Anvil process ownership could not be verified.')
    except (OSError,ValueError):
        with (LOCAL/'anvil.log').open('ab') as log:
            os.chmod(LOCAL/'anvil.log',0o600)
            process=subprocess.Popen(['anvil','--silent','--host','127.0.0.1','--port','18545','--chain-id','31337','--state',str(LOCAL/'anvil-state.json'),'--state-interval','1'],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        marker.write_text(str(process.pid))
        for _ in range(50):
            try: rpc('eth_chainId');break
            except OSError: time.sleep(.1)
        else: raise SystemExit('Local chain did not start.')
    if rpc('eth_chainId')!='0x7a69': raise SystemExit('Expected local chain 31337. No transactions sent.')
    config=LOCAL/'chain.json'
    if config.exists():
        data=json.loads(config.read_text())
        if rpc('eth_getCode',[data['escrow'],'latest'])=='0x': raise SystemExit('Saved chain and deployment differ. Reconcile before starting.')
        print('Local contracts already deployed.');return
    accounts=rpc('eth_accounts')
    def deploy(contract,args=None):
        command=['forge','create',contract,'--broadcast','--unlocked','--from',accounts[0],'--rpc-url',RPC,'--json']
        if args: command+=['--constructor-args',*args]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,check=True)
        return json.loads(result.stdout)
    token=deploy('contracts/DemoToken.sol:DemoToken')
    escrow=deploy('contracts/Stagepay.sol:Stagepay',[token['deployedTo']])
    data={'rpc':RPC,'chain_id':31337,'name':'Local Anvil','token':token['deployedTo'],'escrow':escrow['deployedTo'],'client':accounts[0],'freelancer':accounts[1],'deployment_receipts':[token['transactionHash'],escrow['transactionHash']]}
    config.write_text(json.dumps(data,indent=2));config.chmod(0o600)
    print('Stagepay deployed on the isolated local chain. No public testnet deployment.')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Loopback-only demo workspace. Actual contract calls, durable records, no real funds."""
import hashlib, json, os, re, sqlite3, subprocess, threading, time, uuid
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from scripts.local_chain import rpc
ROOT=Path(__file__).resolve().parent
LOCAL=Path(os.environ.get('STAGEPAY_DATA',str(ROOT/'.local')))
PORT=int(os.environ.get('STAGEPAY_PORT','4321'))
LOCK=threading.RLock()
class Problem(Exception): pass

def database():
    LOCAL.mkdir(exist_ok=True,mode=0o700)
    c=sqlite3.connect(LOCAL/'workspace.sqlite3');c.row_factory=sqlite3.Row
    c.executescript('CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, version INTEGER NOT NULL, body TEXT NOT NULL); CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, project TEXT, state TEXT, body TEXT, tx TEXT, result TEXT);')
    return c

def chain():
    p=ROOT/'.local/chain.json'
    if not p.exists(): raise Problem('Start the local chain with npm run chain, then reload.')
    data=json.loads(p.read_text())
    if data['chain_id']!=31337 or data['rpc']!='http://127.0.0.1:18545' or rpc('eth_chainId')!='0x7a69': raise Problem('Only the dedicated local demo chain is allowed here.')
    if rpc('eth_getCode',[data['escrow'],'latest'])=='0x': raise Problem('Local deployment is missing. Reconcile the saved chain before continuing.')
    return data

def calldata(signature,*args):
    p=subprocess.run(['cast','calldata',signature,*map(str,args)],text=True,capture_output=True,timeout=10)
    if p.returncode: raise Problem('The contract call could not be encoded.')
    return p.stdout.strip()

def read_uint(to,signature,*args):
    return int(rpc('eth_call',[{'to':to,'data':calldata(signature,*args)},'latest']),16)

def digest(text):
    p=subprocess.run(['cast','keccak',text],text=True,capture_output=True,check=True,timeout=10)
    return p.stdout.strip()

def text(value,name,maximum=2000):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum: raise Problem(f'{name} must contain 1 to {maximum} characters.')
    return value.strip()

def amount(value):
    value=str(value)
    if not re.fullmatch(r'[0-9]{1,6}(\.[0-9]{1,2})?',value): raise Problem('Use an amount from 0 to 999999 with at most two decimals.')
    whole,_,fraction=value.partition('.')
    return int(whole)*10**18+int(fraction.ljust(2,'0'))*10**16

def send(c,operation,to,signature,args,actor,request=None):
    cfg=chain();sender=cfg[actor]
    data=calldata(signature,*args)
    # Estimate before recording/broadcasting so ordinary contract reverts are known failures.
    try: gas=rpc('eth_estimateGas',[{'from':sender,'to':to,'data':data}])
    except RuntimeError as e: raise Problem('The contract rejected this action. Refresh the project and check your role and its state.') from e
    intent={'from':sender,'to':to,'data':data,'nonce':rpc('eth_getTransactionCount',[sender,'pending'])}
    journal={'transaction':intent,'request':request}
    c.execute('INSERT INTO actions(id,project,state,body) VALUES(?,?,?,?)',(operation,'chain','pending',json.dumps(journal)));c.commit()
    try:
        tx=rpc('eth_sendTransaction',[dict(intent,gas=hex(int(gas,16)+50000))])
        c.execute('UPDATE actions SET tx=? WHERE id=?',(tx,operation));c.commit()
        receipt=None
        for _ in range(60):
            receipt=rpc('eth_getTransactionReceipt',[tx])
            if receipt: break
            time.sleep(.1)
        if not receipt: raise Problem('Transaction is pending. Further actions pause until its receipt is reconciled.')
        if receipt['status']!='0x1':
            c.execute('UPDATE actions SET state=? WHERE id=?',('reverted',operation));c.commit()
            raise Problem('Transaction reverted. No project decision was saved.')
        return {'hash':tx,'block':int(receipt['blockNumber'],16),'chain_id':31337,'from':sender,'contract':to,'status':'confirmed'}
    except Exception:
        # Keep uncertain broadcasts pending. Never retry with a second transaction automatically.
        raise

def get_project(c,ident):
    row=c.execute('SELECT * FROM projects WHERE id=?',(ident,)).fetchone()
    if not row: raise Problem('This project was not found. Refresh the project list.')
    return json.loads(row['body'])

def snapshot():
    with LOCK,closing(database()) as c,c:
        items=[json.loads(r['body']) for r in c.execute('SELECT body FROM projects ORDER BY rowid DESC')]
        pending=c.execute("SELECT id,tx FROM actions WHERE state='pending'").fetchall()
        try:
            cfg=chain();health={'ready':True,**cfg,'client_credit':str(read_uint(cfg['escrow'],'credits(address)',cfg['client'])),'freelancer_credit':str(read_uint(cfg['escrow'],'credits(address)',cfg['freelancer']))}
        except Exception: health={'ready':False,'name':'Local Anvil','chain_id':31337,'message':'Local chain is unavailable. Run npm run chain and refresh. Your saved project records are kept.'}
        return {'projects':items,'network':health,'pending':[dict(x) for x in pending],'mode':'local_demo','public_testnet':{'chain_id':11155111,'name':'Ethereum Sepolia','configured':False}}

def perform(request):
    with LOCK,closing(database()) as c,c:
        op=text(request.get('request_id'),'Request ID',80)
        if not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',op): raise Problem('Invalid request ID.')
        existing=c.execute('SELECT * FROM actions WHERE id=?',(op,)).fetchone()
        if existing:
            original=json.loads(existing['body']).get('request')
            if original is not None and original!=request: raise Problem('This request ID belongs to a different action.')
            if existing['state']=='done': return json.loads(existing['result'])
            raise Problem('This action was already attempted. Refresh and inspect its receipt before retrying.')
        if c.execute("SELECT 1 FROM actions WHERE state='pending'").fetchone(): raise Problem('An earlier chain action needs reconciliation. Saved records remain available; do not repeat the action.')
        cfg=chain();actor=request.get('actor');kind=request.get('action');body=request.get('body') or {}
        if not isinstance(body,dict): raise Problem('Action details must be an object.')
        if actor not in ('client','freelancer'): raise Problem('Select a local demo role.')
        receipt=None;p=None;label=''
        if kind=='create':
            if actor!='client': raise Problem('Only the client can fund a project.')
            title=text(body.get('title'),'Project name',100);scope=text(body.get('scope'),'Scope',5000)
            names=body.get('milestones')
            if not isinstance(names,list) or not 1<=len(names)<=3: raise Problem('Add one to three milestones.')
            milestones=[]
            for m in names:
                if not isinstance(m,dict): raise Problem('Each milestone needs a name and amount.')
                value=amount(m.get('amount',''))
                if value<=0: raise Problem('Every milestone needs a positive amount.')
                milestones.append({'name':text(m.get('name'),'Milestone name',100),'amount':str(value),'state':'pending','evidence':None})
            if body.get('acknowledge') is not True: raise Problem('Confirm the test-token and dispute limits before funding.')
            # Setup calls are separate durable operations; all are idempotently journaled.
            deposit=sum(int(m['amount']) for m in milestones)
            for suffix,to,sig,args in [('-mint',cfg['token'],'mint(address,uint256)',[cfg['client'],deposit]),('-approve',cfg['token'],'approve(address,uint256)',[cfg['escrow'],deposit])]:
                key=op+suffix
                if not c.execute("SELECT 1 FROM actions WHERE id=? AND state='done'",(key,)).fetchone():
                    setup=send(c,key,to,sig,args,actor)
                    c.execute("UPDATE actions SET state='done',result=? WHERE id=?",(json.dumps(setup),key));c.commit()
            chain_id=read_uint(cfg['escrow'],'nextProject()')
            hashed=digest(scope)
            receipt=send(c,op,cfg['escrow'],'create(address,bytes32,uint256[])',[cfg['freelancer'],hashed,'['+','.join(m['amount'] for m in milestones)+']'],actor,request)
            p={'id':str(chain_id),'title':title,'scope':scope,'scope_hash':hashed,'version':1,'status':'awaiting_agreement','milestones':milestones,'history':[],'proposal':None,'proposal_nonce':0,'disputed':False,'remaining':str(deposit)}
            label='Client funded the agreement'
        else:
            p=get_project(c,str(request.get('project_id')))
            if request.get('version')!=p['version']: raise Problem('This project changed in another tab. Refresh before deciding.')
            if p['status']=='closed' and kind!='withdraw': raise Problem('This project is closed.')
            ident=p['id'];args=[ident];sig='';label=''
            index=body.get('index')
            if kind in ('submit','accept','revision'):
                if not isinstance(index,int) or not 0<=index<len(p['milestones']): raise Problem('Choose a valid milestone.')
                m=p['milestones'][index]
            if kind=='join':sig='join(uint256,bytes32)';args+=[p['scope_hash']];label='Freelancer agreed to the scope'
            elif kind=='submit':
                note=text(body.get('note'),'Delivery note',2000);url=text(body.get('url'),'Evidence link',2000)
                if urlparse(url).scheme not in ('https','http'): raise Problem('Use an http or https evidence link.')
                evidence={'note':note,'url':url,'hash':digest(json.dumps({'note':note,'url':url},sort_keys=True,separators=(',',':')))}
                sig='submit(uint256,uint8,bytes32)';args += [index,evidence['hash']];label='Freelancer submitted '+m['name']
            elif kind=='accept':
                if not m['evidence']: raise Problem('This milestone has no submitted evidence.')
                sig='accept(uint256,uint8,bytes32,bytes32)';args += [index,p['scope_hash'],m['evidence']['hash']];label='Client accepted '+m['name']
            elif kind=='revision':
                if not m['evidence']: raise Problem('This milestone has no evidence to review.')
                note=text(body.get('note'),'Revision note',2000);sig='requestRevision(uint256,uint8,bytes32,bytes32)';args += [index,m['evidence']['hash'],digest(note)];label='Client requested a revision: '+note
            elif kind=='scope':
                note=text(body.get('scope'),'New scope',5000);sig='proposeScope(uint256,bytes32)';args += [digest(note)];label='A scope change was proposed'
            elif kind=='agree_scope':
                proposal=p['proposal']
                if not proposal or proposal['kind']!='scope': raise Problem('There is no scope proposal.')
                sig='agreeScope(uint256,bytes32,uint256)';args += [proposal['hash'],p['proposal_nonce']];label='Both parties agreed to the new scope'
            elif kind=='clear':sig='clearProposal(uint256,uint256)';args += [p['proposal_nonce']];label='The proposal was declined'
            elif kind=='dispute':note=text(body.get('note'),'Dispute reason',2000);sig='dispute(uint256,bytes32)';args += [digest(note)];label='Dispute opened: '+note
            elif kind=='settle':
                payout=amount(body.get('amount',''))
                if payout>int(p['remaining']): raise Problem('The payout cannot exceed the unpaid escrow balance.')
                sig='proposeSettlement(uint256,uint256)';args += [payout];label='A settlement was proposed'
            elif kind=='agree_settlement':
                proposal=p['proposal']
                if not proposal or proposal['kind']!='settlement': raise Problem('There is no settlement proposal.')
                sig='agreeSettlement(uint256,uint256,uint256)';args += [proposal['amount'],p['proposal_nonce']];label='Both parties agreed to settle'
            elif kind=='cancel':sig='cancelBeforeJoin(uint256)';label='Client cancelled before work began'
            elif kind=='withdraw':sig='withdraw(address)';args=[cfg[actor]];label=actor.capitalize()+' withdrew available test tokens'
            else: raise Problem('Unknown project action.')
            receipt=send(c,op,cfg['escrow'],sig,args,actor,request)
            if kind=='join':p['status']='in_progress'
            elif kind=='submit':m['state']='submitted';m['evidence']=evidence;m.pop('revision',None)
            elif kind=='accept':
                m['state']='accepted';p['remaining']=str(int(p['remaining'])-int(m['amount']))
                if int(p['remaining'])==0:p['status']='closed'
            elif kind=='revision':m['state']='pending';m['revision']=note
            elif kind=='scope':p['proposal_nonce']+=1;p['proposal']={'kind':'scope','scope':note,'hash':digest(note),'by':actor}
            elif kind=='agree_scope':
                p['scope']=p['proposal']['scope'];p['scope_hash']=p['proposal']['hash'];p['proposal']=None
                for row in p['milestones']:
                    if row['state']!='accepted':row['state']='pending';row['evidence']=None;row.pop('revision',None)
            elif kind=='clear':p['proposal']=None
            elif kind=='dispute':p['disputed']=True;p['proposal']=None;p['proposal_nonce']+=1
            elif kind=='settle':p['proposal_nonce']+=1;p['proposal']={'kind':'settlement','amount':str(payout),'by':actor}
            elif kind in ('agree_settlement','cancel'):p['status']='closed';p['remaining']='0';p['proposal']=None
            p['version']+=1
        p['history'].append({'action':kind,'label':label,'at':time.time(),'actor':actor,'scope_hash':p['scope_hash'],'receipt':receipt})
        result={'project':p,'receipt':receipt}
        c.execute('INSERT INTO projects VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET version=excluded.version,body=excluded.body',(p['id'],p['version'],json.dumps(p)))
        c.execute("UPDATE actions SET state='done',result=? WHERE id=?",(json.dumps(result),op));c.commit()
        return result

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,code,data,kind='application/json'):
        raw=data if isinstance(data,bytes) else json.dumps(data).encode()
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");self.end_headers();self.wfile.write(raw)
    def trusted(self):return self.headers.get('Host') in (f'127.0.0.1:{PORT}',f'localhost:{PORT}')
    def do_GET(self):
        if not self.trusted():return self.reply(403,{'error':'Use the local workspace address.'})
        path=urlparse(self.path).path
        if path=='/api/state':return self.reply(200,snapshot())
        files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8'),'/font.woff2':('font.woff2','font/woff2')}
        files.update({f'/font-{w}.woff2':(f'font-{w}.woff2','font/woff2') for w in (600,700)})
        if path not in files:return self.reply(404,{'error':'Not found'})
        name,mime=files[path];p=ROOT/'web'/name
        if not p.exists():return self.reply(404,{'error':'File not found'})
        self.reply(200,p.read_bytes(),mime)
    def do_POST(self):
        if not self.trusted() or self.headers.get('Origin') not in (f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}') or self.headers.get('Content-Type')!='application/json':return self.reply(403,{'error':'Open Stagepay locally to make a change.'})
        if self.path!='/api/action':return self.reply(404,{'error':'Not found'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=30000:raise Problem('Request is too large or empty.')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise Problem('Invalid request.')
            self.reply(200,perform(data))
        except (Problem,ValueError,TypeError,KeyError) as e:self.reply(400,{'error':str(e)})
        except Exception:self.reply(503,{'error':'The local chain or service did not finish this action. Refresh and inspect pending receipts before retrying.'})
if __name__=='__main__':
    database().close();print(f'Stagepay local demo: http://127.0.0.1:{PORT}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()

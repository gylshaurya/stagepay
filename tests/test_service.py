"""Integration checks against isolated contracts on the real local Anvil chain."""
import copy
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
import server

class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=server.chain().copy()
        # Dedicated deployments keep these tests away from the workspace's agreements.
        def deploy(name,args=None):
            command=['forge','create',f'contracts/{name}.sol:{name}','--broadcast','--unlocked','--from',cls.cfg['client'],'--rpc-url',cls.cfg['rpc'],'--json']
            if args: command+=['--constructor-args',*args]
            import subprocess
            result=subprocess.run(command,cwd=server.ROOT,text=True,capture_output=True,check=True)
            return json.loads(result.stdout)['deployedTo']
        cls.cfg['token']=deploy('DemoToken')
        cls.cfg['escrow']=deploy('Stagepay',[cls.cfg['token']])
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.local=patch.object(server,'LOCAL',Path(self.tmp.name));self.local.start()
        self.chain=patch.object(server,'chain',return_value=self.cfg);self.chain.start()
        self.project=None
    def tearDown(self):
        self.chain.stop();self.local.stop();self.tmp.cleanup()
    def request(self,action,actor='client',body=None):
        return {'request_id':str(uuid.uuid4()),'action':action,'actor':actor,'body':body or {},'project_id':self.project['id'] if self.project else None,'version':self.project['version'] if self.project else None}
    def act(self,action,actor='client',body=None):
        result=server.perform(self.request(action,actor,body));self.project=result['project'];return result
    def create(self):
        return self.act('create',body={'title':'Integration test agreement','scope':'Deliver an accessible campus website and handover notes.','milestones':[{'name':'Website','amount':'10.25'},{'name':'Handover','amount':'5'}],'acknowledge':True})
    def submit(self,index=0):
        return self.act('submit','freelancer',{'index':index,'note':'Ready for review.','url':'https://example.com/work'})
    def credit(self,actor='freelancer'):
        return server.read_uint(self.cfg['escrow'],'credits(address)',self.cfg[actor])
    def test_happy_flow_receipts_exact_payment_and_persistence(self):
        start=self.credit();self.create();self.act('join','freelancer');self.submit()
        result=self.act('accept',body={'index':0})
        self.assertEqual(self.credit()-start,server.amount('10.25'))
        receipt=server.rpc('eth_getTransactionReceipt',[result['receipt']['hash']]);self.assertEqual(receipt['status'],'0x1')
        self.submit(1);self.act('accept',body={'index':1});self.assertEqual(self.project['status'],'closed')
        # Opening a fresh connection reads the same durable record.
        self.assertEqual(server.snapshot()['projects'][0],self.project)
        self.act('withdraw','freelancer');self.assertEqual(self.credit(),0)
    def test_wrong_role_and_double_accept_do_not_pay(self):
        self.create();self.act('join','freelancer');self.submit();start=self.credit()
        with self.assertRaises(server.Problem):self.act('accept','freelancer',{'index':0})
        self.assertEqual(self.credit(),start)
        self.act('accept',body={'index':0});paid=self.credit()
        with self.assertRaises(server.Problem):self.act('accept',body={'index':0})
        self.assertEqual(self.credit(),paid)
    def test_revision_never_releases_credit(self):
        self.create();self.act('join','freelancer');self.submit();start=self.credit()
        self.act('revision',body={'index':0,'note':'Add keyboard navigation.'})
        self.assertEqual(self.credit(),start);self.assertEqual(self.project['milestones'][0]['state'],'pending')
        with self.assertRaises(server.Problem):self.act('accept',body={'index':0})
        self.submit();self.act('accept',body={'index':0});self.assertEqual(self.credit()-start,server.amount('10.25'))
    def test_mutual_scope_change_resets_only_unpaid_evidence(self):
        self.create();self.act('join','freelancer');self.submit();self.act('accept',body={'index':0});self.submit(1)
        self.act('scope',body={'scope':'Keep the accepted website and include a setup guide in the handover.'})
        with self.assertRaises(server.Problem):self.act('agree_scope')
        self.act('agree_scope','freelancer')
        self.assertEqual(self.project['milestones'][0]['state'],'accepted')
        self.assertIsNone(self.project['milestones'][1]['evidence'])
    def test_dispute_freezes_and_mutual_settlement_conserves(self):
        self.create();self.act('join','freelancer');self.submit()
        freelancer=self.credit();client=self.credit('client')
        self.act('dispute','freelancer',{'note':'The scope needs a shared decision.'})
        with self.assertRaises(server.Problem):self.act('accept',body={'index':0})
        self.act('settle',body={'amount':'4.25'})
        with self.assertRaises(server.Problem):self.act('agree_settlement')
        self.act('agree_settlement','freelancer')
        self.assertEqual(self.credit()-freelancer,server.amount('4.25'))
        self.assertEqual(self.credit('client')-client,server.amount('11'))
        self.assertEqual(self.project['remaining'],'0')
    def test_cancel_before_join_refunds(self):
        self.create();start=self.credit('client');self.act('cancel')
        self.assertEqual(self.credit('client')-start,server.amount('15.25'))
    def test_stale_version_and_exact_replay(self):
        self.create();req=self.request('join','freelancer');result=server.perform(req);self.project=result['project']
        self.assertEqual(server.perform(req),result)
        altered=copy.deepcopy(req);altered['actor']='client'
        with self.assertRaisesRegex(server.Problem,'different action'):server.perform(altered)
        stale=self.request('submit','freelancer',{'index':0,'url':'https://example.com','note':'Work'});stale['version']-=1
        with self.assertRaisesRegex(server.Problem,'another tab'):server.perform(stale)
    def test_invalid_amount_link_and_structures(self):
        with self.assertRaises(server.Problem):server.amount('1.001')
        with self.assertRaises(server.Problem):server.amount('-1')
        self.create();self.act('join','freelancer')
        with self.assertRaises(server.Problem):self.act('submit','freelancer',{'index':0,'note':'Work','url':'javascript:alert(1)'})
        with self.assertRaisesRegex(server.Problem,'object'):server.perform(self.request('submit',body=['not an object']))
    def test_malformed_evidence_links_never_send_a_transaction(self):
        self.create();self.act('join','freelancer')
        invalid=['http:', 'https:///missing-host', 'https://user:password@example.com/work', 'https://exa mple.com/work', 'https://example.com:bad/work', 'https://example.com/\nwork']
        for url in invalid:
            with self.subTest(url=url):
                before=server.rpc('eth_getTransactionCount',[self.cfg['freelancer'],'latest'])
                with self.assertRaises(server.Problem):
                    self.act('submit','freelancer',{'index':0,'note':'Invalid link must not reach the chain.','url':url})
                self.assertEqual(server.rpc('eth_getTransactionCount',[self.cfg['freelancer'],'latest']),before)

    def test_uncertain_broadcast_is_journaled_and_blocks_retries(self):
        self.create();req=self.request('join','freelancer');real_rpc=server.rpc
        def interrupted(method,params=None):
            result=real_rpc(method,params)
            if method=='eth_sendTransaction':raise OSError('Simulated loss after the node accepted a transaction')
            return result
        with patch.object(server,'rpc',side_effect=interrupted):
            with self.assertRaises(OSError):server.perform(req)
        pending=server.snapshot()['pending'];self.assertEqual(len(pending),1)
        with server.closing(server.database()) as c,c:
            row=c.execute('SELECT body FROM actions WHERE id=?',(req['request_id'],)).fetchone()
            self.assertEqual(json.loads(row['body'])['request'],req)
        with self.assertRaisesRegex(server.Problem,'already attempted'):server.perform(req)
        with self.assertRaisesRegex(server.Problem,'reconciliation'):self.act('join','freelancer')

    def interrupt(self,request,method='eth_getTransactionReceipt'):
        real=server.rpc
        def fault(name,params=None):
            result=real(name,params)
            if name==method:raise OSError('Injected interruption after RPC result')
            return result
        with patch.object(server,'rpc',side_effect=fault):
            with self.assertRaises(OSError):server.perform(request)

    def test_known_receipt_applies_once_without_resending(self):
        self.create();req=self.request('join','freelancer');self.interrupt(req)
        before=server.rpc('eth_getTransactionCount',[self.cfg['freelancer'],'latest'])
        recovered=server.reconcile();self.assertEqual(recovered['outcomes'][0]['state'],'done')
        self.assertEqual(server.rpc('eth_getTransactionCount',[self.cfg['freelancer'],'latest']),before)
        result=server.perform(req);self.assertEqual(result['project']['status'],'in_progress')
        self.assertEqual(len(result['project']['history']),2)
        self.assertEqual(server.reconcile()['outcomes'],[])
        self.assertEqual(server.perform(req),result)

    def test_lost_broadcast_hash_found_by_nonce(self):
        self.create();req=self.request('join','freelancer');self.interrupt(req,'eth_sendTransaction')
        self.assertIsNone(server.snapshot()['pending'][0]['tx'])
        before=server.rpc('eth_getTransactionCount',[self.cfg['freelancer'],'latest'])
        self.assertEqual(server.reconcile()['outcomes'][0]['state'],'done')
        self.assertEqual(server.rpc('eth_getTransactionCount',[self.cfg['freelancer'],'latest']),before)
        self.assertEqual(server.perform(req)['project']['status'],'in_progress')

    def test_missing_receipt_and_mismatched_intent_stay_paused(self):
        self.create();req=self.request('join','freelancer');self.interrupt(req);real=server.rpc
        def unavailable(name,params=None):
            if name=='eth_sendTransaction':self.fail('Recovery must never broadcast')
            if name=='eth_getTransactionReceipt':return None
            return real(name,params)
        with patch.object(server,'rpc',side_effect=unavailable):
            self.assertEqual(server.reconcile()['outcomes'][0]['state'],'pending')
        def mismatch(name,params=None):
            result=real(name,params)
            if name=='eth_getTransactionByHash':result={**result,'input':'0x1234'}
            if name=='eth_sendTransaction':self.fail('Recovery must never broadcast')
            return result
        with patch.object(server,'rpc',side_effect=mismatch):
            self.assertEqual(server.reconcile()['outcomes'][0]['state'],'pending')
        self.assertEqual(server.snapshot()['projects'][0]['status'],'awaiting_agreement')
        self.assertEqual(server.reconcile()['outcomes'][0]['state'],'done')

    def test_confirmed_revert_does_not_apply_project_change(self):
        self.create();req=self.request('join','freelancer');real=server.rpc
        def fault(name,params=None):
            if name=='eth_sendTransaction':params=[{**params[0],'gas':hex(24000)}]
            result=real(name,params)
            if name=='eth_getTransactionReceipt':raise OSError('Lost reverted receipt response')
            return result
        with patch.object(server,'rpc',side_effect=fault):
            with self.assertRaises(OSError):server.perform(req)
        pending=server.snapshot()['pending'][0]
        self.assertEqual(real('eth_getTransactionReceipt',[pending['tx']])['status'],'0x0')
        self.assertEqual(server.reconcile()['outcomes'][0]['state'],'reverted')
        self.assertEqual(server.snapshot()['projects'][0]['status'],'awaiting_agreement')
        self.assertEqual(server.snapshot()['pending'],[])
        self.act('join','freelancer');self.assertEqual(self.project['status'],'in_progress')

    def test_interrupted_mint_resumes_saved_funding_without_duplicate_mint(self):
        req=self.request('create',body={'title':'Recovered funding','scope':'Deliver the site.', 'milestones':[{'name':'Website','amount':'3'}],'acknowledge':True})
        self.interrupt(req,'eth_sendTransaction')
        self.assertEqual(server.reconcile()['outcomes'][0]['state'],'done')
        self.assertEqual(server.snapshot()['resumable'][0]['id'],req['request_id'])
        before=server.rpc('eth_getTransactionCount',[self.cfg['client'],'latest'])
        result=server.resume(req['request_id'])
        after=server.rpc('eth_getTransactionCount',[self.cfg['client'],'latest'])
        self.assertEqual(int(after,16)-int(before,16),2) # Only approval and create remain.
        self.assertEqual(result['project']['title'],'Recovered funding')
        self.assertEqual(server.snapshot()['resumable'],[])
        self.assertEqual(server.resume(req['request_id']),result)

    def test_interrupted_create_applies_saved_agreement(self):
        req=self.request('create',body={'title':'Recovered create','scope':'Deliver the site.', 'milestones':[{'name':'Website','amount':'3'}],'acknowledge':True})
        real=server.rpc;calls=0
        def fault(name,params=None):
            nonlocal calls
            result=real(name,params)
            if name=='eth_getTransactionReceipt':
                calls+=1
                if calls==3:raise OSError('Create receipt response lost')
            return result
        with patch.object(server,'rpc',side_effect=fault):
            with self.assertRaises(OSError):server.perform(req)
        self.assertEqual(server.snapshot()['projects'],[])
        self.assertEqual(server.reconcile()['outcomes'][0]['state'],'done')
        self.assertEqual(server.perform(req)['project']['title'],'Recovered create')

if __name__=='__main__':unittest.main()

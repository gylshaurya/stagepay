// One real testnet walkthrough with resumable, project-scoped checkpoints.
import {JsonRpcProvider} from 'ethers';
import {readFileSync,writeFileSync,renameSync,existsSync} from 'node:fs';
import {Desk} from '../public-app/core.mjs';
import {testWallet} from './testnet-wallet.mjs';
const config=JSON.parse(readFileSync('public-app/config.json','utf8'));
const provider=new JsonRpcProvider(config.rpc,undefined,{batchMaxCount:1,cacheTimeout:-1,pollingInterval:3000});
function put(file,data){writeFileSync(file+'.tmp',JSON.stringify(data,null,2),{mode:0o600});renameSync(file+'.tmp',file);}
function storage(role){const file=`.local/sepolia-${role}-desk.json`;let data=existsSync(file)?JSON.parse(readFileSync(file)):{};return {getItem:k=>data[k]||null,setItem:(k,v)=>{data[k]=v;put(file,data);}};}
const checkpoint='.local/sepolia-walkthrough.json',run=existsSync(checkpoint)?JSON.parse(readFileSync(checkpoint)):{steps:{},projectId:null};
const client=(await testWallet('client')).connect(provider),freelancer=(await testWallet('freelancer')).connect(provider);
const desk=new Desk(config,provider,storage('client')),other=new Desk(config,provider,storage('freelancer'));
async function step(key,who,action,body,signer){
 const previous=run.steps[key];if(previous?.state==='done')return previous.result;
 if(previous){if(who.read().pending)await who.reconcile();const saved=who.read();const receipt=saved.receipts[previous.receiptIndex];if(!receipt||receipt.action!==action||receipt.status!=='confirmed')throw Error('Inspect the saved walkthrough step before retrying: '+key);const result={projectId:receipt.projectId,message:'Recovered completed step'};run.steps[key]={state:'done',result,receipt};put(checkpoint,run);return result;}
 run.steps[key]={state:'started',receiptIndex:who.read().receipts.length};put(checkpoint,run);
 const result=await who.send(action,{projectId:run.projectId,...body},signer);if(who.read().pending)throw Error('A walkthrough action is still pending.');
 run.steps[key]={state:'done',result,receipt:who.read().receipts.at(-1)};put(checkpoint,run);console.log(JSON.stringify({step:key,...result}));return result;
}
try{
 await step('mint',desk,'mint',{amount:'3'},client);await step('approve',desk,'approve',{amount:'3'},client);
 const created=await step('create',desk,'create',{title:'Campus club website · test agreement',scope:'Build a club landing page and provide a handover guide. This is an illustrative test agreement, not paid client work.',freelancer:freelancer.address,milestones:[{name:'Landing page',amount:'1'},{name:'Handover guide',amount:'2'}],acknowledge:true},client);run.projectId=created.projectId;put(checkpoint,run);
 // Import only at the stage where those hashes are current. Resume skips old-text imports.
 if(!run.steps.join){await other.import(desk.export(run.projectId));}
 await step('join',other,'join',{},freelancer);
 await step('submit',other,'submit',{index:0,note:'The landing page and navigation are ready for review. This link is the Stagepay source used for this test.',url:'https://github.com/gylshaurya/stagepay'},freelancer);
 if(!run.steps.accept){await desk.import(other.export(run.projectId));}
 await step('accept',desk,'accept',{index:0},client);
 await step('scope',desk,'scope',{scope:'Keep the accepted landing page. Replace the remaining handover with a short setup checklist. This remains an illustrative test agreement.'},client);
 if(!run.steps.agree_scope){await other.import(desk.export(run.projectId));}
 await step('agree_scope',other,'agree_scope',{},freelancer);
 if(!run.steps.dispute){await desk.import(other.export(run.projectId));}
 await step('dispute',other,'dispute',{note:'Agree on a smaller final handover for this test.'},freelancer);
 await step('settle',desk,'settle',{amount:'0.5'},client);
 const proposal=await other.project(run.projectId);await step('agree_settlement',other,'agree_settlement',{expectedNonce:String(proposal.proposalNonce),expectedPayout:String(proposal.settlementPayout)},freelancer);
 await step('client_withdraw',desk,'withdraw',{},client);await step('freelancer_withdraw',other,'withdraw',{},freelancer);
 const p=await desk.project(run.projectId);if(!p.closed||p.remaining!==0n||p.clientCredit!==0n||p.freelancerCredit!==0n)throw Error('Final settlement checks failed.');
 const publicEvidence={chainId:11155111,scope:'Actual Sepolia transactions for an illustrative test agreement. No real client payment or prize claim.',projectId:run.projectId,checkedAt:new Date().toISOString(),checks:{closed:p.closed,remaining:String(p.remaining),clientCredit:String(p.clientCredit),freelancerCredit:String(p.freelancerCredit)},transactions:Object.values(run.steps).map(s=>s.receipt),example:desk.export(run.projectId)};
 writeFileSync('docs/sepolia-walkthrough.json',JSON.stringify(publicEvidence,null,2)+'\n');writeFileSync('public-app/demo.json',JSON.stringify(publicEvidence,null,2)+'\n');console.log('Public Sepolia walkthrough verified. All credit withdrawn.');
}catch(e){console.error(e.shortMessage||e.message);process.exitCode=1;}finally{provider.destroy();}

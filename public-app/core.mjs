import { Contract, Interface, getAddress, id, keccak256, parseUnits, ZeroAddress } from 'ethers';
import abi from './abi.json' with {type:'json'};
export const escrowABI=abi.Stagepay, tokenABI=abi.DemoToken;
export const same=(a,b)=>String(a).toLowerCase()===String(b).toLowerCase();
export function money(value){if(!/^[0-9]{1,6}(\.[0-9]{1,2})?$/.test(String(value)))throw Error('Use an amount with at most two decimals.');return parseUnits(String(value),18);}
export function words(value,name,max=5000){if(typeof value!=='string'||!value.trim()||value.length>max)throw Error(`${name} needs 1 to ${max} characters.`);return value.trim();}
export function link(value){const text=words(value,'Work link',2000);let url;try{url=new URL(text);}catch{throw Error('Use a complete http or https work link.');}if(!['https:','http:'].includes(url.protocol)||url.username||url.password||/[\s\\]/.test(text))throw Error('Use a complete http or https work link without login details.');return text;}
export function evidence(note,url){const value={note:words(note,'Delivery note',2000),url:link(url)};return {...value,hash:id(JSON.stringify(value))};}
const safeJSON=v=>JSON.stringify(v,(_,v)=>typeof v==='bigint'?v.toString():v);
export class Desk {
 constructor(config,provider,storage,{allowLocal=false}={}){
  if(config.chainId!==11155111&&!(allowLocal&&config.chainId===31337))throw Error('This release only supports Ethereum Sepolia.');
  this.config=config;this.provider=provider;this.storage=storage;
  this.key=`stagepay:v1:${config.chainId}:${String(config.escrow).toLowerCase()}`;
  this.escrow=new Contract(config.escrow,escrowABI,provider);this.token=new Contract(config.token,tokenABI,provider);
 }
 read(){const value=this.storage.getItem(this.key);return value?JSON.parse(value):{metadata:{},known:[],pending:null,receipts:[]};}
 save(value){this.storage.setItem(this.key,safeJSON(value));}
 async check(){const chainId=Number(await this.provider.send('eth_chainId',[]));if(chainId!==this.config.chainId)throw Error('The RPC returned the wrong chain. No transaction was sent.');const [a,b]=await Promise.all([this.provider.getCode(this.config.escrow),this.provider.getCode(this.config.token)]);if(a==='0x'||b==='0x'||keccak256(a)!==this.config.escrowCodeHash||keccak256(b)!==this.config.tokenCodeHash)throw Error('The deployment code does not match this release.');if(!same(await this.escrow.token(),this.config.token))throw Error('The token does not match the escrow.');}
 async project(projectId){if(!/^[1-9][0-9]{0,15}$/.test(String(projectId)))throw Error('Use a numeric agreement ID.');await this.check();const p=await this.escrow.projects(projectId);if(p.client===ZeroAddress)throw Error('This agreement was not found.');const milestones=await Promise.all(Array.from({length:Number(p.count)},(_,i)=>this.escrow.milestones(projectId,i)));const doc=this.read().metadata[projectId]||{};return {id:String(projectId),client:p.client,freelancer:p.freelancer,scopeHash:p.scope,remaining:p.remaining,joined:p.joined,disputed:p.disputed,closed:p.closed,scopeProposer:p.scopeProposer,proposedScope:p.proposedScope,settlementProposer:p.settlementProposer,settlementPayout:p.settlementPayout,proposalNonce:p.proposalNonce,doc,scopeMatches:typeof doc.scope==='string'&&id(doc.scope)===p.scope,milestones:milestones.map((m,i)=>({amount:m.amount,state:Number(m.state),hash:m.evidence,name:doc.milestones?.[i]?.name||`Milestone ${i+1}`,evidence:doc.evidence?.[i]?.hash===m.evidence?doc.evidence[i]:null})),clientCredit:await this.escrow.credits(p.client),freelancerCredit:await this.escrow.credits(p.freelancer)};}
 async prepare(action,body,from){
  from=getAddress(from);let method,args,to=this.config.escrow,meta=null,projectId=String(body.projectId||'');
  if(action==='create'){
   const freelancer=getAddress(body.freelancer);if(freelancer===ZeroAddress||same(freelancer,from))throw Error('Use a different freelancer wallet.');
   const title=words(body.title,'Project name',100),scope=words(body.scope,'Scope');if(body.acknowledge!==true)throw Error('Confirm the test-token and dispute limits.');
   if(!Array.isArray(body.milestones)||body.milestones.length<1||body.milestones.length>3)throw Error('Add one to three milestones.');
   const rows=body.milestones.map(m=>({name:words(m.name,'Milestone name',100),amount:money(m.amount)}));if(rows.some(m=>m.amount<=0n))throw Error('Each milestone needs a positive amount.');const total=rows.reduce((a,m)=>a+m.amount,0n);
   if(await this.token.balanceOf(from)<total)throw Error('Mint enough free DEMO tokens first.');
   if(await this.token.allowance(from,this.config.escrow)<total)throw Error('Approve the exact deposit first.');
   method='create';args=[freelancer,id(scope),rows.map(m=>m.amount)];meta={title,scope,milestones:rows.map(m=>({name:m.name})),evidence:{}};
  } else if(action==='mint'){to=this.config.token;method='mint';args=[from,money(body.amount)];if(args[1]<=0n)throw Error('Use a positive amount.');}
  else if(action==='approve'){to=this.config.token;method='approve';args=[this.config.escrow,money(body.amount)];}
  else {
   const p=await this.project(projectId),client=same(from,p.client),freelancer=same(from,p.freelancer);if(!client&&!freelancer)throw Error('Connect a wallet that belongs to this agreement.');
   const i=Number(body.index),m=p.milestones[i];meta=structuredClone(p.doc);
   if(['submit','accept','revision'].includes(action)&&(!Number.isInteger(i)||!m))throw Error('Choose a valid milestone.');
   if(['join','submit'].includes(action)&&!freelancer)throw Error('This action needs the freelancer wallet.');
   if(['accept','revision','cancel'].includes(action)&&!client)throw Error('This action needs the client wallet.');
   switch(action){
    case 'join':if(!p.scopeMatches)throw Error('Import matching scope text before agreeing.');method='join';args=[projectId,p.scopeHash];break;
    case 'submit':{const e=evidence(body.note,body.url);if(meta.revisions)delete meta.revisions[i];method='submit';args=[projectId,i,e.hash];meta.evidence={...meta.evidence,[i]:e};break;}
    case 'accept':if(!p.scopeMatches||!m.evidence)throw Error('Import matching scope and delivery text before accepting.');method='accept';args=[projectId,i,p.scopeHash,m.hash];break;
    case 'revision':{const note=words(body.note,'Revision note',2000);meta.revisions={...meta.revisions,[i]:{note,hash:id(note)}};method='requestRevision';args=[projectId,i,m.hash,id(note)];break;}
    case 'scope':meta.proposedScope=words(body.scope,'New scope');method='proposeScope';args=[projectId,id(meta.proposedScope)];break;
    case 'agree_scope':if(typeof meta.proposedScope!=='string'||id(meta.proposedScope)!==p.proposedScope)throw Error('Import the matching proposed scope before agreeing.');method='agreeScope';args=[projectId,p.proposedScope,p.proposalNonce];meta.scope=meta.proposedScope;delete meta.proposedScope;meta.evidence=Object.fromEntries(Object.entries(meta.evidence||{}).filter(([i])=>p.milestones[i]?.state===2));break;
    case 'clear':if(String(body.expectedNonce)!==String(p.proposalNonce))throw Error('The proposal changed. Refresh before deciding.');delete meta.proposedScope;method='clearProposal';args=[projectId,p.proposalNonce];break;
    case 'dispute':{const note=words(body.note,'Dispute reason',2000);meta.dispute={note,hash:id(note)};delete meta.proposedScope;method='dispute';args=[projectId,id(note)];break;}
    case 'settle':method='proposeSettlement';args=[projectId,money(body.amount)];break;
    case 'agree_settlement':if(String(body.expectedNonce)!==String(p.proposalNonce)||String(body.expectedPayout)!==String(p.settlementPayout))throw Error('The settlement changed. Refresh and review the new split.');method='agreeSettlement';args=[projectId,p.settlementPayout,p.proposalNonce];break;
    case 'cancel':method='cancelBeforeJoin';args=[projectId];break;
    case 'withdraw':method='withdraw';args=[from];break;
    default:throw Error('Unknown agreement action.');
   }
  }
  return {draftKey:body.draftKey||null,to,data:new Interface(same(to,this.config.token)?tokenABI:escrowABI).encodeFunctionData(method,args),from,action,projectId,meta};
 }
 async send(action,body,signer){
  if(this.read().pending)throw Error('Check the pending receipt before sending another action.');await this.check();
  if(Number(await signer.provider.send('eth_chainId',[]))!==this.config.chainId)throw Error('Switch the wallet to Ethereum Sepolia.');
  const from=await signer.getAddress(),intent=await this.prepare(action,body,from);
  await this.provider.estimateGas({from,to:intent.to,data:intent.data});
  intent.nonce=await this.provider.getTransactionCount(from,'pending');intent.startBlock=await this.provider.getBlockNumber();intent.hash=null;
  const saved=this.read();saved.pending=intent;this.save(saved);
  try{const tx=await signer.sendTransaction({to:intent.to,data:intent.data,nonce:intent.nonce,value:0n});const state=this.read();state.pending.hash=tx.hash;this.save(state);const receipt=await tx.wait(1,120000);if(!receipt)throw Error('No receipt yet. Check pending receipts.');return await this.reconcile();}
  catch(e){if((e.code==='ACTION_REJECTED'||e.code===4001)&&!this.read().pending?.hash){const state=this.read();state.pending=null;this.save(state);}throw e;}
 }
 async reconcile(){
  const saved=this.read(),p=saved.pending;if(!p)return {status:'idle',message:'No pending transaction remains.'};await this.check();let hash=p.hash;
  if(!hash){const head=await this.provider.getBlockNumber();for(let b=head;b>=Math.max(p.startBlock,head-127);b--){const block=await this.provider.send('eth_getBlockByNumber',['0x'+b.toString(16),true]);const tx=block?.transactions.find(t=>same(t.from,p.from)&&Number(BigInt(t.nonce))===p.nonce);if(tx){hash=tx.hash;break;}}}
  if(!hash)return {status:'pending',message:'No matching mined transaction was found. Nothing was resent.'};
  const [tx,r]=await Promise.all([this.provider.getTransaction(hash),this.provider.getTransactionReceipt(hash)]);if(!tx||!r)return {status:'pending',message:'The receipt is still unavailable. Nothing was resent.'};
  if(!same(tx.from,p.from)||!same(tx.to,p.to)||tx.data!==p.data||tx.nonce!==p.nonce||tx.value!==0n)throw Error('The transaction differs from the saved intent. Keep it paused for inspection.');
  if(r.status===0){saved.pending=null;saved.receipts.push({hash,action:p.action,status:'reverted',block:r.blockNumber});this.save(saved);return {status:'reverted',message:'The transaction reverted. No project text was changed.'};}
  if(r.status!==1)throw Error('The receipt status is unknown.');
  let projectId=p.projectId;if(p.action==='create'){const found=r.logs.filter(l=>same(l.address,this.config.escrow)).map(l=>{try{return this.escrow.interface.parseLog(l);}catch{return null;}}).find(l=>l?.name==='Created');if(!found)throw Error('The creation receipt has no matching agreement event.');projectId=String(found.args.id);}
  if(p.action==='revision'){const call=this.escrow.interface.parseTransaction({data:p.data});p.meta.revisions[String(call.args[1])].txHash=hash;}if(p.action==='dispute')p.meta.dispute.txHash=hash;
  if(p.meta)saved.metadata[projectId]=p.meta;if(projectId&&!saved.known.includes(projectId))saved.known.push(projectId);
  saved.receipts.push({hash,action:p.action,projectId,status:'confirmed',block:r.blockNumber});saved.pending=null;this.save(saved);return {status:'confirmed',action:p.action,draftKey:p.draftKey,message:'Confirmed on chain. The record is saved.',projectId};
 }
 export(projectId){const s=this.read();return {format:'stagepay-text-v1',chainId:this.config.chainId,escrow:this.config.escrow,projectId,metadata:s.metadata[projectId]||{}};}
 async import(packet){
  if(packet?.format!=='stagepay-text-v1'||packet.chainId!==this.config.chainId||!same(packet.escrow,this.config.escrow))throw Error('This file belongs to a different deployment.');
  const p=await this.project(String(packet.projectId)),m=packet.metadata;
  if(!m||typeof m!=='object'||Array.isArray(m))throw Error('Invalid project text.');
  const title=words(m.title,'Project name',100),scope=words(m.scope,'Scope');if(id(scope)!==p.scopeHash)throw Error('The scope text does not match the current on-chain agreement.');
  if(!Array.isArray(m.milestones)||m.milestones.length!==p.milestones.length)throw Error('Milestone count differs from the agreement.');
  const clean={title,scope,milestones:m.milestones.map(m=>({name:words(m.name,'Milestone name',100)})),evidence:{}};
  for(const [i,e] of Object.entries(m.evidence||{})){if(!/^[0-2]$/.test(i)||!p.milestones[i])throw Error('Invalid evidence index.');const rebuilt=evidence(e.note,e.url);if(rebuilt.hash!==p.milestones[i].hash)throw Error('Delivery text does not match the chain.');clean.evidence[i]=rebuilt;}
  if(m.proposedScope){const proposal=words(m.proposedScope,'Proposed scope');if(id(proposal)!==p.proposedScope)throw Error('Proposed scope text does not match the chain.');clean.proposedScope=proposal;}
  const verifyReason=async(value,event,index)=>{const note=words(value.note,'Reason',2000);if(!/^0x[0-9a-fA-F]{64}$/.test(value.txHash||''))throw Error('The reason needs its confirmed transaction hash.');const receipt=await this.provider.getTransactionReceipt(value.txHash);if(!receipt||receipt.status!==1)throw Error('The reason receipt is unavailable.');const found=receipt.logs.filter(l=>same(l.address,this.config.escrow)).map(l=>{try{return this.escrow.interface.parseLog(l);}catch{return null;}}).find(l=>l?.name===event&&String(l.args.id)===p.id&&l.args.reason===id(note)&&(index===undefined||Number(l.args.milestone)===Number(index)));if(!found)throw Error('The reason text does not match its on-chain event.');return {note,hash:id(note),txHash:value.txHash};};
  clean.revisions={};for(const [i,value] of Object.entries(m.revisions||{})){if(!/^[0-2]$/.test(i)||!p.milestones[i])throw Error('Invalid revision index.');clean.revisions[i]=await verifyReason(value,'RevisionRequested',i);}
  if(m.dispute)clean.dispute=await verifyReason(m.dispute,'Disputed');
  const state=this.read();state.metadata[p.id]=clean;if(!state.known.includes(p.id))state.known.push(p.id);this.save(state);return p.id;
 }
}

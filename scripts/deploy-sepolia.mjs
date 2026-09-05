import {ContractFactory,JsonRpcProvider,getCreateAddress,keccak256,parseEther} from 'ethers';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {testWallet} from './testnet-wallet.mjs';
const rpc='https://ethereum-sepolia-rpc.publicnode.com';
const provider=new JsonRpcProvider(rpc,undefined,{batchMaxCount:1,cacheTimeout:-1,pollingInterval:3000});
const file=new URL('../.local/sepolia-deploy.json',import.meta.url);
await mkdir(new URL('../.local/',import.meta.url),{recursive:true,mode:0o700});
let journal;try{journal=JSON.parse(await readFile(file,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;journal={chainId:11155111,operations:{}};}
const save=()=>writeFile(file,JSON.stringify(journal,null,2),{mode:0o600});
try{
 if(Number(await provider.send('eth_chainId',[]))!==11155111)throw Error('Wrong RPC chain.');
 const wallet=(await testWallet('client')).connect(provider);journal.deployer=wallet.address;
 console.log(JSON.stringify({deployer:wallet.address,balanceWei:String(await provider.getBalance(wallet.address))}));
 async function send(key,request,contract=false){
  if(journal.operations[key]){const old=journal.operations[key],receipt=await provider.getTransactionReceipt(old.hash);if(!receipt)throw Error('Saved transaction still needs reconciliation: '+old.hash);if(receipt.status!==1)throw Error('Saved transaction reverted: '+old.hash);return old;}
  if(Number(await provider.send('eth_chainId',[]))!==11155111)throw Error('Wrong RPC chain.');
  const nonce=await provider.getTransactionCount(wallet.address,'pending'),estimate=await provider.estimateGas({...request,from:wallet.address}),fees=await provider.getFeeData();
  const gasLimit=estimate*12n/10n,maxFeePerGas=fees.maxFeePerGas,maxPriorityFeePerGas=fees.maxPriorityFeePerGas;
  if(!maxFeePerGas||!maxPriorityFeePerGas||gasLimit>8000000n||gasLimit*maxFeePerGas>parseEther('0.02'))throw Error('Testnet gas exceeds the bounded deployment allowance.');
  if(await provider.getBalance(wallet.address)<gasLimit*maxFeePerGas+(request.value||0n))throw Error('Free testnet gas is not available yet.');
  const raw=await wallet.signTransaction({...request,chainId:11155111,nonce,gasLimit,maxFeePerGas,maxPriorityFeePerGas,type:2});
  const entry={hash:keccak256(raw),nonce,kind:key,createdAt:new Date().toISOString(),...(contract?{address:getCreateAddress({from:wallet.address,nonce})}:{to:request.to,value:String(request.value)})};
  journal.operations[key]=entry;await save();
  const tx=await provider.broadcastTransaction(raw);console.log(JSON.stringify({sent:key,hash:tx.hash}));const receipt=await tx.wait(1,90000);if(!receipt||receipt.status!==1)throw Error('Inspect the saved deployment receipt before continuing.');entry.block=receipt.blockNumber;await save();return entry;
 }
 const tokenArtifact=JSON.parse(await readFile(new URL('../out/DemoToken.sol/DemoToken.json',import.meta.url))),escrowArtifact=JSON.parse(await readFile(new URL('../out/Stagepay.sol/Stagepay.json',import.meta.url)));
 const token=await send('token',await new ContractFactory(tokenArtifact.abi,tokenArtifact.bytecode.object,wallet).getDeployTransaction(),true);
 const escrow=await send('escrow',await new ContractFactory(escrowArtifact.abi,escrowArtifact.bytecode.object,wallet).getDeployTransaction(token.address),true);
 const freelancer=await testWallet('freelancer');await send('freelancer-gas',{to:freelancer.address,value:parseEther('0.005')});
 const tokenCode=await provider.getCode(token.address),escrowCode=await provider.getCode(escrow.address);if(tokenCode==='0x'||escrowCode==='0x')throw Error('Deployment code is unavailable.');
 const config={chainId:11155111,name:'Ethereum Sepolia',rpc,explorer:'https://sepolia.etherscan.io',escrow:escrow.address,token:token.address,escrowCodeHash:keccak256(escrowCode),tokenCodeHash:keccak256(tokenCode),deploymentBlock:escrow.block,deploymentStatus:'Deployed and receipt-verified on Ethereum Sepolia'};
 await writeFile(new URL('../public-app/config.json',import.meta.url),JSON.stringify(config,null,2)+'\n');
 await writeFile(new URL('../docs/sepolia-deployment.json',import.meta.url),JSON.stringify({...journal,config},null,2)+'\n');
 console.log(JSON.stringify(config));
}catch(e){console.error(e.shortMessage||e.message);process.exitCode=1;}finally{provider.destroy();}

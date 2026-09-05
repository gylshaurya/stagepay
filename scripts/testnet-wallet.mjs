// Project-only test wallets. No private keys or passwords are written to stdout or .env.
import {Wallet,randomBytes,hexlify} from 'ethers';
import {mkdir,readFile,writeFile,access} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const directory=new URL('../.wallets/',import.meta.url);
export async function testWallet(role,create=false){
 if(!['client','freelancer'].includes(role))throw Error('Unknown test wallet role.');
 const file=new URL(role+'.json',directory),service='stagepay-testnet-'+role+'-v1';
 try{await access(file);}catch{
  if(!create)throw Error('Create the encrypted test wallet first.');
  const wallet=Wallet.createRandom();let password;
  try{password=execFileSync('/usr/bin/security',['find-generic-password','-a','stagepay','-s',service,'-w'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();}catch{password=hexlify(randomBytes(32));}
  await mkdir(directory,{recursive:true,mode:0o700});
  const encrypted=await wallet.encrypt(password);
  // Interactive stdin keeps the new password out of process arguments and shell history.
  execFileSync('/usr/bin/security',['-i'],{input:`add-generic-password -a stagepay -s ${service} -U -w "${password}"\n`,stdio:['pipe','pipe','pipe']});
  const stored=execFileSync('/usr/bin/security',['find-generic-password','-a','stagepay','-s',service,'-w'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
  if(stored!==password)throw Error('Keychain did not store the test-wallet password.');
  await writeFile(file,encrypted,{mode:0o600,flag:'wx'});
 }
 const password=execFileSync('/usr/bin/security',['find-generic-password','-a','stagepay','-s',service,'-w'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
 return Wallet.fromEncryptedJson(await readFile(file,'utf8'),password);
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 try{for(const role of ['client','freelancer']){const wallet=await testWallet(role,process.argv.includes('--create'));console.log(JSON.stringify({role,address:wallet.address,storage:'encrypted keystore; password in macOS Keychain'}));}}
 catch{console.error('The encrypted test wallet could not be opened. Check macOS Keychain access. No secret was printed.');process.exitCode=1;}
}

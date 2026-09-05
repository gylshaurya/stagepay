import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const source = await fs.readFile(new URL('../web/app.js', import.meta.url), 'utf8');
const project = {id:'1',title:'Closed sample',scope:'A clearly labelled test agreement.',scope_hash:'0x123',version:4,status:'closed',disputed:false,proposal:null,remaining:'0',history:[],milestones:[{name:'Accepted step',state:'accepted',amount:'1000000000000000000',evidence:{note:'Delivered test work.',url:'https://example.com/work',hash:'0x'+'a'.repeat(64)}},{name:'Unfinished step',state:'pending',amount:'2000000000000000000',evidence:null}]};
async function render(record = structuredClone(project)) {
  const listeners = new Map();
  const app = {innerHTML:'',addEventListener:(name,fn)=>listeners.set(name,fn),setAttribute(){},removeAttribute(){}};
  const notice = {className:'',textContent:''};
  let blob,download;
  const state = {projects:[record,{...structuredClone(project),id:'2',title:'Another project must not enter the export'}],pending:[],network:{ready:true,client_credit:'0',freelancer_credit:'0'}};
  const context = vm.createContext({
    document:{querySelector:s=>s==='#app'?app:notice,body:{classList:{add(){},remove(){}}},createElement:()=>({click(){download=this.download;}})},
    sessionStorage:{getItem:k=>k==='stagepay-project'?'1':null,setItem(){}},
    fetch:async()=>({ok:true,json:async()=>state}),
    URL:{createObjectURL:value=>{blob=value;return 'blob:test-export';},revokeObjectURL(){}},
    Blob,setTimeout:()=>0,console,
  });
  vm.runInContext(source,context);
  await new Promise(setImmediate);
  return {app,record,export:async()=>{await listeners.get('click')({target:{closest:()=>({dataset:{ui:'export'}})}});return {name:download,body:JSON.parse(await blob.text())};}};
}
test('closed unfinished work is not shown as waiting for delivery',async()=>{
  const {app}=await render();
  assert.match(app.innerHTML,/Not accepted/);
  assert.doesNotMatch(app.innerHTML,/Waiting for work|No delivery yet/);
  assert.match(app.innerHTML,/This agreement is closed/);
});
test('export contains only the selected project and its local-demo label',async()=>{
  const view=await render();const saved=await view.export();
  assert.equal(saved.name,'stagepay-project-1.json');
  assert.deepEqual(saved.body,{mode:'local_demo',...view.record});
  assert.doesNotMatch(JSON.stringify(saved.body),/Another project/);
});
test('project text is escaped before it enters the rendered markup',async()=>{
  const record=structuredClone(project);record.title='<script>alert(1)</script>';record.scope='<img src=x onerror=alert(1)>';
  const {app}=await render(record);
  assert.doesNotMatch(app.innerHTML,/<script>|<img src=x/);
  assert.match(app.innerHTML,/&lt;script&gt;/);assert.match(app.innerHTML,/&lt;img/);
});

const {chromium}=require('playwright');const B='http://localhost:8721/';
(async()=>{const b=await chromium.launch();const out=[];
async function start(msg){const p=await (await b.newContext({viewport:{width:390,height:900}})).newPage();await p.goto(B);await p.waitForSelector('textarea');await p.waitForTimeout(1200);await p.fill('textarea',msg);await p.getByRole('button',{name:'Continue',exact:true}).click();await p.waitForSelector('text=Is this right',{timeout:60000});await p.waitForTimeout(1500);return p;}
async function pick(p,label){await p.getByText(label,{exact:true}).click();await p.waitForTimeout(1500);}
const go=p=>p.getByRole('button',{name:'Looks right, continue'});
// A: user's exact case: failed + money taken + low balance
let p=await start('my sip failed');await pick(p,'Yes');await pick(p,'Not enough balance');let t=await p.innerText('body');
out.push(['A warning shown',t.includes("don't go together")],['A continue disabled',await go(p).isDisabled()]);await p.getByText('Pick one of the options above').scrollIntoViewIfNeeded();await p.screenshot({path:'conflict.png'});
await p.getByRole('button',{name:/Money was taken/}).click();await p.waitForTimeout(1500);t=await p.innerText('body');out.push(['A fix1 clears warning',!t.includes("don't go together")&&!(await go(p).isDisabled())]);
await go(p).click();await p.waitForTimeout(2500);t=await p.innerText('body');out.push(['A fix1 result = money taken not invested',/money was taken|debited|not invested/i.test(t.slice(t.indexOf('Likely reason'),t.indexOf('Likely reason')+300)),t.slice(t.indexOf('Likely reason'),t.indexOf('Likely reason')+90).replace(/\n/g,' ')]);
// B: resolve as no money taken
p=await start('my sip failed');await pick(p,'Yes');await pick(p,'Not enough balance');await p.getByRole('button',{name:/The reason is right/}).click();await p.waitForTimeout(1500);await go(p).click();await p.waitForTimeout(2500);t=await p.innerText('body');out.push(['B result low balance',t.includes('Likely reason')&&/balance/i.test(t.slice(t.indexOf('Likely reason'),t.indexOf('Likely reason')+120))]);
// C: not sure about either
p=await start('my sip failed');await pick(p,'Taken, then returned');await pick(p,'Above the AutoPay limit');t=await p.innerText('body');out.push(['C refunded+limit warns',t.includes('taken and then returned')]);
await p.getByRole('button',{name:/not sure about either/}).click();await p.waitForTimeout(1500);out.push(['C continue enabled',!(await go(p).isDisabled())]);
// D: message itself contradicts (AI prefill)
p=await start('money got deducted but bank sms says insufficient balance and sip failed');t=await p.innerText('body');out.push(['D prefill contradiction caught',t.includes("don't go together")]);
// E: no streamlit warnings
out.push(['E no widget warning',!/Session State API|was created with a default value/.test(t)]);
console.log(JSON.stringify(out,null,1));await b.close();})();

const {chromium}=require('playwright');const B='http://localhost:8751/';
const BAN=[/privacy check/i,/declined/i,/guardrail/i,/fixed rules/i,/general guidance/i,/\[source\]/i,/\bAI\b/,/rules only/i,/you confirmed/i,/from your message/i];
(async()=>{const b=await chromium.launch();const out=[];const errs=[];
for(const [i,want] of [[0,'enough balance'],[1,'above your AutoPay limit'],[2,"can't tell"]]){
const p=await (await b.newContext({viewport:{width:390,height:900}})).newPage();p.on('pageerror',e=>errs.push(e.message));
await p.goto(B);await p.waitForSelector('textarea');await p.waitForTimeout(1200);const t0=Date.now();let taps=0;
await p.getByRole('button',{name:'See it from a failure alert (demo)'}).click();taps++;await p.waitForTimeout(1500);
let t=await p.innerText('body');if(i==0){out.push(['demo page labelled',t.includes('Demo only')]);await p.screenshot({path:'alert_demo.png'});}
await p.getByRole('button',{name:'See how to fix it'}).nth(i).click();taps++;await p.waitForSelector('text=Looks right, continue');await p.waitForTimeout(800);
t=await p.innerText('body');out.push([`A${i} prefilled from alert`,t.includes('Filled in from the alert')&&t.includes('From the alert')]);
await p.getByRole('button',{name:'Looks right, continue'}).click();taps++;await p.waitForTimeout(2000);t=await p.innerText('body');
if(/Did you change/.test(t)){await p.getByRole('button',{name:'No changes'}).click();taps++;await p.waitForTimeout(1800);t=await p.innerText('body');}
out.push([`A${i} outcome`,t.toLowerCase().includes(want.toLowerCase()),`taps ${taps}, ${Math.round((Date.now()-t0)/100)/10}s`]);
out.push([`A${i} no internal words`,!BAN.some(r=>r.test(t))]);
if(i==0){await p.screenshot({path:'alert_result.png'});await p.getByRole('button',{name:'Type instead'}).click();await p.waitForTimeout(1200);out.push(['Type instead from alert opens empty box',(await p.inputValue('textarea'))==='']);}
}
// back from demo
const p=await (await b.newContext({viewport:{width:390,height:900},colorScheme:'dark'})).newPage();await p.goto(B);await p.waitForSelector('textarea');await p.waitForTimeout(1000);
await p.getByRole('button',{name:'See it from a failure alert (demo)'}).click();await p.waitForTimeout(1500);await p.screenshot({path:'alert_dark.png'});
await p.getByRole('button',{name:'← Back'}).click();await p.waitForTimeout(1500);out.push(['Back from demo to home',(await p.innerText('body')).includes('What happened to your SIP?')]);
console.log(JSON.stringify(out));console.log('errors',errs.length);await b.close();})();

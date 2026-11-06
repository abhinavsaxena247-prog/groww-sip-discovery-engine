const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await (await b.newContext({viewport:{width:390,height:700}})).newPage();
await p.goto('http://localhost:8791/');await p.waitForSelector('textarea');await p.waitForTimeout(1500);
const pos=()=>p.evaluate(()=>{const e=document.querySelector('[data-testid=stMain]')||document.querySelector('section.main');return [e?e.scrollTop:-1,window.scrollY]});
const btn=p.getByRole('button',{name:'See it from a failure alert (demo)'});await btn.scrollIntoViewIfNeeded();console.log('before',await pos());
await btn.click();await p.waitForTimeout(2500);console.log('demo page',await pos(),await p.getByText('Demo only').isVisible(), await p.getByText('Demo only').boundingBox());
await p.getByRole('button',{name:'See how to fix it'}).nth(2).scrollIntoViewIfNeeded();await p.getByRole('button',{name:'See how to fix it'}).nth(2).click();await p.waitForTimeout(2500);console.log('check screen',await pos(),await p.getByText('From the alert',{exact:true}).boundingBox());
await b.close();})();

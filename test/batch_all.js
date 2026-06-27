const { chromium } = require('playwright');

const airports = [
    ["NOW加速","https://nowjiasu.com"],
    ["瞬云","https://shunyun.xyz"],
    ["仙路湾","https://xianluwan.com"],
    ["山水云","https://shanshuiyun.com"],
    ["NICE加速","https://nicejiasu.com"],
    ["锦云","https://jinyun.pro"],
    ["寰宇云","https://huanyuyun.com"],
    ["秒秒云","https://miaomiaoyun.com"],
    ["大哥云","https://dageyun.com"],
    ["SKYLUMO","https://skylumo.com"],
    ["宇宙云","https://yuzhouyun.com"],
    ["光年梯","https://guangnianti.com"],
    ["闪狐云","https://shanhuyun.com"],
    ["FSCloud","https://dash.fscloud.app"],
    ["奈云v2ny","https://www.v2ny.com"],
    ["雨燕云","https://yuyan.online"],
    ["逗猫","https://douchat.top"],
    ["泰山Net","https://www.taishan.pro"],
    ["一元机场(old)","https://xn--4gq62f52gdss.top"],
    ["极光加速","https://jiguang.pro"],
    ["besnow","https://besnow.me"],
    ["aiguobit","https://a.aiguobit.com"],
    ["hidexx","https://a.hidexx.com"],
    ["69云","https://69yun69.com"],
    ["淘气兔","https://vip.xn--h5qy56dzhb.vip/#/register"],
];

(async () => {
    const browser = await chromium.launch({ channel: 'msedge', headless: false });
    const page = await browser.newPage();
    page.setDefaultTimeout(10000);
    
    const results = [];
    
    for (const [name, url] of airports) {
        try {
            process.stdout.write(`[${name}] ${url} ... `);
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 12000 });
            await page.waitForTimeout(2000);
            const title = await page.title();
            const finalUrl = page.url();
            const text = (await page.evaluate('document.body.innerText')).substring(0, 500);
            
            // Check if dead
            const dead = /domain.*sale|域名.*出售|parked|godaddy|afternic|buy this domain/i.test(text);
            const hasRegister = /注册|register|sign.?up/i.test(text);
            const captcha = /recaptcha|captcha|人机验证|turnstile|hcaptcha/i.test(text);
            
            const status = dead ? 'DEAD' : (hasRegister ? 'ONLINE_REG' : (text ? 'ONLINE' : 'BLANK'));
            console.log(`${status} | ${title.substring(0,60)}${captcha ? ' [CAPTCHA]' : ''}`);
            results.push({ name, url, finalUrl, status, title, captcha });
            
        } catch (e) {
            console.log(`ERROR: ${e.message.substring(0,60)}`);
            results.push({ name, url, status: 'ERROR', error: e.message.substring(0,80) });
        }
    }
    
    console.log('\n===== SUMMARY =====');
    const online = results.filter(r => r.status === 'ONLINE_REG');
    console.log(`\nREGISTER-ABLE (${online.length}):`);
    online.forEach(r => console.log(`  ${r.name}: ${r.finalUrl}`));
    
    const other = results.filter(r => r.status !== 'ONLINE_REG');
    console.log(`\nOTHER (${other.length}):`);
    other.forEach(r => console.log(`  ${r.name}: ${r.status} - ${r.title||''} ${r.error||''}`));
    
    await browser.close();
})();

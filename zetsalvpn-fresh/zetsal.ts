// zetsal.ts - 使用 puppeteer-core + 系统 tesseract CLI
import puppeteer from 'puppeteer-core';
import { customAlphabet } from 'nanoid';
import { execSync } from 'child_process';
import fs from 'fs';

const nanoid = customAlphabet('abcdefghijklmnopqrstuvwxyz1234567890', 16);
const username = nanoid(10);
const email = nanoid(8) + '@KiNpNAk4EDbyhp5RPsBxpEisR8.com';
const password = nanoid(16);

const chromePath = 'C:\\Users\\XZXyuan\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe';
const tesseractPath = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe';

async function main() {
  console.log(`Username: ${username}`);
  console.log(`Email: ${email}`);
  console.log(`Password: ${password}`);

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--proxy-server=direct://']
  });

  try {
    const page = await browser.newPage();
    await page.goto('https://zetsal.com/register', { waitUntil: 'domcontentloaded', timeout: 120000 });
    console.log('Page loaded');

    // Fill registration form
    await page.type('#username', username);
    await page.type('#email', email);
    await page.type('#password', password);
    await page.type('#password2', password);
    console.log('Form filled');

    // Wait for captcha to fully render, then screenshot
    await new Promise(r => setTimeout(r, 2000));
    const capimg = await page.waitForSelector('#cap', { timeout: 10000 });
    await capimg?.screenshot({ path: 'captcha.png' });
    console.log('Captcha screenshot taken');

    // OCR with system tesseract - try multiple PSM modes with retry
    let captchaText = '';
    let registerSuccess = false;
    
    for (let attempt = 0; attempt < 10; attempt++) {
      // Fresh captcha each attempt
      if (attempt > 0) {
        await page.goto('https://zetsal.com/register', { waitUntil: 'domcontentloaded', timeout: 120000 });
        await page.type('#username', username);
        await page.type('#email', email);
        await page.type('#password', password);
        await page.type('#password2', password);
        const capimg2 = await page.waitForSelector('#cap', { timeout: 10000 });
        await new Promise(r => setTimeout(r, 2000));
        await capimg2?.screenshot({ path: 'captcha.png' });
      }
      
      for (const psm of ['8', '7', '13']) {
        captchaText = execSync(`"${tesseractPath}" captcha.png - --psm ${psm} -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`, { encoding: 'utf-8' }).trim().replace(/[^a-zA-Z0-9]/g, '');
        if (captchaText.length >= 3 && captchaText.length <= 8) break;
      }
      console.log(`Attempt ${attempt+1} captcha: ${captchaText}`);
      
      // Clear captcha field and type new value
      await page.evaluate(() => {
        const el = document.querySelector('#captcha') as HTMLInputElement;
        if (el) { el.value = ''; el.dispatchEvent(new Event('input', {bubbles: true})); }
      });
      await page.type('#captcha', captchaText);
      await page.click('#btn');
      await new Promise(r => setTimeout(r, 5000));
      
      const currentUrl = page.url();
      console.log(`After submit URL: ${currentUrl}`);
      
      if (!currentUrl.includes('register')) {
        registerSuccess = true;
        break;
      }
    }
    
    if (!registerSuccess) {
      console.log('Registration failed after 10 attempts');
      await browser.close();
      return;
    }
    
    console.log('Registration success!');

    // Login first (registration redirected to login page)
    await page.goto('https://zetsal.com/login', { waitUntil: 'domcontentloaded', timeout: 120000 });
    await new Promise(r => setTimeout(r, 2000));
    await page.type('#username', username);
    await page.type('#password', password);
    await page.click('#btn');
    await new Promise(r => setTimeout(r, 5000));
    console.log('Logged in, URL:', page.url());

    // Go to plans and claim
    await page.goto('https://zetsal.com/plans', { waitUntil: 'domcontentloaded', timeout: 120000 });
    await new Promise(r => setTimeout(r, 3000));
    try {
      const claimBtn = await page.waitForSelector('body > .slim-mainpanel > .container > .alert > .btn', { timeout: 10000 });
      await claimBtn?.click();
      await new Promise(r => setTimeout(r, 5000));
      console.log('Free trial claimed');
    } catch {
      console.log('No claim button found, checking page content...');
      const text = await page.evaluate(() => document.body.innerText.substring(0, 500));
      console.log('Page text:', text);
    }

    // Save account
    const line = `${username}:${password}\n`;
    fs.appendFileSync('./zetsal.txt', line);
    console.log(`\nAccount saved: ${username}:${password}`);
  } catch (e: any) {
    console.error('Error:', e.message || e);
  } finally {
    await browser.close();
  }
}

main();

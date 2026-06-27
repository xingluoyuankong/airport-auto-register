/**
 * airport_register_browser.js — 浏览器 + 临时邮箱 机场自动注册
 * 
 * 流程:
 * 1. temp_mail.js 创建临时邮箱
 * 2. Puppeteer 打开机场注册页
 * 3. 填表提交 → 触发验证码邮件
 * 4. temp_mail.js 轮询收验证码
 * 5. 填验证码完成注册
 * 6. 提取订阅链接
 * 
 * 用法: node airport_register_browser.js
 */

const puppeteer = require("puppeteer-core");
const tm = require("./temp_mail"); // need to copy from ZO plugin
const fs = require("fs");
const path = require("path");

const CONFIG = {
  edgePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  resultsDir: path.join(__dirname, "register_results"),
  timeout: 120000, // 2 min per airport
};

// ========== Airport Configs ==========
// These airports have web-based registration (not API-only)
// and don't block temp mail domains (test each)
const AIRPORTS = [
  {
    name: "奈云 v2ny",
    url: "https://www.v2ny.com",
    signupPath: "/#/register",
    selectors: {
      email: 'input[placeholder*="邮箱"], input[name="email"], input[type="email"]',
      password: 'input[placeholder*="密码"], input[name="password"], input[type="password"]',
      confirmPassword: 'input[placeholder*="确认"], input[name="confirm_password"]',
      emailCode: 'input[placeholder*="验证码"], input[name="email_code"]',
      sendCode: 'button:contains("发送"), button:contains("获取"), button:contains("Send")',
      submit: 'button:contains("注册"), button:contains("Sign"), button[type="submit"]',
    },
    emailCodeRequired: true,
  },
  {
    name: "雨燕云",
    url: "https://yuyan.online",
    signupPath: "/#/register",
    selectors: {
      email: 'input[placeholder*="邮箱"], input[name="email"]',
      password: 'input[placeholder*="密码"], input[name="password"]',
      emailCode: 'input[placeholder*="验证码"], input[name="email_code"]',
      sendCode: 'button:contains("发送"), button:contains("获取")',
      submit: 'button:contains("注册"), button[type="submit"]',
    },
    emailCodeRequired: true,
  },
  {
    name: "泰山Net",
    url: "https://www.taishan.pro",
    signupPath: "/#/register",
    selectors: {
      email: 'input[placeholder*="邮箱"], input[name="email"]',
      password: 'input[placeholder*="密码"], input[name="password"]',
      emailCode: 'input[placeholder*="验证码"], input[name="email_code"]',
      sendCode: 'button:contains("发送"), button:contains("获取")',
      submit: 'button:contains("注册"), button[type="submit"]',
    },
    emailCodeRequired: true,
  },
  {
    name: "Speedy",
    url: "https://cloud.speedypro.xyz",
    signupPath: "/#/register",
    selectors: {
      email: 'input[placeholder*="邮箱"], input[name="email"]',
      password: 'input[placeholder*="密码"], input[name="password"]',
      emailCode: 'input[placeholder*="验证码"], input[name="email_code"]',
      sendCode: 'button:contains("发送"), button:contains("获取")',
      submit: 'button:contains("注册"), button[type="submit"]',
    },
    emailCodeRequired: true,
  },
  {
    name: "GLaDOS",
    url: "https://glados.network",
    signupPath: "/#/register",
    selectors: {
      email: 'input[placeholder*="邮箱"], input[name="email"]',
      password: 'input[placeholder*="密码"], input[name="password"]',
      submit: 'button:contains("注册"), button:contains("Sign")',
    },
    emailCodeRequired: false,
    note: "可能需要邀请码，先测试",
  },
];

// ========== Core Logic ==========
async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function createTempEmail(log) {
  // Prefer tempmailplus, guerrillamail, maildrop — no account needed
  const providers = ["tempmailplus", "guerrilla", "maildrop", "inboxes", "catchmail", "tempmailio", "mailtm", "mailgw"];
  // Use the ZO temp_mail module
  const tmModule = require("E:/API获取工具/ZO注册/plugin/temp_mail");
  return await tmModule.createEmail({ 
    providers, 
    log: (msg) => log(`[TEMP] ${msg}`) 
  });
}

async function pollForCode(email, credentials, providerInstance, provider, opts = {}) {
  const tmModule = require("E:/API获取工具/ZO注册/plugin/temp_mail");
  try {
    return await tmModule.pollInbox(email, credentials, {
      providerInstance,
      provider,
      keyword: opts.keyword || "",
      timeout: opts.timeout || 120,
      interval: 3000,
      log: (msg) => console.log(`[POLL] ${msg}`),
    });
  } catch (e) {
    return null;
  }
}

async function launchBrowser(log) {
  const tempDir = fs.mkdtempSync(path.join(require("os").tmpdir(), "ap_reg_"));
  const browser = await puppeteer.launch({
    executablePath: CONFIG.edgePath,
    headless: false,
    protocolTimeout: 300000,
    userDataDir: tempDir,
    args: [
      "--no-first-run", "--no-default-browser-check",
      "--window-size=1280,800", "--disable-gpu",
      "--disable-features=Translate,msSmartScreenProtection",
    ],
    defaultViewport: { width: 1280, height: 800 },
    ignoreDefaultArgs: ["--enable-automation"],
  });
  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();
  log(`[BROWSER] Edge launched, temp=${tempDir}`);
  return { browser, page, tempDir };
}

async function fillInput(page, selector, value, log) {
  // Try multiple times
  for (let attempt = 0; attempt < 5; attempt++) {
    const el = await page.$(selector);
    if (!el) {
      log(`  [FILL] selector not found: ${selector.slice(0, 60)}`);
      await sleep(1000);
      continue;
    }
    await el.click({ clickCount: 3 });
    await sleep(200);
    await el.type(value, { delay: 30 });
    await sleep(100);
    return true;
  }
  return false;
}

async function clickButton(page, selectors, log) {
  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        await el.click();
        log(`  [CLICK] ${sel}`);
        return true;
      }
    } catch {}
  }
  // XPath fallback for text-based buttons
  const textSels = selectors.filter(s => s.includes("contains"));
  for (const textSel of textSels) {
    const match = textSel.match(/:contains\("([^"]+)"\)/);
    if (!match) continue;
    const text = match[1];
    try {
      const xpath = `//button[contains(text(),"${text}") or contains(.,"${text}")] | //a[contains(text(),"${text}")]`;
      const el = await page.$x(xpath);
      if (el.length > 0) {
        await el[0].click();
        log(`  [CLICK] xpath: "${text}"`);
        return true;
      }
    } catch {}
  }
  return false;
}

async function registerAirport(airport, log) {
  log(`\n========== [${airport.name}] ==========`);
  if (airport.note) log(`  NOTE: ${airport.note}`);
  
  // Step 1: Create temp email
  log(`  Creating temp email...`);
  let tempResult;
  try {
    tempResult = await createTempEmail(log);
    log(`  ✅ Temp email: ${tempResult.email}`);
  } catch (e) {
    log(`  ❌ Temp email failed: ${e.message}`);
    return { success: false, error: e.message, airport: airport.name };
  }
  
  const { email, credentials, providerInstance, provider } = tempResult;
  
  // Step 2: Launch browser
  let browserCtx;
  try {
    browserCtx = await launchBrowser(log);
  } catch (e) {
    log(`  ❌ Browser failed: ${e.message}`);
    return { success: false, error: e.message, airport: airport.name, email };
  }
  const { browser, page } = browserCtx;
  
  try {
    // Step 3: Navigate to signup
    const signupUrl = airport.url + airport.signupPath;
    log(`  Navigating to ${signupUrl}`);
    await page.goto(signupUrl, { waitUntil: "networkidle2", timeout: 30000 });
    await sleep(2000);
    
    // Check for Cloudflare
    const pageText = await page.evaluate(() => document.body.innerText.slice(0, 500));
    if (pageText.includes("Just a moment") || pageText.includes("Checking your browser")) {
      log(`  ⚠️ Cloudflare detected, waiting 10s...`);
      await sleep(10000);
    }
    
    // Step 4: Fill email
    log(`  Filling email: ${email}`);
    await fillInput(page, airport.selectors.email, email, log);
    await sleep(500);
    
    // Step 5: Fill password
    const pwd = "Aa123456!@#";
    log(`  Filling password`);
    await fillInput(page, airport.selectors.password, pwd, log);
    if (airport.selectors.confirmPassword) {
      await fillInput(page, airport.selectors.confirmPassword, pwd, log);
    }
    await sleep(500);
    
    // Step 6: Send verification code
    if (airport.emailCodeRequired) {
      log(`  Clicking send code...`);
      const sent = await clickButton(page, airport.selectors.sendCode, log);
      if (!sent) {
        log(`  ❌ Could not find send code button`);
        return { success: false, error: "send_code_button_not_found", airport: airport.name, email };
      }
      
      // Step 7: Poll for code
      log(`  Polling for verification code...`);
      await sleep(3000); // wait for email to arrive
      const codeResult = await pollForCode(email, credentials, providerInstance, provider, {
        timeout: 60,
        keyword: airport.name.toLowerCase().includes("v2ny") ? "奈云" : airport.name.toLowerCase(),
      });
      
      if (!codeResult) {
        log(`  ❌ Verification code not received`);
        return { success: false, error: "no_code", airport: airport.name, email };
      }
      
      const code = codeResult.code || 
                   (codeResult.message?.text || codeResult.message?.html || "").match(/\b(\d{6})\b/)?.[1] ||
                   (codeResult.messageDetail?.text || codeResult.messageDetail?.html || "").match(/\b(\d{6})\b/)?.[1];
      
      if (!code) {
        log(`  ❌ No 6-digit code found in email`);
        log(`  Email subject: ${codeResult.message?.subject || codeResult.messageDetail?.subject || "?"}`);
        // Dump first 200 chars
        const preview = (codeResult.message?.text || codeResult.messageDetail?.text || "").slice(0, 200);
        log(`  Preview: ${preview}`);
        return { success: false, error: "code_not_extracted", airport: airport.name, email };
      }
      
      log(`  ✅ Verification code: ${code}`);
      
      // Fill code
      await fillInput(page, airport.selectors.emailCode, code, log);
      await sleep(500);
    }
    
    // Step 8: Submit
    log(`  Submitting registration...`);
    await clickButton(page, airport.selectors.submit, log);
    await sleep(5000);
    
    // Step 9: Check success
    const currentUrl = page.url();
    const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
    
    if (bodyText.includes("注册成功") || bodyText.includes("success") || 
        currentUrl.includes("dashboard") || currentUrl.includes("user") || 
        !currentUrl.includes("register")) {
      log(`  ✅ Registration SUCCESS!`);
      log(`  URL: ${currentUrl}`);
      
      // Step 10: Extract subscription link
      let subLink = "";
      try {
        // Navigate to user page to find subscribe link
        await page.goto(airport.url + "/#/user", { waitUntil: "networkidle2", timeout: 15000 });
        await sleep(3000);
        const subText = await page.evaluate(() => document.body.innerText);
        const subMatch = subText.match(/https?:\/\/[^\s]+subscribe[^\s]*/i);
        if (subMatch) subLink = subMatch[0];
        
        if (!subLink) {
          // Try API
          const cookies = await page.cookies();
          const authCookie = cookies.find(c => c.name.includes("auth") || c.name.includes("token") || c.name.includes("session"));
          // Try dashboard copy button
          const copyBtns = await page.$$('button:has-text("复制"), button:has-text("Copy"), button:has-text("订阅")');
          if (copyBtns.length > 0) {
            await copyBtns[0].click();
            await sleep(500);
            subLink = await page.evaluate(() => navigator.clipboard.readText().catch(() => ""));
          }
        }
      } catch {}
      
      log(`  SUB: ${subLink || "(not found)"}`);
      
      return {
        success: true,
        airport: airport.name,
        email,
        password: pwd,
        subscriptionLink: subLink,
      };
    }
    
    log(`  ❌ Registration failed: ${bodyText.slice(0, 200)}`);
    return { success: false, error: "reg_failed", airport: airport.name, email, details: bodyText.slice(0, 200) };
    
  } catch (e) {
    log(`  ❌ Exception: ${e.message}`);
    return { success: false, error: e.message, airport: airport.name, email };
  } finally {
    await browser.close();
    // Cleanup temp dir
    try { fs.rmSync(browserCtx.tempDir, { recursive: true, force: true }); } catch {}
  }
}

async function main() {
  console.log("=== AIRPORT REGISTRATION - BROWSER + TEMP MAIL ===\n");
  
  if (!fs.existsSync(CONFIG.resultsDir)) fs.mkdirSync(CONFIG.resultsDir, { recursive: true });
  
  const results = [];
  const subLinks = [];
  
  for (const airport of AIRPORTS) {
    const result = await registerAirport(airport, (msg) => console.log(msg));
    results.push(result);
    
    if (result.success && result.subscriptionLink) {
      subLinks.push(`${result.airport} | ${result.email} | ${result.subscriptionLink}`);
    }
    
    // Pause between airports
    await sleep(3000);
  }
  
  console.log("\n========== RESULTS ==========");
  const ok = results.filter(r => r.success).length;
  console.log(`OK: ${ok} | FAIL: ${results.length - ok}`);
  
  if (subLinks.length > 0) {
    console.log("\n=== SUBSCRIPTION LINKS ===");
    subLinks.forEach(l => console.log(l));
  }
  
  fs.writeFileSync(
    path.join(CONFIG.resultsDir, "browser_results.json"),
    JSON.stringify(results, null, 2)
  );
  fs.writeFileSync(
    path.join(CONFIG.resultsDir, "browser_subs.txt"),
    subLinks.join("\n")
  );
  console.log(`\nSAVED: ${CONFIG.resultsDir}/browser_results.json`);
}

main().catch(e => console.error("FATAL:", e));

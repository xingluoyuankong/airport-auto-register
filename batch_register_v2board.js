/**
 * 批量机场注册 - V2Board API POST 模式
 * 基于已有 hidexx/zcapi 的注册经验
 * 使用系统代理 127.0.0.1:7897 访问
 */
const https = require('https');
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

// 真实 Outlook 邮箱（密码从已使用文件夹提取）
const EMAILS = [
  { email: 'sanchezquinncu3w1kkhtuc74@outlook.com', password: '3pKPx5!rE9%9nJDLJC' },
  { email: 'hendricktamm95v80awzaxli@outlook.com', password: '@^NdxP5KN#s9G2Hqu0!' },
  { email: 'parker738403dcp34kfdl6j@outlook.com', password: 'oo^5v=Q%&RU$pdDrax' },
];

// 机场列表 - 把 405 的 POST 注册 + 已知 V2Board + 其他面板
const AIRPORTS = [
  // V2Board 返回 405 (需要POST) - 最可能成功
  { name: '奈云v2ny', registerUrl: 'https://www.v2ny.com/api/v1/passport/auth/register', type: 'v2board' },
  { name: 'Speedy', registerUrl: 'https://cloud.speedypro.xyz/api/v1/passport/auth/register', type: 'v2board' },
  { name: '雨燕云', registerUrl: 'https://yuyan.online/api/v1/passport/auth/register', type: 'v2board' },
  { name: '逗猫', registerUrl: 'https://doucat.top/api/v1/passport/auth/register', type: 'v2board' },
  { name: '泰山Net', registerUrl: 'https://www.taishan.pro/api/v1/passport/auth/register', type: 'v2board' },
  // V2Board 返回 403 - 也试试 POST
  { name: 'FSCloud', registerUrl: 'https://dash.fscloud.app/api/v1/passport/auth/register', type: 'v2board' },
  { name: '一元机场', registerUrl: 'https://xn--4gq62f52gdss.top/api/v1/passport/auth/register', type: 'v2board' },
  { name: '魔戒', registerUrl: 'https://www.mojie.me/api/v1/passport/auth/register', type: 'v2board' },
  { name: '狗头加速', registerUrl: 'https://lksi.xyz/api/v1/passport/auth/register', type: 'v2board' },
  { name: 'besnow', registerUrl: 'https://besnow.me/api/v1/passport/auth/register', type: 'v2board' },
  // SSPanel 表单注册 (需要解析HTML)
  { name: '69云', registerUrl: 'https://69yun69.com/auth/register', type: 'sspanel' },
  { name: '泰山', registerUrl: 'https://jp.taishan.pro/register', type: 'sspanel' },
];

const PROXY = { host: '127.0.0.1', port: 7897 };

function proxyRequest(method, targetUrl, data, headers) {
  return new Promise((resolve, reject) => {
    const u = new URL(targetUrl);
    const opts = {
      hostname: PROXY.host,
      port: PROXY.port,
      method: method,
      path: targetUrl,
      headers: {
        ...headers,
        'Host': u.hostname,
        'Proxy-Connection': 'keep-alive',
      },
      rejectUnauthorized: false,
      timeout: 15000,
    };

    const mod = u.protocol === 'https:' ? https : http;
    const req = mod.request(opts, (res) => {
      let raw = '';
      res.on('data', (chunk) => raw += chunk);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: raw }));
    });
    req.on('error', (e) => reject(e));
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    if (data) req.write(data);
    req.end();
  });
}

async function tryV2BoardRegister(airport, email, password) {
  const payload = JSON.stringify({
    email: email,
    password: password,
    email_code: null,  // 不绕过邮箱验证，留空让面板决定
    invite_code: '',
    recaptcha_data: '',
  });

  const headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': new URL(airport.registerUrl).origin + '/',
    'Origin': new URL(airport.registerUrl).origin,
  };

  try {
    const res = await proxyRequest('POST', airport.registerUrl, payload, headers);
    let parsed = null;
    try { parsed = JSON.parse(res.body); } catch(e) {}

    if (res.status === 200 && parsed && parsed.data) {
      const token = parsed.data.token || parsed.data.auth_data || '';
      return { success: true, email, password, token, raw: JSON.stringify(parsed).substring(0, 300) };
    } else if (res.status === 200 && parsed) {
      const msg = parsed.message || parsed.msg || JSON.stringify(parsed).substring(0, 150);
      return { success: false, reason: `API_REFUSED: ${msg}` };
    } else if (res.status === 429) {
      return { success: false, reason: 'RATE_LIMITED' };
    } else if (res.status === 403) {
      return { success: false, reason: 'FORBIDDEN (可能Cloudflare)' };
    } else {
      return { success: false, reason: `HTTP_${res.status}: ${res.body.substring(0, 100)}` };
    }
  } catch (e) {
    return { success: false, reason: `NET_ERR: ${e.message}` };
  }
}

async function trySSPanelRegister(airport, email, password) {
  // SSPanel 需要先GET注册页获取token，再POST表单
  try {
    const getRes = await proxyRequest('GET', airport.registerUrl, null, {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0',
    });
    const html = getRes.body;
    // 简单检查是否可注册
    if (html.includes('注册') || html.includes('register') || html.includes('Register')) {
      return { success: false, reason: 'SSPanel_NEEDS_BROWSER (验证码/CF)' };
    }
    return { success: false, reason: `SSPanel_UNKNOWN: body=${html.length}bytes` };
  } catch (e) {
    return { success: false, reason: `SSPanel_NET_ERR: ${e.message}` };
  }
}

async function main() {
  const results = [];
  const outDir = path.join(__dirname, 'register_results');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  for (const ap of AIRPORTS) {
    console.log(`\n=== ${ap.name} (${ap.type}) ===`);
    for (const user of EMAILS) {
      console.log(`  Testing: ${user.email.substring(0, 25)}...`);
      let result;
      if (ap.type === 'v2board') {
        result = await tryV2BoardRegister(ap, user.email, user.password);
      } else {
        result = await trySSPanelRegister(ap, user.email, user.password);
      }
      result.airport = ap.name;
      result.url = ap.registerUrl;
      console.log(`  -> ${result.success ? '✅ SUCCESS' : '❌ ' + result.reason}`);
      if (result.success) {
        // 成功后尝试获取订阅链接
        console.log(`     Token: ${result.token}`);
        results.push(result);
      }
      // 同一机场不同邮箱间隔2秒
      await new Promise(r => setTimeout(r, 2000));
    }
    // 机场间隔3秒
    await new Promise(r => setTimeout(r, 3000));
  }

  // 保存
  const summaryPath = path.join(outDir, `register_summary_${Date.now()}.json`);
  fs.writeFileSync(summaryPath, JSON.stringify(results, null, 2), 'utf-8');

  console.log('\n\n===== 汇总 =====');
  console.log(`成功: ${results.length} 个账号`);
  results.forEach(r => {
    console.log(`  ✅ ${r.airport}: ${r.email} | token=${r.token}`);
  });
  if (results.length === 0) {
    console.log('  ⚠️ 全部失败，分析中...');
  }
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });

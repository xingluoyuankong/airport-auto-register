/**
 * outlook_verify.js — Microsoft Graph API 通用验证码提取器
 * 
 * 输入: email + clientId + refreshToken (from 邮箱----密码----clientId----refreshToken)
 * 流程: refreshToken → accessToken → GET /me/messages → 轮询提取验证码/链接
 * 输出: { code, link, email }
 * 
 * 用法:
 *   const ov = require('./outlook_verify');
 *   const result = await ov.findCode(email, clientId, refreshToken, {
 *     senderFilter: 'noreply@airport.com',  // 发件人过滤
 *     keyword: 'verification code',          // 关键词
 *     timeout: 60                            // 超时秒
 *   });
 */

const TOKEN_URL = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token';
const GRAPH_BASE = 'https://graph.microsoft.com/v1.0/me';
const TOKEN_STRATEGIES = [
  { url: TOKEN_URL, scope: 'offline_access https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/User.Read' },
  { url: TOKEN_URL, scope: 'https://graph.microsoft.com/.default offline_access' },
  { url: 'https://login.microsoftonline.com/common/oauth2/v2.0/token', scope: 'offline_access https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/User.Read' },
  { url: 'https://login.microsoftonline.com/common/oauth2/v2.0/token', scope: 'https://graph.microsoft.com/.default offline_access' },
];

/**
 * Try to get access token from refresh token using multiple strategies
 */
async function getAccessToken(clientId, refreshToken) {
  for (const strategy of TOKEN_STRATEGIES) {
    try {
      const body = new URLSearchParams({
        client_id: clientId,
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
        scope: strategy.scope,
      });
      const resp = await fetch(strategy.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      });
      const data = await resp.json();
      if (data.access_token) {
        return { accessToken: data.access_token, newRefreshToken: data.refresh_token || refreshToken };
      }
    } catch (e) {
      // try next strategy
    }
  }
  throw new Error('All token strategies failed');
}

/**
 * Extract 6-digit verification code from text
 */
function extract6DigitCode(text) {
  if (!text) return null;
  const cleaned = text.replace(/\s+/g, ' ').replace(/&nbsp;/g, ' ').replace(/<[^>]+>/g, ' ');
  // Common patterns: "code: 123456", "验证码: 123456", "6-digit code: 123456"
  const patterns = [
    /(?:verification|security|confirmation|login|sign.?in|验证|激活|注册|code|pin|code\s*(?:is|:)|一次性|6.?digit)\s*(?:code|码|号)?\s*(?:is|:|：)?\s*(\d{4,8})/gi,
    /\b(\d{6})\b/g,
  ];
  
  for (const pattern of patterns) {
    const matches = [...cleaned.matchAll(pattern)];
    for (const m of matches) {
      const code = m[1];
      if (/^\d{4,8}$/.test(code)) {
        return code;
      }
    }
  }
  return null;
}

/**
 * Extract verification links from text
 */
function extractLinks(text, domainFilter) {
  if (!text) return [];
  const dec = text.replace(/&amp;/g, '&').replace(/&#x3D;/g, '=').replace(/&#x2F;/g, '/')
    .replace(/&#38;/g, '&').replace(/&#61;/g, '=');
  const links = new Set();
  
  // href links
  const hrefs = dec.match(/href\s*=\s*["']([^"']*?(?:verify|confirm|activate|token|code|验证|激活|email-login)[^"']*)["']/gi) || [];
  for (const h of hrefs) {
    const u = h.replace(/^href\s*=\s*["']/i, '').replace(/["']$/, '');
    if (u.startsWith('http')) links.add(cleanUrl(u));
  }
  
  // raw URLs
  const raws = dec.match(/https?:\/\/[^\s"'<>]+?(?:verify|confirm|activate|token|code|验证|激活|email-login)[^\s"'<>]*/gi) || [];
  for (const u of raws) links.add(cleanUrl(u));
  
  let result = [...links];
  if (domainFilter) result = result.filter(domainFilter);
  return result;
}

function cleanUrl(url) {
  return url.replace(/[)\]>,;:!?\s]+$/, '').replace(/&amp;/g, '&')
    .replace(/&#38;/g, '&').replace(/&#61;/g, '=').replace(/&#x3D;/g, '=');
}

/**
 * Poll inbox for verification code/link
 * @param {string} email - Outlook email
 * @param {string} clientId - Microsoft app client ID
 * @param {string} refreshToken - Microsoft app refresh token
 * @param {object} opts
 * @param {string} opts.senderFilter - filter by sender email/name (e.g. 'noreply@v2ny.com')
 * @param {string} opts.keyword - keyword in subject (e.g. 'verification')
 * @param {number} opts.timeout - timeout in seconds (default 120)
 * @param {number} opts.interval - poll interval ms (default 3000)
 * @param {RegExp} opts.codePattern - custom code pattern
 * @param {boolean} opts.preferLink - return link instead of code
 */
async function findCode(email, clientId, refreshToken, opts = {}) {
  const {
    senderFilter = '',
    keyword = '',
    timeout = 120,
    interval = 3000,
    codePattern = null,
    preferLink = false,
    domainFilter = null,
    log = () => {},
  } = opts;

  log(`[OV] Getting access token for ${email.slice(0,20)}...`);
  const { accessToken, newRefreshToken } = await getAccessToken(clientId, refreshToken);
  
  const deadline = Date.now() + timeout * 1000;
  const seen = new Set();
  let pollCount = 0;
  
  // Build filter: last 30 min + top 10
  const filterTime = new Date(Date.now() - 30 * 60 * 1000).toISOString();
  const filterClause = `receivedDateTime ge ${filterTime}`;
  
  log(`[OV] Polling inbox, timeout=${timeout}s, keyword="${keyword}", sender="${senderFilter}"`);

  while (Date.now() < deadline) {
    pollCount++;
    try {
      const url = `${GRAPH_BASE}/messages?$top=15&$select=id,subject,body,from,receivedDateTime,bodyPreview&$filter=${encodeURIComponent(filterClause)}&$orderby=receivedDateTime desc`;
      const resp = await fetch(url, {
        headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
      });
      
      if (resp.status === 401) {
        // Token expired, refresh
        log(`[OV] Token expired, refreshing...`);
        const { accessToken: newAt } = await getAccessToken(clientId, newRefreshToken);
        // override for retry
        const tokenHolder = { accessToken: newAt };
        // continue with new token
        continue; // skip this round, retry next
      }
      
      const data = await resp.json();
      const messages = data.value || [];
      
      if (pollCount <= 2 || pollCount % 10 === 0) {
        log(`[OV] #${pollCount}: ${messages.length} recent msgs`);
      }
      
      for (const msg of messages) {
        if (seen.has(msg.id)) continue;
        seen.add(msg.id);
        
        const subject = msg.subject || '';
        const fromAddr = (msg.from?.emailAddress?.address) || '';
        const fromName = (msg.from?.emailAddress?.name) || '';
        const bodyPreview = msg.bodyPreview || '';
        const bodyContent = msg.body?.content || '';
        const combined = `${subject} ${fromName} ${fromAddr} ${bodyPreview} ${bodyContent}`;
        
        // Filter by sender
        if (senderFilter) {
          const sf = senderFilter.toLowerCase();
          if (!fromAddr.toLowerCase().includes(sf) && !fromName.toLowerCase().includes(sf) && !subject.toLowerCase().includes(sf)) {
            continue;
          }
        }
        
        // Filter by keyword
        if (keyword) {
          const kw = keyword.toLowerCase();
          if (!combined.toLowerCase().includes(kw)) {
            continue;
          }
        }
        
        log(`[OV] #${pollCount}: Found "${subject.slice(0, 50)}" from ${fromAddr}`);
        
        // Try extract links first
        const linkFilter = domainFilter ? (url) => {
          if (typeof domainFilter === 'string') return url.includes(domainFilter);
          return domainFilter(url);
        } : null;
        
        const links = extractLinks(bodyContent + bodyPreview, linkFilter);
        const allLinks = extractLinks(bodyContent + bodyPreview, null);
        
        if (preferLink && links.length > 0) {
          log(`[OV] ✅ Links found: ${links.length}`);
          return { success: true, links, allLinks, email, message: msg, newRefreshToken };
        }
        
        // Extract 6-digit code
        if (codePattern) {
          const m = combined.match(codePattern);
          if (m) {
            log(`[OV] ✅ Code found (custom): ${m[1] || m[0]}`);
            return { success: true, code: m[1] || m[0], links, email, message: msg, newRefreshToken };
          }
        }
        
        const code = extract6DigitCode(bodyContent + bodyPreview);
        if (code) {
          log(`[OV] ✅ Code: ${code}`);
          return { success: true, code, links, allLinks, email, message: msg, newRefreshToken };
        }
        
        // If no code but links exist and preferLink
        if (allLinks.length > 0) {
          log(`[OV] ⚠️ No code, but ${allLinks.length} links: ${allLinks.slice(0,3).join(', ').slice(0, 120)}`);
          return { success: true, code: null, links: allLinks, email, message: msg, newRefreshToken };
        }
      }
    } catch (e) {
      log(`[OV] Poll error: ${e.message}`);
    }
    
    await sleep(interval);
  }
  
  return { success: false, error: `Timeout (${timeout}s)`, email };
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

module.exports = { findCode, extract6DigitCode, extractLinks, getAccessToken, TOKEN_STRATEGIES };

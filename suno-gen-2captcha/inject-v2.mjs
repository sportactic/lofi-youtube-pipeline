import { chromium } from 'playwright';
import fs from 'fs';

const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';

function log(m) { console.log(`[${new Date().toISOString().substring(11,19)}] ${m}`); }

const browser = await chromium.launch({
  headless: true,
  executablePath: '/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome',
  args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
});
const ctx = await browser.newContext({
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
  viewport: { width: 1280, height: 800 },
  locale: 'en-US', timezoneId: 'America/New_York',
});
const clientVal = fs.readFileSync('/workspace/suno-client-fresh.txt', 'utf8').trim();
const sessionVal = fs.readFileSync('/workspace/suno-session-fresh.txt', 'utf8').trim();
await ctx.addCookies([
  { name: '__client', value: clientVal, domain: '.suno.com', path: '/', httpOnly: true, secure: true, sameSite: 'None' },
  { name: '__session', value: sessionVal, domain: '.suno.com', path: '/', httpOnly: true, secure: true, sameSite: 'Lax' },
]);
const page = await ctx.newPage();
await page.goto('https://suno.com/');
await page.waitForTimeout(20000);
await page.goto('https://suno.com/create');
await page.waitForTimeout(8000);

await page.evaluate(() => {
  document.querySelectorAll('[role="radio"]').forEach(r => {
    if (r.textContent?.trim().toLowerCase() === 'instrumental') r.click();
  });
});
await page.waitForTimeout(2000);

await page.evaluate(() => {
  const allEls = Array.from(document.querySelectorAll('label, div, span'));
  const sdLabel = allEls.find(el => el.textContent?.trim().startsWith('Song Description'));
  const ta = sdLabel?.parentElement?.querySelector('textarea');
  if (ta) {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(ta, 'Lo-fi chillhop with warm Rhodes piano');
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  }
});
await page.waitForTimeout(1000);
await page.evaluate(() => document.querySelector('button[aria-label="Create song"]')?.click());

// Wait for captcha
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(1000);
  const has = await page.evaluate(() => Array.from(document.querySelectorAll('iframe')).some(f => (f.getAttribute('src')||'').includes('hcaptcha-assets-prod.suno.com')));
  if (has) break;
}
await page.waitForTimeout(5000);

// Get sitekey and submit to 2captcha
const sitekey = await page.evaluate(() => {
  const iframes = Array.from(document.querySelectorAll('iframe[src*="hcaptcha"]'));
  for (const iframe of iframes) {
    const src = iframe.getAttribute('src');
    const m = src.match(/sitekey=([^&]+)/);
    if (m) return decodeURIComponent(m[1]);
  }
  return null;
});
log(`Sitekey: ${sitekey?.substring(0, 30)}`);

const idRes = await fetch('https://2captcha.com/in.php', {
  method: 'POST',
  body: new URLSearchParams({ key: TWO_CAPTCHA_KEY, method: 'hcaptcha', sitekey, pageurl: page.url(), json: '1' }),
});
const idData = await idRes.json();
log(`Submit: ${JSON.stringify(idData)}`);

let token = null;
for (let i = 0; i < 30; i++) {
  await new Promise(r => setTimeout(r, 5000));
  const r = await fetch(`https://2captcha.com/res.php?key=${TWO_CAPTCHA_KEY}&action=get&id=${idData.request}&json=1`);
  const j = await r.json();
  if (j.status === 1) { token = j.request; log(`Got token at poll ${i}`); break; }
}

if (!token) { log('No token'); await browser.close(); process.exit(1); }

// Try posting the token directly to Suno's hcaptcha validation endpoint
// Common pattern: https://hcaptcha-endpoint-prod.suno.com/1/check or similar
const endpointCheck = await page.evaluate(async (token) => {
  // Try various endpoints
  const endpoints = [
    'https://hcaptcha-endpoint-prod.suno.com/1/check',
    'https://hcaptcha-endpoint-prod.suno.com/check',
    'https://hcaptcha-endpoint-prod.suno.com/siteverify',
    'https://hcaptcha-endpoint-prod.suno.com/api/v1/siteverify',
  ];
  const results = [];
  for (const url of endpoints) {
    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: token, sitekey: 'd65453de-3f1a-4aac-9366-a0f06e' }),
      });
      const text = await r.text();
      results.push({ url, status: r.status, body: text.substring(0, 200) });
    } catch (e) {
      results.push({ url, error: e.message });
    }
  }
  return results;
}, token);
console.log('Endpoint checks:', JSON.stringify(endpointCheck, null, 2));

// Now try injection with multiple methods + postMessage
log('\nInjecting via multiple methods + postMessage...');
const injectResult = await page.evaluate((token) => {
  const results = [];
  
  // 1) Top-level textareas
  const topTas = document.querySelectorAll('textarea[name="h-captcha-response"], textarea[name="g-recaptcha-response"]');
  for (const t of topTas) {
    t.value = token;
    t.innerHTML = token;
    t.style.display = 'block';
    t.dispatchEvent(new Event('input', { bubbles: true }));
    t.dispatchEvent(new Event('change', { bubbles: true }));
    results.push(`top textarea ${t.name}`);
  }
  
  // 2) postMessage to all iframes
  const iframes = document.querySelectorAll('iframe');
  for (const iframe of iframes) {
    try {
      const win = iframe.contentWindow;
      if (win) {
        win.postMessage({ 
          type: 'hcaptcha:response',
          response: token,
          'h-captcha-response': token,
        }, '*');
        results.push(`postMessage to ${(iframe.getAttribute('src')||'').substring(0, 50)}`);
      }
    } catch (e) { results.push(`postMessage err: ${e.message}`); }
  }
  
  // 3) hcaptcha global setData (challenge data)
  if (window.hcaptcha) {
    try {
      // Pass the response via setData
      window.hcaptcha.setData({ response: token });
      results.push('hcaptcha.setData');
    } catch (e) { results.push(`setData err: ${e.message}`); }
  }
  
  return results;
}, token);
log(`Inject: ${JSON.stringify(injectResult)}`);

await page.waitForTimeout(5000);

// Try clicking submit on captcha iframe
for (const f of page.frames()) {
  const url = f.url();
  if (url.includes('hcaptcha-assets-prod.suno.com')) {
    try {
      // Look for any submit-like element
      const submitClicked = await f.evaluate(() => {
        // Try clicking task cells based on textarea value (set top-level)
        const tas = document.querySelectorAll('textarea[name="h-captcha-response"]');
        if (tas.length > 0 && tas[0].value) {
          // Find the "task" cells with image data
          const tasks = document.querySelectorAll('.task');
          // We don't have coords, just simulate click
          // Actually for our purposes - we just need to trigger the submit
          // Some hCaptcha widgets auto-submit when textarea is filled
          return { hasTasks: tasks.length, textareaFilled: tas[0].value.length > 0 };
        }
        return { noTextarea: true };
      });
      log(`Frame state: ${JSON.stringify(submitClicked)}`);
    } catch (e) {}
  }
}

// Wait and check
await page.waitForTimeout(20000);
const final = await page.evaluate(() => ({
  bodySlice: document.body.innerText.substring(0, 800).replace(/\n+/g, ' '),
}));
log(`Final: ${final.bodySlice}`);

await browser.close();

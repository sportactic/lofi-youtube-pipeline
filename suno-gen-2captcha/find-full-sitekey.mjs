import { chromium } from 'playwright';
import fs from 'fs';

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

// Capture all requests to find any URL with sitekey
const sitekeyUrls = [];
page.on('request', req => {
  const url = req.url();
  if (url.includes('hcaptcha')) {
    sitekeyUrls.push(url);
  }
});

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
    setter.call(ta, 'test prompt');
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  }
});
await page.waitForTimeout(1000);

await page.evaluate(() => document.querySelector('button[aria-label="Create song"]')?.click());

// Wait for captcha and capture ALL related requests
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(1000);
  const has = await page.evaluate(() => Array.from(document.querySelectorAll('iframe')).some(f => (f.getAttribute('src')||'').includes('hcaptcha')));
  if (has) break;
}
await page.waitForTimeout(8000);

// Find sitekey from iframe
const sk = await page.evaluate(() => {
  const out = {};
  const iframes = Array.from(document.querySelectorAll('iframe'));
  for (const iframe of iframes) {
    const src = iframe.getAttribute('src') || '';
    if (src.includes('hcaptcha')) {
      out.iframeSrc = src;
      const m = src.match(/sitekey=([^&]+)/);
      if (m) out.sitekey = decodeURIComponent(m[1]);
      // Check inside iframe too
      try {
        const doc = iframe.contentDocument;
        const skEl = doc?.querySelector('[data-sitekey]') || doc?.querySelector('input[name="sitekey"]');
        if (skEl) out.innerSitekey = skEl.getAttribute('data-sitekey') || skEl.value;
      } catch (e) { out.crossOrigin = true; }
    }
  }
  // Also check page-level hcaptcha config
  const hcap = window.hcaptcha;
  out.hcapKeys = hcap ? Object.keys(hcap) : null;
  return out;
});
log('Sitekey info:');
console.log(JSON.stringify(sk, null, 2));

// Print all captured URLs
log('\nAll hcaptcha-related URLs captured:');
for (const u of sitekeyUrls.slice(-10)) {
  console.log(`  ${u}`);
}

await browser.close();

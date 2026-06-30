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

// ALL responses - capture full body
const allResponses = [];
page.on('response', async resp => {
  const url = resp.url();
  // Only interesting APIs
  if (url.includes('studio-api-prod.suno.com') || url.includes('suno.ai') && url.includes('.mp3')) {
    try {
      const status = resp.status();
      const ct = resp.headers()['content-type'] || '';
      let body = null;
      if (ct.includes('json') || url.includes('/api/')) {
        try { body = await resp.text(); } catch {}
      }
      allResponses.push({ time: Date.now(), url: url.substring(0, 150), status, ct, body: body?.substring(0, 500) });
    } catch (e) {}
  }
});

await page.goto('https://suno.com/');
await page.waitForTimeout(20000);
await page.goto('https://suno.com/create');
await page.waitForTimeout(8000);

// Switch to Instrumental
await page.evaluate(() => {
  const radios = document.querySelectorAll('[role="radio"]');
  for (const r of radios) {
    if (r.textContent?.trim().toLowerCase() === 'instrumental') r.click();
  }
});
await page.waitForTimeout(2000);

// Fill textarea
await page.evaluate(() => {
  const tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent);
  const t = tas[tas.length - 1];
  const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
  setter.call(t, 'Lo-fi hip hop, mellow piano, soft rain ambience, dreamy chill, slow tempo, anime aesthetic');
  t.dispatchEvent(new Event('input', { bubbles: true }));
});
await page.waitForTimeout(500);

// Click all the buttons
await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button'));
  all.find(b => b.getAttribute('aria-label')?.toLowerCase().includes('instrumental'))?.click();
  all.find(b => b.textContent?.trim() === 'v5.5')?.click();
  document.querySelector('button[aria-label="Create song"]')?.click();
});

log('Create clicked. Polling for activity for 90s...');
const start = Date.now();
let lastCount = 0;
while (Date.now() - start < 90_000) {
  await page.waitForTimeout(10_000);
  const newCount = allResponses.length - lastCount;
  if (newCount > 0) {
    log(`[${Math.round((Date.now() - start) / 1000)}s] ${newCount} new responses`);
    for (const r of allResponses.slice(lastCount)) {
      console.log(`  ${r.status} ${r.url}`);
      if (r.body) console.log(`    ${r.body.substring(0, 300)}`);
    }
    lastCount = allResponses.length;
  } else {
    log(`[${Math.round((Date.now() - start) / 1000)}s] ${allResponses.length} total responses, no new`);
  }
}

// Final page state
const body = await page.evaluate(() => document.body.innerText.substring(0, 1500));
log('Final body:');
console.log(body);

await browser.close();

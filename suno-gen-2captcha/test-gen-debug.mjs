import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

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

// Capture ALL outbound API requests
const requests = [];
page.on('request', req => {
  const url = req.url();
  if (url.includes('suno.com') || url.includes('suno.ai') || url.includes('ably')) {
    requests.push({ time: Date.now(), method: req.method(), url: url.substring(0, 120) });
  }
});

// Capture all responses
const responses = [];
page.on('response', async resp => {
  const url = resp.url();
  if (url.includes('suno.com') || url.includes('suno.ai') || url.includes('ably')) {
    const status = resp.status();
    let body = null;
    try {
      const text = await resp.text();
      if (text && text.length < 5000) body = text.substring(0, 800);
      else if (text) body = text.substring(0, 200) + '... [truncated]';
    } catch (e) {}
    responses.push({ time: Date.now(), status, url: url.substring(0, 120), body });
  }
});

log('Loading / for handshake...');
await page.goto('https://suno.com/');
await page.waitForTimeout(20000);
await page.goto('https://suno.com/create');
await page.waitForTimeout(8000);

log(`Logged in: ${await page.evaluate(() => document.body.innerText.includes('8,920'))}`);

// Switch to Instrumental mode
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
  setter.call(t, 'Lo-fi hip hop, mellow piano, soft rain ambience, dreamy');
  t.dispatchEvent(new Event('input', { bubbles: true }));
});

// Click Instrumental checkbox + v5.5 + Create
await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button'));
  all.find(b => b.getAttribute('aria-label')?.toLowerCase().includes('instrumental'))?.click();
  all.find(b => b.textContent?.trim() === 'v5.5')?.click();
  document.querySelector('button[aria-label="Create song"]')?.click();
});

log('Create clicked. Waiting 60s for activity...');
await page.waitForTimeout(60000);

// Check requests
log('\n=== REQUESTS after Create ===');
for (const r of requests.slice(-30)) {
  console.log(`  ${r.method} ${r.url}`);
}

log('\n=== RESPONSES (last 30) ===');
for (const r of responses.slice(-30)) {
  console.log(`  ${r.status} ${r.url}`);
  if (r.body) console.log(`     ${r.body.substring(0, 200)}`);
}

// Check page state
const state = await page.evaluate(() => {
  const t = document.body.innerText;
  return {
    has8920: t.includes('8,920'),
    hasGenerating: t.match(/generating|creating|waiting/i)?.slice(0, 5),
    bodySlice: t.substring(0, 500),
  };
});
log(`\nFinal state: ${JSON.stringify(state)}`);

await browser.close();

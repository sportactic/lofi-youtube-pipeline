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
await page.goto('https://suno.com/');
await page.waitForTimeout(20000);
await page.goto('https://suno.com/create');
await page.waitForTimeout(8000);

// Switch to Instrumental
await page.evaluate(() => {
  document.querySelectorAll('[role="radio"]').forEach(r => {
    if (r.textContent?.trim().toLowerCase() === 'instrumental') r.click();
  });
});
await page.waitForTimeout(2000);

// Fill textarea
await page.evaluate(() => {
  const tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent);
  const t = tas[tas.length - 1];
  const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
  setter.call(t, 'Lo-fi chillhop with warm Rhodes piano and gentle vinyl crackle, slow tempo, dreamy and cozy, anime aesthetic');
  t.dispatchEvent(new Event('input', { bubbles: true }));
});
log('Filled. Checking state before click...');

const before = await page.evaluate(() => {
  return {
    createDisabled: document.querySelector('button[aria-label="Create song"]')?.disabled,
    createText: document.querySelector('button[aria-label="Create song"]')?.textContent,
    textareaValue: Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent).map(t => t.value?.substring(0, 30)),
    radioChecked: Array.from(document.querySelectorAll('[role="radio"]')).map(r => ({ text: r.textContent?.trim(), checked: r.getAttribute('aria-checked') })),
    bodyMatch: document.body.innerText.match(/generating|creating|loading|please wait/i)?.slice(0, 3),
  };
});
log(`Before: ${JSON.stringify(before)}`);

// Now click Create
const clickResult = await page.evaluate(() => {
  const btn = document.querySelector('button[aria-label="Create song"]');
  if (!btn) return 'no button';
  if (btn.disabled) return 'disabled';
  btn.click();
  return 'clicked';
});
log(`Click result: ${clickResult}`);

// Check state every 10s for 1 minute
for (let i = 0; i < 6; i++) {
  await page.waitForTimeout(10000);
  const state = await page.evaluate(() => ({
    createText: document.querySelector('button[aria-label="Create song"]')?.textContent,
    createDisabled: document.querySelector('button[aria-label="Create song"]')?.disabled,
    bodyMatch: document.body.innerText.match(/generating|creating|loading|please wait|queued|adding/i)?.slice(0, 3),
    bodySlice: document.body.innerText.substring(0, 800).replace(/\n+/g, ' '),
  }));
  log(`[${(i+1)*10}s] State:`);
  console.log(`  createText: "${state.createText}"`);
  console.log(`  bodySlice: ${state.bodySlice}`);
}

// Take final screenshot
await page.screenshot({ path: '/workspace/suno-gen-2captcha/debug-gen-flow.png' });

await browser.close();

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

// Initial radio state
const initialRadios = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('[role="radio"]')).map(r => ({
    text: r.textContent?.trim().substring(0, 20),
    ariaChecked: r.getAttribute('aria-checked'),
    parentCls: r.parentElement?.className?.substring(0, 30),
  }));
});
log('Initial radios:');
console.log(JSON.stringify(initialRadios, null, 2));

// Click Instrumental
const clickResult = await page.evaluate(() => {
  const radios = document.querySelectorAll('[role="radio"]');
  for (const r of radios) {
    if (r.textContent?.trim().toLowerCase() === 'instrumental') {
      r.click();
      return { ok: true, before: r.getAttribute('aria-checked') };
    }
  }
  return { ok: false };
});
log(`Click Instrumental: ${JSON.stringify(clickResult)}`);
await page.waitForTimeout(2000);

// Re-check radios
const afterClickRadios = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('[role="radio"]')).map(r => ({
    text: r.textContent?.trim().substring(0, 20),
    ariaChecked: r.getAttribute('aria-checked'),
  }));
});
log('After Instrumental click:');
console.log(JSON.stringify(afterClickRadios, null, 2));

// Check page text after
const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 1500));
log('Body after click:');
console.log(bodyText);

await browser.close();

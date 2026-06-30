import { chromium } from 'playwright';
import fs from 'fs';

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

// Find all radios with aria-checked
const radios = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('[role="radio"]')).map(r => ({
    text: r.textContent?.trim().substring(0, 30),
    rect: r.getBoundingClientRect(),
    offsetParent: !!r.offsetParent,
    parentTag: r.parentElement?.tagName,
    parentVisible: !!r.parentElement?.offsetParent,
    grandParentVisible: !!r.parentElement?.parentElement?.offsetParent,
    greatGrandParentVisible: !!r.parentElement?.parentElement?.parentElement?.offsetParent,
    aria: r.getAttribute('aria-label'),
    ariaChecked: r.getAttribute('aria-checked'),
  }));
});
console.log('=== RADIOS ===');
console.log(JSON.stringify(radios, null, 2));

// Click on the Instrumental checkbox (y=334)
log('Clicking Instrumental checkbox...');
const cb = page.locator('button[aria-label="Check this to generate an instrumental only song"]').first();
await cb.click();
await page.waitForTimeout(2000);

// After clicking, check the textareas again
const tas2 = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent).map(t => ({
    placeholder: t.placeholder?.substring(0, 60),
    value: t.value?.substring(0, 50),
    rect: t.getBoundingClientRect(),
  }));
});
console.log('\n=== TEXTAREAS AFTER INSTRUMENTAL CLICK ===');
console.log(JSON.stringify(tas2, null, 2));

await page.screenshot({ path: '/workspace/suno-gen-2captcha/after-instrumental.png' });
await browser.close();

function log(m) { console.log(`[${new Date().toISOString().substring(11,19)}] ${m}`); }

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

// Fill the textarea by ID/index regardless of visibility
log('Filling via JS evaluate...');
const result = await page.evaluate(() => {
  const tas = document.querySelectorAll('textarea');
  const results = [];
  tas.forEach((t, i) => {
    const isVisible = t.offsetParent !== null;
    const ph = t.placeholder?.substring(0, 30);
    const computed = window.getComputedStyle(t);
    results.push({
      i, visible: isVisible, ph,
      display: computed.display,
      visibility: computed.visibility,
      opacity: computed.opacity,
      rect: t.getBoundingClientRect(),
    });
  });
  return results;
});
console.log(JSON.stringify(result, null, 2));

// Try to fill the second one (style) directly via JS, then trigger React events
const fillResult = await page.evaluate(() => {
  const tas = document.querySelectorAll('textarea');
  if (tas.length < 2) return { ok: false, count: tas.length };
  const t = tas[1]; // style textarea
  const ph = t.placeholder?.substring(0, 50);
  // Use React-compatible setter
  const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
  setter.call(t, 'TEST PROMPT: Lo-fi hip hop, mellow piano, soft rain ambience');
  t.dispatchEvent(new Event('input', { bubbles: true }));
  t.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: true, ph, value: t.value };
});
console.log('\nFill result:', JSON.stringify(fillResult));

// Now try to find Instrumental radio (force click even if "not visible")
log('\nForcing Instrumental click via JS...');
const instResult = await page.evaluate(() => {
  // Find all Instrumental buttons
  const all = Array.from(document.querySelectorAll('button')).filter(b => 
    b.textContent?.trim().toLowerCase().includes('instrumental') ||
    b.getAttribute('aria-label')?.toLowerCase().includes('instrumental')
  );
  return all.map(b => ({
    text: b.textContent?.trim().substring(0, 30),
    cls: b.className?.substring(0, 80),
    aria: b.getAttribute('aria-label'),
    rect: b.getBoundingClientRect(),
    offsetParent: !!b.offsetParent,
  }));
});
console.log(JSON.stringify(instResult, null, 2));

// Try clicking the SECOND Instrumental button (the checkbox at y=334)
const cb = page.locator('button[aria-label*="instrumental" i]').first();
await cb.click({ force: true });
console.log('Force-clicked Instrumental checkbox');
await page.waitForTimeout(2000);

// Check if page state changed
const afterClick = await page.evaluate(() => {
  const tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent);
  return tas.map(t => ({
    placeholder: t.placeholder?.substring(0, 50),
    value: t.value?.substring(0, 30),
    rect: t.getBoundingClientRect(),
  }));
});
console.log('\nTextareas after click:');
console.log(JSON.stringify(afterClick, null, 2));

await page.screenshot({ path: '/workspace/suno-gen-2captcha/test-after-force.png' });
await browser.close();

function log(m) { console.log(`[${new Date().toISOString().substring(11,19)}] ${m}`); }

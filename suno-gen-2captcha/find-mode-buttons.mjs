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

// Find ALL elements with role=radio
log('Finding all radios...');
const all = await page.evaluate(() => {
  const out = [];
  const els = document.querySelectorAll('[role="radio"]');
  for (const el of els) {
    const text = el.textContent?.trim().substring(0, 30);
    if (!text) continue;
    let parent = el.parentElement;
    const ancestors = [];
    while (parent && ancestors.length < 5) {
      const cs = window.getComputedStyle(parent);
      ancestors.push({
        tag: parent.tagName,
        cls: parent.className?.substring(0, 50),
        display: cs.display,
        visibility: cs.visibility,
        opacity: cs.opacity,
        offsetParent: !!parent.offsetParent,
      });
      parent = parent.parentElement;
    }
    out.push({
      text,
      rect: el.getBoundingClientRect(),
      offsetParent: !!el.offsetParent,
      aria: el.getAttribute('aria-label'),
      ancestors,
    });
  }
  return out;
});
console.log(JSON.stringify(all, null, 2));

// Look for the parent that hides it
log('Click via JS force...');
const clicked = await page.evaluate(() => {
  const radios = document.querySelectorAll('[role="radio"]');
  const inst = Array.from(radios).find(r => r.textContent?.trim().toLowerCase().includes('instrumental'));
  if (!inst) return { ok: false, reason: 'not found' };
  // Click it
  inst.click();
  return { ok: true, rect: inst.getBoundingClientRect() };
});
console.log('Clicked:', JSON.stringify(clicked));
await page.waitForTimeout(3000);

// Check state
const after = await page.evaluate(() => {
  const tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent);
  return tas.map(t => ({
    placeholder: t.placeholder?.substring(0, 30),
    value: t.value?.substring(0, 30),
    rect: t.getBoundingClientRect(),
  }));
});
console.log('\nTextareas after Instrumental click via JS:');
console.log(JSON.stringify(after, null, 2));

await page.screenshot({ path: '/workspace/suno-gen-2captcha/after-mode-click.png' });
await browser.close();

function log(m) { console.log(`[${new Date().toISOString().substring(11,19)}] ${m}`); }

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
    setter.call(ta, 'Test track');
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  }
});
await page.waitForTimeout(1000);
await page.evaluate(() => document.querySelector('button[aria-label="Create song"]')?.click());

// Wait for captcha
for (let i = 0; i < 20; i++) {
  await page.waitForTimeout(1000);
  const has = await page.evaluate(() => Array.from(document.querySelectorAll('iframe')).some(f => (f.getAttribute('src')||'').includes('hcaptcha')));
  if (has) break;
}
await page.waitForTimeout(5000);

// Inspect hcaptcha internals
const internal = await page.evaluate(() => {
  if (!window.hcaptcha) return { found: false };
  const keys = Object.keys(window.hcaptcha);
  return {
    found: true,
    keys,
    nodesCount: window.hcaptcha.nodes?.length || 0,
    nodeTypes: window.hcaptcha.nodes?.map(n => n?.constructor?.name).filter(Boolean).slice(0, 3),
    hasGetResponse: typeof window.hcaptcha.getResponse === 'function',
    hasExecute: typeof window.hcaptcha.execute === 'function',
    hasSetData: typeof window.hcaptcha.setData === 'function',
    hasReset: typeof window.hcaptcha.reset === 'function',
    firstNodeMethods: window.hcaptcha.nodes?.[0] ? Object.keys(window.hcaptcha.nodes[0]).slice(0, 30) : null,
  };
});
console.log('hCaptcha internal:', JSON.stringify(internal, null, 2));

// Look for any onclick handlers on the captcha iframe
const submitButtons = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('button')).filter(b => 
    b.textContent?.match(/verify|submit|continue|next|done|solved|send|check/i)
  ).map(b => ({
    text: b.textContent?.trim(),
    visible: b.offsetParent !== null,
    disabled: b.disabled,
    cls: b.className?.substring(0, 60),
  }));
});
console.log('Submit buttons:', JSON.stringify(submitButtons, null, 2));

// Try to find any retry/verify button in the captcha iframe
for (const f of page.frames()) {
  const url = f.url();
  if (url.includes('hcaptcha-assets-prod.suno.com')) {
    try {
      const buttons = await f.evaluate(() => {
        return Array.from(document.querySelectorAll('button, [role="button"]')).map(b => ({
          text: b.textContent?.trim().substring(0, 30),
          visible: b.offsetParent !== null,
          cls: b.className?.substring(0, 60),
        }));
      });
      console.log(`Frame ${url.substring(0, 60)} buttons:`, JSON.stringify(buttons));
      
      // Also check if there's a "Skip" button
      const skipButton = await f.evaluate(() => {
        const allBtns = Array.from(document.querySelectorAll('button, div[role="button"]'));
        return allBtns.find(b => b.textContent?.toLowerCase().includes('skip'));
      });
      console.log('Skip button:', skipButton ? 'FOUND' : 'NOT FOUND');
      
    } catch (e) {
      console.log(`Cannot access frame: ${e.message}`);
    }
  }
}

await browser.close();

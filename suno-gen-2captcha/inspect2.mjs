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
await page.waitForTimeout(10000);

// Find ALL buttons and their aria-labels, including those with text
const data = await page.evaluate(() => {
  const out = { createBtns: [], auraBtns: [], instrumentals: [], v5btns: [] };
  
  document.querySelectorAll('button').forEach(b => {
    const text = (b.textContent || '').trim().substring(0, 50);
    const cls = b.className || '';
    const aria = b.getAttribute('aria-label') || '';
    if (text.toLowerCase().includes('create') || cls.includes('aura')) {
      out.createBtns.push({ text, cls: cls.substring(0, 60), aria, rect: b.getBoundingClientRect() });
    }
    if (cls.includes('aura')) {
      out.auraBtns.push({ text, cls: cls.substring(0, 60), aria, rect: b.getBoundingClientRect() });
    }
    if (text.toLowerCase().includes('instrumental')) {
      out.instrumentals.push({ text, cls: cls.substring(0, 60), aria, rect: b.getBoundingClientRect() });
    }
    if (text.toLowerCase().includes('v5')) {
      out.v5btns.push({ text, cls: cls.substring(0, 60), aria, rect: b.getBoundingClientRect() });
    }
  });
  
  // Also check divs for clickable instrument/prompt/lyrics toggles
  const modeToggles = [];
  document.querySelectorAll('[role="radio"], [role="tab"], [class*="mode"], [class*="toggle"]').forEach(el => {
    const text = (el.textContent || '').trim().substring(0, 50);
    if (el.offsetParent && (text.toLowerCase().includes('instrumental') || 
                              text.toLowerCase().includes('lyric') ||
                              text.toLowerCase().includes('prompt'))) {
      modeToggles.push({ tag: el.tagName, text, cls: (el.className || '').substring(0, 60), aria: el.getAttribute('aria-label') || '' });
    }
  });
  out.modeToggles = modeToggles;
  
  return out;
});

console.log(JSON.stringify(data, null, 2));

await browser.close();

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

const data = await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button')).filter(b => {
    const txt = b.textContent?.trim().toLowerCase() || '';
    return txt.includes('instrumental') || txt.includes('lyric') || txt.includes('prompt');
  });
  return all.map(b => ({
    text: b.textContent?.trim().substring(0, 30),
    rect: b.getBoundingClientRect(),
    offsetParent: !!b.offsetParent,
    parentTag: b.parentElement?.tagName,
    parentCls: b.parentElement?.className?.substring(0, 60),
    hidden: b.hidden || b.style.display === 'none' || b.style.visibility === 'hidden',
    cls: b.className?.substring(0, 80),
    aria: b.getAttribute('aria-label'),
  }));
});
console.log(JSON.stringify(data, null, 2));
await browser.close();

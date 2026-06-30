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

const beforeTas = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('textarea')).map(t => ({
    placeholder: t.placeholder?.substring(0, 50),
    visible: t.offsetParent !== null,
    rect: t.getBoundingClientRect(),
    parentCls: t.parentElement?.className?.substring(0, 50),
    grandParentCls: t.parentElement?.parentElement?.className?.substring(0, 50),
  }));
});
log(`Before mode switch (Lyrics mode):`);
console.log(JSON.stringify(beforeTas, null, 2));

// Switch to Instrumental
await page.evaluate(() => {
  document.querySelectorAll('[role="radio"]').forEach(r => {
    if (r.textContent?.trim().toLowerCase() === 'instrumental') r.click();
  });
});
await page.waitForTimeout(3000);

const afterTas = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('textarea')).map(t => ({
    placeholder: t.placeholder?.substring(0, 50),
    visible: t.offsetParent !== null,
    rect: t.getBoundingClientRect(),
    parentCls: t.parentElement?.className?.substring(0, 50),
    parentVisible: !!t.parentElement?.offsetParent,
  }));
});
log(`\nAfter Instrumental switch:`);
console.log(JSON.stringify(afterTas, null, 2));

// Try to find Song Description label and click on its associated input
const sd = await page.evaluate(() => {
  // Find the "Song Description" label
  const allLabels = Array.from(document.querySelectorAll('label'));
  const allDivs = Array.from(document.querySelectorAll('div, span'));
  const songDescLabel = allLabels.concat(allDivs).find(el => 
    el.textContent?.trim() === 'Song Description' ||
    el.textContent?.trim().startsWith('Song Description\n')
  );
  if (!songDescLabel) return { found: false };
  
  // Find the sibling textarea
  const parent = songDescLabel.parentElement;
  const ta = parent?.querySelector('textarea');
  if (!ta) return { found: false, labelRect: songDescLabel.getBoundingClientRect() };
  
  return {
    found: true,
    labelRect: songDescLabel.getBoundingClientRect(),
    taPlaceholder: ta.placeholder?.substring(0, 50),
    taRect: ta.getBoundingClientRect(),
    taVisible: ta.offsetParent !== null,
  };
});
log(`\nSong Description label:`);
console.log(JSON.stringify(sd, null, 2));

// Take screenshot showing Instrumental mode
await page.screenshot({ path: '/workspace/suno-gen-2captcha/instrumental-mode.png' });

await browser.close();

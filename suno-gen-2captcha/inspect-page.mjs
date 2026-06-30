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
log('Loading...');
await page.goto('https://suno.com/', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(20000);
await page.goto('https://suno.com/create', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(10000);

log(`URL: ${page.url()}`);

// Dump all visible buttons with their text + class
const buttons = await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button'));
  return all.filter(b => b.offsetParent).map(b => ({
    text: b.textContent?.trim().substring(0, 40),
    cls: b.className.substring(0, 80),
    rect: b.getBoundingClientRect(),
    type: b.type,
  }));
});
console.log('=== VISIBLE BUTTONS ===');
for (const b of buttons) {
  console.log(`  [${b.rect.y.toFixed(0)},${b.rect.x.toFixed(0)}] "${b.text}" cls=${b.cls.substring(0, 60)}`);
}

// Dump all tabs/mode toggles
const tabs = await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('[role="tab"], button[class*="tab"], div[class*="tab"]'));
  return all.filter(t => t.offsetParent).map(t => ({
    text: t.textContent?.trim().substring(0, 30),
    cls: t.className.substring(0, 80),
  }));
});
console.log('\n=== TABS ===');
for (const t of tabs) {
  console.log(`  "${t.text}" cls=${t.cls.substring(0, 60)}`);
}

// Dump all textareas with full info
const tas = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('textarea')).map(t => ({
    placeholder: t.placeholder?.substring(0, 60),
    visible: t.offsetParent !== null,
    value: t.value?.substring(0, 50),
    cls: t.className?.substring(0, 60),
    rect: t.getBoundingClientRect(),
  }));
});
console.log('\n=== TEXTAREAS ===');
for (const t of tas) {
  console.log(`  [${t.rect.y.toFixed(0)}] visible=${t.visible} "${t.placeholder}"`);
  console.log(`     value="${t.value}"`);
}

// Take a screenshot
await page.screenshot({ path: '/workspace/suno-gen-2captcha/page-inspect.png', fullPage: false });
console.log('\nScreenshot saved to /workspace/suno-gen-2captcha/page-inspect.png');

await browser.close();

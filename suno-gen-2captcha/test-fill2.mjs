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

// Try focusing + typing instead of direct value set
log('Finding Song Description textarea by label...');

// Find the label "Song Description" and the textarea near it
const result = await page.evaluate(() => {
  // Find all labels
  const labels = Array.from(document.querySelectorAll('label, div, span')).filter(el => 
    el.textContent?.trim().startsWith('Song Description') || 
    el.textContent?.trim() === 'Style of Music'
  );
  
  return labels.map(l => ({
    text: l.textContent?.trim().substring(0, 50),
    tag: l.tagName,
    cls: l.className?.substring(0, 50),
    nextTextarea: l.parentElement?.querySelector('textarea')?.placeholder?.substring(0, 40),
    rect: l.getBoundingClientRect(),
  }));
});
console.log('Labels:', JSON.stringify(result, null, 2));

// Try the locator.fill approach with proper focus events
log('\nTrying page.locator().fill() approach...');
const songDescriptionTa = page.locator('textarea').filter({ hasNot: page.locator('[disabled]') }).last();
const ph = await songDescriptionTa.getAttribute('placeholder').catch(() => '');
log(`Target textarea placeholder: "${ph?.substring(0, 50)}"`);

// Click then fill
await songDescriptionTa.click();
await page.waitForTimeout(500);
await songDescriptionTa.fill('Lo-fi chillhop, warm Rhodes piano, vinyl crackle, slow tempo, dreamy, cozy');
await page.waitForTimeout(1000);

// Check state
const after = await page.evaluate(() => ({
  charCounter: document.body.innerText.match(/\d+\/3000/)?.[0],
  createDisabled: document.querySelector('button[aria-label="Create song"]')?.disabled,
  textareaValues: Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent).map(t => t.value?.substring(0, 30)),
}));
log(`After fill: ${JSON.stringify(after)}`);

await page.screenshot({ path: '/workspace/suno-gen-2captcha/test-fill2.png' });
await browser.close();

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

// Try clicking the "Instrumental" mode radio at y=172
// It's a radio with aria-checked
log('Trying to find Instrumental radio at top...');
const radios = await page.locator('[role="radio"]:has-text("Instrumental")').all();
console.log(`Found ${radios.length} Instrumental radios`);
for (const r of radios) {
  const isVisible = await r.isVisible();
  const text = await r.textContent();
  const cls = await r.getAttribute('class');
  console.log(`  - visible=${isVisible}, text="${text}", cls=${cls.substring(0, 80)}`);
}

// Check what's the "Prompt" textarea
const promptTa = page.locator('textarea[placeholder*="Describe"]').first();
const promptVisible = await promptTa.isVisible();
console.log(`\nPrompt textarea visible: ${promptVisible}`);

// Check current state of Lyrics/Prompt toggle
const lyricsButton = page.locator('button:has-text("Lyrics")').first();
const promptButton = page.locator('button:has-text("Prompt")').first();
console.log(`Lyrics button: count=${await lyricsButton.count()}`);
console.log(`Prompt button: count=${await promptButton.count()}`);

// Try clicking the Prompt tab
if (await promptButton.count() > 0) {
  const isVisible = await promptButton.isVisible();
  console.log(`Prompt button visible: ${isVisible}`);
  if (isVisible) {
    await promptButton.click();
    await page.waitForTimeout(1500);
    console.log('Clicked Prompt button');
  }
}

// Re-check textareas
const tas = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent).map(t => ({
    placeholder: t.placeholder?.substring(0, 50),
    rect: t.getBoundingClientRect(),
    isVisible: window.getComputedStyle(t).display !== 'none',
  }));
});
console.log('\nVisible textareas after Prompt click:');
for (const t of tas) console.log(`  [${t.rect.y.toFixed(0)}] "${t.placeholder}"`);

await page.screenshot({ path: '/workspace/suno-gen-2captcha/after-prompt-click.png' });
await browser.close();

function log(m) { console.log(`[${new Date().toISOString().substring(11,19)}] ${m}`); }

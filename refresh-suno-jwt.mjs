#!/usr/bin/env node
/**
 * Suno JWT refresh — works WITHOUT Google OAuth flow.
 * 
 * Uses Playwright to load suno.com with the saved __client cookie,
 * captures the fresh Bearer JWT from outbound API calls.
 *
 * Usage:
 *   SUNO_COOKIE='eyJh...' node refresh-suno-jwt.mjs
 *
 * Output:
 *   /workspace/suno-jwt.txt — fresh JWT (1717 chars)
 *
 * Discovery (2026-06-29):
 *   - /api/feed/v2 is dead, use /api/feed/v3 (POST)
 *   - /api/project/me returns all workspaces (your "channel" projects)
 *   - GET /api/project/{id} returns ALL clips with audio_url, title, duration
 *   - This means: NO NEED to ask user for share URLs anymore
 *   - Just refresh JWT → fetch all 3 channel projects → download via CDN
 */
import { chromium } from 'playwright-extra';
import stealth from 'puppeteer-extra-plugin-stealth';
chromium.use(stealth);
import { writeFileSync } from 'fs';

const COOKIE = process.env.SUNO_COOKIE;
if (!COOKIE) { console.error('Set SUNO_COOKIE env var (refresh token from auth.suno.com)'); process.exit(1); }

const log = (...a) => console.log(`[${new Date().toISOString().slice(11,19)}]`, ...a);

const browser = await chromium.launch({
  executablePath: '/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome',
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
});
const ctx = await browser.newContext({
  userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  viewport: { width: 1440, height: 900 },
});
await ctx.addCookies([
  { name: '__client', value: COOKIE, domain: '.suno.com', path: '/', httpOnly: false, secure: true, sameSite: 'None' }
]);

const page = await ctx.newPage();
const apiCalls = [];
page.on('request', req => {
  const u = req.url();
  if (u.includes('studio-api-prod.suno.com')) {
    apiCalls.push({
      method: req.method(),
      url: u,
      auth: req.headers().authorization || '',
    });
  }
});

log('Loading /me...');
await page.goto('https://suno.com/me', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(12000);
log(`URL: ${page.url()}`);

const authReqs = apiCalls.filter(c => c.auth?.startsWith('Bearer '));
log(`Bearer requests: ${authReqs.length}`);

if (authReqs.length > 0) {
  let longest = '';
  for (const r of authReqs) {
    const auth = r.auth.replace('Bearer ', '');
    if (auth.length > longest.length) longest = auth;
  }
  log(`JWT: ${longest.length} chars`);
  writeFileSync('/workspace/suno-jwt.txt', longest);
  log('Saved to /workspace/suno-jwt.txt');
  log('Use it: export SUNO_JWT=$(cat /workspace/suno-jwt.txt)');
}

await browser.close();

// Refresh JWT - load all 32 cookies from full browser state
import { chromium } from 'playwright';
import fs from 'fs';

function log(msg) {
  const ts = new Date().toISOString().substring(11, 19);
  console.log(`[${ts}] ${msg}`);
}

const browser = await chromium.launch({
  headless: true,
  executablePath: '/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome',
  args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
});
const ctx = await browser.newContext({
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
  viewport: { width: 1280, height: 800 },
  locale: 'en-US',
  timezoneId: 'America/New_York',
});

// Add ALL cookies from the previous successful run
const cookieFiles = {
  '__client': '/workspace/suno-client-fresh.txt',
  '__session': '/workspace/suno-session-fresh.txt',
};
const cookies = [];
for (const [name, file] of Object.entries(cookieFiles)) {
  if (fs.existsSync(file)) {
    const value = fs.readFileSync(file, 'utf8').trim();
    cookies.push({
      name, value,
      domain: '.suno.com',
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: name === '__session' ? 'Lax' : 'None',
    });
  }
}
log(`Adding ${cookies.length} base cookies`);
await ctx.addCookies(cookies);

const page = await ctx.newPage();

// Capture all auth
const capturedJWTs = new Set();
page.on('request', req => {
  const auth = req.headers()['authorization'];
  if (auth && auth.startsWith('Bearer ') && auth.length > 200) {
    capturedJWTs.add(auth.substring(7));
  }
});

// First visit / to populate session cookies via Clerk handshake
log('Step 1: Visiting / to initialize Clerk session...');
try {
  await page.goto('https://suno.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
} catch (e) { log(`Err: ${e.message}`); }

// Wait for Clerk handshake
log('Step 2: Waiting 25s for Clerk handshake...');
await page.waitForTimeout(25000);

// Now navigate to /create
log('Step 3: Navigating to /create...');
try {
  await page.goto('https://suno.com/create', { waitUntil: 'domcontentloaded', timeout: 60000 });
} catch (e) { log(`Err: ${e.message}`); }

// Wait for API calls
log('Step 4: Waiting 20s for initial polls...');
await page.waitForTimeout(20000);

log(`Captured ${capturedJWTs.size} JWTs`);
log(`Final URL: ${page.url()}`);

// Save fresh cookies
const freshCookies = await ctx.cookies('https://suno.com');
for (const c of freshCookies) {
  if (c.name === '__client') {
    fs.writeFileSync('/workspace/suno-client-fresh.txt', c.value);
    log(`Saved __client (${c.value.length} chars)`);
  }
  if (c.name === '__session') {
    fs.writeFileSync('/workspace/suno-session-fresh.txt', c.value);
    log(`Saved __session (${c.value.length} chars)`);
  }
}

if (capturedJWTs.size > 0) {
  const longest = [...capturedJWTs].sort((a, b) => b.length - a.length)[0];
  fs.writeFileSync('/workspace/suno-jwt-fresh.txt', longest);
  log(`Saved JWT (${longest.length} chars)`);
  
  try {
    const payload = JSON.parse(Buffer.from(longest.split('.')[1], 'base64').toString());
    const exp = new Date(payload.exp * 1000).toISOString();
    const minsLeft = Math.round((payload.exp * 1000 - Date.now()) / 60000);
    log(`JWT exp: ${exp} (${minsLeft} min from now)`);
    log(`Plan: ${payload.plan}`);
  } catch (e) {}
}

const state = await page.evaluate(() => {
  return {
    url: location.href,
    title: document.title,
    hasCredits: document.body.innerText.includes('Credits'),
    hasCreate: !!document.querySelector('button.hxc-btn-variant-aura'),
    bodyStart: document.body.innerText.substring(0, 200),
    textareas: Array.from(document.querySelectorAll('textarea')).map(t => ({
      placeholder: t.placeholder,
      visible: t.offsetParent !== null,
    })),
  };
});
log(`Title: ${state.title}`);
log(`Has Credits: ${state.hasCredits}`);
log(`Has Create: ${state.hasCreate}`);
log(`Textareas: ${state.textareas.length}`);
log(`Body: ${state.bodyStart}`);

await page.screenshot({ path: '/workspace/suno-gen-2captcha/refresh-result.png' });
await browser.close();
log('Done');

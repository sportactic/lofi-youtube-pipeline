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

// Switch to Instrumental + fill
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
    setter.call(ta, 'Lo-fi chillhop with warm Rhodes piano and gentle vinyl crackle, slow tempo, dreamy, cozy, anime aesthetic, late night study vibe');
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  }
});
await page.waitForTimeout(1000);

// Click Create
await page.evaluate(() => document.querySelector('button[aria-label="Create song"]')?.click());
log('Create clicked. Waiting for captcha to appear...');

// Wait for hCaptcha iframe
let captchaFound = false;
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(1000);
  const f = await page.evaluate(() => {
    const iframes = Array.from(document.querySelectorAll('iframe'));
    for (const iframe of iframes) {
      const src = iframe.getAttribute('src') || '';
      if (src.includes('hcaptcha')) {
        return { found: true, src: src.substring(0, 100) };
      }
    }
    return { found: false };
  });
  if (f.found) {
    log(`hCaptcha found: ${f.src}`);
    captchaFound = true;
    break;
  }
}

if (!captchaFound) {
  log('No captcha appeared');
  await browser.close();
  process.exit(1);
}

// Wait a bit for iframe to load
await page.waitForTimeout(5000);

// Take screenshot of captcha state
await page.screenshot({ path: '/workspace/suno-gen-2captcha/captcha-state.png' });

// Check what's in the iframe
log('Inspecting iframe contents...');
const frames = page.frames();
log(`Total frames: ${frames.length}`);
for (const f of frames) {
  const url = f.url();
  if (url.includes('hcaptcha')) {
    log(`Frame: ${url.substring(0, 100)}`);
    try {
      const inner = await f.evaluate(() => ({
        title: document.title,
        bodyText: document.body?.innerText?.substring(0, 200),
        buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent?.trim()).filter(Boolean),
        hasTextarea: !!document.querySelector('textarea[name="h-captcha-response"]'),
        textareaValue: document.querySelector('textarea[name="h-captcha-response"]')?.value?.substring(0, 30),
      }));
      log(`  Inner: ${JSON.stringify(inner)}`);
    } catch (e) { log(`  Cannot access: ${e.message}`); }
  }
}

// Inject 2captcha solution
const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';
const sitekey = await page.evaluate(() => {
  const iframes = Array.from(document.querySelectorAll('iframe[src*="hcaptcha"]'));
  for (const iframe of iframes) {
    const src = iframe.getAttribute('src');
    const m = src.match(/sitekey=([^&]+)/);
    if (m) return decodeURIComponent(m[1]);
  }
  return null;
});
log(`Sitekey: ${sitekey?.substring(0, 30)}`);

if (sitekey) {
  log('Submitting to 2captcha...');
  const idRes = await fetch('https://2captcha.com/in.php', {
    method: 'POST',
    body: new URLSearchParams({ key: TWO_CAPTCHA_KEY, method: 'hcaptcha', sitekey, pageurl: page.url(), json: '1' }),
  });
  const idData = await idRes.json();
  log(`Submit result: ${JSON.stringify(idData)}`);
  
  if (idData.status === 1) {
    log('Polling...');
    let token = null;
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 5000));
      const r = await fetch(`https://2captcha.com/res.php?key=${TWO_CAPTCHA_KEY}&action=get&id=${idData.request}&json=1`);
      const j = await r.json();
      log(`  Poll ${i}: ${j.status === 1 ? 'READY' : j.request}`);
      if (j.status === 1) {
        token = j.request;
        break;
      }
    }
    
    if (token) {
      log(`Got token (len=${token.length}). Injecting...`);
      
      // Try multiple injection methods
      const results = await page.evaluate((token) => {
        const out = [];
        // 1) Top-level textareas
        const topTas = document.querySelectorAll('textarea[name="h-captcha-response"], textarea[name="g-recaptcha-response"]');
        for (const t of topTas) {
          t.value = token;
          t.innerHTML = token;
          t.style.display = 'block';
          t.dispatchEvent(new Event('input', { bubbles: true }));
          t.dispatchEvent(new Event('change', { bubbles: true }));
          out.push(`top textarea (${t.name})`);
        }
        // 2) hcaptcha global
        if (window.hcaptcha) {
          out.push('window.hcaptcha exists');
          // Try internal methods
          try {
            const internal = window.hcaptcha;
            for (const k of Object.keys(internal)) {
              if (typeof internal[k] === 'function' && k.toLowerCase().includes('set')) {
                out.push(`hcaptcha.${k}() exists`);
              }
            }
          } catch (e) { out.push(`hcaptcha inspect err: ${e.message}`); }
        }
        // 3) Look for any postMessage handler
        if (window.hcaptcha?.nodes) {
          try {
            window.hcaptcha.nodes.forEach((n, i) => {
              if (n && typeof n.setResponse === 'function') {
                n.setResponse(token);
                out.push(`hcaptcha.nodes[${i}].setResponse`);
              }
              if (n && typeof n._setResponse === 'function') {
                n._setResponse(token);
                out.push(`hcaptcha.nodes[${i}]._setResponse`);
              }
            });
          } catch (e) { out.push(`nodes err: ${e.message}`); }
        }
        return out;
      }, token);
      log(`Inject results: ${JSON.stringify(results)}`);
      
      // Check iframe state after injection
      await page.waitForTimeout(3000);
      
      // Look for any "Verify" / "Submit" buttons in any frame
      log('\nLooking for Submit/Verify button after injection...');
      for (const f of page.frames()) {
        const url = f.url();
        if (url.includes('hcaptcha')) {
          try {
            const btnTexts = await f.evaluate(() => 
              Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.textContent?.trim(),
                disabled: b.disabled,
                visible: b.offsetParent !== null,
              }))
            );
            for (const btn of btnTexts) {
              if (btn.text && (btn.text.match(/verify|submit|continue|next|done/i) && btn.visible && !btn.disabled)) {
                log(`  Found button: "${btn.text}"`);
              }
            }
          } catch (e) {}
        }
      }
    }
  }
}

await page.waitForTimeout(15000);

// Check state
const final = await page.evaluate(() => {
  const t = document.body.innerText;
  return {
    bodyMatch: t.match(/generating|creating|loading|please wait|queued|adding|generat/i)?.slice(0, 3),
    audioIframes: Array.from(document.querySelectorAll('audio')).map(a => a.src).slice(0, 5),
    bodySlice: t.substring(0, 1500).replace(/\n+/g, ' '),
  };
});
log(`\nFinal state: ${JSON.stringify(final)}`);

await page.screenshot({ path: '/workspace/suno-gen-2captcha/after-captcha-solve.png' });
await browser.close();

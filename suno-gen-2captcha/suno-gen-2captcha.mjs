// Suno + 2captcha: Complete Generation Pipeline (v6 - target Song Description)
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';

function log(msg) { console.log(`[${new Date().toISOString().substring(11,19)}] ${msg}`); }
function readCookieValue(name) {
  const p = path.join('/workspace', name);
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8').trim() : '';
}

async function submitCaptcha(sitekey, pageurl) {
  const params = new URLSearchParams({ key: TWO_CAPTCHA_KEY, method: 'hcaptcha', sitekey, pageurl, json: '1' });
  const r = await fetch('https://2captcha.com/in.php', { method: 'POST', body: params });
  const j = await r.json();
  if (j.status !== 1) throw new Error(`2captcha submit failed: ${JSON.stringify(j)}`);
  return j.request;
}

async function pollCaptcha(id, maxMs = 180000) {
  const start = Date.now();
  let delay = 6000;
  while (Date.now() - start < maxMs) {
    await new Promise(r => setTimeout(r, delay));
    delay = Math.min(delay + 2000, 12000);
    const params = new URLSearchParams({ key: TWO_CAPTCHA_KEY, action: 'get', id, json: '1' });
    const r = await fetch(`https://2captcha.com/res.php?${params}`);
    const j = await r.json();
    if (j.status === 1) {
      log(`✓ 2captcha solved in ${Math.round((Date.now() - start) / 1000)}s`);
      return j.request;
    }
    if (j.request !== 'CAPCHA_NOT_READY') throw new Error(`2captcha error: ${JSON.stringify(j)}`);
  }
  throw new Error(`2captcha timeout after ${maxMs}ms`);
}

async function getCaptchaSitekey(page) {
  await page.waitForTimeout(2000);
  return await page.evaluate(() => {
    try {
      const scripts = Array.from(document.scripts);
      for (const s of scripts) {
        if (s.src && s.src.includes('hcaptcha')) {
          const m = s.src.match(/sitekey=([^&]+)/);
          if (m) return decodeURIComponent(m[1]);
        }
      }
      const all = Array.from(document.querySelectorAll('*'));
      for (const el of all) {
        for (const attr of el.attributes) {
          if (attr.name && attr.name.toLowerCase().includes('sitekey')) return attr.value;
        }
      }
      const iframes = Array.from(document.querySelectorAll('iframe[src*="hcaptcha"]'));
      for (const iframe of iframes) {
        const src = iframe.getAttribute('src');
        if (src) {
          const m = src.match(/sitekey=([^&]+)/);
          if (m) return decodeURIComponent(m[1]);
        }
      }
      return null;
    } catch (e) { return null; }
  });
}

async function injectCaptchaSolution(page, token) {
  return await page.evaluate((token) => {
    const results = [];
    const topTas = document.querySelectorAll('textarea[name="h-captcha-response"], textarea[name="g-recaptcha-response"]');
    for (const t of topTas) {
      t.value = token; t.innerHTML = token; t.style.display = 'block';
      t.dispatchEvent(new Event('input', { bubbles: true }));
      t.dispatchEvent(new Event('change', { bubbles: true }));
      results.push('top-level textarea');
    }
    return results;
  }, token);
}

// Find Song Description textarea by label
async function findSongDescriptionTextarea(page) {
  return await page.evaluate(() => {
    // Method 1: Find by sibling label
    const allEls = Array.from(document.querySelectorAll('label, div, span'));
    const sdLabel = allEls.find(el => el.textContent?.trim().startsWith('Song Description'));
    if (sdLabel) {
      const ta = sdLabel.parentElement?.querySelector('textarea');
      if (ta && ta.offsetParent) {
        return { ok: true, method: 'label', ph: ta.placeholder?.substring(0, 50) };
      }
    }
    // Method 2: Find textarea with maxlength 3000 (Song Description)
    const tas = Array.from(document.querySelectorAll('textarea'));
    const sdTa = tas.find(t => t.offsetParent && t.maxLength === 3000);
    if (sdTa) return { ok: true, method: 'maxlength', ph: sdTa.placeholder?.substring(0, 50) };
    // Method 3: First visible textarea
    const firstVisible = tas.find(t => t.offsetParent);
    if (firstVisible) return { ok: true, method: 'first-visible', ph: firstVisible.placeholder?.substring(0, 50) };
    return { ok: false, reason: 'not found' };
  });
}

async function fillSongDescription(page, text) {
  return await page.evaluate((text) => {
    const allEls = Array.from(document.querySelectorAll('label, div, span'));
    const sdLabel = allEls.find(el => el.textContent?.trim().startsWith('Song Description'));
    let targetTa = null;
    if (sdLabel) {
      targetTa = sdLabel.parentElement?.querySelector('textarea');
    }
    if (!targetTa) {
      const tas = Array.from(document.querySelectorAll('textarea'));
      targetTa = tas.find(t => t.offsetParent && t.maxLength === 3000) || tas.find(t => t.offsetParent);
    }
    if (!targetTa) return { ok: false, reason: 'no textarea' };
    
    // Use React-compatible setter
    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(targetTa, text);
    targetTa.dispatchEvent(new Event('input', { bubbles: true }));
    targetTa.dispatchEvent(new Event('change', { bubbles: true }));
    
    return { ok: true, value: targetTa.value?.substring(0, 50), ph: targetTa.placeholder?.substring(0, 50) };
  }, text);
}

async function main() {
  const [, , channelArg] = process.argv;
  const CHANNEL = channelArg || 'thelofi';
  const N_TRACKS = parseInt(process.argv[3] || '2', 10);
  
  log(`Channel: ${CHANNEL}, Tracks: ${N_TRACKS}`);
  
  const promptsFile = `/workspace/all-channels-suno-prompts/json/prompts-${CHANNEL}.json`;
  const promptsData = JSON.parse(fs.readFileSync(promptsFile, 'utf8'));
  const prompts = promptsData.prompts;
  
  const cookies = [];
  const clientVal = readCookieValue('suno-client-fresh.txt');
  const sessionVal = readCookieValue('suno-session-fresh.txt');
  if (clientVal) cookies.push({ name: '__client', value: clientVal, domain: '.suno.com', path: '/', httpOnly: true, secure: true, sameSite: 'None' });
  if (sessionVal) cookies.push({ name: '__session', value: sessionVal, domain: '.suno.com', path: '/', httpOnly: true, secure: true, sameSite: 'Lax' });
  log(`Cookies: ${cookies.length}`);
  
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
  await ctx.addCookies(cookies);
  
  const page = await ctx.newPage();
  
  const capturedAudios = [];
  const seenClipIds = new Set();
  
  page.on('request', req => {
    const url = req.url();
    if (url && url.includes('cdn1.suno.ai') && url.includes('.mp3') && !url.includes('sil-100')) {
      capturedAudios.push({ url, time: Date.now(), source: 'request' });
      log(`🎵 AUDIO (req): ${url.substring(0, 100)}`);
    }
  });
  
  page.on('response', async resp => {
    const url = resp.url();
    if (url.includes('/api/feed/v3') || url.includes('/api/feed/v2')) {
      try {
        const body = await resp.text();
        const data = JSON.parse(body);
        const clips = data.clips || [];
        for (const c of clips) {
          if (c.id && !seenClipIds.has(c.id)) {
            seenClipIds.add(c.id);
            if (c.audio_url && c.audio_url.includes('cdn1')) {
              capturedAudios.push({ url: c.audio_url, time: Date.now(), source: 'feed', title: c.title, clipId: c.id, status: c.status });
              log(`🎵 AUDIO (feed): ${c.title || c.id} [${c.status}] - ${c.audio_url.substring(0, 80)}`);
            }
          }
        }
      } catch (e) {}
    }
  });
  
  // Handshake
  log('Loading / for handshake...');
  try { await page.goto('https://suno.com/', { waitUntil: 'domcontentloaded', timeout: 60000 }); }
  catch (e) { log(`Goto err: ${e.message}`); }
  await page.waitForTimeout(20000);
  
  log('Loading /create...');
  try { await page.goto('https://suno.com/create', { waitUntil: 'domcontentloaded', timeout: 60000 }); }
  catch (e) { log(`Goto err: ${e.message}`); }
  await page.waitForTimeout(8000);
  
  const state = await page.evaluate(() => ({ has8920: document.body.innerText.includes('8,920') }));
  if (!state.has8920) {
    log('❌ Not logged in!');
    await browser.close();
    return;
  }
  log('✓ Logged in');
  
  // Switch to Instrumental mode
  log('Switching to Instrumental mode...');
  await page.evaluate(() => {
    document.querySelectorAll('[role="radio"]').forEach(r => {
      if (r.textContent?.trim().toLowerCase() === 'instrumental') r.click();
    });
  });
  await page.waitForTimeout(2000);
  
  const sdInfo = await findSongDescriptionTextarea(page);
  log(`Song Description textarea: ${JSON.stringify(sdInfo)}`);
  
  // Generate tracks
  const generated = [];
  for (let i = 0; i < Math.min(N_TRACKS, prompts.length); i++) {
    const prompt = prompts[i];
    log(`\n=== Track ${i + 1}/${N_TRACKS}: ${prompt.name} ===`);
    log(`Prompt: ${prompt.prompt.substring(0, 80)}...`);
    
    const audiosBefore = capturedAudios.length;
    
    // Fill Song Description textarea
    const fillResult = await fillSongDescription(page, prompt.prompt);
    log(`  Fill: ${JSON.stringify(fillResult)}`);
    if (!fillResult.ok) {
      log('  ⚠ Fill failed');
      continue;
    }
    await page.waitForTimeout(1000);
    
    // Verify Create is now enabled
    const beforeClick = await page.evaluate(() => ({
      createDisabled: document.querySelector('button[aria-label="Create song"]')?.disabled,
      charCounter: document.body.innerText.match(/\d+\/3000/)?.[0],
    }));
    log(`  State: ${JSON.stringify(beforeClick)}`);
    
    if (beforeClick.createDisabled) {
      log('  ⚠ Create still disabled, waiting longer for React state sync...');
      await page.waitForTimeout(3000);
      const retry = await page.evaluate(() => document.querySelector('button[aria-label="Create song"]')?.disabled);
      if (retry) {
        log('  ✗ Create still disabled after wait, skipping');
        continue;
      }
    }
    
    // Click Create
    await page.evaluate(() => document.querySelector('button[aria-label="Create song"]')?.click());
    log('  ✓ Create clicked');
    
    // Wait
    let captchaSolved = false;
    let audioFound = false;
    const maxWait = 240_000;
    const startWait = Date.now();
    
    while (Date.now() - startWait < maxWait) {
      await page.waitForTimeout(3000);
      
      if (capturedAudios.length > audiosBefore) {
        const newAudios = capturedAudios.slice(audiosBefore);
        log(`  ✓ ${newAudios.length} new audio(s)!`);
        for (const a of newAudios) log(`    → ${a.title || '?'}: ${a.url.substring(0, 80)}`);
        generated.push({
          name: prompt.name,
          prompt: prompt.prompt,
          audioUrls: newAudios.map(a => a.url),
          audioMeta: newAudios,
          captchaSolved,
        });
        audioFound = true;
        break;
      }
      
      const captchaInfo = await page.evaluate(() => {
        const iframes = Array.from(document.querySelectorAll('iframe'));
        for (const f of iframes) {
          const src = f.getAttribute('src') || '';
          if (src.includes('hcaptcha-endpoint-prod.suno.com') || src.includes('hcaptcha-assets-prod.suno.com')) {
            return { found: true };
          }
        }
        return { found: false };
      });
      
      if (captchaInfo.found && !captchaSolved) {
        log('  🔐 hCaptcha');
        const sitekey = await getCaptchaSitekey(page);
        if (sitekey) {
          try {
            log(`  Sitekey: ${sitekey.substring(0, 16)}...`);
            const id = await submitCaptcha(sitekey, page.url());
            const token = await pollCaptcha(id);
            await injectCaptchaSolution(page, token);
            captchaSolved = true;
            log('  ✓ Captcha solved');
          } catch (e) {
            log(`  ✗ 2captcha error: ${e.message}`);
          }
        }
      }
      
      const elapsed = Math.round((Date.now() - startWait) / 1000);
      if (elapsed % 30 === 0) {
        log(`  ${elapsed}s, new audios=${capturedAudios.length - audiosBefore}, captcha=${captchaSolved}`);
      }
    }
    
    if (!audioFound) {
      log(`  ✗ No audio after ${Math.round((Date.now() - startWait) / 1000)}s`);
      generated.push({
        name: prompt.name,
        prompt: prompt.prompt,
        audioUrls: [],
        captchaSolved,
        failed: true,
      });
    }
    
    if (i < Math.min(N_TRACKS, prompts.length) - 1) {
      log('  Waiting 10s...');
      await page.waitForTimeout(10000);
    }
  }
  
  const outFile = `/workspace/suno-gen-2captcha/result-${CHANNEL}-${Date.now()}.json`;
  fs.writeFileSync(outFile, JSON.stringify({
    channel: CHANNEL,
    timestamp: new Date().toISOString(),
    totalPrompts: prompts.length,
    attempted: N_TRACKS,
    generated,
    capturedAudios: capturedAudios.map(a => ({ url: a.url, title: a.title })),
  }, null, 2));
  log(`\nSaved ${outFile}`);
  log(`Success: ${generated.filter(g => g.audioUrls && g.audioUrls.length > 0).length}/${N_TRACKS}`);
  
  await browser.close();
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});

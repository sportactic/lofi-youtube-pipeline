// Suno Generation Pipeline v7 - Direct API + 2captcha
// Workflow:
// 1. Use existing fresh JWT + cookies
// 2. For each prompt: get captcha token from 2captcha, POST to /api/generate/v2-web/
// 3. Poll /api/feed/ until audio_url is ready
// 4. Output track metadata to JSON

import fs from 'fs';
import path from 'path';

const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';
const SITEKEY = 'd65453de-3f1a-4aac-9366-a0f06e52b2ce';
const PAGEURL = 'https://suno.com/create';
const POLL_INTERVAL_MS = 8000;
const MAX_POLL_MS = 240_000;

function log(msg) {
  const ts = new Date().toISOString().substring(11, 19);
  console.log(`[${ts}] ${msg}`);
}

function readFile(name) {
  const p = path.join('/workspace', name);
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8').trim() : '';
}

async function getCaptchaToken() {
  const idRes = await fetch('https://2captcha.com/in.php', {
    method: 'POST',
    body: new URLSearchParams({
      key: TWO_CAPTCHA_KEY, method: 'hcaptcha',
      sitekey: SITEKEY, pageurl: PAGEURL, json: '1',
    }),
  });
  const idData = await idRes.json();
  if (idData.status !== 1) throw new Error(`2captcha submit failed: ${JSON.stringify(idData)}`);
  
  const id = idData.request;
  log(`  2captcha ID: ${id}, polling...`);
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 5000));
    const r = await fetch(`https://2captcha.com/res.php?key=${TWO_CAPTCHA_KEY}&action=get&id=${id}&json=1`);
    const j = await r.json();
    if (j.status === 1) {
      log(`  ✓ 2captcha solved in ${(i+1) * 5}s`);
      return j.request;
    }
  }
  throw new Error('2captcha timeout');
}

async function generateTrack(jwt, prompt, title, token) {
  const body = {
    token,
    token_provider: 2,
    make_instrumental: true,
    prompt,
    title,
    metadata: { web_client_pathname: '/create' },
    mv: 'chirp-fenix',
  };
  const res = await fetch('https://studio-api-prod.suno.com/api/generate/v2-web/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwt}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  if (res.status !== 200) {
    throw new Error(`API ${res.status}: ${text.substring(0, 300)}`);
  }
  const data = JSON.parse(text);
  return data;
}

async function pollTrack(jwt, clipId) {
  const start = Date.now();
  let delay = POLL_INTERVAL_MS;
  while (Date.now() - start < MAX_POLL_MS) {
    await new Promise(r => setTimeout(r, delay));
    delay = Math.min(delay + 1000, 15000);
    const res = await fetch(`https://studio-api-prod.suno.com/api/feed/?ids=${clipId}`, {
      headers: { 'Authorization': `Bearer ${jwt}` },
    });
    const text = await res.text();
    if (!text) continue;
    let clips;
    try { clips = JSON.parse(text); } catch { continue; }
    if (!Array.isArray(clips) || clips.length === 0) continue;
    const c = clips[0];
    const elapsed = Math.round((Date.now() - start) / 1000);
    if (c.audio_url && c.status === 'complete') {
      log(`  ✓ Track ready in ${elapsed}s`);
      return c;
    }
    if (elapsed % 30 === 0) {
      log(`  ${elapsed}s: status=${c.status}, has_audio=${!!c.audio_url}`);
    }
    if (c.status === 'error' || c.status === 'failed') {
      throw new Error(`Track failed: ${JSON.stringify(c).substring(0, 200)}`);
    }
  }
  throw new Error('Poll timeout');
}

async function main() {
  const [, , channelArg, nArg] = process.argv;
  const CHANNEL = channelArg || 'thelofi';
  const N = parseInt(nArg || '5', 10);
  
  log(`Channel: ${CHANNEL}, Tracks: ${N}`);
  
  // Read JWT
  let jwt = readFile('suno-jwt-fresh.txt');
  if (!jwt) { log('No JWT'); process.exit(1); }
  
  // Check expiry
  try {
    const payload = JSON.parse(Buffer.from(jwt.split('.')[1], 'base64').toString());
    const minsLeft = Math.round((payload.exp * 1000 - Date.now()) / 60000);
    log(`JWT: ${minsLeft} min left`);
    if (minsLeft < 5) {
      log('JWT expiring soon, please refresh first');
    }
  } catch {}
  
  // Load prompts
  const promptsFile = `/workspace/all-channels-suno-prompts/json/prompts-${CHANNEL}.json`;
  if (!fs.existsSync(promptsFile)) {
    log(`Prompts file not found: ${promptsFile}`);
    process.exit(1);
  }
  const { prompts } = JSON.parse(fs.readFileSync(promptsFile, 'utf8'));
  
  const results = [];
  for (let i = 0; i < Math.min(N, prompts.length); i++) {
    const p = prompts[i];
    log(`\n=== Track ${i + 1}/${N}: ${p.name} ===`);
    
    try {
      // Get captcha token
      const token = await getCaptchaToken();
      
      // Generate
      log(`  Generating: ${p.prompt.substring(0, 60)}...`);
      const submitData = await generateTrack(jwt, p.prompt, p.name, token);
      const clip = submitData.clips?.[0];
      if (!clip) throw new Error('No clip returned');
      log(`  ✓ Submitted: ${clip.id} (${clip.status})`);
      
      // Poll for audio
      const completed = await pollTrack(jwt, clip.id);
      log(`  🎵 ${completed.audio_url}`);
      log(`  Duration: ${completed.metadata?.duration}s`);
      
      results.push({
        name: p.name,
        prompt: p.prompt,
        clipId: clip.id,
        title: completed.title,
        audioUrl: completed.audio_url,
        imageUrl: completed.image_url,
        imageLargeUrl: completed.image_large_url,
        duration: completed.metadata?.duration,
        model: completed.metadata?.model_name || completed.model_name,
        status: completed.status,
        createdAt: completed.created_at,
      });
    } catch (e) {
      log(`  ✗ Error: ${e.message}`);
      results.push({
        name: p.name,
        prompt: p.prompt,
        error: e.message,
      });
    }
  }
  
  const outFile = `/workspace/suno-gen-2captcha/gen-${CHANNEL}-${Date.now()}.json`;
  fs.writeFileSync(outFile, JSON.stringify({
    channel: CHANNEL,
    timestamp: new Date().toISOString(),
    attempted: N,
    success: results.filter(r => !r.error).length,
    failed: results.filter(r => r.error).length,
    results,
  }, null, 2));
  log(`\n=== DONE ===`);
  log(`Saved ${outFile}`);
  log(`Success: ${results.filter(r => !r.error).length}/${N}`);
  
  // Print all audio URLs for easy download
  const downloads = results.filter(r => r.audioUrl).map(r => ({
    name: r.name,
    url: r.audioUrl,
    duration: r.duration,
  }));
  if (downloads.length > 0) {
    console.log('\n=== READY FOR DOWNLOAD ===');
    for (const d of downloads) {
      console.log(`# ${d.name} (${d.duration}s)`);
      console.log(`curl -L -o "${d.name.replace(/[^a-z0-9]/gi, '_')}.mp3" "${d.url}"`);
    }
  }
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});

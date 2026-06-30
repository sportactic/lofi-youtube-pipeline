import fs from 'fs';

const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';
const SITEKEY = 'd65453de-3f1a-4aac-9366-a0f06e52b2ce';

const idRes = await fetch('https://2captcha.com/in.php', {
  method: 'POST',
  body: new URLSearchParams({
    key: TWO_CAPTCHA_KEY, method: 'hcaptcha',
    sitekey: SITEKEY, pageurl: 'https://suno.com/create', json: '1',
  }),
});
const idData = await idRes.json();
if (idData.status !== 1) process.exit(1);

let token = null;
for (let i = 0; i < 30; i++) {
  await new Promise(r => setTimeout(r, 5000));
  const r = await fetch(`https://2captcha.com/res.php?key=${TWO_CAPTCHA_KEY}&action=get&id=${idData.request}&json=1`);
  const j = await r.json();
  if (j.status === 1) { token = j.request; console.log(`Token in ${i*5}s`); break; }
}
if (!token) process.exit(1);

const jwtVal = fs.readFileSync('/workspace/suno-jwt-fresh.txt', 'utf8').trim();
const clientVal = fs.readFileSync('/workspace/suno-client-fresh.txt', 'utf8').trim();
const sessionVal = fs.readFileSync('/workspace/suno-session-fresh.txt', 'utf8').trim();

// Try token_provider as int 1
console.log('\n1) token_provider=1 (int)...');
let result = await fetch('https://studio-api-prod.suno.com/api/generate/v2-web/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtVal}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    params: {
      token, token_provider: 1,
      make_instrumental: true,
      prompt: 'Lo-fi hip hop with mellow piano',
      title: 'API Test 1',
      metadata: { web_client_pathname: '/create' },
      mv: 'chirp-fenix',
    }
  }),
});
console.log(`  Status: ${result.status}`);
console.log(`  Body: ${(await result.text()).substring(0, 800)}`);

// Try token_provider as int 2
console.log('\n2) token_provider=2 (int)...');
result = await fetch('https://studio-api-prod.suno.com/api/generate/v2-web/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtVal}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    token, token_provider: 2,
    make_instrumental: true,
    prompt: 'Lo-fi hip hop with mellow piano',
    title: 'API Test 2',
    metadata: { web_client_pathname: '/create' },
    mv: 'chirp-fenix',
  }),
});
console.log(`  Status: ${result.status}`);
console.log(`  Body: ${(await result.text()).substring(0, 800)}`);

// Try without params wrapper, with int
console.log('\n3) Flat with token_provider=1...');
result = await fetch('https://studio-api-prod.suno.com/api/generate/v2-web/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtVal}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    token, token_provider: 1,
    make_instrumental: true,
    prompt: 'Lo-fi hip hop with mellow piano',
    title: 'API Test 3',
    metadata: { web_client_pathname: '/create' },
    mv: 'chirp-fenix',
  }),
});
console.log(`  Status: ${result.status}`);
console.log(`  Body: ${(await result.text()).substring(0, 800)}`);

// Try token_provider as null
console.log('\n4) token_provider=null...');
result = await fetch('https://studio-api-prod.suno.com/api/generate/v2-web/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtVal}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    token, token_provider: null,
    make_instrumental: true,
    prompt: 'Lo-fi hip hop with mellow piano',
    title: 'API Test 4',
    metadata: { web_client_pathname: '/create' },
    mv: 'chirp-fenix',
  }),
});
console.log(`  Status: ${result.status}`);
console.log(`  Body: ${(await result.text()).substring(0, 800)}`);

const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';
const SITEKEY = 'd65453de-3f1a-4aac-9366-a0f06e';

console.log('Submitting to 2captcha...');
const params = new URLSearchParams();
params.append('key', TWO_CAPTCHA_KEY);
params.append('method', 'hcaptcha');
params.append('sitekey', SITEKEY);
params.append('pageurl', 'https://suno.com/create');
params.append('json', '1');

console.log('Params:', params.toString());

const idRes = await fetch('https://2captcha.com/in.php', {
  method: 'POST',
  body: params,
});
const idData = await idRes.json();
console.log('Submit result:', JSON.stringify(idData));

if (idData.status !== 1) {
  console.log('Failed');
  process.exit(1);
}

// Poll for token
let token = null;
for (let i = 0; i < 30; i++) {
  await new Promise(r => setTimeout(r, 5000));
  const r = await fetch(`https://2captcha.com/res.php?key=${TWO_CAPTCHA_KEY}&action=get&id=${idData.request}&json=1`);
  const j = await r.json();
  console.log(`  Poll ${i}: status=${j.status}, request=${j.request?.substring(0, 60)}`);
  if (j.status === 1) { token = j.request; break; }
}

if (!token) { console.log('No token'); process.exit(1); }
console.log(`Token length: ${token.length}`);

// Read JWT
import fs from 'fs';
const clientVal = fs.readFileSync('/workspace/suno-client-fresh.txt', 'utf8').trim();
const sessionVal = fs.readFileSync('/workspace/suno-session-fresh.txt', 'utf8').trim();
const jwtVal = fs.readFileSync('/workspace/suno-jwt-fresh.txt', 'utf8').trim();

console.log('\nTesting /api/generate/v2-web/ with token...');
const reqBody = {
  token: token,
  token_provider: 'hcaptcha',
  make_instrumental: true,
  prompt: 'Lo-fi hip hop with mellow piano and soft rain ambience',
  title: 'API Test Track',
  metadata: { web_client_pathname: '/create' },
};

const result = await fetch('https://studio-api-prod.suno.com/api/generate/v2-web/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtVal}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(reqBody),
});
const responseText = await result.text();
console.log(`Status: ${result.status}`);
console.log(`Response: ${responseText.substring(0, 800)}`);

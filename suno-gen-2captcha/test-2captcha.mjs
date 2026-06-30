const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';
const SITEKEY = 'd65453de-3f1a-4aac-9366-a0f06e52b2ce';
const PAGEURL = 'https://suno.com/create';

console.log(`Submitting to 2captcha with sitekey=${SITEKEY}`);

const params = new URLSearchParams();
params.append('key', TWO_CAPTCHA_KEY);
params.append('method', 'hcaptcha');
params.append('sitekey', SITEKEY);
params.append('pageurl', PAGEURL);
params.append('json', '1');

console.log('Params:', params.toString());

const idRes = await fetch('https://2captcha.com/in.php', {
  method: 'POST',
  body: params,
});
const idData = await idRes.json();
console.log('Submit:', JSON.stringify(idData));

if (idData.status === 1) {
  console.log(`Captcha ID: ${idData.request}`);
  
  // Poll
  let token = null;
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 5000));
    const r = await fetch(`https://2captcha.com/res.php?key=${TWO_CAPTCHA_KEY}&action=get&id=${idData.request}&json=1`);
    const j = await r.json();
    if (j.status === 1) { 
      token = j.request; 
      console.log(`Token in ${i*5}s, length=${token.length}`);
      break; 
    }
    console.log(`  Poll ${i}: ${j.request}`);
  }
  
  if (token) {
    // Now use the token with Suno's API
    const fs = await import('fs');
    const jwtVal = fs.readFileSync('/workspace/suno-jwt-fresh.txt', 'utf8').trim();
    const clientVal = fs.readFileSync('/workspace/suno-client-fresh.txt', 'utf8').trim();
    const sessionVal = fs.readFileSync('/workspace/suno-session-fresh.txt', 'utf8').trim();
    
    console.log('\nTesting API call with token...');
    const result = await fetch('https://studio-api-prod.suno.com/api/generate/v2-web/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${jwtVal}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: token,
        token_provider: 'hcaptcha',
        make_instrumental: true,
        prompt: 'Lo-fi hip hop with mellow piano and soft rain ambience, dreamy chill',
        title: 'API Test v1',
        metadata: { web_client_pathname: '/create' },
        mv: 'chirp-fenix',
      }),
    });
    const text = await result.text();
    console.log(`Status: ${result.status}`);
    console.log(`Response: ${text.substring(0, 1000)}`);
  }
}

const TWO_CAPTCHA_KEY = '544f51b527ff79e2bcae3f4ae92b4ffc';

const r = await fetch(`https://2captcha.com/getcaptcha?key=${TWO_CAPTCHA_KEY}`);
const text = await r.text();
console.log(text.substring(0, 2000));

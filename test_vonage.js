// Test Vonage SMS API
const apiKey = '05d97a06';
const apiSecret = 'OZHvkdkCPJEY8xpW';
const from = '14352381767';
const to = '+19146022064';
const url = 'https://rest.nexmo.com/sms/json';
const params = new URLSearchParams();
params.append('api_key', apiKey);
params.append('api_secret', apiSecret);
params.append('to', to);
params.append('from', from);
params.append('text', 'Test message from Vonage API');

console.log('Testing Vonage API...');
console.log('URL:', url);
console.log('To:', to);
console.log('From:', from);
console.log('Text:', 'Test message from Vonage API');

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: params.toString(),
})
.then(response => {
  console.log('Response status:', response.status);
  return response.json();
})
.then(data => {
  console.log('Response data:', data);
  if (data.messages && data.messages[0] && data.messages[0].status === '0') {
    console.log('Success! Message ID:', data.messages[0]['message-id']);
  } else {
    console.log('Error:', data.messages?.[0]?.['error-text'] || 'Unknown error');
  }
})
.catch(error => {
  console.error('Error:', error);
}); 
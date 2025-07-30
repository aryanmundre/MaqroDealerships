const accountSid = 'AC519eddc3d92556b1f11c472bc39afb49';
const authToken = 'e1921e6a56a9acbaaa195b6e52eee449';
const from = '+12134747233';
const to = '+19146022064';

const url = `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`;
const params = new URLSearchParams();
params.append('To', to);
params.append('From', from);
params.append('Body', 'Test message from Twilio API');

console.log('Testing Twilio API...');
console.log('URL:', url);
console.log('To:', to);
console.log('From:', from);
console.log('Body:', 'Test message from Twilio API');

fetch(url, {
  method: 'POST',
  headers: {
    'Authorization': 'Basic ' + Buffer.from(accountSid + ':' + authToken).toString('base64'),
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
  if (data.error_code) {
    console.log('Error:', data.error_message);
  } else {
    console.log('Success! Message SID:', data.sid);
  }
})
.catch(error => {
  console.error('Error:', error);
}); 
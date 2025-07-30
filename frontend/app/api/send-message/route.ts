import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { to, body } = await request.json();
    console.log('Sending SMS:', { to, body });
    
    if (!to || !body) {
      console.log('Missing to or body');
      return NextResponse.json({ error: 'Missing to or body' }, { status: 400 });
    }

    const accountSid = process.env.TWILIO_ACCOUNT_SID;
    const authToken = process.env.TWILIO_AUTH_TOKEN;
    const from = process.env.TWILIO_PHONE_NUMBER;

    if (!accountSid || !authToken || !from) {
      console.log('Twilio credentials not set');
      return NextResponse.json({ error: 'Twilio credentials not set' }, { status: 500 });
    }

    const url = `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`;
    const params = new URLSearchParams();
    params.append('To', to);
    params.append('From', from);
    params.append('Body', body);

    console.log('Twilio API call:', { url, to, from, body });

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + Buffer.from(accountSid + ':' + authToken).toString('base64'),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    console.log('Twilio response status:', res.status);

    if (!res.ok) {
      const error = await res.json();
      console.log('Twilio error:', error);
      return NextResponse.json({ error: error.message || 'Failed to send message' }, { status: 500 });
    }

    const data = await res.json();
    console.log('Twilio success:', data);
    return NextResponse.json({ success: true, sid: data.sid });
  } catch (error) {
    console.log('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 
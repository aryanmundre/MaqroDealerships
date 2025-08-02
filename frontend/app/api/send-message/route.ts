import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { to, body } = await request.json();
    console.log('Sending SMS:', { to, body });
    
    if (!to || !body) {
      console.log('Missing to or body');
      return NextResponse.json({ error: 'Missing to or body' }, { status: 400 });
    }

    const apiKey = process.env.VONAGE_API_KEY;
    const apiSecret = process.env.VONAGE_API_SECRET;
    const from = process.env.VONAGE_PHONE_NUMBER;

    if (!apiKey || !apiSecret || !from) {
      console.log('Vonage credentials not set');
      return NextResponse.json({ error: 'Vonage credentials not set' }, { status: 500 });
    }

    console.log('Vonage SMS call:', { to, from, body });

    // Send SMS using Vonage REST API
    const url = 'https://rest.nexmo.com/sms/json';
    const params = new URLSearchParams();
    params.append('api_key', apiKey);
    params.append('api_secret', apiSecret);
    params.append('to', to);
    params.append('from', from);
    params.append('text', body);

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    console.log('Vonage response status:', res.status);

    if (!res.ok) {
      const error = await res.text();
      console.log('Vonage error:', error);
      return NextResponse.json({ error: 'Failed to send message' }, { status: 500 });
    }

    const data = await res.json();
    console.log('Vonage success:', data);
    
    if (data.messages && data.messages[0] && data.messages[0].status === '0') {
      return NextResponse.json({ 
        success: true, 
        messageId: data.messages[0]['message-id'] 
      });
    } else {
      const errorMessage = data.messages?.[0]?.['error-text'] || 'Failed to send message';
      console.log('Vonage delivery error:', errorMessage);
      return NextResponse.json({ error: errorMessage }, { status: 500 });
    }

  } catch (error) {
    console.log('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 
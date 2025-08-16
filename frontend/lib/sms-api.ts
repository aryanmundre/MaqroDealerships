import { getAuthenticatedApi } from './api-client';

export interface SMSResponse {
  success: boolean;
  message_id?: string;
  to?: string;
  message?: string;
  error?: string;
}

export async function sendSMS(to: string, body: string): Promise<SMSResponse> {
  try {
    const api = await getAuthenticatedApi();
    // Use WhatsApp API as primary, fallback to Vonage if needed
    return api.post<SMSResponse>('/whatsapp/send-message', { to, body });
  } catch (error) {
    console.error('WhatsApp sending error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to send WhatsApp message'
    };
  }
}

// Keep legacy function for backward compatibility
export async function sendVonageSMS(to: string, body: string): Promise<SMSResponse> {
  try {
    const api = await getAuthenticatedApi();
    return api.post<SMSResponse>('/vonage/send-sms', { to, body });
  } catch (error) {
    console.error('Vonage SMS sending error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to send SMS'
    };
  }
}
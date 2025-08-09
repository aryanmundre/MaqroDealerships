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
    return api.post<SMSResponse>('/vonage/send-sms', { to, body });
  } catch (error) {
    console.error('SMS sending error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to send SMS'
    };
  }
}
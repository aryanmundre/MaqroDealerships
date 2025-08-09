import { supabase } from './supabase';


// 1. Helper to get Supabase session
async function getSupabaseAuth() {
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error) {
    console.error('Error getting Supabase session:', error);
    return null;
  }
  if (!session) {
    console.warn('No active Supabase session found.');
    return null;
  }
  return session;
}

// 2. Main API client function
export async function getAuthenticatedApi() {
  const session = await getSupabaseAuth();
  
  if (!session?.access_token) {
    throw new Error('User not authenticated. Cannot make API calls.');
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`,
  };

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

  return {
    get: async <T>(endpoint: string): Promise<T> => {
      try {
        const response = await fetch(`${baseUrl}${endpoint}`, {
          method: 'GET',
          headers,
        });
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => response.statusText);
          console.error(`GET ${endpoint} failed:`, errorText);
          
          // Handle authentication errors specifically
          if (response.status === 401) {
            throw new Error('Authentication failed. Please log in again.');
          }
          
          throw new Error(`GET ${endpoint} failed: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
      } catch (error) {
        console.error(`Network error for GET ${endpoint}:`, error);
        throw error;
      }
    },
    post: async <T>(endpoint: string, body: any): Promise<T> => {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
        
        // Handle authentication errors specifically
        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        }
        
        throw new Error(`POST ${endpoint} failed: ${errorBody.detail}`);
      }
      return response.json();
    },
    put: async <T>(endpoint: string, body: any): Promise<T> => {
        const response = await fetch(`${baseUrl}${endpoint}`, {
          method: 'PUT',
          headers,
          body: JSON.stringify(body),
        });
        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
          
          // Handle authentication errors specifically
          if (response.status === 401) {
            throw new Error('Authentication failed. Please log in again.');
          }
          
          throw new Error(`PUT ${endpoint} failed: ${errorBody.detail}`);
        }
        return response.json();
      },
  
      delete: async <T>(endpoint: string): Promise<T> => {
        const response = await fetch(`${baseUrl}${endpoint}`, {
          method: 'DELETE',
          headers,
        });
        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
          
          // Handle authentication errors specifically
          if (response.status === 401) {
            throw new Error('Authentication failed. Please log in again.');
          }
          
          throw new Error(`DELETE ${endpoint} failed: ${errorBody.detail}`);
        }
        return response.json();
      },
  };
}

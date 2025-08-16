import { type Inventory } from './supabase';
import { getAuthenticatedApi } from './api-client';

export type InventoryUploadResult = {
  successCount: number;
  errorCount: number;
  embeddingsGenerated?: number; // New field for embedding count
  embeddingsError?: string | null; // New field for embedding errors
  errors: Array<{
    row: number;
    error: string;
  }>;
};

export type InventoryRow = {
  make: string;
  model: string;
  year: number;
  price: number | string; // Support both numbers and strings like "TBD"
  mileage?: number;
  description?: string;
  features?: string;
};

export const inventoryApi = {
  async getInventory(): Promise<Inventory[]> {
    const api = await getAuthenticatedApi();
    const result = await api.get<Inventory[]>('/inventory');
    return result;
  },

  async uploadInventory(file: File): Promise<InventoryUploadResult> {
    // Get authentication session for file upload
    const { supabase } = await import('./supabase');
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.access_token) {
      throw new Error('User not authenticated. Cannot upload file.');
    }

    const formData = new FormData();
    formData.append('file', file);

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';
    
    const response = await fetch(`${apiBaseUrl}/inventory/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        // Note: Don't set Content-Type for FormData - let browser set it with boundary
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      
      // Handle authentication errors specifically
      if (response.status === 401) {
        throw new Error('Authentication failed. Please log in again.');
      }
      
      throw new Error(errorData.detail);
    }

    const result = await response.json();
    
    return {
      successCount: result.success_count || 0,
      errorCount: result.error_count || 0,
      embeddingsGenerated: result.embeddings_generated || 0,
      embeddingsError: result.embeddings_error || null,
      errors: result.errors || []
    };
  },

  async deleteInventory(id: string): Promise<void> {
    const api = await getAuthenticatedApi();
    await api.delete<void>(`/inventory/${id}`);
  },

  async updateInventory(id: string, updates: Partial<Inventory>): Promise<Inventory> {
    const api = await getAuthenticatedApi();
    return api.put<Inventory>(`/inventory/${id}`, updates);
  },

  async getInventoryCount(): Promise<number> {
    const api = await getAuthenticatedApi();
    return api.get<number>('/inventory/count');
  },
};

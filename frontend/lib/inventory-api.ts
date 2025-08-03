import { type Inventory } from './supabase';
import { getAuthenticatedApi } from './api-client';

export type InventoryUploadResult = {
  successCount: number;
  errorCount: number;
  errors: Array<{
    row: number;
    error: string;
  }>;
};

export type InventoryRow = {
  make: string;
  model: string;
  year: number;
  price: number;
  mileage?: number;
  description?: string;
  features?: string;
};

export const inventoryApi = {
  async getInventory(): Promise<Inventory[]> {
    const api = await getAuthenticatedApi();
    return api.get<Inventory[]>('/inventory');
  },

  async uploadInventory(file: File): Promise<InventoryUploadResult> {
    const formData = new FormData();
    formData.append('file', file);

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';
    
    const response = await fetch(`${apiBaseUrl}/inventory/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(errorData.detail);
    }

    const result = await response.json();
    
    return {
      successCount: result.success_count || 0,
      errorCount: result.error_count || 0,
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

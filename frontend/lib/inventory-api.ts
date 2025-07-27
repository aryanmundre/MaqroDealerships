import { supabase, type Inventory } from './supabase';
import { inventoryValidation, type ValidationResult } from './inventory-validation';

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
  // Get all inventory for the current dealership
  async getInventory(): Promise<Inventory[]> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await supabase
      .from('inventory')
      .select('*')
      .eq('dealership_id', user.id)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  // Upload inventory in bulk
  async uploadInventory(inventoryRows: InventoryRow[]): Promise<InventoryUploadResult> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    // Validate inventory rows
    const validationResult: ValidationResult = inventoryValidation.validateInventoryRows(inventoryRows);
    
    const result: InventoryUploadResult = {
      successCount: 0,
      errorCount: validationResult.errors.length,
      errors: validationResult.errors
    };

    if (validationResult.validRows.length === 0) {
      return result;
    }

    // Add dealership_id to valid rows
    const validRows = validationResult.validRows.map(row => ({
      ...row,
      dealership_id: user.id,
      status: 'active'
    }));

    // Insert valid rows
    const { data, error } = await supabase
      .from('inventory')
      .insert(validRows)
      .select();

    if (error) {
      throw new Error(`Failed to upload inventory: ${error.message}`);
    }

    result.successCount = data?.length || 0;
    return result;
  },

  // Delete inventory item
  async deleteInventory(id: string): Promise<void> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { error } = await supabase
      .from('inventory')
      .delete()
      .eq('id', id)
      .eq('dealership_id', user.id);

    if (error) throw error;
  },

  // Update inventory item
  async updateInventory(id: string, updates: Partial<Inventory>): Promise<Inventory> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await supabase
      .from('inventory')
      .update(updates)
      .eq('id', id)
      .eq('dealership_id', user.id)
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  // Get inventory count
  async getInventoryCount(): Promise<number> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { count, error } = await supabase
      .from('inventory')
      .select('*', { count: 'exact', head: true })
      .eq('dealership_id', user.id);

    if (error) throw error;
    return count || 0;
  }
}; 
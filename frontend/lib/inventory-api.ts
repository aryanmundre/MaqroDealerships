import { supabase, type Inventory } from './supabase';

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

    const result: InventoryUploadResult = {
      successCount: 0,
      errorCount: 0,
      errors: []
    };

    // Validate each row
    const validRows: any[] = [];
    
    inventoryRows.forEach((row, index) => {
      const rowNumber = index + 1; // 1-based row numbers for user display
      
      // Validate required fields
      if (!row.make || !row.make.trim()) {
        result.errorCount++;
        result.errors.push({ row: rowNumber, error: 'Missing make' });
        return;
      }
      
      if (!row.model || !row.model.trim()) {
        result.errorCount++;
        result.errors.push({ row: rowNumber, error: 'Missing model' });
        return;
      }
      
      if (!row.year || isNaN(row.year) || row.year < 1900 || row.year > new Date().getFullYear() + 1) {
        result.errorCount++;
        result.errors.push({ row: rowNumber, error: 'Invalid year' });
        return;
      }
      
      if (!row.price || isNaN(row.price) || row.price <= 0) {
        result.errorCount++;
        result.errors.push({ row: rowNumber, error: 'Invalid price' });
        return;
      }

      // Add dealership_id to valid rows
      validRows.push({
        ...row,
        dealership_id: user.id,
        status: 'active'
      });
    });

    if (validRows.length === 0) {
      return result;
    }

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
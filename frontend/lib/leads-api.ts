import { supabase } from './supabase';
import type { Lead } from './supabase';

export async function getLeads(searchTerm?: string): Promise<Lead[]> {
  let query = supabase
    .from('leads')
    .select('*')
    .order('created_at', { ascending: false });

  // Add search functionality if searchTerm is provided
  if (searchTerm) {
    query = query.or(
      `name.ilike.%${searchTerm}%,car.ilike.%${searchTerm}%,source.ilike.%${searchTerm}%,status.ilike.%${searchTerm}%`
    );
  }

  const { data, error } = await query;

  if (error) {
    console.error('Error fetching leads:', error);
    throw new Error(`Error fetching leads: ${error.message}`);
  }

  return data || [];
}

export async function getLead(id: string): Promise<Lead | null> {
  const { data, error } = await supabase
    .from('leads')
    .select('*')
    .eq('id', id)
    .single();

  if (error) {
    console.error(`Error fetching lead ${id}:`, error);
    throw new Error(`Error fetching lead: ${error.message}`);
  }

  return data;
}

export async function createLead(lead: Omit<Lead, 'id' | 'created_at' | 'user_id'>): Promise<Lead> {
  // Get current user ID
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    throw new Error('User must be logged in to create a lead');
  }

  const { data, error } = await supabase
    .from('leads')
    .insert([{ ...lead, user_id: user.id }])
    .select()
    .single();

  if (error) {
    console.error('Error creating lead:', error);
    throw new Error(`Error creating lead: ${error.message}`);
  }

  return data;
}

export async function updateLead(id: string, updates: Partial<Lead>): Promise<Lead> {
  const { data, error } = await supabase
    .from('leads')
    .update(updates)
    .eq('id', id)
    .select()
    .single();

  if (error) {
    console.error(`Error updating lead ${id}:`, error);
    throw new Error(`Error updating lead: ${error.message}`);
  }

  return data;
}

export async function deleteLead(id: string): Promise<void> {
  const { error } = await supabase
    .from('leads')
    .delete()
    .eq('id', id);

  if (error) {
    console.error(`Error deleting lead ${id}:`, error);
    throw new Error(`Error deleting lead: ${error.message}`);
  }
}

export async function getLeadStats(): Promise<{
  total: number;
  byStatus: Record<string, number>;
}> {
  const { data, error } = await supabase
    .from('leads')
    .select('status');

  if (error) {
    console.error('Error fetching lead stats:', error);
    throw new Error(`Error fetching lead stats: ${error.message}`);
  }

  // Calculate stats
  const total = data.length;
  const byStatus = data.reduce((acc, lead) => {
    const status = lead.status;
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return { total, byStatus };
} 
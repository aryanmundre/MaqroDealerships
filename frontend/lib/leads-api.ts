import { getAuthenticatedApi } from './api-client';
import type { Lead } from './supabase';

export async function getLeads(searchTerm?: string): Promise<Lead[]> {
  const api = await getAuthenticatedApi();
  const endpoint = searchTerm ? `/leads?search=${searchTerm}` : '/leads';
  return api.get<Lead[]>(endpoint);
}

export async function getLeadById(id: string): Promise<Lead | null> {
  const api = await getAuthenticatedApi();
  return api.get<Lead | null>(`/leads/${id}`);
}

export async function createLead(lead: Omit<Lead, 'id' | 'created_at' | 'user_id'>): Promise<Lead> {
  const api = await getAuthenticatedApi();
  return api.post<Lead>('/leads', lead);
}

export async function updateLead(id: string, updates: Partial<Lead>): Promise<Lead> {
  const api = await getAuthenticatedApi();
  return api.put<Lead>(`/leads/${id}`, updates);
}

export async function deleteLead(id: string): Promise<void> {
  const api = await getAuthenticatedApi();
  await api.delete<void>(`/leads/${id}`);
}

export async function getLeadStats(): Promise<{
  total: number;
  by_status: Record<string, number>;
}> {
  const api = await getAuthenticatedApi();
  return api.get<{
    total: number;
    by_status: Record<string, number>;
  }>('/leads/stats');
}

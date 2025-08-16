import { getAuthenticatedApi } from './api-client';
import type { Conversation, Lead } from './supabase';

export async function getConversations(leadId: string): Promise<Conversation[]> {
  const api = await getAuthenticatedApi();
  return api.get<Conversation[]>(`/leads/${leadId}/conversations`);
}

export async function addMessage(leadId: string, message: string): Promise<Conversation> {
  const api = await getAuthenticatedApi();
  return api.post<Conversation>('/messages', { lead_id: leadId, message, sender: 'agent' });
}

export async function getLeadsWithConversations(opts: {
  scope?: 'mine' | 'dealership';
  dealershipId?: string;
  searchTerm?: string;
} = {}): Promise<LeadWithConversationSummary[]> {
  const { scope = 'mine', dealershipId, searchTerm } = opts;

  const api = await getAuthenticatedApi();

  // Use optimized endpoint for 'mine' scope to eliminate N+1 queries
  if (scope === 'mine') {
    // TODO: Add search support to the optimized endpoint
    if (searchTerm) {
      console.warn('Search not yet supported with optimized endpoint, falling back to old method');
      return getLeadsWithConversationsLegacy(opts);
    }
    
    // Single optimized API call that returns leads with conversation summaries
    return api.get<LeadWithConversationSummary[]>('/me/leads-with-conversations-summary');
  }

  // For dealership scope, fall back to the legacy method for now
  return getLeadsWithConversationsLegacy(opts);
}

// Legacy method kept for dealership scope and search functionality
async function getLeadsWithConversationsLegacy(opts: {
  scope?: 'mine' | 'dealership';
  dealershipId?: string;
  searchTerm?: string;
} = {}): Promise<LeadWithConversationSummary[]> {
  const { scope = 'mine', dealershipId, searchTerm } = opts;

  const api = await getAuthenticatedApi();

  /* ────────────────────────────────────────────────────────────────────────
     1. Figure out which lead list endpoint to hit
     ──────────────────────────────────────────────────────────────────────── */
  let leadsEndpoint: string;
  if (scope === 'mine') {
    leadsEndpoint = searchTerm
      ? `/me/leads?search=${encodeURIComponent(searchTerm)}`
      : '/me/leads';
  } else {
    if (!dealershipId)
      throw new Error('dealershipId is required when scope = "dealership"');
    leadsEndpoint = searchTerm
      ? `/dealerships/${dealershipId}/leads?search=${encodeURIComponent(
          searchTerm
        )}`
      : `/dealerships/${dealershipId}/leads`;
  }

  /* ────────────────────────────────────────────────────────────────────────
     2. Fetch leads, then enrich each one with its latest message
     ──────────────────────────────────────────────────────────────────────── */
  const leads = await api.get<Lead[]>(leadsEndpoint);

  const leadsWithConversations: LeadWithConversationSummary[] = await Promise.all(
    leads.map(async (lead) => {
      try {
        const conversations = await api.get<Conversation[]>(
          `/leads/${lead.id}/conversations`
        );

        const latest = conversations.at(-1); // last element or undefined
        return {
          id: lead.id,
          name: lead.name,
          car_interest: lead.car_interest ?? '',
          status: lead.status,
          email: lead.email,
          phone: lead.phone,
          lastMessage: latest?.message ?? 'No messages yet',
          lastMessageTime: latest
            ? formatTimeAgo(latest.created_at)
            : 'Never',
          unreadCount: 0, // TODO: compute from backend flag
          created_at: lead.created_at,
          conversationCount: conversations.length,
        };
      } catch (e) {
        console.error(`Failed to fetch conv for lead ${lead.id}`, e);
        return {
          id: lead.id,
          name: lead.name,
          car_interest: lead.car_interest ?? '',
          status: lead.status,
          email: lead.email,
          phone: lead.phone,
          lastMessage: 'Error loading messages',
          lastMessageTime: 'Unknown',
          unreadCount: 0,
          created_at: lead.created_at,
          conversationCount: 0,
        };
      }
    })
  );

  /* ────────────────────────────────────────────────────────────────────────
     3. Sort by most recent conversation
     ──────────────────────────────────────────────────────────────────────── */
  leadsWithConversations.sort((a, b) =>
    b.created_at.localeCompare(a.created_at)
  );

  return leadsWithConversations;
}


// Helper function to format time ago
function formatTimeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

// Type for the conversation list view
export type LeadWithConversationSummary = {
  id: string;
  name: string;
  car_interest: string;
  status: 'new' | 'warm' | 'hot' | 'follow-up' | 'cold' | 'deal_won' | 'deal_lost' | 'appointment_booked';
  email?: string;
  phone?: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  created_at: string;
  deal_value?: number;
  appointment_date?: string;
  conversationCount: number;
};

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

// New function to get leads with their conversation summaries
export async function getLeadsWithConversations(): Promise<LeadWithConversationSummary[]> {
  const api = await getAuthenticatedApi();
  // Get all leads first
  const leads = await api.get<Lead[]>('/leads');
  
  // For each lead, get their conversations to find the latest message
  const leadsWithConversations = await Promise.all(
    leads.map(async (lead) => {
      try {
        const conversations = await api.get<Conversation[]>(`/leads/${lead.id}/conversations`);
        // The backend returns conversations ordered by creation date, so the last one is the newest.
        const latestConversation = conversations.length > 0 
          ? conversations[conversations.length - 1] 
          : null;
        
        return {
          id: lead.id,
          name: lead.name,
          car: lead.car || '',
          status: lead.status,
          email: lead.email,
          phone: lead.phone,
          lastMessage: latestConversation?.message || 'No messages yet',
          lastMessageTime: latestConversation ? formatTimeAgo(latestConversation.created_at) : 'Never',
          unreadCount: 0, // TODO: Implement unread count logic
          created_at: lead.created_at,
          conversationCount: conversations.length
        };
      } catch (error) {
        console.error(`Error fetching conversations for lead ${lead.id}:`, error);
        return {
          id: lead.id,
          name: lead.name,
          car: lead.car || '',
          status: lead.status,
          email: lead.email,
          phone: lead.phone,
          lastMessage: 'Error loading messages',
          lastMessageTime: 'Unknown',
          unreadCount: 0,
          created_at: lead.created_at,
          conversationCount: 0
        };
      }
    })
  );
  
  // Sort leads by the most recent conversation
  leadsWithConversations.sort((a, b) => {
    if (a.lastMessageTime === 'Never') return 1;
    if (b.lastMessageTime === 'Never') return -1;
    if (a.lastMessageTime === 'Unknown') return 1;
    if (b.lastMessageTime === 'Unknown') return -1;
    // A simple sort that assumes `created_at` can be compared lexicographically
    return b.created_at.localeCompare(a.created_at);
  });
  
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
  car: string;
  status: 'new' | 'warm' | 'hot' | 'follow-up' | 'cold';
  email?: string;
  phone?: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  created_at: string;
  conversationCount: number;
};

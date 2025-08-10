import { createClient } from '@supabase/supabase-js';

// These environment variables need to be set in your .env.local file
// NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
// NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key';

if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
  console.warn('Missing Supabase environment variables. Check your .env.local file.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Type definitions for your Supabase tables
export type Lead = {
  id: string;
  created_at: string;
  name: string;
  car_interest: string;
  source: string;
  status: 'new' | 'warm' | 'hot' | 'follow-up' | 'cold' | 'deal_won' | 'deal_lost' | 'appointment_booked';
  last_contact_at: string;
  email?: string;
  phone?: string;
  message?: string;
  max_price?: string;
  user_id: string; // Foreign key to auth.users
  conversations?: Conversation[];
};

export type Inventory = {
  id: string;
  created_at: string;
  updated_at: string;
  make: string;
  model: string;
  year: number;
  price: number;
  mileage?: number;
  description?: string;
  features?: string;
  condition?: string;
  dealership_id: string; // Foreign key to auth.users
  status: 'active' | 'sold' | 'pending';
};

export type Conversation = {
  id: string;
  created_at: string;
  message: string;
  sender: 'customer' | 'agent'
  lead_id: string;
}

export type UserProfile ={
  id: string
  user_id: string
  dealership_id?: string | null
  full_name: string
  phone?: string
  role: string
  timezone: string
  created_at: string
  updated_at: string
}

// Helper function to check if user is logged in
export const isUserLoggedIn = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  return !!session;
};

// Helper function to get current user
export const getCurrentUser = async () => {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
};

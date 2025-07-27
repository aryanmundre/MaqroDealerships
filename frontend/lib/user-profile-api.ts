import { supabase } from './supabase';

export type UserProfile = {
  id: string;
  user_id: string;
  full_name: string | null;
  phone: string | null;
  role: string | null;
  timezone: string;
  created_at: string;
  updated_at: string;
};

// Test function to verify database setup
export async function testDatabaseConnection(): Promise<void> {
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    throw new Error('User must be logged in to test database connection');
  }

  console.log('Testing database connection for user:', user.id);

  // Test 1: Check if table exists
  const { data: tableTest, error: tableError } = await supabase
    .from('user_profiles')
    .select('count')
    .limit(1);

  if (tableError) {
    console.error('Table access error:', tableError);
    throw new Error(`Cannot access user_profiles table: ${tableError.message}`);
  }

  console.log('✅ Table access successful');

  // Test 2: Check RLS policies
  const { data: policyTest, error: policyError } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('user_id', user.id)
    .limit(1);

  if (policyError) {
    console.error('RLS policy error:', policyError);
    throw new Error(`RLS policy issue: ${policyError.message}`);
  }

  console.log('✅ RLS policies working correctly');
}

// Get current user's profile
export async function getUserProfile(): Promise<UserProfile | null> {
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    throw new Error('User must be logged in to get profile');
  }

  const { data, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('user_id', user.id)
    .single();

  if (error && error.code !== 'PGRST116') { // PGRST116 is "not found"
    console.error('Error fetching user profile:', error);
    throw new Error(`Error fetching user profile: ${error.message}`);
  }

  return data;
}

// Create or update user profile
export async function upsertUserProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    throw new Error('User must be logged in to update profile');
  }

  // Prepare the profile data
  const profileData = {
    user_id: user.id,
    full_name: profile.full_name || null,
    phone: profile.phone || null,
    role: profile.role || null,
    timezone: profile.timezone || 'America/New_York',
  };

  console.log('Attempting to upsert profile data:', profileData);

  // First, try to get existing profile
  const { data: existingProfile, error: fetchError } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('user_id', user.id)
    .single();

  if (fetchError && fetchError.code !== 'PGRST116') {
    console.error('Error fetching existing profile:', fetchError);
    throw new Error(`Error checking existing profile: ${fetchError.message}`);
  }

  let result;
  if (existingProfile) {
    // Update existing profile
    console.log('Updating existing profile');
    const { data, error } = await supabase
      .from('user_profiles')
      .update(profileData)
      .eq('user_id', user.id)
      .select()
      .single();

    if (error) {
      console.error('Error updating user profile:', error);
      throw new Error(`Error updating user profile: ${error.message}`);
    }
    result = data;
  } else {
    // Insert new profile
    console.log('Creating new profile');
    const { data, error } = await supabase
      .from('user_profiles')
      .insert(profileData)
      .select()
      .single();

    if (error) {
      console.error('Error creating user profile:', error);
      throw new Error(`Error creating user profile: ${error.message}`);
    }
    result = data;
  }

  return result;
}

// Change user password
export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    throw new Error('User must be logged in to change password');
  }

  // First, verify the current password by attempting to sign in
  const { error: signInError } = await supabase.auth.signInWithPassword({
    email: user.email!,
    password: currentPassword,
  });

  if (signInError) {
    throw new Error('Current password is incorrect');
  }

  // Update the password
  const { error } = await supabase.auth.updateUser({
    password: newPassword,
  });

  if (error) {
    console.error('Error changing password:', error);
    throw new Error(`Error changing password: ${error.message}`);
  }
}

// Get user profile with fallback to auth user data
export async function getUserProfileWithFallback(): Promise<{
  full_name: string;
  email: string;
  phone: string;
  role: string;
  timezone: string;
}> {
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    throw new Error('User must be logged in');
  }

  // Try to get profile from database
  const profile = await getUserProfile();
  
  // Return profile data with fallbacks to auth user data
  return {
    full_name: profile?.full_name || user.user_metadata?.name || 'User',
    email: user.email || '',
    phone: profile?.phone || '',
    role: profile?.role || 'User',
    timezone: profile?.timezone || 'America/New_York',
  };
} 
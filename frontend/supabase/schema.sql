-- Migration script for adding dealership functionality to existing database
-- This script is safe to run on existing databases with data

-- First, create the dealerships table if it doesn't exist
CREATE TABLE IF NOT EXISTS dealerships (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  name TEXT NOT NULL,
  location TEXT
);

-- Add dealership_id to user_profiles if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name = 'user_profiles' AND column_name = 'dealership_id') THEN
    ALTER TABLE user_profiles ADD COLUMN dealership_id UUID REFERENCES dealerships(id) ON DELETE CASCADE;
  END IF;
END $$;

-- Add new columns to leads table if they don't exist
DO $$ 
BEGIN
  -- Add dealership_id column
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name = 'leads' AND column_name = 'dealership_id') THEN
    ALTER TABLE leads ADD COLUMN dealership_id UUID REFERENCES dealerships(id) ON DELETE CASCADE;
  END IF;
  
  -- Add deal_value column
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name = 'leads' AND column_name = 'deal_value') THEN
    ALTER TABLE leads ADD COLUMN deal_value DECIMAL(10,2);
  END IF;
  
  -- Add appointment_datetime column
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name = 'leads' AND column_name = 'appointment_datetime') THEN
    ALTER TABLE leads ADD COLUMN appointment_datetime TIMESTAMP WITH TIME ZONE;
  END IF;
END $$;

-- Modify existing user_id column in leads to be nullable (for assigned salesperson)
DO $$
BEGIN
  -- First check if the constraint exists and drop it
  IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
             WHERE table_name = 'leads' AND constraint_name LIKE '%user_id%' AND constraint_type = 'FOREIGN KEY') THEN
    ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_user_id_fkey;
  END IF;
  
  -- Make user_id nullable
  ALTER TABLE leads ALTER COLUMN user_id DROP NOT NULL;
  
  -- Re-add the foreign key constraint with SET NULL on delete
  ALTER TABLE leads ADD CONSTRAINT leads_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
END $$;

-- Handle inventory dealership_id migration
DO $$
DECLARE
  sample_dealership_id UUID;
BEGIN
  -- Drop the old foreign key constraint first
  ALTER TABLE inventory DROP CONSTRAINT IF EXISTS inventory_dealership_id_fkey;
  
  -- Create a sample dealership if none exists
  IF NOT EXISTS (SELECT 1 FROM dealerships LIMIT 1) THEN
    INSERT INTO dealerships (name, location)
    VALUES ('Migrated Dealership', 'Migration Location')
    RETURNING id INTO sample_dealership_id;
  ELSE
    SELECT id INTO sample_dealership_id FROM dealerships LIMIT 1;
  END IF;
  
  -- Update all existing inventory records to use the sample dealership
  -- since the old dealership_id values were referencing auth.users
  UPDATE inventory SET dealership_id = sample_dealership_id;
  
  -- Now add the new foreign key constraint to dealerships table
  ALTER TABLE inventory ADD CONSTRAINT inventory_dealership_id_fkey 
    FOREIGN KEY (dealership_id) REFERENCES dealerships(id) ON DELETE CASCADE;
END $$;

-- Update leads status constraint to include new statuses
DO $$
BEGIN
  -- Drop existing check constraint if it exists
  ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_status_check;
  
  -- Add new check constraint with expanded statuses
  ALTER TABLE leads ADD CONSTRAINT leads_status_check 
    CHECK (status IN ('new', 'warm', 'hot', 'follow-up', 'cold', 'deal_won', 'deal_lost'));
END $$;

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS leads_dealership_id_idx ON leads(dealership_id);
CREATE INDEX IF NOT EXISTS user_profiles_dealership_id_idx ON user_profiles(dealership_id);

-- Enable Row Level Security on all tables
ALTER TABLE dealerships ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Drop all existing policies to recreate them with new dealership-based logic
DROP POLICY IF EXISTS "Users can view their own leads" ON leads;
DROP POLICY IF EXISTS "Users can insert their own leads" ON leads;
DROP POLICY IF EXISTS "Users can update their own leads" ON leads;
DROP POLICY IF EXISTS "Users can delete their own leads" ON leads;
DROP POLICY IF EXISTS "Users can view leads in their dealership" ON leads;
DROP POLICY IF EXISTS "Users can insert leads for their dealership" ON leads;
DROP POLICY IF EXISTS "Users can update leads in their dealership" ON leads;
DROP POLICY IF EXISTS "Users can delete leads in their dealership" ON leads;

-- Create new dealership-based policies for leads
CREATE POLICY "Users can view leads in their dealership"
  ON leads
  FOR SELECT
  USING (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can insert leads for their dealership"
  ON leads
  FOR INSERT
  WITH CHECK (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can update leads in their dealership"
  ON leads
  FOR UPDATE
  USING (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can delete leads in their dealership"
  ON leads
  FOR DELETE
  USING (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

-- Drop existing inventory policies
DROP POLICY IF EXISTS "Dealerships can view their own inventory" ON inventory;
DROP POLICY IF EXISTS "Dealerships can insert their own inventory" ON inventory;
DROP POLICY IF EXISTS "Dealerships can update their own inventory" ON inventory;
DROP POLICY IF EXISTS "Dealerships can delete their own inventory" ON inventory;
DROP POLICY IF EXISTS "Users can view inventory for their dealership" ON inventory;
DROP POLICY IF EXISTS "Users can insert inventory for their dealership" ON inventory;
DROP POLICY IF EXISTS "Users can update inventory for their dealership" ON inventory;
DROP POLICY IF EXISTS "Users can delete inventory for their dealership" ON inventory;

-- Create new dealership-based policies for inventory
CREATE POLICY "Users can view inventory for their dealership"
  ON inventory
  FOR SELECT
  USING (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can insert inventory for their dealership"
  ON inventory
  FOR INSERT
  WITH CHECK (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can update inventory for their dealership"
  ON inventory
  FOR UPDATE
  USING (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can delete inventory for their dealership"
  ON inventory
  FOR DELETE
  USING (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

-- Drop existing user_profiles policies
DROP POLICY IF EXISTS "Users can view their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can delete their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can view profiles in their dealership" ON user_profiles;

-- Create new policies for user_profiles
CREATE POLICY "Users can view profiles in their dealership"
  ON user_profiles
  FOR SELECT
  USING (dealership_id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can insert their own profile"
  ON user_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
  ON user_profiles
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own profile"
  ON user_profiles
  FOR DELETE
  USING (auth.uid() = user_id);

-- Create dealership policies
DROP POLICY IF EXISTS "Users can view their own dealership" ON dealerships;

CREATE POLICY "Users can view their own dealership"
  ON dealerships
  FOR SELECT
  USING (id = (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid()));

-- Drop existing conversation policies
DROP POLICY IF EXISTS "Users can manage conversations for their leads" ON conversations;
DROP POLICY IF EXISTS "Users can manage conversations for their dealership leads" ON conversations;

-- Create new conversation policies
CREATE POLICY "Users can manage conversations for their dealership leads"
  ON conversations
  FOR ALL
  USING (
    (SELECT dealership_id FROM leads WHERE id = conversations.lead_id) = 
    (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid())
  )
  WITH CHECK (
    (SELECT dealership_id FROM leads WHERE id = conversations.lead_id) = 
    (SELECT dealership_id FROM public.user_profiles WHERE user_id = auth.uid())
  );

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing triggers
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
DROP TRIGGER IF EXISTS update_inventory_updated_at ON inventory;
DROP TRIGGER IF EXISTS update_dealerships_updated_at ON dealerships;

-- Create triggers for updated_at columns
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inventory_updated_at 
    BEFORE UPDATE ON inventory 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dealerships_updated_at 
    BEFORE UPDATE ON dealerships 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Complete the migration by setting up user profiles and updating remaining data
DO $$
DECLARE
  sample_dealership_id UUID;
  sample_user_id UUID;
BEGIN
  -- Get the dealership (should exist from previous migration steps)
  SELECT id INTO sample_dealership_id FROM dealerships LIMIT 1;
  
  -- Get the first user ID from auth.users (for testing purposes)
  SELECT id INTO sample_user_id FROM auth.users LIMIT 1;
  
  -- Create user profile linked to dealership (only if user exists and doesn't have profile)
  IF sample_user_id IS NOT NULL AND sample_dealership_id IS NOT NULL 
     AND NOT EXISTS (SELECT 1 FROM user_profiles WHERE user_id = sample_user_id) THEN
    INSERT INTO user_profiles (user_id, dealership_id, full_name, role)
    VALUES (sample_user_id, sample_dealership_id, 'Demo User', 'salesperson');
  END IF;
  
  -- Update existing leads to belong to the sample dealership (if they don't have one)
  IF sample_dealership_id IS NOT NULL THEN
    UPDATE leads 
    SET dealership_id = sample_dealership_id 
    WHERE dealership_id IS NULL;
  END IF;
END
$$;

-- Make dealership_id NOT NULL for leads after migration
DO $$
BEGIN
  -- Only make it NOT NULL if there are no NULL values
  IF NOT EXISTS (SELECT 1 FROM leads WHERE dealership_id IS NULL) THEN
    ALTER TABLE leads ALTER COLUMN dealership_id SET NOT NULL;
  END IF;
END $$;

-- Make dealership_id NOT NULL for inventory after migration  
DO $$
BEGIN
  -- Only make it NOT NULL if there are no NULL values
  IF NOT EXISTS (SELECT 1 FROM inventory WHERE dealership_id IS NULL) THEN
    ALTER TABLE inventory ALTER COLUMN dealership_id SET NOT NULL;
  END IF;
END $$;
-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  name TEXT NOT NULL,
  car TEXT NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('new', 'warm', 'hot', 'follow-up', 'cold')),
  last_contact TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  message TEXT,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  full_name TEXT,
  phone TEXT,
  role TEXT,
  timezone TEXT DEFAULT 'America/New_York',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS leads_user_id_idx ON leads(user_id);
CREATE INDEX IF NOT EXISTS leads_status_idx ON leads(status);
CREATE INDEX IF NOT EXISTS user_profiles_user_id_idx ON user_profiles(user_id);

-- Enable Row Level Security
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies for leads (if they exist)
DROP POLICY IF EXISTS "Users can view their own leads" ON leads;
DROP POLICY IF EXISTS "Users can insert their own leads" ON leads;
DROP POLICY IF EXISTS "Users can update their own leads" ON leads;
DROP POLICY IF EXISTS "Users can delete their own leads" ON leads;

-- Create policies for leads
-- 1. Users can view their own leads
CREATE POLICY "Users can view their own leads"
  ON leads
  FOR SELECT
  USING (auth.uid() = user_id);

-- 2. Users can insert their own leads
CREATE POLICY "Users can insert their own leads"
  ON leads
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- 3. Users can update their own leads
CREATE POLICY "Users can update their own leads"
  ON leads
  FOR UPDATE
  USING (auth.uid() = user_id);

-- 4. Users can delete their own leads
CREATE POLICY "Users can delete their own leads"
  ON leads
  FOR DELETE
  USING (auth.uid() = user_id);

-- Drop existing policies for user_profiles (if they exist)
DROP POLICY IF EXISTS "Users can view their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can delete their own profile" ON user_profiles;

-- Create policies for user_profiles
-- 1. Users can view their own profile
CREATE POLICY "Users can view their own profile"
  ON user_profiles
  FOR SELECT
  USING (auth.uid() = user_id);

-- 2. Users can insert their own profile
CREATE POLICY "Users can insert their own profile"
  ON user_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- 3. Users can update their own profile
CREATE POLICY "Users can update their own profile"
  ON user_profiles
  FOR UPDATE
  USING (auth.uid() = user_id);

-- 4. Users can delete their own profile
CREATE POLICY "Users can delete their own profile"
  ON user_profiles
  FOR DELETE
  USING (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;

-- Create trigger for user_profiles
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing (only runs if leads table is empty)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM leads LIMIT 1) THEN
    -- Get the first user ID from auth.users (for testing purposes)
    INSERT INTO leads (name, car, source, status, last_contact, user_id)
    SELECT
      'Sarah Johnson',
      '2019 Honda Civic',
      'Website',
      'warm',
      '2 hours ago',
      id
    FROM auth.users
    LIMIT 1;
    
    INSERT INTO leads (name, car, source, status, last_contact, user_id)
    SELECT
      'Mike Chen',
      '2021 Toyota Camry',
      'Facebook',
      'hot',
      '30 minutes ago',
      id
    FROM auth.users
    LIMIT 1;
    
    INSERT INTO leads (name, car, source, status, last_contact, user_id)
    SELECT
      'Emily Davis',
      '2020 BMW X3',
      'Instagram',
      'new',
      'Just now',
      id
    FROM auth.users
    LIMIT 1;
  END IF;
END
$$; 
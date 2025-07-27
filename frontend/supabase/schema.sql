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

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS leads_user_id_idx ON leads(user_id);
CREATE INDEX IF NOT EXISTS leads_status_idx ON leads(status);

-- Enable Row Level Security
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create policies
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
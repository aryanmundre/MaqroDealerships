-- Migration: Allow 'system' as valid sender in conversations table
-- Date: 2025-08-10
-- Description: Update conversations sender check constraint to allow 'system' sender
-- This fixes the error: new row for relation "conversations" violates check constraint "conversations_sender_check"

-- Start transaction
BEGIN;

-- Drop the existing check constraint
ALTER TABLE conversations 
DROP CONSTRAINT conversations_sender_check;

-- Add new check constraint that allows 'customer', 'agent', and 'system'
ALTER TABLE conversations 
ADD CONSTRAINT conversations_sender_check 
CHECK (sender = ANY (ARRAY['customer'::text, 'agent'::text, 'system'::text]));

-- Add comment to document the valid sender values
COMMENT ON COLUMN conversations.sender IS 'Message sender type: customer, agent, or system';

-- Commit transaction
COMMIT;
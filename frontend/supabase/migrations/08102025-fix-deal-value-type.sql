-- Migration: Fix deal_value column type mismatch
-- Date: 2025-08-10
-- Description: Convert deal_value column from NUMERIC to TEXT to match SQLAlchemy String type
-- This fixes the error: column "deal_value" is of type numeric but expression is of type character varying

-- Start transaction
BEGIN;

-- Convert deal_value column from NUMERIC to TEXT to allow flexible values like "TBD", "25000", "$25K", etc.
ALTER TABLE leads 
ALTER COLUMN deal_value TYPE TEXT;

-- Add comment to document the column
COMMENT ON COLUMN leads.deal_value IS 'Deal value (stored as text for flexibility: "25000", "$25K", "TBD", etc.)';

-- Commit transaction
COMMIT;
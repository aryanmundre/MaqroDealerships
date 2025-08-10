-- Migration: Add max_price to leads, rename car to car_interest, add condition to inventory
-- Date: 2025-08-10
-- Description: 
-- 1. Add max_price column to leads table for price range tracking
-- 2. Rename car column to car_interest in leads table for better semantics (can include type like sedan)
-- 3. Add condition column to inventory table for vehicle condition tracking

-- Start transaction
BEGIN;

-- 1. Add max_price column to leads table
ALTER TABLE leads 
ADD COLUMN max_price TEXT;

-- 2. Rename car column to car_interest in leads table
ALTER TABLE leads 
RENAME COLUMN car TO car_interest;

-- 3. Add condition column to inventory table
ALTER TABLE inventory 
ADD COLUMN condition TEXT;

-- 4. Convert price column from DECIMAL/NUMERIC to TEXT to allow flexible pricing like "TBD", "Call for price", etc.
ALTER TABLE inventory 
ALTER COLUMN price TYPE TEXT;

-- Update any existing NULL car_interest values to 'Unknown' for consistency
UPDATE leads 
SET car_interest = 'Unknown' 
WHERE car_interest IS NULL;

-- Update any existing NULL condition values to 'Unknown' for consistency
UPDATE inventory 
SET condition = 'Unknown' 
WHERE condition IS NULL;

-- Add comments to document the new columns
COMMENT ON COLUMN leads.max_price IS 'Maximum price range for the lead (stored as text for flexibility: "25000", "25K", "TBD", etc.)';
COMMENT ON COLUMN leads.car_interest IS 'Type of car the lead is interested in (can include type like "Toyota Camry sedan" or just "sedan")';
COMMENT ON COLUMN inventory.condition IS 'Physical condition of the vehicle (excellent, good, fair, poor, etc.)';
COMMENT ON COLUMN inventory.price IS 'Vehicle price (stored as text for flexibility: "25000", "TBD", "Call for price", etc.)';

-- Commit transaction
COMMIT;
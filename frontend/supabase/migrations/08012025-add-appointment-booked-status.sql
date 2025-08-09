/* ────────────────────────────────────────────────────────────────
   Add appointment_booked status to leads table
   ──────────────────────────────────────────────────────────────── */
DO $$
BEGIN
  -- Drop existing check constraint if it exists
  ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_status_check;
  
  -- Add new check constraint with appointment_booked status included
  ALTER TABLE leads ADD CONSTRAINT leads_status_check 
    CHECK (status IN ('new', 'warm', 'hot', 'follow-up', 'cold', 'appointment_booked', 'deal_won', 'deal_lost'));
END $$;

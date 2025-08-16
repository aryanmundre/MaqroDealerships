/* ────────────────────────────────────────────────────────────────
   1. Add canonical timestamp column on leads
   ──────────────────────────────────────────────────────────────── */
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'leads' AND column_name = 'last_contact_at'
  ) THEN
    ALTER TABLE leads
      ADD COLUMN last_contact_at TIMESTAMPTZ;          -- nullable during back-fill
  END IF;
END $$;

/* ────────────────────────────────────────────────────────────────
   2. One-time back-fill from conversations
   ──────────────────────────────────────────────────────────────── */
UPDATE leads l
SET    last_contact_at = c.latest
FROM  (SELECT lead_id, MAX(created_at) AS latest
       FROM   conversations
       GROUP  BY lead_id) c
WHERE  l.id = c.lead_id
  AND  l.last_contact_at IS NULL;      -- idempotent

/* Optional: initialise untouched leads with their own created_at  */
UPDATE leads
SET    last_contact_at = created_at
WHERE  last_contact_at IS NULL;

/* ────────────────────────────────────────────────────────────────
   3. Make the column not-null & (optionally) drop text column
   ──────────────────────────────────────────────────────────────── */
ALTER TABLE leads
  ALTER COLUMN last_contact_at SET NOT NULL;

--   If you still need the old string column for a short time,
--     comment out the next two lines and remove them later.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'leads' AND column_name = 'last_contact'
  ) THEN
    ALTER TABLE leads DROP COLUMN last_contact;
  END IF;
END $$;

/* ────────────────────────────────────────────────────────────────
   4. Keep it in sync: trigger bumps the timestamp on every message
   ──────────────────────────────────────────────────────────────── */
CREATE OR REPLACE FUNCTION bump_last_contact() RETURNS TRIGGER AS $$
BEGIN
  UPDATE leads
  SET    last_contact_at = NEW.created_at
  WHERE  id = NEW.lead_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS conversations_bump_lead ON conversations;

CREATE TRIGGER conversations_bump_lead
AFTER INSERT OR UPDATE ON conversations
FOR EACH ROW
EXECUTE FUNCTION bump_last_contact();

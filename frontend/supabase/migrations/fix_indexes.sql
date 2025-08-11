-- Fix pgvector indexes - Remove problematic composite index
-- Run this in Supabase SQL Editor

-- 1. Drop the problematic composite index
DROP INDEX IF EXISTS vehicle_embeddings_dealership_embedding_idx;

-- 2. Keep the essential indexes (these work fine)
-- The vector similarity index (already exists)
-- CREATE INDEX vehicle_embeddings_embedding_idx ON vehicle_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- The dealership filter index (already exists)  
-- CREATE INDEX vehicle_embeddings_dealership_id_idx ON vehicle_embeddings (dealership_id);

-- The inventory lookup index (already exists)
-- CREATE INDEX vehicle_embeddings_inventory_id_idx ON vehicle_embeddings (inventory_id);

-- 3. Verify indexes are working
SELECT indexname, tablename FROM pg_indexes WHERE tablename = 'vehicle_embeddings';

-- 4. Test that we can insert now
-- (This will be tested when you restart your server)
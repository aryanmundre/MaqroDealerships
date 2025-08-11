-- pgVector RAG System Setup for Supabase
-- Run this in Supabase Dashboard -> SQL Editor

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create vehicle embeddings table
CREATE TABLE IF NOT EXISTS vehicle_embeddings (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    inventory_id uuid NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    embedding vector(1536), -- OpenAI ada-002 embedding size (1536 dimensions)
    formatted_text text NOT NULL, -- The text that was embedded for debugging
    dealership_id uuid NOT NULL REFERENCES dealerships(id), -- For fast filtering
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- 3. Create indexes for fast similarity search
CREATE INDEX IF NOT EXISTS vehicle_embeddings_embedding_idx 
ON vehicle_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 4. Create index for fast inventory lookups
CREATE INDEX IF NOT EXISTS vehicle_embeddings_inventory_id_idx 
ON vehicle_embeddings (inventory_id);

-- 5. Create index for dealership filtering
CREATE INDEX IF NOT EXISTS vehicle_embeddings_dealership_id_idx 
ON vehicle_embeddings (dealership_id);

-- 6. Create composite index for dealership + similarity search
CREATE INDEX IF NOT EXISTS vehicle_embeddings_dealership_embedding_idx 
ON vehicle_embeddings (dealership_id) INCLUDE (embedding);

-- 7. Add RLS (Row Level Security) policies to match existing tables
ALTER TABLE vehicle_embeddings ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access embeddings for their dealership
CREATE POLICY "Users can view embeddings for their dealership" 
ON vehicle_embeddings FOR SELECT 
USING (
    dealership_id IN (
        SELECT dealership_id FROM user_profiles 
        WHERE user_id = auth.uid()
    )
);

-- Policy: Users can insert embeddings for their dealership
CREATE POLICY "Users can insert embeddings for their dealership" 
ON vehicle_embeddings FOR INSERT 
WITH CHECK (
    dealership_id IN (
        SELECT dealership_id FROM user_profiles 
        WHERE user_id = auth.uid()
    )
);

-- Policy: Users can update embeddings for their dealership
CREATE POLICY "Users can update embeddings for their dealership" 
ON vehicle_embeddings FOR UPDATE 
USING (
    dealership_id IN (
        SELECT dealership_id FROM user_profiles 
        WHERE user_id = auth.uid()
    )
);

-- Policy: Users can delete embeddings for their dealership
CREATE POLICY "Users can delete embeddings for their dealership" 
ON vehicle_embeddings FOR DELETE 
USING (
    dealership_id IN (
        SELECT dealership_id FROM user_profiles 
        WHERE user_id = auth.uid()
    )
);

-- 8. Create function to sync embeddings when inventory changes
CREATE OR REPLACE FUNCTION sync_vehicle_embeddings()
RETURNS TRIGGER AS $$
BEGIN
    -- When inventory is updated, mark embeddings as needing refresh
    -- (The application will handle regenerating embeddings)
    IF TG_OP = 'UPDATE' THEN
        UPDATE vehicle_embeddings 
        SET updated_at = now() 
        WHERE inventory_id = NEW.id;
        RETURN NEW;
    END IF;
    
    -- When inventory is deleted, clean up embeddings
    IF TG_OP = 'DELETE' THEN
        DELETE FROM vehicle_embeddings WHERE inventory_id = OLD.id;
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 9. Create trigger to automatically sync embeddings
CREATE TRIGGER sync_embeddings_on_inventory_change
    AFTER UPDATE OR DELETE ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION sync_vehicle_embeddings();

-- 10. Verification queries (optional - run these to test)
-- SELECT * FROM pg_extension WHERE extname = 'vector';
-- SELECT COUNT(*) FROM vehicle_embeddings;
-- SELECT COUNT(*) FROM inventory;

COMMENT ON TABLE vehicle_embeddings IS 'Stores vector embeddings for inventory items for RAG similarity search';
COMMENT ON COLUMN vehicle_embeddings.embedding IS 'OpenAI ada-002 1536-dimension embedding vector';
COMMENT ON COLUMN vehicle_embeddings.formatted_text IS 'The formatted text that was embedded (for debugging)';
COMMENT ON INDEX vehicle_embeddings_embedding_idx IS 'IVFFlat index for fast cosine similarity search';
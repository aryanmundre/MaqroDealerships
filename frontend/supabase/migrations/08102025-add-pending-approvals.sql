-- Add pending_approvals table for RAG response verification workflow
-- This table tracks when salespeople need to approve/reject RAG responses before sending to customers

CREATE TABLE public.pending_approvals (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    lead_id uuid NOT NULL,
    user_id uuid NOT NULL,
    customer_message text NOT NULL,
    generated_response text NOT NULL,
    customer_phone text NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, 'expired'::text])),
    dealership_id uuid NOT NULL,
    expires_at timestamp with time zone DEFAULT (now() + INTERVAL '1 hour'),
    CONSTRAINT pending_approvals_pkey PRIMARY KEY (id),
    CONSTRAINT pending_approvals_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE,
    CONSTRAINT pending_approvals_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT pending_approvals_dealership_id_fkey FOREIGN KEY (dealership_id) REFERENCES public.dealerships(id) ON DELETE CASCADE
);

-- Index for quick lookups by user_id (most common query)
CREATE INDEX idx_pending_approvals_user_id ON public.pending_approvals(user_id);

-- Index for cleanup of expired approvals
CREATE INDEX idx_pending_approvals_status_expires ON public.pending_approvals(status, expires_at);

-- Index for lead-specific lookups
CREATE INDEX idx_pending_approvals_lead_id ON public.pending_approvals(lead_id);

-- Ensure only one pending approval per user at a time (business rule)
CREATE UNIQUE INDEX idx_pending_approvals_user_pending ON public.pending_approvals(user_id) 
WHERE status = 'pending';

COMMENT ON TABLE public.pending_approvals IS 'Tracks RAG responses awaiting salesperson approval before sending to customers';
COMMENT ON COLUMN public.pending_approvals.customer_message IS 'Original message from customer that triggered the RAG response';
COMMENT ON COLUMN public.pending_approvals.generated_response IS 'AI-generated response awaiting approval';
COMMENT ON COLUMN public.pending_approvals.customer_phone IS 'Customer phone number (denormalized for quick access)';
COMMENT ON COLUMN public.pending_approvals.expires_at IS 'When this approval request expires (default 1 hour)';
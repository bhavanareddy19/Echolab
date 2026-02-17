-- =============================================================================
-- MIGRATION: Add Ticket Resolution Tracking
-- =============================================================================
-- This migration adds columns to track which experiments resolve which tickets
-- Allows automatic ticket resolution when experiments complete successfully
-- =============================================================================

-- Add experiment tracking columns to core.tickets
ALTER TABLE core.tickets
ADD COLUMN IF NOT EXISTS experiment_id INTEGER REFERENCES analytics.hypotheses(id),
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resolved_by_experiment INTEGER REFERENCES analytics.hypotheses(id),
ADD COLUMN IF NOT EXISTS resolution_notes TEXT;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_tickets_experiment ON core.tickets(experiment_id);
CREATE INDEX IF NOT EXISTS idx_tickets_resolved ON core.tickets(resolved_at) WHERE resolved_at IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN core.tickets.experiment_id IS 'Links ticket to experiment testing a fix for its pain point';
COMMENT ON COLUMN core.tickets.resolved_at IS 'When ticket was marked as resolved';
COMMENT ON COLUMN core.tickets.resolved_by_experiment IS 'Which experiment successfully resolved this ticket';
COMMENT ON COLUMN core.tickets.resolution_notes IS 'Notes about how the ticket was resolved';

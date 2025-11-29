-- Add is_finalized column to track whether an event has been auto-finalized
-- This prevents race conditions where ended events disappear from get_active_event()
-- Using INTEGER (0 = not finalized, 1 = finalized) for better readability

ALTER TABLE events 
ADD COLUMN is_finalized INTEGER DEFAULT 0;

-- Set existing events as finalized (if they exist)
UPDATE events SET is_finalized = 1;

-- Add index for faster queries
CREATE INDEX idx_events_is_finalized ON events(is_finalized);

-- Add constraint to ensure only 0 or 1 values
ALTER TABLE events ADD CONSTRAINT check_is_finalized CHECK (is_finalized IN (0, 1));

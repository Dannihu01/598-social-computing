-- Migrate events table from day_duration to duration_minutes
-- This converts existing day_duration values to minutes (day * 1440)

-- Step 1: Add new column
ALTER TABLE events ADD COLUMN duration_minutes INTEGER;

-- Step 2: Copy existing data (convert days to minutes: 1 day = 1440 minutes)
UPDATE events SET duration_minutes = day_duration * 1440 WHERE day_duration IS NOT NULL;

-- Step 3: Drop old column
ALTER TABLE events DROP COLUMN day_duration;

-- Step 4: Set default value for new events (default: 60 minutes = 1 hour)
ALTER TABLE events ALTER COLUMN duration_minutes SET DEFAULT 60;

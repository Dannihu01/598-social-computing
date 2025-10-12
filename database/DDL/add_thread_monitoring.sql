-- Track threads being monitored
CREATE TABLE monitored_threads (
    thread_ts           TEXT PRIMARY KEY,
    channel_id          TEXT NOT NULL,
    original_message    TEXT,
    started_at          TIMESTAMPTZ DEFAULT NOW(),
    last_activity       TIMESTAMPTZ,
    message_count       INTEGER DEFAULT 0,
    bot_intervened      BOOLEAN DEFAULT FALSE,
    intervention_type   TEXT,
    topic_summary       TEXT,
    related_event_id    TEXT REFERENCES events(id),
    metadata            JSONB
);

-- Track participant engagement in threads
CREATE TABLE thread_participants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_ts           TEXT REFERENCES monitored_threads(thread_ts) ON DELETE CASCADE,
    user_id             UUID REFERENCES users(uuid),  
    slack_id            TEXT NOT NULL,
    message_count       INTEGER DEFAULT 0,
    reaction_count      INTEGER DEFAULT 0,
    first_engaged       TIMESTAMPTZ DEFAULT NOW(),
    last_engaged        TIMESTAMPTZ,
    engagement_score    INTEGER DEFAULT 0,
    UNIQUE(thread_ts, user_id)
);

-- Track bot interventions
CREATE TABLE bot_interventions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_thread_ts    TEXT REFERENCES monitored_threads(thread_ts),
    intervention_type   TEXT NOT NULL,
    target_user_ids     UUID[],
    target_slack_ids    TEXT[],
    channel_id          TEXT,
    new_thread_ts       TEXT,
    content             TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    successful          BOOLEAN DEFAULT TRUE,
    related_event_id    TEXT REFERENCES events(id)  
);

-- Indexes for performance
CREATE INDEX idx_monitored_threads_active ON monitored_threads(last_activity DESC) WHERE NOT bot_intervened;
CREATE INDEX idx_monitored_threads_event ON monitored_threads(related_event_id);  
CREATE INDEX idx_thread_participants_thread ON thread_participants(thread_ts, engagement_score DESC);
CREATE INDEX idx_thread_participants_user ON thread_participants(user_id);
CREATE INDEX idx_bot_interventions_thread ON bot_interventions(source_thread_ts);
CREATE INDEX idx_bot_interventions_event ON bot_interventions(related_event_id);  
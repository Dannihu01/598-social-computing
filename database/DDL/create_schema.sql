-- 1. ENUM Type for sys_messages.type
CREATE TYPE sys_message_type AS ENUM ('private', 'aggregated');

-- 2. Users Table
CREATE TABLE users (
    uuid        UUID PRIMARY KEY,
    slack_id    TEXT UNIQUE
);

-- 3. Events Table
CREATE TABLE events (
    id              TEXT PRIMARY KEY,
    time_start      TIMESTAMPTZ,
    day_duration    INTEGER
);

-- 4. Sys Messages Table
CREATE TABLE sys_messages (
    id          TEXT PRIMARY KEY,
    type        sys_message_type,
    content     TEXT
);

-- 5. Responses Table
CREATE TABLE responses (
    id              TEXT PRIMARY KEY,
    entry           TEXT,
    submitted_at    TIMESTAMPTZ,
    user_id         UUID REFERENCES users(uuid) ON DELETE CASCADE,
    event_id        TEXT REFERENCES events(id) ON DELETE CASCADE
);

-- 6. Event Messaging Table (Linking Table with Composite PK)
CREATE TABLE event_messaging (
    event_id        TEXT REFERENCES events(id) ON DELETE CASCADE,
    sys_message_id  TEXT REFERENCES sys_messages(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, sys_message_id)
);

-- (Optional) Indexes for performance
CREATE INDEX idx_responses_user_id ON responses(user_id);
CREATE INDEX idx_responses_event_id ON responses(event_id);
CREATE INDEX idx_event_messaging_sys_message_id ON event_messaging(sys_message_id);
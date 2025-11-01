-- Drop existing tables (in reverse dependency order)
DROP TABLE IF EXISTS bot_interventions;
DROP TABLE IF EXISTS thread_participants;
DROP TABLE IF EXISTS monitored_threads;
DROP TABLE IF EXISTS event_messaging;
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS sys_messages;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS slack_enterprises;
DROP TYPE IF EXISTS sys_message_type;

-- 1. ENUM Type for sys_messages.type and users.role
CREATE TYPE sys_message_type AS ENUM ('private', 'aggregated');
CREATE TYPE user_role_type AS ENUM ('USER', 'ADMIN');

-- 2. Users Table
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    slack_id    TEXT,
    role        user_role_type
);

-- 3. Events Table (with SERIAL ID)
CREATE TABLE events (
    id              SERIAL PRIMARY KEY,
    time_start      TIMESTAMPTZ,
    day_duration    INTEGER
);

-- 4. Sys Messages Table (with SERIAL ID)
CREATE TABLE sys_messages (
    id          SERIAL PRIMARY KEY,
    type        sys_message_type,
    content     TEXT
);

-- 5. Responses Table (with SERIAL ID)
CREATE TABLE responses (
    id              SERIAL PRIMARY KEY,
    entry           TEXT,
    submitted_at    TIMESTAMPTZ,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_id        INTEGER REFERENCES events(id) ON DELETE CASCADE
);

-- 6. Event Messaging Table (Linking Table with Composite PK)
CREATE TABLE event_messaging (
    event_id        INTEGER REFERENCES events(id) ON DELETE CASCADE,
    sys_message_id  INTEGER REFERENCES sys_messages(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, sys_message_id)
);

-- 7. Slack Enterprise Table
CREATE TABLE slack_enterprises (
    id              SERIAL PRIMARY KEY,
    enterprise_name TEXT NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);


-- (Optional) Indexes for performance
CREATE INDEX idx_responses_user_id ON responses(user_id);
CREATE INDEX idx_responses_event_id ON responses(event_id);
CREATE INDEX idx_event_messaging_sys_message_id ON event_messaging(sys_message_id);
CREATE INDEX idx_slack_enterprises_name ON slack_enterprises(enterprise_name);
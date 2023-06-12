-- DROP tables if they exist
DROP TABLE IF EXISTS interaction_messages;
DROP TABLE IF EXISTS interaction;
DROP TABLE IF EXISTS message_embedding;
DROP TABLE IF EXISTS message_file;
DROP TABLE IF EXISTS message;
-- Extensions
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- Tables
CREATE TABLE IF NOT EXISTS message (
    id VARCHAR(32) PRIMARY KEY,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    name VARCHAR(32),
    n_tokens INT NOT NULL
);
CREATE TABLE IF NOT EXISTS message_embedding (
    msg_id VARCHAR(32),
    embedding vector(1536) NOT NULL,
    CONSTRAINT pk_message_embedding PRIMARY KEY (msg_id),
    CONSTRAINT fk_message_embedding_msg_id FOREIGN KEY (msg_id) REFERENCES message (id)
);
CREATE TABLE IF NOT EXISTS message_file (
    msg_id VARCHAR(32),
    file_name VARCHAR(64),
    -- file_size_bytes INT NOT NULL, -- size in bytes
    -- file_length_sec DECIMAL NOT NULL, -- length in seconds
    -- file_sr_hz INT NOT NULL, -- sampling rate in Hz
    CONSTRAINT pk_message_file PRIMARY KEY (msg_id),
    CONSTRAINT fk_message_file_msg_id FOREIGN KEY (msg_id) REFERENCES message (id)
);
CREATE TABLE IF NOT EXISTS interaction (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP(0)
);
CREATE TABLE IF NOT EXISTS interaction_messages (
    id SERIAL,
    ia_id BIGINT,
    msg_id VARCHAR(32),
    CONSTRAINT pk_interaction_messages PRIMARY KEY (id, ia_id, msg_id),
    CONSTRAINT fk_interaction_messages_ia_id FOREIGN KEY (ia_id) REFERENCES interaction (id),
    CONSTRAINT fk_interaction_messages_msg_id FOREIGN KEY (msg_id) REFERENCES message (id)
);
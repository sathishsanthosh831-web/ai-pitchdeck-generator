-- Pitch Deck Generator: PostgreSQL schema
-- (Run this against your Render PostgreSQL database - no CREATE DATABASE needed,
--  Render already creates the database for you)

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS decks (
    id SERIAL PRIMARY KEY,
    user_id INT,
    startup_name VARCHAR(200) NOT NULL,
    idea_description TEXT NOT NULL,
    industry VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'generated', 'edited', 'exported')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Each row is one slide belonging to a deck, stored as editable JSON content
CREATE TABLE IF NOT EXISTS slides (
    id SERIAL PRIMARY KEY,
    deck_id INT NOT NULL,
    slide_order INT NOT NULL,
    slide_type VARCHAR(60) NOT NULL,   -- e.g. problem, solution, market, business_model
    title VARCHAR(255),
    content_json JSONB,                -- flexible: bullet points, stats, text blocks
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_slides_deck ON slides(deck_id);
CREATE INDEX IF NOT EXISTS idx_decks_user ON decks(user_id);

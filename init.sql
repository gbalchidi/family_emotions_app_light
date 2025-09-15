-- Create analytics events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_event_type ON analytics_events ((event_data->>'event'));
CREATE INDEX IF NOT EXISTS idx_user_id ON analytics_events ((event_data->'properties'->>'user_id'));
CREATE INDEX IF NOT EXISTS idx_timestamp ON analytics_events ((event_data->'properties'->>'timestamp'));
CREATE INDEX IF NOT EXISTS idx_created_at ON analytics_events (created_at);

-- Add a comment
COMMENT ON TABLE analytics_events IS 'Store all analytics events as JSONB documents';
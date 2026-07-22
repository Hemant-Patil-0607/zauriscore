-- ZauriScore Database Initialization
-- This runs once when the container is first created.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Log
DO $$
BEGIN
  RAISE NOTICE 'ZauriScore database initialized successfully';
END $$;

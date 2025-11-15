-- SaaS Survey Platform Database Initialization
-- PostgreSQL 18
-- This script runs once when the database is first created

-- Ensure UTF-8 encoding
ALTER DATABASE saas_survey SET client_encoding TO 'UTF8';

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types if needed
-- Example: CREATE TYPE user_role AS ENUM ('TENANT_ADMIN', 'SURVEY_MANAGER', 'RESPONDENT');

-- Set default timezone
SET timezone = 'Asia/Seoul';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE saas_survey TO survey_admin;

-- Create schemas for multi-tenancy (optional)
-- CREATE SCHEMA IF NOT EXISTS tenant_shared;
-- GRANT ALL PRIVILEGES ON SCHEMA tenant_shared TO survey_admin;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'SaaS Survey Database initialized successfully';
    RAISE NOTICE 'Database: saas_survey';
    RAISE NOTICE 'User: survey_admin';
    RAISE NOTICE 'Encoding: UTF8';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_stat_statements';
END $$;

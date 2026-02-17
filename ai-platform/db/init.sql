-- =============================================================================
-- ECHOLAB DATABASE INITIALIZATION - PREREQUISITE SETUP
-- =============================================================================
-- This file runs BEFORE airflow-init.sql (01-init.sql < 02-airflow-init.sql)
-- It enables the pgvector extension required by the main schema.
-- The full schema (tables, seed data, agents) is in 02-airflow-init.sql.
-- =============================================================================

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schemas (idempotent - airflow-init.sql also creates these)
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS agents;

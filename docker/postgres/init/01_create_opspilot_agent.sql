-- Phase 11.1: isolated Agent Checkpoint database.
-- Runs only on first Postgres volume initialization (docker-entrypoint-initdb.d).
-- If the volume already exists, Agent startup ensure_agent_database() creates it.

CREATE DATABASE opspilot_agent;

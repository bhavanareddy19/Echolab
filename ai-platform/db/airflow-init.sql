-- =============================================================================
-- ECHOLAB DATABASE INITIALIZATION - AIRFLOW & ANALYTICS SCHEMAS
-- =============================================================================
-- Creates the database schema for the Echolab AI platform.
-- Runs automatically when PostgreSQL container starts for the first time.
--
-- INTERVIEW TIP: Explain the 3-layer architecture:
-- RAW    → Ingested data (no transformation)
-- CORE   → Cleaned, normalized data (ready for ML)
-- ANALYTICS → ML outputs (clusters, hypotheses, embeddings, agent results)
-- =============================================================================

-- Airflow database is created by 00-create-airflow-db.sh (runs before this file)

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- RAW SCHEMA - Data Ingestion Layer
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.tickets (
    id              SERIAL PRIMARY KEY,
    ticket_key      VARCHAR(50) UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    priority        VARCHAR(10),
    status          VARCHAR(50),
    created_at      TIMESTAMP WITH TIME ZONE,
    updated_at      TIMESTAMP WITH TIME ZONE,
    reporter        VARCHAR(100),
    product         VARCHAR(100),
    component       VARCHAR(100),
    source          VARCHAR(20) DEFAULT 'jira',
    raw_payload     JSONB,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.feedback (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(50) NOT NULL,
    content         TEXT NOT NULL,
    metadata        JSONB,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- CORE SCHEMA - Cleaned & Enriched Data
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.tickets (
    id                  SERIAL PRIMARY KEY,
    raw_ticket_id       INTEGER REFERENCES raw.tickets(id),
    ticket_key          VARCHAR(50) UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    description_clean   TEXT,
    priority            VARCHAR(10),
    status              VARCHAR(50),
    product             VARCHAR(100),
    component           VARCHAR(100),
    -- AI Classification Results
    feature_type        VARCHAR(30),
    sentiment           VARCHAR(20),
    urgency_score       FLOAT,
    customer_problem    TEXT,
    root_cause          TEXT,
    -- Embedding (pgvector)
    embedding           vector(384),
    -- Clustering
    cluster_id          INTEGER,
    cluster_confidence  FLOAT,
    -- Metadata
    classified_at       TIMESTAMP WITH TIME ZONE,
    classified_by       VARCHAR(50),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW index for <50ms p99 vector search
CREATE INDEX IF NOT EXISTS idx_core_tickets_embedding
    ON core.tickets USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- =============================================================================
-- ANALYTICS SCHEMA - ML Outputs
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS analytics;

-- Pain point clusters
CREATE TABLE IF NOT EXISTS analytics.clusters (
    id                  SERIAL PRIMARY KEY,
    cluster_label       TEXT NOT NULL,
    description         TEXT,
    num_tickets         INTEGER DEFAULT 0,
    avg_urgency         FLOAT,
    top_keywords        JSONB,
    representative_ids  JSONB,
    centroid            vector(384),
    status              VARCHAR(20) DEFAULT 'active',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated hypotheses for A/B testing
CREATE TABLE IF NOT EXISTS analytics.hypotheses (
    id                  SERIAL PRIMARY KEY,
    cluster_id          INTEGER REFERENCES analytics.clusters(id),
    hypothesis_text     TEXT NOT NULL,
    confidence_score    FLOAT,
    expected_impact     VARCHAR(20),
    experiment_config   JSONB,
    status              VARCHAR(20) DEFAULT 'draft',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Competitor analysis results (from multi-agent system)
CREATE TABLE IF NOT EXISTS analytics.competitor_insights (
    id                  SERIAL PRIMARY KEY,
    competitor_name     VARCHAR(200) NOT NULL,
    analysis_type       VARCHAR(50),
    findings            JSONB NOT NULL,
    sources             JSONB,
    agent_id            VARCHAR(100),
    confidence          FLOAT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- AGENT ORCHESTRATION SCHEMA - 15 Specialized Agents
-- =============================================================================
-- INTERVIEW TIP: This tracks all 15 specialized agents that reduce
-- analysis time by 85%. Each agent has a specific role and can be
-- monitored independently for performance and cost.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS agents;

-- Registry of all 15 specialized agents
CREATE TABLE IF NOT EXISTS agents.registry (
    id                  SERIAL PRIMARY KEY,
    agent_name          VARCHAR(100) UNIQUE NOT NULL,
    agent_type          VARCHAR(50) NOT NULL,         -- langchain, crewai, autogen
    description         TEXT,
    role                TEXT,                          -- Agent's system prompt/role
    tools               JSONB,                        -- Tools available to this agent
    model_backend       VARCHAR(50),                  -- gpt-4, llama-3.1, gpt-4-turbo
    is_active           BOOLEAN DEFAULT TRUE,
    avg_latency_ms      FLOAT,
    success_rate        FLOAT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent execution logs - tracks every run of every agent
CREATE TABLE IF NOT EXISTS agents.execution_log (
    id                  SERIAL PRIMARY KEY,
    agent_id            INTEGER REFERENCES agents.registry(id),
    workflow_run_id     VARCHAR(100),                  -- Links to Airflow DAG run
    task_type           VARCHAR(50),                   -- classify, cluster, analyze, etc.
    input_data          JSONB,
    output_data         JSONB,
    tokens_used         INTEGER,
    cost_usd            FLOAT,
    latency_ms          FLOAT,
    status              VARCHAR(20) DEFAULT 'running', -- running, success, failed, timeout
    error_message       TEXT,
    started_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at        TIMESTAMP WITH TIME ZONE
);

-- Agent collaboration tracking - which agents work together
CREATE TABLE IF NOT EXISTS agents.collaborations (
    id                  SERIAL PRIMARY KEY,
    workflow_name       VARCHAR(100) NOT NULL,
    agent_sequence      JSONB NOT NULL,                -- Ordered list of agent IDs
    description         TEXT,
    avg_time_saved_pct  FLOAT,                         -- % time saved vs manual
    total_runs          INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INSERT 15 SPECIALIZED AGENTS INTO REGISTRY
-- =============================================================================
-- INTERVIEW TIP: Be ready to explain each agent's role, what tools it uses,
-- and how they collaborate to reduce analysis time by 85%.
-- =============================================================================
INSERT INTO agents.registry (agent_name, agent_type, description, role, tools, model_backend) VALUES
-- === PIPELINE 1: Ticket Ingestion & Classification ===
('ticket_classifier', 'langchain',
 'Classifies tickets into bug/feature/improvement with sentiment analysis',
 'You are a ticket classification expert. Analyze support tickets and classify them accurately.',
 '["llm_chain", "output_parser", "retry_parser"]'::jsonb, 'gpt-4'),

('priority_assessor', 'langchain',
 'Assesses ticket urgency and business impact on a 0-1 scale',
 'You assess the urgency and business impact of customer issues.',
 '["llm_chain", "structured_output"]'::jsonb, 'gpt-4'),

('root_cause_extractor', 'langchain',
 'Extracts customer problem statement and technical root cause from tickets',
 'You are a technical analyst. Extract the core customer problem and likely root cause.',
 '["llm_chain", "rag_retriever", "output_parser"]'::jsonb, 'gpt-4'),

-- === PIPELINE 2: Semantic Clustering & Pain Point Discovery ===
('embedding_generator', 'langchain',
 'Generates sentence-transformer embeddings for semantic search and clustering',
 'Generate high-quality embeddings for ticket text.',
 '["sentence_transformers", "faiss_index", "batch_processor"]'::jsonb, 'sentence-transformers'),

('cluster_analyzer', 'langchain',
 'Runs KMeans/HDBSCAN clustering and generates cluster labels using LLM',
 'You analyze clusters of similar tickets and generate meaningful labels.',
 '["sklearn_cluster", "llm_chain", "summarizer"]'::jsonb, 'gpt-4'),

('pain_point_synthesizer', 'langchain',
 'Synthesizes pain points from clusters into actionable product insights',
 'You synthesize customer pain points into clear, actionable product insights.',
 '["llm_chain", "rag_retriever", "structured_output"]'::jsonb, 'gpt-4'),

-- === PIPELINE 3: RAG-Powered Hypothesis Generation ===
('context_retriever', 'langchain',
 'Retrieves relevant context from knowledge base using FAISS/Qdrant vector search',
 'Retrieve the most relevant documentation and context for a given query.',
 '["faiss_retriever", "qdrant_retriever", "reranker"]'::jsonb, 'sentence-transformers'),

('hypothesis_generator', 'langgraph',
 'Generates A/B test hypotheses from pain points + retrieved context using RAG',
 'You generate data-driven hypotheses for product experiments.',
 '["rag_chain", "structured_output", "validator"]'::jsonb, 'gpt-4'),

('experiment_designer', 'langchain',
 'Designs GrowthBook experiments with metrics, variants, and success criteria',
 'You design rigorous A/B test experiments with clear success metrics.',
 '["llm_chain", "growthbook_api", "structured_output"]'::jsonb, 'gpt-4'),

-- === PIPELINE 4: Competitor Analysis (CrewAI Multi-Agent) ===
('market_researcher', 'crewai',
 'Researches competitor products, features, and market positioning',
 'You are a senior market researcher specializing in B2B SaaS competitive analysis.',
 '["web_search", "document_analyzer", "summarizer"]'::jsonb, 'gpt-4'),

('feature_gap_analyst', 'crewai',
 'Identifies feature gaps by comparing competitor capabilities with pain points',
 'You identify feature gaps between our product and competitors.',
 '["comparison_tool", "llm_chain", "structured_output"]'::jsonb, 'gpt-4'),

('strategy_advisor', 'crewai',
 'Synthesizes research into strategic recommendations with ROI estimates',
 'You are a product strategy advisor. Provide actionable recommendations.',
 '["llm_chain", "roi_calculator", "report_generator"]'::jsonb, 'gpt-4'),

-- === PIPELINE 5: Continuous Monitoring & Alerting ===
('trend_detector', 'langchain',
 'Detects emerging trends and spikes in ticket volume or new issue categories',
 'You monitor ticket streams and detect emerging trends or anomalies.',
 '["time_series_analyzer", "anomaly_detector", "llm_chain"]'::jsonb, 'gpt-4-turbo'),

('quality_auditor', 'langchain',
 'Audits classification and clustering quality, triggers retraining when accuracy drops',
 'You audit ML model outputs and flag quality issues.',
 '["metrics_calculator", "drift_detector", "alert_sender"]'::jsonb, 'gpt-4-turbo'),

('report_generator', 'autogen',
 'Generates comprehensive weekly/monthly analysis reports with visualizations',
 'You generate executive-level reports from analytics data.',
 '["data_aggregator", "chart_generator", "llm_chain", "pdf_renderer"]'::jsonb, 'gpt-4')

ON CONFLICT (agent_name) DO NOTHING;

-- =============================================================================
-- INSERT AGENT COLLABORATION WORKFLOWS
-- =============================================================================
INSERT INTO agents.collaborations (workflow_name, agent_sequence, description, avg_time_saved_pct) VALUES
('ticket_classification_pipeline',
 '[1, 2, 3]'::jsonb,
 'Classify → Assess Priority → Extract Root Cause',
 75.0),

('semantic_clustering_pipeline',
 '[4, 5, 6]'::jsonb,
 'Generate Embeddings → Cluster → Synthesize Pain Points',
 80.0),

('hypothesis_generation_pipeline',
 '[7, 8, 9]'::jsonb,
 'Retrieve Context → Generate Hypothesis → Design Experiment',
 85.0),

('competitor_analysis_pipeline',
 '[10, 11, 12]'::jsonb,
 'Research Market → Analyze Gaps → Advise Strategy',
 50.0),

('monitoring_pipeline',
 '[13, 14, 15]'::jsonb,
 'Detect Trends → Audit Quality → Generate Reports',
 90.0)

ON CONFLICT DO NOTHING;

-- =============================================================================
-- SEED DATA: RAW TICKETS
-- =============================================================================
INSERT INTO raw.tickets (ticket_key, title, description, priority, status, reporter, product, component, created_at, updated_at) VALUES
('ECHO-101', 'Checkout freezes on payment step', 'When users click "Pay Now" on the checkout page, the entire page freezes for 10+ seconds. Multiple customers reported this issue across Chrome and Firefox. The spinner keeps loading but nothing happens.', 'High', 'Open', 'alice.chen', 'EchoPay', 'Checkout', NOW() - INTERVAL '25 days', NOW() - INTERVAL '25 days'),
('ECHO-102', 'Export to CSV fails for large datasets', 'Attempting to export reports with more than 5000 rows results in a timeout error. The download never completes and users see a 504 gateway timeout.', 'High', 'Open', 'bob.smith', 'EchoAnalytics', 'Export', NOW() - INTERVAL '24 days', NOW() - INTERVAL '24 days'),
('ECHO-103', 'Feature request: Add dark mode support', 'Many users have requested dark mode for the dashboard. This would improve usability during nighttime and reduce eye strain. Love the product otherwise!', 'Low', 'Open', 'carol.jones', 'EchoDash', 'UI', NOW() - INTERVAL '23 days', NOW() - INTERVAL '22 days'),
('ECHO-104', 'Login fails with SSO after password reset', 'After resetting password through the SSO provider, users cannot login to Echolab. The auth flow redirects back to the login page without any error message.', 'Critical', 'In Progress', 'dave.wilson', 'EchoAuth', 'Authentication', NOW() - INTERVAL '22 days', NOW() - INTERVAL '20 days'),
('ECHO-105', 'Dashboard loading is extremely slow', 'The main dashboard takes 15-20 seconds to load. This is frustrating and unacceptable for daily use. The performance has degraded significantly over the past month.', 'High', 'Open', 'emma.brown', 'EchoDash', 'Dashboard', NOW() - INTERVAL '21 days', NOW() - INTERVAL '21 days'),
('ECHO-106', 'Payment declined error shows wrong message', 'When a payment is declined, the error message says "Network Error" instead of showing the actual decline reason from the payment processor.', 'Medium', 'Open', 'frank.lee', 'EchoPay', 'Checkout', NOW() - INTERVAL '20 days', NOW() - INTERVAL '20 days'),
('ECHO-107', 'Add ability to schedule report exports', 'Feature request: We need the ability to schedule automated CSV/PDF exports on a daily or weekly basis. Currently we have to manually export every time.', 'Medium', 'Open', 'grace.kim', 'EchoAnalytics', 'Export', NOW() - INTERVAL '19 days', NOW() - INTERVAL '19 days'),
('ECHO-108', 'UI button overlapping on mobile view', 'The "Submit" and "Cancel" buttons overlap on screens smaller than 768px. This makes it impossible to click the correct button on mobile devices.', 'Medium', 'Open', 'henry.davis', 'EchoDash', 'UI', NOW() - INTERVAL '18 days', NOW() - INTERVAL '18 days'),
('ECHO-109', 'Timeout error when loading ticket history', 'Loading ticket history for accounts with 1000+ tickets causes a timeout. Users see a blank page after waiting 30 seconds. Need pagination or lazy loading.', 'High', 'In Progress', 'iris.wang', 'EchoSupport', 'Performance', NOW() - INTERVAL '17 days', NOW() - INTERVAL '15 days'),
('ECHO-110', 'Two-factor auth not working with Authy', 'Users using Authy for 2FA are getting "Invalid code" errors even with correct codes. Google Authenticator works fine. This is blocking several enterprise customers.', 'Critical', 'Open', 'jack.taylor', 'EchoAuth', 'Authentication', NOW() - INTERVAL '16 days', NOW() - INTERVAL '16 days'),
('ECHO-111', 'Cart items disappear after page refresh', 'Shopping cart loses all items when the page is refreshed. This is causing abandoned checkouts and frustrated customers who have to re-add everything.', 'High', 'Open', 'kate.martin', 'EchoPay', 'Checkout', NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days'),
('ECHO-112', 'Add multi-language support for dashboard', 'We have customers in Japan, Germany, and Brazil who need the dashboard in their local languages. Currently only English is supported.', 'Low', 'Open', 'leo.garcia', 'EchoDash', 'UI', NOW() - INTERVAL '14 days', NOW() - INTERVAL '14 days'),
('ECHO-113', 'Report PDF download produces blank pages', 'When exporting analytics reports as PDF, pages 2+ are completely blank. Only the first page has content. This happens for all report types.', 'High', 'Open', 'maya.patel', 'EchoAnalytics', 'Export', NOW() - INTERVAL '13 days', NOW() - INTERVAL '13 days'),
('ECHO-114', 'API response time degraded after update', 'Since the v2.3 update, API response times have increased from 200ms to 2s average. This is causing timeout issues for integrations and slow dashboard loading.', 'Critical', 'In Progress', 'noah.clark', 'EchoAPI', 'Performance', NOW() - INTERVAL '12 days', NOW() - INTERVAL '10 days'),
('ECHO-115', 'SSO session expires too quickly', 'SSO sessions are expiring after 15 minutes of inactivity. Enterprise customers need at least 8 hours. Users are frustrated with constant re-authentication.', 'Medium', 'Open', 'olivia.wright', 'EchoAuth', 'Authentication', NOW() - INTERVAL '11 days', NOW() - INTERVAL '11 days'),
('ECHO-116', 'Checkout page not accessible for screen readers', 'The checkout flow is not accessible - screen readers cannot navigate the payment form. This is a compliance issue for ADA requirements.', 'High', 'Open', 'peter.hall', 'EchoPay', 'Checkout', NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days'),
('ECHO-117', 'Feature: Bulk ticket assignment', 'We need the ability to select multiple tickets and assign them to an agent in bulk. Currently each ticket must be assigned individually which is very slow.', 'Medium', 'Open', 'quinn.adams', 'EchoSupport', 'UI', NOW() - INTERVAL '9 days', NOW() - INTERVAL '9 days'),
('ECHO-118', 'Dashboard charts not rendering in Safari', 'All charts on the analytics dashboard show as blank in Safari 17+. Chrome and Firefox work fine. This affects about 20% of our users.', 'High', 'Open', 'rachel.baker', 'EchoDash', 'Dashboard', NOW() - INTERVAL '8 days', NOW() - INTERVAL '8 days'),
('ECHO-119', 'Export fails silently for date range queries', 'When exporting data with a custom date range filter, the export button appears to work but the downloaded file is empty. No error message is shown.', 'Medium', 'Open', 'sam.nelson', 'EchoAnalytics', 'Export', NOW() - INTERVAL '7 days', NOW() - INTERVAL '7 days'),
('ECHO-120', 'Password reset email not being received', 'Multiple users report not receiving password reset emails. Checked spam folders. The issue seems intermittent - some users get it on retry.', 'High', 'Open', 'tina.mitchell', 'EchoAuth', 'Authentication', NOW() - INTERVAL '6 days', NOW() - INTERVAL '6 days')
ON CONFLICT (ticket_key) DO NOTHING;

-- =============================================================================
-- SEED DATA: CLUSTERS (Pain Points)
-- =============================================================================
INSERT INTO analytics.clusters (id, cluster_label, description, num_tickets, avg_urgency, top_keywords, status) VALUES
(1, 'Checkout Issues', 'Payment flow problems causing cart abandonment and checkout failures', 4, 0.82, '["checkout", "payment", "cart", "freeze", "declined"]'::jsonb, 'active'),
(2, 'Performance Problems', 'Slow loading times, timeouts, and degraded API response times', 4, 0.85, '["slow", "timeout", "loading", "performance", "degraded"]'::jsonb, 'active'),
(3, 'Export Failures', 'CSV and PDF exports failing for large datasets or producing blank output', 4, 0.65, '["export", "csv", "pdf", "download", "timeout"]'::jsonb, 'active'),
(4, 'Auth Problems', 'SSO, 2FA, and password reset issues blocking user access', 4, 0.88, '["login", "sso", "auth", "password", "2fa"]'::jsonb, 'active'),
(5, 'UI Bugs', 'Display issues, accessibility problems, and mobile responsiveness bugs', 4, 0.45, '["ui", "display", "mobile", "button", "layout"]'::jsonb, 'active')
ON CONFLICT (id) DO NOTHING;

-- Reset the sequence for clusters
SELECT setval('analytics.clusters_id_seq', (SELECT COALESCE(MAX(id), 0) FROM analytics.clusters));

-- =============================================================================
-- SEED DATA: CORE (Classified) TICKETS
-- =============================================================================
INSERT INTO core.tickets (raw_ticket_id, ticket_key, title, description_clean, priority, status, product, component, feature_type, sentiment, urgency_score, customer_problem, root_cause, cluster_id, classified_at, classified_by) VALUES
(1, 'ECHO-101', 'Checkout freezes on payment step', 'When users click Pay Now on the checkout page, the entire page freezes for 10+ seconds. Multiple customers reported this issue across Chrome and Firefox.', 'High', 'Open', 'EchoPay', 'Checkout', 'bug', 'negative', 0.9, 'Checkout page freezes when attempting to complete payment', 'Unhandled exception in payment processing logic', 1, NOW() - INTERVAL '24 days', 'rule_engine'),
(2, 'ECHO-102', 'Export to CSV fails for large datasets', 'Attempting to export reports with more than 5000 rows results in a timeout error. The download never completes.', 'High', 'Open', 'EchoAnalytics', 'Export', 'bug', 'negative', 0.8, 'Cannot export large datasets to CSV', 'Performance degradation - possible backend latency or resource exhaustion', 3, NOW() - INTERVAL '23 days', 'rule_engine'),
(3, 'ECHO-103', 'Feature request: Add dark mode support', 'Many users have requested dark mode for the dashboard. This would improve usability during nighttime and reduce eye strain.', 'Low', 'Open', 'EchoDash', 'UI', 'feature', 'positive', 0.2, 'Users want dark mode for better nighttime usability', NULL, 5, NOW() - INTERVAL '22 days', 'rule_engine'),
(4, 'ECHO-104', 'Login fails with SSO after password reset', 'After resetting password through the SSO provider, users cannot login to Echolab. The auth flow redirects back to login page.', 'Critical', 'In Progress', 'EchoAuth', 'Authentication', 'bug', 'negative', 0.95, 'SSO login broken after password reset', 'Authentication/authorization flow issue', 4, NOW() - INTERVAL '21 days', 'rule_engine'),
(5, 'ECHO-105', 'Dashboard loading is extremely slow', 'The main dashboard takes 15-20 seconds to load. Performance has degraded significantly over the past month.', 'High', 'Open', 'EchoDash', 'Dashboard', 'bug', 'negative', 0.85, 'Dashboard load times are unacceptable at 15-20 seconds', 'Performance degradation - possible backend latency or resource exhaustion', 2, NOW() - INTERVAL '20 days', 'rule_engine'),
(6, 'ECHO-106', 'Payment declined error shows wrong message', 'When a payment is declined, the error message says Network Error instead of showing actual decline reason.', 'Medium', 'Open', 'EchoPay', 'Checkout', 'bug', 'neutral', 0.6, 'Incorrect error messages for payment declines', 'Frontend rendering issue', 1, NOW() - INTERVAL '19 days', 'rule_engine'),
(7, 'ECHO-107', 'Add ability to schedule report exports', 'We need the ability to schedule automated CSV/PDF exports on a daily or weekly basis.', 'Medium', 'Open', 'EchoAnalytics', 'Export', 'feature', 'neutral', 0.4, 'Need automated scheduled exports', NULL, 3, NOW() - INTERVAL '18 days', 'rule_engine'),
(8, 'ECHO-108', 'UI button overlapping on mobile view', 'The Submit and Cancel buttons overlap on screens smaller than 768px. Impossible to click correct button on mobile.', 'Medium', 'Open', 'EchoDash', 'UI', 'bug', 'neutral', 0.5, 'Button overlap on mobile devices', 'Frontend rendering issue', 5, NOW() - INTERVAL '17 days', 'rule_engine'),
(9, 'ECHO-109', 'Timeout error when loading ticket history', 'Loading ticket history for accounts with 1000+ tickets causes a timeout. Users see blank page after 30 seconds.', 'High', 'In Progress', 'EchoSupport', 'Performance', 'bug', 'negative', 0.8, 'Ticket history page times out for large accounts', 'Performance degradation - possible backend latency or resource exhaustion', 2, NOW() - INTERVAL '16 days', 'rule_engine'),
(10, 'ECHO-110', 'Two-factor auth not working with Authy', 'Users using Authy for 2FA are getting Invalid code errors even with correct codes. Blocking enterprise customers.', 'Critical', 'Open', 'EchoAuth', 'Authentication', 'bug', 'negative', 0.95, '2FA broken for Authy users', 'Authentication/authorization flow issue', 4, NOW() - INTERVAL '15 days', 'rule_engine'),
(11, 'ECHO-111', 'Cart items disappear after page refresh', 'Shopping cart loses all items when the page is refreshed. Causing abandoned checkouts.', 'High', 'Open', 'EchoPay', 'Checkout', 'bug', 'negative', 0.85, 'Cart state is not persisted across page refreshes', 'Unhandled exception in application logic', 1, NOW() - INTERVAL '14 days', 'rule_engine'),
(12, 'ECHO-112', 'Add multi-language support for dashboard', 'Customers in Japan, Germany, and Brazil need the dashboard in their local languages.', 'Low', 'Open', 'EchoDash', 'UI', 'feature', 'neutral', 0.3, 'International customers need localized dashboard', NULL, 5, NOW() - INTERVAL '13 days', 'rule_engine'),
(13, 'ECHO-113', 'Report PDF download produces blank pages', 'When exporting analytics reports as PDF, pages 2+ are completely blank. Only first page has content.', 'High', 'Open', 'EchoAnalytics', 'Export', 'bug', 'negative', 0.75, 'PDF exports are incomplete with blank pages', 'Unhandled exception in application logic', 3, NOW() - INTERVAL '12 days', 'rule_engine'),
(14, 'ECHO-114', 'API response time degraded after update', 'Since v2.3 update, API response times increased from 200ms to 2s. Causing timeout issues.', 'Critical', 'In Progress', 'EchoAPI', 'Performance', 'bug', 'negative', 0.95, 'API latency increased 10x after recent update', 'Performance degradation - possible backend latency or resource exhaustion', 2, NOW() - INTERVAL '11 days', 'rule_engine'),
(15, 'ECHO-115', 'SSO session expires too quickly', 'SSO sessions expiring after 15 minutes. Enterprise customers need at least 8 hours.', 'Medium', 'Open', 'EchoAuth', 'Authentication', 'bug', 'negative', 0.6, 'SSO session timeout is too aggressive', 'Authentication/authorization flow issue', 4, NOW() - INTERVAL '10 days', 'rule_engine'),
(16, 'ECHO-116', 'Checkout page not accessible for screen readers', 'Checkout flow not accessible - screen readers cannot navigate payment form. ADA compliance issue.', 'High', 'Open', 'EchoPay', 'Checkout', 'bug', 'neutral', 0.7, 'Payment form fails accessibility standards', 'Frontend rendering issue', 1, NOW() - INTERVAL '9 days', 'rule_engine'),
(17, 'ECHO-117', 'Feature: Bulk ticket assignment', 'Need ability to select multiple tickets and assign to agent in bulk. Current individual assignment is slow.', 'Medium', 'Open', 'EchoSupport', 'UI', 'feature', 'neutral', 0.4, 'Ticket assignment workflow is too slow', NULL, 5, NOW() - INTERVAL '8 days', 'rule_engine'),
(18, 'ECHO-118', 'Dashboard charts not rendering in Safari', 'All charts on analytics dashboard blank in Safari 17+. Chrome and Firefox work fine. Affects 20% of users.', 'High', 'Open', 'EchoDash', 'Dashboard', 'bug', 'neutral', 0.7, 'Charts broken in Safari browser', 'Frontend rendering issue', 2, NOW() - INTERVAL '7 days', 'rule_engine'),
(19, 'ECHO-119', 'Export fails silently for date range queries', 'Exporting data with custom date range filter produces empty file. No error message shown.', 'Medium', 'Open', 'EchoAnalytics', 'Export', 'bug', 'neutral', 0.5, 'Date range exports produce empty files', 'Unhandled exception in application logic', 3, NOW() - INTERVAL '6 days', 'rule_engine'),
(20, 'ECHO-120', 'Password reset email not being received', 'Multiple users not receiving password reset emails. Issue seems intermittent.', 'High', 'Open', 'EchoAuth', 'Authentication', 'bug', 'negative', 0.8, 'Password reset emails not delivered', 'Authentication/authorization flow issue', 4, NOW() - INTERVAL '5 days', 'rule_engine')
ON CONFLICT (ticket_key) DO NOTHING;

-- =============================================================================
-- SEED DATA: HYPOTHESES
-- =============================================================================
INSERT INTO analytics.hypotheses (cluster_id, hypothesis_text, confidence_score, expected_impact, experiment_config, status) VALUES
(1, 'If we implement optimistic UI updates and async payment processing, then checkout completion rate will increase by 15% because users currently abandon due to perceived freezing', 0.92, 'high',
 '{"variant_a": "Current synchronous checkout flow", "variant_b": "Async payment with optimistic UI feedback", "primary_metric": "checkout_completion_rate", "secondary_metric": "time_to_complete", "duration_days": 14}'::jsonb, 'draft'),
(2, 'If we add database query caching and CDN for static assets, then dashboard load time will decrease from 15s to under 3s because most queries are repeated reads', 0.88, 'high',
 '{"variant_a": "Current uncached dashboard queries", "variant_b": "Redis-cached queries with CDN static assets", "primary_metric": "page_load_time", "secondary_metric": "user_satisfaction_score", "duration_days": 7}'::jsonb, 'draft'),
(3, 'If we implement streaming CSV export with chunked downloads, then export success rate will increase to 99% because large exports currently timeout', 0.78, 'medium',
 '{"variant_a": "Current single-request export", "variant_b": "Streaming chunked export with progress bar", "primary_metric": "export_success_rate", "secondary_metric": "export_completion_time", "duration_days": 14}'::jsonb, 'experiment'),
(4, 'If we implement token refresh with silent re-authentication, then auth-related support tickets will decrease by 40% because session expiry is the top auth complaint', 0.85, 'high',
 '{"variant_a": "Current 15-min session timeout", "variant_b": "Silent token refresh with 8-hour session", "primary_metric": "auth_support_tickets", "secondary_metric": "session_duration", "duration_days": 21}'::jsonb, 'draft'),
(5, 'If we add responsive breakpoints and touch-friendly tap targets, then mobile task completion rate will increase by 25% because button overlaps block mobile users', 0.64, 'medium',
 '{"variant_a": "Current non-responsive layout", "variant_b": "Responsive design with 48px tap targets", "primary_metric": "mobile_task_completion", "secondary_metric": "mobile_bounce_rate", "duration_days": 14}'::jsonb, 'testing'),
(1, 'If we persist cart state in localStorage with server-side backup, then cart abandonment will decrease by 20% because users lose items on page refresh', 0.75, 'medium',
 '{"variant_a": "Session-only cart storage", "variant_b": "localStorage + server-synced cart", "primary_metric": "cart_abandonment_rate", "secondary_metric": "items_per_checkout", "duration_days": 14}'::jsonb, 'draft')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- MODEL PERFORMANCE TRACKING (78% -> 94% accuracy story)
-- =============================================================================
CREATE TABLE IF NOT EXISTS analytics.model_metrics (
    id                  SERIAL PRIMARY KEY,
    model_name          VARCHAR(100) NOT NULL,
    model_version       VARCHAR(50),
    task                VARCHAR(50),
    accuracy            FLOAT,
    precision_score     FLOAT,
    recall_score        FLOAT,
    f1_score            FLOAT,
    latency_p50_ms      FLOAT,
    latency_p99_ms      FLOAT,
    throughput_qps      FLOAT,
    cost_per_query      FLOAT,
    eval_dataset_size   INTEGER,
    config              JSONB,
    evaluated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Embedding index metadata
CREATE TABLE IF NOT EXISTS analytics.embedding_indices (
    id                  SERIAL PRIMARY KEY,
    index_name          VARCHAR(100) NOT NULL,
    model_name          VARCHAR(100),
    dimension           INTEGER NOT NULL,
    num_vectors         BIGINT DEFAULT 0,
    index_type          VARCHAR(50),
    storage_backend     VARCHAR(50),
    latency_p99_ms      FLOAT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- SEED MODEL METRICS - THE ACCURACY IMPROVEMENT STORY
-- =============================================================================
-- INTERVIEW TIP: This is the story of how you improved from 78% to 94%.
-- Be ready to explain each step and why it improved accuracy.
-- =============================================================================
INSERT INTO analytics.model_metrics (model_name, model_version, task, accuracy, precision_score, recall_score, f1_score, latency_p50_ms, latency_p99_ms, cost_per_query, eval_dataset_size, config) VALUES
-- Step 1: Baseline - GPT-4 with basic prompting (78% accuracy)
('gpt-4', 'baseline-v1', 'classification', 0.78, 0.76, 0.74, 0.75, 850, 2100, 0.035, 5000,
 '{"method": "basic_prompt", "temperature": 0.7, "notes": "Simple zero-shot classification without context"}'::jsonb),

-- Step 2: Structured prompting + output parsing (82% accuracy)
('gpt-4', 'structured-v2', 'classification', 0.82, 0.80, 0.79, 0.795, 900, 2200, 0.038, 5000,
 '{"method": "structured_prompt", "temperature": 0.3, "notes": "Added structured output format and few-shot examples"}'::jsonb),

-- Step 3: RAG with FAISS context retrieval (87% accuracy)
('gpt-4+rag', 'rag-v3', 'classification', 0.87, 0.86, 0.85, 0.855, 1100, 2800, 0.042, 5000,
 '{"method": "rag_enhanced", "retriever": "faiss", "top_k": 5, "notes": "Added domain context via RAG - major accuracy jump"}'::jsonb),

-- Step 4: Ensemble with fine-tuned LLaMA 3.1 (91% accuracy)
('ensemble-gpt4-llama', 'ensemble-v4', 'classification', 0.91, 0.90, 0.89, 0.895, 650, 1800, 0.015, 5000,
 '{"method": "ensemble", "models": ["gpt-4+rag", "llama-3.1-qlora"], "strategy": "weighted_vote", "notes": "LLaMA handles common cases, GPT-4 handles edge cases"}'::jsonb),

-- Step 5: QLoRA fine-tuned LLaMA + Qdrant hybrid search (94% accuracy)
('ensemble-qlora-qdrant', 'final-v5', 'classification', 0.94, 0.93, 0.92, 0.925, 450, 980, 0.008, 5000,
 '{"method": "ensemble_rag_qlora", "models": ["llama-3.1-qlora", "gpt-4-fallback"], "retriever": "qdrant_hybrid", "quantization": "int8", "notes": "Final production model - QLoRA + hybrid search + confidence routing"}'::jsonb)

ON CONFLICT DO NOTHING;

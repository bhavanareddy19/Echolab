#!/bin/bash
# Example: How I inserted data into Docker PostgreSQL

# Method 1: Insert tickets using docker exec
docker exec echolab-postgres psql -U echolab -d echolab -c "
INSERT INTO raw.tickets (ticket_key, title, description, priority, status, reporter, product, component, created_at, updated_at) VALUES
('ECHO-101', 'Checkout freezes on payment step', 'Description here...', 'High', 'Open', 'alice.chen', 'EchoPay', 'Checkout', NOW() - INTERVAL '25 days', NOW() - INTERVAL '25 days'),
('ECHO-102', 'Export to CSV fails', 'Another description...', 'High', 'Open', 'bob.smith', 'EchoAnalytics', 'Export', NOW() - INTERVAL '24 days', NOW() - INTERVAL '24 days')
ON CONFLICT (ticket_key) DO NOTHING;
"

# Method 2: Insert clusters
docker exec echolab-postgres psql -U echolab -d echolab -c "
INSERT INTO analytics.clusters (id, cluster_label, description, num_tickets, avg_urgency, top_keywords, status) VALUES
(1, 'Checkout Issues', 'Payment flow problems', 4, 0.82, '[\"checkout\", \"payment\"]'::jsonb, 'active'),
(2, 'Performance Problems', 'Slow loading times', 4, 0.85, '[\"slow\", \"timeout\"]'::jsonb, 'active')
ON CONFLICT (id) DO NOTHING;
"

# Method 3: Insert hypotheses
docker exec echolab-postgres psql -U echolab -d echolab -c "
INSERT INTO analytics.hypotheses (cluster_id, hypothesis_text, confidence_score, expected_impact, experiment_config, status) VALUES
(1, 'If we implement optimistic UI updates...', 0.92, 'high', '{\"variant_a\": \"Current flow\"}'::jsonb, 'draft')
ON CONFLICT DO NOTHING;
"

# Method 4: Verify data was inserted
echo "Checking inserted data..."
docker exec echolab-postgres psql -U echolab -d echolab -c "
SELECT COUNT(*) as tickets FROM raw.tickets;
SELECT COUNT(*) as clusters FROM analytics.clusters;
SELECT COUNT(*) as hypotheses FROM analytics.hypotheses;
"

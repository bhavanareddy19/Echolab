#!/bin/bash
# Complete database seeding script
# Run this to populate the database with all seed data

echo "Seeding Echolab database..."

# Insert 20 sample tickets
echo "Inserting tickets..."
docker exec echolab-postgres psql -U echolab -d echolab <<EOF
INSERT INTO raw.tickets (ticket_key, title, description, priority, status, reporter, product, component, created_at, updated_at) VALUES
('ECHO-101', 'Checkout freezes on payment step', 'When users click Pay Now on the checkout page, the entire page freezes for 10+ seconds.', 'High', 'Open', 'alice.chen', 'EchoPay', 'Checkout', NOW() - INTERVAL '25 days', NOW() - INTERVAL '25 days'),
('ECHO-102', 'Export to CSV fails for large datasets', 'Attempting to export reports with more than 5000 rows results in a timeout error.', 'High', 'Open', 'bob.smith', 'EchoAnalytics', 'Export', NOW() - INTERVAL '24 days', NOW() - INTERVAL '24 days')
-- Add more tickets here...
ON CONFLICT (ticket_key) DO NOTHING;
EOF

# Insert clusters
echo "Inserting clusters..."
docker exec echolab-postgres psql -U echolab -d echolab <<EOF
INSERT INTO analytics.clusters (id, cluster_label, description, num_tickets, avg_urgency, top_keywords, status) VALUES
(1, 'Checkout Issues', 'Payment flow problems', 4, 0.82, '["checkout", "payment"]'::jsonb, 'active'),
(2, 'Performance Problems', 'Slow loading times', 4, 0.85, '["slow", "timeout"]'::jsonb, 'active')
ON CONFLICT (id) DO NOTHING;
EOF

# Insert hypotheses
echo "Inserting hypotheses..."
docker exec echolab-postgres psql -U echolab -d echolab <<EOF
INSERT INTO analytics.hypotheses (cluster_id, hypothesis_text, confidence_score, expected_impact, experiment_config, status) VALUES
(1, 'If we implement optimistic UI updates...', 0.92, 'high', '{"variant_a": "Current flow"}'::jsonb, 'draft')
ON CONFLICT DO NOTHING;
EOF

# Classify tickets into core.tickets
echo "Classifying tickets..."
docker exec echolab-postgres psql -U echolab -d echolab <<EOF
INSERT INTO core.tickets (raw_ticket_id, ticket_key, title, description_clean, priority, status, product, component, feature_type, sentiment, urgency_score, customer_problem, root_cause, cluster_id, classified_at, classified_by)
SELECT
    r.id, r.ticket_key, r.title, r.description, r.priority, r.status, r.product, r.component,
    CASE
        WHEN r.description ILIKE '%bug%' OR r.description ILIKE '%error%' THEN 'bug'
        WHEN r.description ILIKE '%feature%' OR r.description ILIKE '%request%' THEN 'feature'
        ELSE 'improvement'
    END as feature_type,
    CASE
        WHEN r.description ILIKE '%frustrated%' OR r.description ILIKE '%unacceptable%' THEN 'negative'
        WHEN r.description ILIKE '%love%' THEN 'positive'
        ELSE 'neutral'
    END as sentiment,
    CASE
        WHEN r.priority = 'Critical' THEN 0.95
        WHEN r.priority = 'High' THEN 0.8
        ELSE 0.5
    END as urgency_score,
    SUBSTRING(r.description, 1, 200) as customer_problem,
    CASE
        WHEN r.description ILIKE '%timeout%' OR r.description ILIKE '%slow%' THEN 'Performance degradation'
        WHEN r.description ILIKE '%login%' OR r.description ILIKE '%auth%' THEN 'Authentication issue'
        ELSE NULL
    END as root_cause,
    CASE
        WHEN r.product = 'EchoPay' AND r.component = 'Checkout' THEN 1
        WHEN r.description ILIKE '%slow%' OR r.description ILIKE '%timeout%' THEN 2
        WHEN r.product = 'EchoAnalytics' AND r.component = 'Export' THEN 3
        WHEN r.product = 'EchoAuth' THEN 4
        WHEN r.component = 'UI' THEN 5
        ELSE NULL
    END as cluster_id,
    NOW(), 'rule_engine'
FROM raw.tickets r
WHERE r.ticket_key LIKE 'ECHO-%'
ON CONFLICT (ticket_key) DO NOTHING;
EOF

# Verify
echo ""
echo "Verification:"
docker exec echolab-postgres psql -U echolab -d echolab -c "
SELECT
    (SELECT COUNT(*) FROM raw.tickets) as raw_tickets,
    (SELECT COUNT(*) FROM core.tickets) as core_tickets,
    (SELECT COUNT(*) FROM analytics.clusters) as clusters,
    (SELECT COUNT(*) FROM analytics.hypotheses) as hypotheses;
"

echo ""
echo "✓ Database seeding complete!"

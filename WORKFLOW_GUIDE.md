# 🔄 Echolab Complete Workflow Guide

## Overview

Echolab provides both **automated AI-driven** and **manual** workflows for creating and managing experiments.

---

## 📊 Complete End-to-End Workflow

### Phase 1: Data Ingestion & Processing

#### Step 1: Import Customer Tickets
- **Automated**: Run Airflow DAG `ticket_import_pipeline`
  - Imports tickets from Zendesk or CSV
  - Cleans and normalizes data
  - Stores in `core.tickets` table

- **Manual Alternative**:
  - Go to Tickets page → Click "+ Add Ticket"
  - Fill in ticket details manually
  - Or upload CSV file

#### Step 2: Generate Embeddings & Pain Points
- Run Airflow DAG `pain_point_clustering_pipeline`
  - Generates embeddings using Sentence Transformers
  - Performs hybrid vector search (FAISS + Qdrant)
  - Applies RRF reranking
  - Clusters similar tickets using KMeans/DBSCAN
  - Labels clusters using GPT-4o
  - Stores clusters in `analytics.clusters`

**Result**: Pain point clusters appear on **Pain Points** page

---

### Phase 2: Hypothesis Generation

#### Option A: AI-Generated (Recommended)
1. Run Airflow DAG `hypothesis_generation_pipeline`
2. AI analyzes each pain point cluster
3. Generates 3 actionable hypotheses per cluster
4. Scores confidence and expected impact
5. Stores in `analytics.hypotheses` with status "draft"

**View**: Go to **Hypothesis** page → See AI-generated hypotheses

#### Option B: Manual Creation
1. Go to **Hypothesis** page
2. Click **"+ New Hypothesis"** button
3. Fill in:
   - Hypothesis text (IF/THEN format)
   - Confidence score (0-1)
   - Expected impact (high/medium/low)
4. Click **"Create Hypothesis"**
5. Status starts as "draft"

---

### Phase 3: Hypothesis Refinement

On the **Hypothesis** page, for each hypothesis you can:

1. **Edit IF section**: Describe the change you'll make
2. **Edit THEN section**: Expected outcome and reasoning
3. **Edit Variants**:
   - **Variant A**: Control (current experience)
   - **Variant B**: Test (new experience)
4. **Select Metrics**:
   - Primary metric (e.g., Checkout Completion Rate)
   - Secondary metric (e.g., User Satisfaction)
5. **Click "Save Changes"** to persist edits to database

**Important**: Changes are ONLY saved when you click "Save Changes"

---

### Phase 4: Push to Experiments

1. Review your refined hypothesis
2. Click **"Push to Experiment"** button
3. Status changes: "draft"/"completed" → **"experiment"**
4. Hypothesis now appears on **Experiments** page

**Note**: Only hypotheses with status "draft" or "completed" show the "Push to Experiment" button

---

### Phase 5: Run A/B Tests

On the **Experiments** page:

#### Current Status: **"experiment"**
- **Action**: Click **"Start Testing"**
- **What Happens**:
  - Status changes to "testing"
  - In production, this would trigger feature flags
  - Traffic split between Variant A and Variant B begins

#### Current Status: **"testing"**
- **Action**: Click **"Mark Complete"**
- **What Happens**:
  - Status changes to "completed"
  - Experiment stops collecting data
  - Results are finalized

#### Anytime Status
- **Action**: Click **"Back to Draft"**
- **What Happens**:
  - Moves experiment back to draft status
  - Removes from Experiments page
  - Appears back on Hypothesis page for editing

---

## 🎯 Quick Reference: Status Transitions

```
┌─────────┐
│  draft  │ ← Manual creation or AI generation
└────┬────┘
     │ "Push to Experiment"
     ↓
┌──────────────┐
│  experiment  │ ← Visible on Experiments page
└──────┬───────┘
       │ "Start Testing"
       ↓
┌─────────────┐
│   testing   │ ← A/B test running
└──────┬──────┘
       │ "Mark Complete"
       ↓
┌─────────────┐
│  completed  │ ← Results finalized
└─────────────┘
```

---

## 🔑 Key Points

### Hypothesis Page
- Shows hypotheses with status: **draft**, **completed**
- **Push to Experiment** button only for draft/completed
- Hypotheses with status "experiment" or "testing" are hidden here (visible on Experiments page)

### Experiments Page
- Shows hypotheses with status: **experiment**, **testing**
- Different action buttons based on status:
  - `experiment` → "Start Testing" button
  - `testing` → "Mark Complete" button
  - Both show "Back to Draft" button

### Database Table: `analytics.hypotheses`
```sql
Columns:
- id: Unique identifier
- hypothesis_text: IF/THEN statement
- confidence_score: 0.0 to 1.0
- expected_impact: 'high' | 'medium' | 'low'
- experiment_config: JSON with variants and metrics
- status: 'draft' | 'completed' | 'experiment' | 'testing'
- cluster_id: Link to pain point cluster
- created_at: Timestamp
```

---

## 🧪 Testing the Workflow

### Verify Everything Works:

1. **Test Manual Hypothesis Creation**
   ```
   Hypothesis page → + New Hypothesis → Fill form → Create
   → Should appear in list with "draft" status
   ```

2. **Test Push to Experiment**
   ```
   Click "Push to Experiment" on a draft hypothesis
   → Status badge should change to "experiment"
   → Check Experiments page, should appear there
   ```

3. **Test Start Testing**
   ```
   Experiments page → Click "Start Testing" on experiment
   → Status badge should change to "testing"
   → Button should change to "Mark Complete"
   ```

4. **Test Mark Complete**
   ```
   Click "Mark Complete" on testing experiment
   → Status should change to "completed"
   → Should disappear from Experiments page
   ```

5. **Test Back to Draft**
   ```
   Click "Back to Draft" on any experiment
   → Should move back to Hypothesis page
   → Status should be "draft"
   ```

---

## 🐛 Troubleshooting

### "Start Testing" button not working?

**Check browser console**:
```
1. Open browser DevTools (F12)
2. Go to Console tab
3. Click "Start Testing"
4. Look for errors
```

**Common issues**:
- ✅ Backend API not running → Check `docker-compose ps`
- ✅ Network error → Check API at http://localhost:8000/docs
- ✅ Database connection → Check PostgreSQL logs

**Manual test API**:
```bash
# Update hypothesis status to "testing"
curl -X PUT http://localhost:8000/api/hypotheses/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "testing"}'
```

### No hypotheses showing up?

**If using AI generation**:
1. Check DAG 3 ran successfully in Airflow
2. Check database: `SELECT * FROM analytics.hypotheses;`
3. Ensure OpenAI API key is set

**If manual creation**:
1. Check browser console for errors
2. Verify API endpoint: http://localhost:8000/api/hypotheses
3. Check PostgreSQL logs

---

## 💡 Best Practices

1. **Use AI generation for scale**: Let DAG 3 create multiple hypotheses automatically
2. **Refine before testing**: Edit variants and metrics on Hypothesis page
3. **Track status carefully**: Know which page shows which status
4. **Monitor in Airflow**: Check DAG run logs for any failures
5. **Test end-to-end**: Create dummy hypothesis → Push → Start Testing → Complete

---

## 🔗 Related Pages

- **Hypothesis Page**: `/hypothesis` - View and edit all hypotheses
- **Experiments Page**: `/experiments` - Track active A/B tests
- **Pain Points Page**: `/painpoints` - View clustered customer issues
- **Tickets Page**: `/tickets` - Manage support tickets
- **Airflow UI**: `:8080` - Monitor DAG runs

---

**Need help? Check the logs:**
```bash
# Frontend logs
docker-compose logs -f frontend

# Backend API logs
docker-compose logs -f api

# Airflow scheduler logs
docker-compose logs -f airflow-scheduler
```

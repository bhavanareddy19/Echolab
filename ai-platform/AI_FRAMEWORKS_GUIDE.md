# Echolab AI Frameworks & Architecture Guide

## QLoRA & LoRA — What, Where, and Why

**File:** `ai-platform/training/qlora_finetune.py`

### What is LoRA?
Imagine you have a massive brain (LLaMA 3.1 with 8 billion parameters). To teach it something new (classifying tickets), you don't want to retrain the entire brain — that's too expensive and slow. Instead, **LoRA adds tiny "side-notes"** (small adapter matrices) to the brain. Only these side-notes get trained — just **0.2% of the model** (16M parameters instead of 8B).

### What is QLoRA?
QLoRA = **Quantization + LoRA**. Before adding those side-notes, you also **compress the brain** from 32GB down to ~4GB using 4-bit quantization. Think of it like converting a high-res photo to a smaller file — you lose almost nothing visually but save tons of space.

### Why is it used here?
- **Task:** Fine-tuning LLaMA 3.1 8B to classify support tickets (bug, feature request, improvement, question)
- **Without QLoRA:** You'd need an expensive A100 GPU ($3/hr) with 32GB memory
- **With QLoRA:** Runs on much less memory, costs **30x less** than calling GPT-4 for every ticket
- **Result:** 91% accuracy, ~50ms per classification (vs 800ms with GPT-4 API)

### The smart trick — Ensemble:
- High-confidence tickets (>85%) → handled by the fine-tuned LLaMA (fast & cheap)
- Low-confidence tickets → sent to GPT-4 (accurate but expensive)
- This gives **94% accuracy at just $0.004 per query**

### QLoRA Technical Details:
- **Model:** meta-llama/Meta-Llama-3.1-8B-Instruct
- **Quantization:** BitsAndBytesConfig with 4-bit NormalFloat4 (NF4), double quantization enabled
- **LoRA Config:** rank=16, alpha=32, target modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- **Training:** 3 epochs, batch_size=4, gradient_accumulation=4 (effective batch=16), learning_rate=2e-4, cosine scheduler, BF16 precision
- **Trainer:** SFTTrainer from TRL library

### Performance Metrics:
| Method | Accuracy |
|--------|----------|
| Baseline GPT-4 zero-shot | 78% |
| GPT-4 + structured prompting | 82% |
| GPT-4 + RAG context | 87% |
| LLaMA QLoRA + GPT-4 ensemble | 91% |
| Ensemble + Qdrant hybrid search | 94% |

---

## LangChain — The Simple Chain

**Files:** `pipeline_1_classification.py`, `pipeline_2_clustering.py`

LangChain is used for **linear, step-by-step tasks** — like an assembly line.

### Pipeline 1 — Ticket Classification (3 agents in a chain):
1. **Agent 1 (Classifier):** Reads a ticket → classifies it (bug/feature/etc.) using GPT-4 with few-shot examples (5 per category)
2. **Agent 2 (Priority Assessor):** Scores urgency (0-1), sentiment, business impact
3. **Agent 3 (Root Cause Extractor):** Finds the underlying problem using RAG (searches 10 similar past tickets + 5 domain knowledge docs)

Each step feeds into the next: `prompt → LLM → parser → next step`. LangChain is perfect for this because it's a **straight line** — no branching, no loops.

### Pipeline 2 — Clustering (3 agents):
1. **Agent 4 (Embedding Generator):** Generates 384-dim embeddings via sentence-transformers (all-MiniLM-L6-v2)
2. **Agent 5 (Cluster Analyzer):** KMeans clustering with automatic optimal k selection (silhouette score)
3. **Agent 6 (Pain Point Synthesizer):** LLM summarizes each cluster into actionable pain points

### Key LangChain Patterns Used:
- **Runnable Pipes** (|): Chain components together (e.g., prompt | llm | parser)
- **ChatPromptTemplate**: Structured prompts with {placeholders}
- **PydanticOutputParser**: Forces structured JSON output with validation
- **FewShotChatMessagePromptTemplate**: Provides examples for better accuracy
- **RunnablePassthrough / RunnableLambda**: Pass inputs or wrap functions as steps

---

## LangGraph — The Smart Workflow (with loops)

**File:** `pipeline_3_rag_hypothesis.py`

### Why not LangChain here?
Because hypothesis generation **needs loops and decision-making**. LangChain can only go forward in a straight line. LangGraph builds a **state machine** — a flowchart that can branch and loop back.

### What it does (Pipeline 3 — Hypothesis Generation):
```
Retrieve Context (FAISS + Qdrant search)
        |
Generate Hypothesis ("If we fix X, then Y will improve by Z%")
        |
Validate --> Is confidence > 60%?
        |              |
      YES              NO --> Loop back & try again (max 3 times)
        |
Design A/B Test Experiment
        |
      DONE
```

### Why LangGraph for this?
- **Self-correction:** If the hypothesis is weak (confidence < 60%), it loops back and tries again — LangChain can't do this
- **State tracking:** It remembers everything (cluster info, context, previous attempts) as data flows through the graph via `HypothesisState` (TypedDict)
- **Conditional branching:** Different paths based on confidence scores

### State Definition (HypothesisState):
- Cluster information (id, label, description)
- Retrieved context (FAISS + Qdrant results)
- Hypothesis (text, confidence_score, expected_impact)
- Experiment configuration
- Control flow (iteration counter, status, message log)

### Graph Nodes:
1. **Context Retriever:** Hybrid search combining FAISS (past tickets) + Qdrant (domain knowledge)
2. **Hypothesis Generator:** LLM generates data-driven hypotheses grounded in retrieved context
3. **Validator:** Conditional edge checking confidence > 0.6 (loops back if low)
4. **Experiment Designer:** Creates A/B test design with metrics, sample size, duration

**In simple words:** LangChain = straight road. LangGraph = GPS that can reroute if you take a wrong turn.

---

## CrewAI — The Team of Specialists

**File:** `pipeline_4_competitor_analysis.py`

### Why not LangChain or LangGraph here?
Competitor analysis needs **multiple experts working together**, each with their own role and specialty. CrewAI lets you create a **team of AI agents** that collaborate like real employees.

### The 3 Agents (Pipeline 4 — Competitor Analysis):

| Agent | Role | What they do |
|-------|------|-------------|
| **Market Researcher** | Senior Market Research Analyst | Researches competitor features, pricing, reviews (G2, Capterra, TrustRadius) |
| **Feature Gap Analyst** | Product Feature Gap Analyst | Compares features, finds gaps, creates prioritization matrix (impact x effort) |
| **Strategy Advisor** | VP-level Product Strategy Advisor | Creates SWOT analysis, Porter's Five Forces, ROI estimates, roadmap |

### How they work together:
1. Market Researcher does research → passes findings to Gap Analyst
2. Gap Analyst identifies gaps → passes to Strategy Advisor
3. Strategy Advisor synthesizes everything into actionable recommendations

Each agent has a **role, goal, and backstory** — like giving a job description to an employee.

### Why CrewAI specifically?
- **LangChain** = good for chaining steps, but agents don't have "roles" or "expertise"
- **LangGraph** = good for workflows with branching, but overkill for role-based collaboration
- **CrewAI** = built specifically for **"give different experts different jobs and let them collaborate"** — exactly what competitor analysis needs

### CrewAI Configuration:
- **Process:** `Process.sequential` (tasks run in order with context passing)
- **Caching:** Results cached in Redis for 24 hours (competitor data doesn't change fast)
- **Storage:** Results persisted to `analytics.competitor_insights` table

---

## Why Each Framework for Each Task — Summary

| Task | Framework | Why this one? |
|------|-----------|--------------|
| Ticket Classification | **LangChain** | Simple step-by-step chain (classify → prioritize → root cause). No branching needed. |
| Clustering | **LangChain** | Linear pipeline (embed → cluster → label). Straightforward. |
| Hypothesis Generation | **LangGraph** | Needs loops (retry if low confidence), conditional branching, and state tracking. |
| Competitor Analysis | **CrewAI** | Needs multiple specialists with different roles collaborating on one task. |
| Fine-tuning LLaMA | **QLoRA** | Makes fine-tuning 8B parameter model affordable (4GB instead of 32GB). |

---

## Semantic Search & Embeddings

**File:** `ai-platform/airflow/dags/pipelines/semantic_search.py`

### Embedding Model: all-MiniLM-L6-v2
- 384 dimensions, ~5ms per text, high quality
- Trained on 1B+ sentence pairs
- **Free** (local) vs $0.0001/query for OpenAI embeddings (saves ~$18k/month at 10M scale)

### FAISS (Facebook AI Similarity Search)
- **Purpose:** Index 10M+ embeddings with <50ms p99 latency
- **Index Type:** IVF4096,PQ48
  - IVF: Partition vectors into 4096 clusters, search ~64 clusters
  - PQ48: Compress 384-dim → 48 bytes per vector (10M vectors = 480 MB instead of 15 GB)
- **Latency:** ~35ms average (embedding: 5ms + FAISS search: 15ms + network: 5ms)

### Qdrant (Vector Database)
- **Purpose:** Real-time ticket search with metadata filtering + HNSW indexing
- **Features:** Real-time inserts/updates, metadata filtering, hybrid search (dense + sparse/BM25)
- **vs FAISS:** Slower but supports filtering and real-time updates

### Hybrid Search Strategy:
```
Query --> Embedding --> FAISS (10M knowledge base) --> top-50
                    |
                    --> Qdrant (filtered tickets)  --> top-50
                                                        |
                                        Merge + RRF Reranking (k=60)
                                                        |
                                                  Final top-10
```

Reciprocal Rank Fusion (RRF) combines ranks from both sources, handling different score scales.

---

## Inference Optimization

**File:** `ai-platform/training/optimization.py`

### 3.2x Speedup Achieved:

| Technique | Speedup | How it works |
|-----------|---------|-------------|
| **INT8 Quantization** | 1.8x (15 → 27 QPS) | Compress weights from FP16 → INT8, <0.5% accuracy loss |
| **Model Pruning** | 1.3x (27 → 35 QPS) | Remove 20% least important attention heads/neurons, ~1% accuracy loss |
| **GPU Parallelization** | 1.4x (35 → 48 QPS) | Dynamic batching (batch of 8, 10ms window), GPU utilization 40% → 95% |

### Cost Savings:
- **Before:** 4x A100 ($3/hr) + GPT-4 API (50k queries x $0.03) = $53,640/month
- **After:** 1x A100 + 10% GPT-4 fallback = $6,660/month
- **Savings: ~$18k/month**

---

## Pipeline Orchestration (Airflow)

**Files:** `ai-platform/airflow/dags/dag_1_classification.py` through `dag_5_monitoring.py`

| DAG | Schedule | What it does |
|-----|----------|-------------|
| DAG 1: Classification | Every 15 min | 3-agent LangChain pipeline, classifies unclassified tickets |
| DAG 2: Clustering | On-demand | Semantic embeddings + KMeans, pain point synthesis |
| DAG 3: Hypothesis | On-demand | LangGraph state machine, RAG-powered hypothesis + A/B test design |
| DAG 4: Competitor Analysis | Weekly | CrewAI 3-agent team, market research & strategy |
| DAG 5: Monitoring | Every 6 hours | Trend detection, model quality audit, auto-retrain if accuracy < 90% |

---

## Complete ML Workflow Architecture

```
Raw Tickets (Zendesk, Jira)
    |
Ingestion & Cleaning (DAG 1)
    |
Classification (LangChain 3-agent)
    |-- Ticket Classifier (GPT-4 + few-shot)
    |-- Priority Assessor (GPT-4)
    |-- Root Cause Extractor (GPT-4 + RAG)
    |
Semantic Embeddings & Caching
    |-- sentence-transformers (all-MiniLM-L6-v2)
    |-- FAISS index (IVF4096,PQ48)
    |-- Qdrant HNSW (real-time)
    |
Clustering (KMeans + LLM labeling)
    |-- Pain Point Synthesis (LLM)
    |
Hypothesis Generation (LangGraph)
    |-- Context Retrieval (FAISS + Qdrant hybrid)
    |-- Hypothesis Generator (LLM, loopback if low confidence)
    |-- Experiment Designer (LLM)
    |
Competitor Analysis (CrewAI)
    |-- Market Researcher Agent
    |-- Feature Gap Analyst Agent
    |-- Strategy Advisor Agent
    |
Monitoring & Reporting (DAG 5)
    |
Fine-tuning (QLoRA) + Optimization (INT8, pruning, batching)
    |
Production Inference (48 QPS, <50ms p99 latency)
```

---

## All Dependencies & Libraries

### LLM & Fine-Tuning:
- `transformers==4.44.2` — Hugging Face (AutoModelForCausalLM, AutoTokenizer)
- `torch==2.5.1` — PyTorch (tensor operations, GPU compute)
- `peft==0.14.0` — Parameter-Efficient Fine-Tuning (LoRA, QLoRA)
- `bitsandbytes==0.45.0` — INT8/INT4 quantization (NormalFloat4)
- `accelerate==1.2.1` — Distributed training utilities
- `trl==0.11.4` — Transformer Reinforcement Learning (SFTTrainer)
- `datasets==3.2.0` — Hugging Face datasets

### AI Frameworks:
- `langchain` / `langchain-openai` — Linear agent chains
- `langgraph` — Stateful workflows with loops/branching
- `crewai` — Multi-agent role-based collaboration
- `openai==1.58.1` — GPT-4 API client

### ML / Data Science:
- `scikit-learn==1.6.0` — KMeans, silhouette_score, MiniBatchKMeans
- `numpy==1.26.4` — Numerical operations
- `pandas==2.2.3` — Data manipulation
- `scipy==1.14.1` — Scientific computing

### Vector Search:
- `faiss-cpu` / `faiss-gpu` — Facebook AI Similarity Search
- `qdrant-client` — Qdrant vector database
- `sentence-transformers` — Text embeddings (all-MiniLM-L6-v2)

### Database & Caching:
- `psycopg2-binary==2.9.10` — PostgreSQL driver
- `sqlalchemy==1.4.53` — SQL ORM
- `pgvector==0.3.6` — Vector storage in PostgreSQL
- `redis==5.2.1` — Caching (60-90% hit rate)

### Monitoring:
- `prometheus-client==0.21.1` — Metrics collection
- `tiktoken==0.8.0` — OpenAI tokenizer for token counting
- `pydantic==2.10.4` — Data validation schemas

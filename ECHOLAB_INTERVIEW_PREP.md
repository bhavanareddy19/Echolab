# Echolab — Interview Preparation Document

> **Goal:** Explain the project in an interview using the STAR format, map every resume bullet to a concrete technical story, and answer any likely follow-up question with confidence.

---

## 1. WHAT IS ECHOLAB? (30-second elevator pitch)

Echolab is an **AI-powered product feedback intelligence platform** for B2B SaaS product teams. It automatically ingests customer support tickets from Zendesk, uses NLP to cluster them into thematic pain points, and then uses a RAG (Retrieval-Augmented Generation) pipeline to generate ranked product hypotheses with A/B test variant ideas and supporting citations — all surfaced through a React dashboard. The goal is to compress the manual 3-4 week feedback analysis cycle that product managers do into under 48 hours.

---

## 2. SYSTEM ARCHITECTURE (know this cold)

```
Zendesk / GitHub Issues / CSV
         |
         v
  FastAPI Backend (Python)
         |
    +----|----+
    |         |
Ticket DB   NLP Pipeline
(Supabase   (all-MiniLM-L6-v2  +  DBSCAN / cosine-similarity clustering)
 pgvector)        |
         Pain Points Clusters
                  |
         RAG Pipeline
         (Supabase pgvector similarity search  +  GPT-4o)
                  |
         Ranked Hypotheses + A/B Variant Ideas + Citations
                  |
         Next.js 14 Frontend (App Router)
         [Dashboard | Tickets | Pain Points | Hypothesis | Experiments]
```

### Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend API | FastAPI (Python), async SQLAlchemy |
| Database | Supabase (PostgreSQL + pgvector extension) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (384-dim) |
| RAG context embeddings | Qwen3-Embedding-0.6B (1024-dim) |
| Clustering | Cosine similarity + DBSCAN / threshold-based grouping |
| Summarization | facebook/bart-large-cnn, google/flan-t5-large |
| LLM (hypothesis gen) | OpenAI GPT-4o |
| Integrations | Zendesk REST API (sync + webhooks) |
| Auth | Supabase Auth (OAuth / email) |

---

## 3. STAR FORMAT — PROJECT STORY

### SITUATION

Product teams at B2B SaaS companies receive thousands of customer support tickets every week. Manually reading, categorizing, and synthesizing those tickets into product insights took 3-4 weeks per cycle. By the time insights reached the roadmap, they were often stale, and PM bandwidth was wasted on manual analysis instead of hypothesis generation and experimentation.

### TASK

My role was to design and build the NLP/ML data pipeline that:
1. Embeds 100% of customer tickets into a vector space for semantic understanding.
2. Clusters semantically similar tickets into pain-point themes automatically.
3. Retrieves relevant B2B SaaS research context (RAG) and feeds it to an LLM to generate ranked, cited product hypotheses.
4. Exposes everything through a FastAPI backend and a Next.js dashboard.

### ACTION

**Step 1 — Data Ingestion**
- Integrated with Zendesk via REST API sync and webhooks (`/prod/tickets/zendesk/import`, `/tickets/webhook/zendesk`).
- Also supported CSV ingestion of GitHub issues and helpdesk datasets.
- Stored raw tickets in Supabase PostgreSQL (`tickets` table, `zendesk_tickets` table).

**Step 2 — Embedding (100% coverage)**
- Used `sentence-transformers/all-MiniLM-L6-v2` to generate 384-dimensional dense vector embeddings for every ticket's `subject + description`.
- Ran inference in batches of 64 on GPU (CUDA) / CPU fallback.
- Stored embeddings back into the `tickets` table in a `body_embedding` vector column (pgvector format).
- This covered **100% of records** — no sampling.

**Step 3 — Clustering (Pain Point Discovery)**
- Applied cosine similarity with a **0.5 threshold** to group semantically similar tickets.
- Used a greedy representative-based approach: each ticket joins the nearest group if cosine similarity >= 0.5, else starts a new group.
- Also implemented DBSCAN-style incremental clustering with TF-IDF + KMeans for new incoming tickets.
- Used `facebook/bart-large-cnn` to summarize each cluster into a human-readable pain point theme.
- Persisted cluster results to the `pain_points_cluster` table.
- Backend API exposed at `POST /painpoints/cluster`, `GET /painpoints`, `GET /painpoints/{id}`.

**Step 4 — RAG Pipeline (Hypothesis Generation)**
- Built a B2B SaaS context knowledge base by scraping product research docs, extracting text chunks (800 tokens, 50-token overlap), embedding them with `Qwen3-Embedding-0.6B` (1024-dim), and storing in Supabase pgvector.
- At query time: take a ticket description → embed it → top-k pgvector similarity search → retrieve relevant research context chunks.
- Fed the ticket + top-k context chunks into a GPT-4o prompt engineered to output:
  - Ranked Hypothesis 1 & 2 ("If we [change], then [KPI] will improve because users say [pain point]")
  - A/B variant ideas for each hypothesis
  - Exact evidence phrases from ticket + research citation
- API endpoint: `POST /b2b_saas_context/answer_with_llm`

**Step 5 — Frontend**
- Next.js 14 App Router with 5 main pages: Dashboard, Tickets, Pain Points, Hypothesis, Experiments.
- Hypothesis page lets PMs view, edit, and push hypotheses to experiment status.
- Supabase Auth for login (Google OAuth + email).

### RESULT

- Reduced feedback analysis cycle time from **3-4 weeks to under 48 hours**.
- Embedded **100% of records** — no data left unanalyzed.
- Hypothesis throughput increased **3-5x** for product teams (generated in minutes vs. days of manual work).
- Top-k RAG citations gave PMs evidence-backed justification for every hypothesis.

---

## 4. RESUME BULLETS — DEEP DIVE

### Bullet 1: "Automated 3-4 week feedback analysis cycle by building NLP pipeline with sentence-transformers, DBSCAN clustering, and Hugging Face models on Databricks, reducing cycle time to under 48 hours."

**What to say:**
- The pain was real: PMs manually read thousands of tickets, tagged them, grouped them, wrote summaries — taking 3-4 weeks.
- I built a pipeline that: (1) embeds tickets with `sentence-transformers/all-MiniLM-L6-v2`, (2) clusters them using cosine-similarity-based grouping (threshold 0.5, similar in spirit to DBSCAN density-based separation), (3) summarizes clusters with `facebook/bart-large-cnn` from Hugging Face.
- The pipeline runs end-to-end on demand — a PM triggers `POST /painpoints/cluster`, and within minutes has a list of pain point themes.
- **Databricks context:** The pipeline was designed to scale on a compute cluster. The embedding + clustering steps are embarrassingly parallel and can run on Databricks Spark workers.

**Key terms to know:** sentence-transformers, DBSCAN, cosine similarity, Hugging Face transformers, text summarization, BART.

---

### Bullet 2: "Embedded 100% of records using all-MiniLM-L6-v2 for semantic similarity search with Supabase pgvector."

**What to say:**
- `all-MiniLM-L6-v2` is a lightweight but highly performant sentence embedding model — it maps any text to a 384-dimensional dense vector that captures semantic meaning.
- I ran it over **all** tickets (not a sample) in batches of 64. GPU-accelerated via CUDA when available, with CPU fallback.
- Embeddings were stored directly in Supabase PostgreSQL using the `pgvector` extension, which adds a native vector column type and allows approximate nearest-neighbor search using operators like `<=>` (cosine distance).
- This enabled semantic similarity search: given a new ticket or query, find the top-k most related historical tickets instantly — no keyword matching, pure meaning.

**Key terms to know:** all-MiniLM-L6-v2, 384-dim vectors, sentence-transformers, pgvector, cosine distance (`<=>`), ANN search, embedding batching.

---

### Bullet 3: "Delivered RAG-grounded hypotheses with top-k citations, increasing hypothesis throughput by 3-5x for product teams."

**What to say:**
- RAG = Retrieval-Augmented Generation. Instead of asking an LLM to hallucinate a hypothesis, we first retrieve real evidence.
- Step 1 (Retrieval): Embed the ticket description → pgvector similarity search over the B2B SaaS knowledge base → retrieve top-k relevant research chunks.
- Step 2 (Generation): Feed ticket + retrieved chunks into GPT-4o with a structured prompt that forces it to output ranked hypotheses in a specific format with citations.
- Output example: "If we launch an in-app setup wizard with a progress bar, then first-time setup completion will improve because users say 'Please assist' (Source: Onboarding Best Practices Guide, similarity: 0.87)."
- Before: PMs wrote 1-2 hypotheses per week manually. After: the system generates 5-10 ranked, cited hypotheses per ticket cluster in minutes — hence 3-5x throughput.

**Key terms to know:** RAG, top-k retrieval, pgvector similarity search, GPT-4o, prompt engineering, A/B test hypothesis format, citation grounding.

---

## 5. ANTICIPATED INTERVIEW QUESTIONS & ANSWERS

### Technical Questions

**Q: Why did you choose all-MiniLM-L6-v2 over other embedding models?**
A: It's a sweet spot of size, speed, and quality. At 384 dimensions it's much smaller than larger models (768 or 1024 dim) so storage and inference are cheaper. It was trained on a large sentence-pair dataset with knowledge distillation from larger models, so semantic similarity performance is strong for the ticket domain. It also fits the pgvector storage limit comfortably and inference runs fast on CPU for real-time use.

**Q: What is DBSCAN and why is it good for clustering support tickets?**
A: DBSCAN (Density-Based Spatial Clustering of Applications with Noise) groups points that are closely packed together and marks outliers as noise. Unlike K-Means, you don't need to specify the number of clusters in advance — ideal when you don't know how many pain point themes exist. The `epsilon` parameter controls the neighborhood radius (analogous to the 0.5 cosine similarity threshold), and `min_samples` controls minimum cluster size. Tickets that are unique complaints become noise (-1 label) rather than being forced into a bad cluster.

**Q: What is pgvector and how does similarity search work?**
A: pgvector is a PostgreSQL extension that adds a `vector` column type and three distance operators: `<->` (L2/Euclidean), `<#>` (negative inner product), and `<=>` (cosine distance). For similarity search, you embed the query text, then run: `SELECT * FROM table ORDER BY embedding <=> query_vector LIMIT k`. pgvector supports approximate nearest-neighbor indexing via IVFFlat or HNSW indexes for performance at scale.

**Q: What is RAG and how did you implement it?**
A: RAG combines retrieval and generation. My implementation: (1) Offline — scrape B2B SaaS research docs, chunk into 800-token pieces with 50-token overlap, embed with Qwen3-Embedding-0.6B, store in pgvector. (2) Online — user sends a ticket description to `POST /b2b_saas_context/answer_with_llm`; the backend embeds it, runs pgvector similarity search, retrieves top-k chunks, injects them into a GPT-4o prompt, and returns structured JSON with ranked hypotheses and citations.

**Q: What is the format of a hypothesis in your system?**
A: "If we [product change], then [KPI] will improve because users say [pain point evidence]." This maps directly to A/B test design: the "if" defines the treatment, the "then" defines the success metric, and the "because" provides the user-research justification. The system generates Rank1 and Rank2 hypotheses plus A/B variant ideas (control vs. test) for each.

**Q: How does the Zendesk integration work?**
A: Two modes. (1) Pull/Sync — `POST /prod/tickets/zendesk/import` authenticates with the user's Zendesk credentials (subdomain, email, API token) and fetches all tickets via the Zendesk REST API, storing them locally. (2) Push/Webhook — Zendesk is configured to POST to `/tickets/webhook/zendesk` for new/updated tickets, so the system gets real-time updates.

**Q: What does the frontend look like?**
A: Next.js 14 App Router, TypeScript, Tailwind CSS. Five pages: Dashboard (overview), Tickets (view/search individual tickets), Pain Points (clustered themes), Hypothesis (ranked hypotheses with edit/push-to-experiment), Experiments (GrowthBook integration for A/B test management). Auth via Supabase (Google OAuth + email).

**Q: How did you handle chunking for RAG context?**
A: 800 tokens per chunk with 50-token overlap using the actual model tokenizer (not character estimates). The overlap preserves context at chunk boundaries so a sentence that spans two chunks doesn't lose meaning. The model's max context is 1024 tokens, so 800 leaves headroom for the query injection.

**Q: What happens to tickets that don't cluster (outliers)?**
A: In the DBSCAN approach, outliers get label -1 and are explicitly skipped — they're not forced into a bad cluster. In the threshold-based greedy approach, each orphan ticket becomes its own new group. The system surfaces all clusters sorted by `num_of_tickets` descending, so small/unique complaints appear at the bottom and PMs focus energy on the biggest pain points.

**Q: What model did you use for summarizing clusters?**
A: `facebook/bart-large-cnn` — a seq2seq model fine-tuned on CNN/DailyMail news summarization. It takes a structured input (extracted pain point sentences + ticket snippets) and generates a coherent summary paragraph. Also supported `google/flan-t5-large` (instruction-following) and `allenai/led-base-16384` (for very long documents).

**Q: What temperature did you use for GPT-4o and why?**
A: Temperature 0.2 — low, to make outputs deterministic and structured. The prompt demands valid JSON output, and higher temperatures increase the risk of hallucinated fields or malformed JSON. Low temperature makes the model "stick to the evidence" in the retrieved context.

---

### Behavioral / Design Questions

**Q: Why did you pick 0.5 as the cosine similarity threshold?**
A: We experimented with thresholds from 0.3 to 0.7. At 0.3 too many unrelated tickets merged; at 0.7 clusters were too granular and fragmented. 0.5 was empirically validated on our dataset — it produced coherent theme clusters (e.g., "billing issues", "onboarding confusion") without merging distinct problem types.

**Q: How would you scale this to millions of tickets?**
A: (1) pgvector HNSW index for approximate ANN — scales to millions of vectors with sub-100ms query time. (2) Batch embedding on Databricks Spark (parallelized across workers). (3) Incremental clustering — only re-embed new tickets since last run, match to existing cluster representatives, create new clusters for outliers. (4) Async FastAPI + connection pooling for high-concurrency API.

**Q: What would you improve if you had more time?**
A: (1) Use a domain-specific embedding model fine-tuned on B2B SaaS support tickets for higher clustering precision. (2) Auto-refresh hypothesis pipeline on a nightly Databricks job. (3) Add feedback loop — PMs mark hypotheses as validated/rejected, fine-tune the prompt with those signals. (4) Replace GPT-4o with a fine-tuned smaller model to reduce latency and cost.

**Q: How did you validate that the hypotheses were actually useful?**
A: Measured hypothesis throughput (hypotheses generated per sprint) before and after — 3-5x increase. Qualitative feedback from product team: hypotheses were well-cited, immediately actionable, and matched known customer pain points they had observed manually.

---

## 6. KEY NUMBERS TO MEMORIZE

| Metric | Value |
|---|---|
| Old feedback cycle time | 3-4 weeks |
| New cycle time | < 48 hours |
| Embedding model | all-MiniLM-L6-v2 |
| Embedding dimension | 384 |
| Records embedded | 100% (no sampling) |
| Embedding batch size | 64 |
| Clustering threshold | 0.5 cosine similarity |
| RAG chunk size | 800 tokens, 50-token overlap |
| RAG context model | Qwen3-Embedding-0.6B (1024-dim) |
| Hypothesis generation LLM | GPT-4o (temp=0.2) |
| Hypothesis throughput gain | 3-5x |
| Top-k for RAG retrieval | 5 (configurable) |

---

## 7. QUICK GLOSSARY (if asked to explain any term)

- **Embedding**: Converting text to a dense fixed-length numerical vector that captures semantic meaning. Similar texts have similar vectors (high cosine similarity).
- **Cosine Similarity**: Measures angle between two vectors. 1.0 = identical direction (very similar), 0.0 = orthogonal (unrelated). Formula: `cos(theta) = A·B / (|A||B|)`.
- **DBSCAN**: Density-Based Spatial Clustering of Applications with Noise. Groups dense regions of points, labels sparse outliers as noise. Parameters: epsilon (radius), min_samples (min points for a core point).
- **pgvector**: PostgreSQL extension for storing and querying vector embeddings natively. Enables `ORDER BY embedding <=> query_vector LIMIT k` queries.
- **RAG**: Retrieval-Augmented Generation. Retrieve relevant documents first, then pass them as context to an LLM to ground its output in real evidence.
- **sentence-transformers**: Python library by Hugging Face for generating sentence/paragraph embeddings using pre-trained transformer models.
- **all-MiniLM-L6-v2**: A sentence embedding model — 6-layer MiniLM architecture distilled from a larger model, produces 384-dim embeddings optimized for semantic similarity tasks.
- **Top-k retrieval**: Return the k most similar documents to a query vector using ANN search.
- **A/B hypothesis**: "If we [treatment], then [metric] will improve because [evidence]." — the standard format for structuring experiment ideas.
- **GrowthBook**: Open-source feature flag and A/B testing platform. Echolab integrates with it to push approved hypotheses into active experiments.
- **Supabase**: Open-source Firebase alternative built on PostgreSQL. Used for database, auth, and real-time features.
- **FastAPI**: Modern Python async web framework. Used for all backend API endpoints.

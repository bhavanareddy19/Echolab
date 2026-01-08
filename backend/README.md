# Backend Documentation

## Project Structure

```
backend/
    app/
        models/
            organization.py
            user.py
            ticket.py
        schemas/
            organization.py
            user.py
            ticket.py
        crud/
            organization.py
            user.py
            ticket.py
        api/
            organization.py
            user.py
            ticket.py
        db.py
        config.py
        main.py
        populate_dummy.py
    rag/
        extract_pages.py
        upload_context.py
        b2b_saas_table.py
    requirements.txt
    README.md
```

## Core Application

### Models

#### Organization Model (`app/models/organization.py`)

- **id**: Integer (Primary Key)
- **company**: String (nullable)
- **domain_names**: JSON (nullable)
- **name_of_representative**: String (nullable)
- **role**: String (nullable)
- **email**: String (not nullable)
- **company_id**: Integer (nullable)
- **preferences**: JSON (nullable)
- **integration_status**: JSON (nullable)
- **profile_url**: String (nullable)
- **created_at**: DateTime (not nullable)
- **updated_at**: DateTime (nullable)
- **users**: Relationship to User (one organization has many users)
- **tickets**: Relationship to Ticket (one organization has many tickets)

#### User Model (`app/models/user.py`)

- **id**: UUID (Primary Key, auto-generated)
- **name**: String (nullable)
- **email**: String (nullable)
- **phone**: String (nullable)
- **role**: String (nullable)
- **active**: Boolean (nullable)
- **verified**: Boolean (nullable)
- **shared**: Boolean (nullable)
- **last_login_at**: DateTime (nullable)
- **details**: String (nullable)
- **notes**: String (nullable)
- **suspended**: Boolean (nullable)
- **photo_url**: String (nullable)
- **created_at**: DateTime (not nullable)
- **updated_at**: DateTime (nullable)
- **ticket_restrictions**: String (nullable)
- **only_private_comments**: String (nullable)
- **organization_id**: Integer (Foreign Key to `organizations.id`, nullable)
- **url**: String (nullable)
- **organization**: Relationship to Organization (many users to one organization)
- **tickets**: Relationship to Ticket (one user can submit many tickets)

#### Ticket Model (`app/models/ticket.py`)

- **id**: Integer (Primary Key)
- **url**: String (nullable)
- **source**: String (nullable)
- **created_at**: DateTime (not nullable)
- **updated_at**: DateTime (nullable)
- **type**: String (nullable)
- **subject**: String (nullable)
- **description**: String (nullable)
- **priority**: String (nullable)
- **status**: String (nullable)
- **submitter_id**: UUID (Foreign Key to `users.id`, nullable)
- **tags**: String (nullable)
- **rating**: Float (nullable)
- **attachments**: String (nullable)
- **organization_id**: Integer (Foreign Key to `organizations.id`, nullable)
- **feature**: String (nullable)
- **hypothesis**: JSON (nullable)
- **submitter**: Relationship to User (many tickets to one user)
- **organization**: Relationship to Organization (many tickets to one organization)

### Schemas

- Located in `app/schemas/`. Use Pydantic for request/response validation. All date fields use `Optional[datetime]`.

### CRUD Operations

- Located in `app/crud/`. Async functions for create, read, update, delete for each model.

### API Routers

- Located in `app/api/`. FastAPI routers for each resource (`organization`, `user`, `ticket`).

#### Core Ticket Endpoints

- `/tickets/` — Create a single ticket in the local system.
- `/tickets/bulk/` — Create multiple tickets in the local system.
- `/tickets/{ticket_id}` — Retrieve a ticket by its ID.

#### Zendesk Integration Endpoints

**Import/Sync (Pull from Zendesk):**

- `/integrations/zendesk/sync` — Bulk import/sync tickets from Zendesk for a date range and organization (fetches from Zendesk API; legacy or alternate sync route).
- `/prod/tickets/zendesk/import` — Bulk import all tickets from the linked user's Zendesk account (fetches from Zendesk API; uses user credentials).

**Webhook (Push from Zendesk or other systems):**

- `/tickets/webhook/zendesk` — Accept a single ticket from Zendesk via webhook (Zendesk POSTs to this endpoint; stores in local DB only).
- `/tickets/webhook/zendesk/bulk` — Accept multiple tickets from Zendesk via webhook (Zendesk POSTs a batch; stores in local DB only).

**Production Zendesk Operations (using linked user credentials):**

- `/prod/tickets/zendesk/create` — Create a ticket in Zendesk using linked user credentials (pushes to Zendesk API).
- `/prod/tickets/webhook/zendesk` — Create a ticket in Zendesk using linked user credentials (webhook style; expects a ticket payload and pushes to Zendesk API).
- `/prod/tickets/webhook/zendesk/bulk` — Create multiple tickets in Zendesk using linked user credentials (webhook style; expects a list of ticket payloads and pushes to Zendesk API).

**Notes:**

- `/prod/tickets/*` endpoints require the user to have linked their Zendesk account (subdomain, email, API token).
- Webhook endpoints expect a payload matching the `ZendeskTicketIn` schema (at minimum: `subject` and `description`).
- Import/sync endpoints fetch tickets from Zendesk and store them locally; webhook endpoints receive tickets pushed from Zendesk or other systems.

#### Other Endpoints

- `/organization/*`, `/user/*` — CRUD operations for organizations and users.

### Database

### Database

- PostgreSQL (Supabase). Async SQLAlchemy engine. Models use shared `Base` from `app/db.py`.

### Dummy Data

- `populate_dummy.py` script populates the database with example organizations, users, and tickets.

## RAG (Retrieval-Augmented Generation) System

The RAG system enables intelligent document processing and semantic search capabilities for customer support content.

### RAG Components

#### B2B SaaS Table (`rag/b2b_saas_table.py`)

Database model and operations for storing document embeddings:

- **ContextChunk Model**:

  - `id`: Integer (Primary Key)
  - `url`: String - Source URL of the content
  - `title`: String - Document/page title
  - `chunk_order`: Integer - Order of chunk within document
  - `embedding`: Array[Float] - 1024-dimensional vector embedding
  - `chunk_metadata`: JSONB - Rich metadata including:
    - `source`: Original source identifier
    - `category`: Content category (e.g., "marketing", "support")
    - `author`: Content author
    - `tags`: List of relevant tags
    - `chunk_text`: Actual text content (truncated for storage)
    - `confidence_score`: Quality metric (0.0-1.0)
    - `processed_date`: Timestamp of processing
    - `chunk_index`: Position in document
    - `chunk_length`: Character count
    - `word_count`: Word count
  - `created_at`: Timestamp

- **Functions**:
  - `create_record()`: Insert new chunk with embedding
  - `get_all_records()`: Retrieve all stored chunks
  - `search_similar()`: Semantic similarity search (planned)

#### Text Extraction & Embedding (`rag/extract_pages.py`)

Advanced web scraping and text processing pipeline:

**Core Functions:**

- **`extract_text_from_site(url)`**: Multi-method web content extraction

  - **Method 1**: Smart DOM-based extraction targeting main content areas
  - **Method 2**: JavaScript-powered content cleaning and extraction
  - **Method 3**: Regex-based HTML parsing fallback
  - Uses `nodriver` (undetected Chrome) to bypass anti-bot measures
  - Handles dynamic content and JavaScript-rendered pages

- **`split_into_chunks_by_tokens(text, max_tokens=800, overlap_tokens=50)`**:

  - Intelligent text chunking using actual tokenizer
  - Maintains context with configurable overlap
  - Optimized for embedding model's 1024 token limit

- **`get_embedding_local_with_confidence(text)`**:

  - Generates 1024-dimensional embeddings using Qwen/Qwen3-Embedding-0.6B
  - Calculates quality confidence scores based on text characteristics
  - Returns both embedding vector and confidence metric

- **`calculate_text_confidence(text)`**: Quality scoring based on:

  - Text length and word count
  - Character diversity
  - Sentence structure
  - Alphanumeric content ratio

- **`main_from_url(url)`**: Complete URL-to-embeddings pipeline
- **`main(text)`**: Direct text processing for pre-extracted content

**Features:**

- Robust error handling with graceful fallbacks
- Detailed logging and progress tracking
- Bypass detection mechanisms for protected content
- Quality metrics for content assessment

#### Upload Context (`rag/upload_context.py`)

Database integration and batch processing:

- **`create_sample_data()`**: Processes URLs/text and stores embeddings
- **`view_all_data()`**: Database inspection and debugging
- Integrates web scraping → embedding generation → database storage
- Handles batch processing of multiple content chunks
- Rich metadata preservation for each processed chunk

### RAG System Workflow

1. **Content Ingestion**:

   - Input URL or raw text
   - Multi-method extraction handles various website structures
   - Content cleaning removes navigation, ads, scripts

2. **Text Processing**:

   - Tokenization using embedding model's tokenizer
   - Intelligent chunking with context preservation
   - Quality assessment and confidence scoring

3. **Embedding Generation**:

   - Local Qwen3-Embedding-0.6B model (no API dependencies)
   - 1024-dimensional vector representations
   - Confidence scores for quality control

4. **Storage**:
   - PostgreSQL with vector arrays
   - Rich JSONB metadata for filtering and search
   - Chunk ordering and relationship preservation

### RAG Dependencies

```bash
# Core ML and embeddings
pip install transformers torch

# Web scraping and automation
pip install nodriver "curl-cffi[requests]"

# Environment and utilities
pip install python-dotenv
```

## Setup & Running

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:

   ```
   # Database
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key

   # Optional: Model tokens
   HUGGINGFACE_TOKEN=your_hf_token
   OPENAI_API_KEY=your_openai_key
   ```

3. Run migrations or let FastAPI create tables on startup.

4. Start backend:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Populate dummy data:

   ```bash
   python -m app.populate_dummy
   ```

6. Process content for RAG (example):
   ```bash
   cd rag
   python upload_context.py
   ```

## API Endpoints

### Core Application API Endpoints

#### Organization Endpoints

- `POST /organizations/` — Create an organization
- `GET /organizations/{org_id}` — Retrieve an organization by ID
- `GET /organizations/` — List all organizations
- `PUT /organizations/{org_id}` — Update an organization (if implemented)
- `DELETE /organizations/{org_id}` — Delete an organization (if implemented)

#### User Endpoints

- `POST /users/` — Create a user
- `GET /users/{user_id}` — Retrieve a user by ID
- `GET /users/` — List all users
- `PUT /users/{user_id}` — Update a user (if implemented)
- `DELETE /users/{user_id}` — Delete a user (if implemented)

#### Ticket Endpoints

- `POST /tickets/` — Create a ticket
- `GET /tickets/{ticket_id}` — Retrieve a ticket by ID
- `GET /tickets/` — List all tickets
- `PUT /tickets/{ticket_id}` — Update a ticket (if implemented)
- `DELETE /tickets/{ticket_id}` — Delete a ticket (if implemented)

### RAG System (Planned)

- `/rag/upload` - Process and store new content
- `/rag/search` - Semantic search across stored content
- `/rag/similar` - Find similar content chunks

## B2B SaaS Context & LLM Integration

### Features

- **B2B SaaS Context Management**
  - Create, retrieve, and list context chunks with embeddings.
  - Search for similar context chunks using vector similarity (pgvector).
- **LLM-Powered Ticket Analysis (OpenAI)**
  - `/b2b_saas_context/answer_with_llm`: Given a support ticket, retrieves the most relevant context and generates an answer using OpenAI's GPT models (default: gpt-4o).
  - `/b2b_saas_context/search_similar`: Debug endpoint to retrieve similar context chunks for a ticket.
- **Async SQLAlchemy & PostgreSQL**
  - All database operations are async.
  - Embeddings are stored as vectors for similarity search.
- **Pydantic v2 Schemas**
  - All API models use Pydantic v2 with `from_attributes=True` for ORM compatibility.

### Requirements

- Python 3.10+
- PostgreSQL (with [pgvector](https://github.com/pgvector/pgvector) extension enabled)
- [openai](https://pypi.org/project/openai/) (for LLM inference)
- [numpy](https://numpy.org/)
- [torch](https://pytorch.org/)

### Setup

1. **Clone the repository** and enter the backend directory.
2. **Create and activate a virtual environment**.
3. **Install dependencies** using the provided `requirements.txt`.
4. **Configure your environment variables** for database and OpenAI model.  
   _Do not commit secrets or credentials to version control._
   - `OPENAI_API_KEY` (required for LLM-powered endpoints)
   - `OPENAI_MODEL` (optional, defaults to `gpt-4o`)
5. **Run database migrations** (if using Alembic or similar).
6. **Start the server** with Uvicorn.
7. **Access the API docs** at `/docs` in your browser.

### API Overview

#### B2B SaaS Context Endpoints

- `POST /b2b_saas_context/`  
   Create a new context chunk.

- `GET /b2b_saas_context/{context_id}`  
   Retrieve a context chunk by ID.

- `GET /b2b_saas_context/`  
   List all context chunks.

- `POST /b2b_saas_context/search_similar`  
   Retrieve the most similar context chunks for a given ticket text (for debugging).

  **Request:**

  ```json
  {
    "ticket_text": "My product is not showing up in the docs...",
    "top_k": 5
  }
  ```

  **Response:**

  ```json
  [
     {
        "record": { ...context fields... },
        "similarity": 0.42
     }
  ]
  ```

#### LLM-Powered Answer Endpoint

- `POST /b2b_saas_context/answer_with_llm`  
   Given a ticket, retrieves relevant context and generates an answer using OpenAI GPT (default: gpt-4o).

  **Request:**

  ```json
  {
    "ticket_id": "12345",
    "description": "My product is not showing up in the docs...",
    "feature": "Search",
    "top_k": 5
  }
  ```

  **Response:**

  ```json
  {
    "llm_answer": {
      "TicketId": "12345",
      "SuggestedHypotheses": {
        "Rank1": "<hypothesis with source reference>",
        "Rank2": "<hypothesis with source reference>"
      },
      "ABVariantIdea": "<variant idea with source reference>",
      "ExactPhrasesEvidence": {
        "FromTicket": "<quote or paraphrased ticket evidence>",
        "FromResearch": "<title + link>"
      }
    },
    "used_context": [
      {
        "title": "Context Title",
        "chunk_text": "Relevant context chunk...",
        "similarity": 0.42
      }
    ]
  }
  ```

### Development Notes

- All complex logic for context search and embedding is in the `crud` folder.
- The `rag` folder is for testing and is not part of the main project logic.
- The project uses `.gitignore` to exclude `__pycache__/` and other unnecessary files.

---

**Note:**  
This section covers only the main project. The `rag` folder is excluded from documentation and should not be modified or deleted as part of the main workflow.

- **Token Limits**: 800 tokens per chunk with 50-token overlap
- **Quality Scoring**: Multi-factor confidence assessment
- **Web Scraping**: Anti-detection with multiple extraction fallbacks
- **Storage**: PostgreSQL arrays for embeddings, JSONB for metadata

### Performance Considerations

- Local embedding model eliminates API latency and costs
- Chunking strategy balances context preservation with processing efficiency
- Confidence scoring enables quality-based filtering
- Async processing throughout for scalability

---

For further details, review the source code in each module and the comments provided.

# 🎯 Echolab - AI-Powered Customer Feedback Intelligence Platform

<div align="center">

![Echolab Logo](frontend/public/images/echolab-logo.png)

**Transform customer support tickets into actionable product insights with AI**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js_15-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Screenshots](#-screenshots)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

---

## 🌟 Overview

**Echolab** is an enterprise-grade platform that leverages AI and machine learning to transform unstructured customer feedback into actionable product insights. Built for Product Managers, Customer Success teams, and Data Analysts, Echolab automatically clusters support tickets, identifies pain points, and generates testable hypotheses for product improvements.

### The Problem We Solve

Product teams receive thousands of support tickets, feature requests, and bug reports across multiple channels. Manually analyzing this feedback is:
- **Time-consuming**: Hours spent reading and categorizing tickets
- **Inconsistent**: Human bias leads to missed patterns
- **Reactive**: Insights come too late to influence product decisions

### Our Solution

Echolab uses advanced NLP and machine learning to:
1. **Automatically cluster** similar tickets using semantic embeddings
2. **Extract pain points** with AI-powered sentiment analysis
3. **Generate hypotheses** for A/B testing and product experiments
4. **Integrate seamlessly** with existing tools (Zendesk, GrowthBook)

---

## ✨ Key Features

### 🤖 AI-Powered Analysis
- **Semantic Clustering**: Groups similar tickets using transformer-based embeddings (MiniLM-L6-v2, Qwen3-Embedding-0.6B)
- **Pain Point Extraction**: Identifies customer frustrations using BART and GPT-4o
- **Hypothesis Generation**: Creates data-driven product improvement suggestions with supporting evidence

### 🔗 Enterprise Integrations
- **Zendesk Sync**: Bi-directional ticket synchronization with webhook support
- **GrowthBook**: Generate A/B test variants from customer feedback
- **RAG System**: Semantic search across documentation and support content

### 📊 Analytics Dashboard
- Real-time visualization of ticket trends and pain point clusters
- Customizable filters by organization, feature, and time period
- Export capabilities for stakeholder presentations

### 🔐 Security & Scalability
- Multi-tenant architecture with organization-level isolation
- Supabase authentication with OAuth support
- Async PostgreSQL operations for high-throughput processing
- pgvector extension for efficient similarity search

### 🎨 Modern UI/UX
- Built with Next.js 15 and React 19
- Responsive design with TailwindCSS
- Server-side rendering for optimal performance
- Real-time updates with optimistic UI patterns

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Frontend
        A[Next.js App] --> B[React Components]
        B --> C[Supabase Auth]
    end

    subgraph Backend
        D[FastAPI Server] --> E[SQLAlchemy ORM]
        E --> F[(PostgreSQL + pgvector)]
        D --> G[OpenAI API]
        D --> H[Zendesk API]
        D --> I[GrowthBook SDK]
    end

    subgraph AI Pipeline
        J[Embedding Models] --> K[Clustering Engine]
        K --> L[Pain Point Analyzer]
        L --> M[Hypothesis Generator]
    end

    A --> D
    J --> F
    M --> F
    H --> D
    I --> D
</mermaid>

### Data Flow

1. **Ingestion**: Tickets arrive via Zendesk webhooks or manual import
2. **Processing**: Text is cleaned, tokenized, and embedded using local transformer models
3. **Clustering**: Semantic similarity groups tickets into actionable themes
4. **Analysis**: GPT-4o analyzes clusters to extract pain points and hypotheses
5. **Presentation**: Results displayed in dashboard with drill-down capabilities
6. **Action**: Export to GrowthBook for A/B testing or CSV for reporting

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (async endpoints, automatic OpenAPI docs)
- **ORM**: SQLAlchemy 2.0 (async session management)
- **Database**: PostgreSQL with pgvector extension for embeddings
- **AI/ML**:
  - OpenAI GPT-4o for hypothesis generation
  - Transformers (Hugging Face) for local embeddings
  - BART-large-CNN for summarization
- **Authentication**: Supabase Auth
- **Task Queue**: Async processing with asyncio
- **API Clients**: Zendesk API, GrowthBook SDK

### Frontend
- **Framework**: Next.js 15 with App Router
- **UI Library**: React 19 with Server Components
- **Styling**: TailwindCSS 4.x + Radix UI primitives
- **State Management**: React Context + Server State
- **Animations**: Framer Motion
- **Icons**: Lucide React, Tabler Icons
- **Forms**: React Hook Form with Zod validation

### DevOps & Tools
- **Version Control**: Git with conventional commits
- **Package Management**: npm (frontend), pip (backend)
- **Environment**: dotenv for configuration
- **API Testing**: FastAPI automatic interactive docs
- **Database Migrations**: Alembic

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 14+** with [pgvector extension](https://github.com/pgvector/pgvector)
- **Supabase account** (or self-hosted Supabase)
- **OpenAI API key** (for GPT-4o)
- **Zendesk account** (optional, for integration)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/bhavanareddy19/Echolab.git
cd Echolab/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials:
# - SUPABASE_URL
# - SUPABASE_KEY
# - OPENAI_API_KEY
# - ZENDESK_SUBDOMAIN (optional)
# - ZENDESK_EMAIL (optional)
# - ZENDESK_API_TOKEN (optional)

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with:
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY
# - NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Quick Start with Docker (Coming Soon)

```bash
docker-compose up -d
```

---

## 💡 Usage

### 1. Authentication

Navigate to `http://localhost:3000/login` and sign up with:
- Email/password
- Google OAuth (configured in Supabase)

### 2. Import Tickets

**Option A: Zendesk Integration**
1. Go to Settings → Integrations
2. Connect your Zendesk account (subdomain, email, API token)
3. Click "Sync Tickets" to import historical data

**Option B: Manual Upload**
1. Navigate to Tickets → Import
2. Upload CSV with columns: `subject`, `description`, `priority`, `tags`

### 3. Analyze Feedback

The AI pipeline automatically:
- Generates embeddings for all tickets
- Clusters similar issues (threshold: 0.5 similarity)
- Extracts pain points using GPT-4o
- Creates hypotheses ranked by confidence

### 4. View Insights

**Dashboard**: See aggregate metrics and trends
**Pain Points**: Drill into specific customer frustrations
**Hypotheses**: Review AI-generated product improvement ideas
**Tickets**: Inspect individual tickets and their classifications

### 5. Export & Act

- **Export to CSV**: Download clusters for stakeholder presentations
- **GrowthBook Integration**: Push hypotheses as A/B test variants
- **Zendesk Comments**: Add analysis results back to tickets

---

## 📚 API Documentation

### Core Endpoints

#### Organizations
```http
POST   /organizations/          # Create organization
GET    /organizations/{id}      # Get organization details
GET    /organizations/          # List all organizations
```

#### Tickets
```http
POST   /tickets/                # Create single ticket
POST   /tickets/bulk/           # Bulk create tickets
GET    /tickets/{id}            # Get ticket with analysis
GET    /tickets/                # List tickets with filters
```

#### Zendesk Integration
```http
POST   /integrations/zendesk/sync                  # Sync tickets from Zendesk
POST   /prod/tickets/zendesk/import                # Import using user credentials
POST   /tickets/webhook/zendesk                    # Webhook receiver (single)
POST   /tickets/webhook/zendesk/bulk               # Webhook receiver (bulk)
POST   /prod/tickets/zendesk/create                # Create ticket in Zendesk
```

#### AI Analysis
```http
POST   /b2b_saas_context/answer_with_llm           # Generate hypothesis for ticket
POST   /b2b_saas_context/search_similar           # Find similar context chunks
GET    /painpoints/                                # List all pain point clusters
POST   /painpoints/analyze                         # Trigger pain point analysis
```

#### GrowthBook
```http
POST   /growthbook/features                        # Create feature from hypothesis
GET    /growthbook/experiments                     # List experiments
```

### Example Request

```bash
# Create a ticket and get AI analysis
curl -X POST http://localhost:8000/tickets/ \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Login page is slow on mobile",
    "description": "It takes 10+ seconds to load the login page on my iPhone. Very frustrating!",
    "priority": "high",
    "organization_id": 1
  }'
```

### Example Response

```json
{
  "id": 123,
  "subject": "Login page is slow on mobile",
  "description": "It takes 10+ seconds to load the login page on my iPhone...",
  "priority": "high",
  "feature": "Authentication",
  "hypothesis": {
    "Rank1": "Optimizing mobile login page load time may reduce user frustration and increase conversion rates",
    "Rank2": "Implementing lazy loading for non-critical assets could improve perceived performance",
    "ABVariantIdea": "A: Current login page | B: Optimized mobile login with lazy loading",
    "ExactPhrasesEvidence": {
      "FromTicket": "takes 10+ seconds to load the login page on my iPhone",
      "FromResearch": "Mobile Performance Best Practices - https://web.dev/mobile"
    }
  },
  "created_at": "2026-01-08T10:30:00Z"
}
```

---

## 📂 Project Structure

```
Echolab/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   ├── ticket.py     # Ticket CRUD endpoints
│   │   │   ├── zendesk_sync.py
│   │   │   ├── pain_points.py
│   │   │   ├── b2b_saas_context.py
│   │   │   └── growthbook.py
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── ticket.py
│   │   │   ├── organization.py
│   │   │   ├── user.py
│   │   │   └── b2b_saas_context.py
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── crud/             # Database operations
│   │   ├── services/         # Business logic
│   │   │   ├── zendesk_client.py
│   │   │   ├── pain_points_cluster.py
│   │   │   └── ingest.py
│   │   ├── rag/              # RAG system components
│   │   │   ├── extract_pages.py
│   │   │   ├── b2b_saas_table.py
│   │   │   └── upload_context.py
│   │   ├── config.py         # Configuration management
│   │   ├── db.py             # Database connection
│   │   └── main.py           # Application entry point
│   ├── requirements.txt
│   └── alembic.ini           # Database migrations
│
├── frontend/
│   ├── app/                  # Next.js App Router
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── hypothesis/
│   │   └── page.tsx          # Dashboard
│   ├── components/           # React components
│   │   ├── UI/               # Reusable UI primitives
│   │   ├── Dashboard.tsx
│   │   ├── CustomerPainPoints.tsx
│   │   └── BugsAndFeatures.tsx
│   ├── actions/              # Server actions
│   ├── utils/                # Utility functions
│   │   └── supabase/         # Supabase client setup
│   ├── types/                # TypeScript definitions
│   ├── package.json
│   └── next.config.ts
│
├── Embedding/                # Standalone embedding scripts
│   ├── embedding.py          # Generate embeddings
│   └── semantic.py           # Semantic clustering
│
├── requirements.txt          # Root-level dependencies
├── alembic.ini
└── README.md
```

---

## 🖼️ Screenshots

### Dashboard Overview
![Dashboard](docs/screenshots/dashboard.png)
*Real-time metrics showing ticket volume, pain point distribution, and hypothesis generation*

### Pain Points Analysis
![Pain Points](docs/screenshots/pain-points.png)
*AI-clustered customer pain points with severity scoring and trend analysis*

### Hypothesis Generation
![Hypotheses](docs/screenshots/hypotheses.png)
*AI-generated product improvement hypotheses with supporting evidence and A/B test variants*

### Ticket Management
![Tickets](docs/screenshots/tickets.png)
*Comprehensive ticket view with filtering, tagging, and AI-powered categorization*

---

## 🗺️ Roadmap

### Q1 2026
- [x] Core ticket ingestion and clustering
- [x] Zendesk integration (sync + webhooks)
- [x] GPT-4o hypothesis generation
- [x] Basic dashboard UI
- [ ] User feedback loop (thumbs up/down on hypotheses)
- [ ] Advanced filtering and search

### Q2 2026
- [ ] Jira integration
- [ ] Slack notifications for high-priority pain points
- [ ] Custom ML model training on user feedback
- [ ] Multi-language support (Spanish, French, German)
- [ ] Role-based access control (RBAC)

### Q3 2026
- [ ] Automated A/B test deployment to GrowthBook
- [ ] Sentiment analysis dashboard
- [ ] API rate limiting and usage analytics
- [ ] White-label customization

### Future
- [ ] Intercom, HubSpot, Salesforce integrations
- [ ] Predictive analytics (churn risk, feature adoption)
- [ ] Voice-of-customer reports (auto-generated PDF/PPT)
- [ ] Mobile app (iOS/Android)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint/Prettier for TypeScript/React
- Write tests for new features
- Update documentation for API changes
- Keep commit messages clear and descriptive

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o API
- **Hugging Face** for transformer models
- **Supabase** for authentication and database hosting
- **FastAPI** for excellent async framework
- **Vercel** for Next.js and deployment platform

---

## 📞 Contact

**Project Maintainer**: Bhavana Reddy

- GitHub: [@bhavanareddy19](https://github.com/bhavanareddy19)
- LinkedIn: [Connect with me](https://linkedin.com/in/bhavanareddy19)
- Email: bhavana.reddy@example.com

---

<div align="center">

**⭐ If you find Echolab useful, please consider giving it a star on GitHub! ⭐**

Made with ❤️ by the Echolab team

</div>

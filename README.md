# 🔬 Echolab - AI-Powered Customer Feedback Intelligence

<div align="center">

![Python](https://img.shields.io/badge/Python-74.6%25-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-22.3%25-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)

**Transform unstructured customer feedback into actionable product insights**

[Features](#-key-features) • [Tech Stack](#-tech-stack) • [Architecture](#-architecture) • [Installation](#-installation)

</div>

---

## 📋 Overview

**Echolab** is an enterprise-grade AI platform that automatically converts thousands of support tickets into data-driven product insights. Using advanced NLP and machine learning, Echolab identifies pain points, clusters similar issues, and generates actionable hypotheses for product improvements.

### 🎯 The Problem

Product teams face a critical challenge:
- **Thousands of support tickets** arrive daily across multiple channels
- **Manual analysis** is time-consuming and inconsistent
- **Valuable insights** are buried in unstructured text
- **Product decisions** lack data-driven foundations

### ✅ The Solution

Echolab automates customer feedback analysis:
- **Semantic Clustering** groups similar tickets using transformer embeddings
- **AI Analysis** powered by GPT-4o extracts pain points and patterns
- **Automated Insights** generate product improvement hypotheses
- **Integrated Workflow** connects with Zendesk, GrowthBook, and more

---

## ✨ Key Features

### 🤖 **Intelligent Ticket Analysis**
- GPT-4o-powered semantic analysis of support tickets
- Automatic pain point extraction and categorization
- Multi-dimensional sentiment analysis
- Context-aware issue understanding

### 📊 **Semantic Clustering**
- Transformer-based embeddings (Hugging Face models)
- Automatic grouping of similar customer issues
- Vector similarity search with pgvector
- Cluster visualization and exploration

### 🔗 **Zendesk Integration**
- Bi-directional sync with Zendesk API
- Real-time webhook processing
- Custom field mapping
- Automated ticket ingestion

### 🧪 **GrowthBook Integration**
- A/B test variant generation from insights
- Hypothesis-driven experiment creation
- Feature flag management
- Experiment tracking and analytics

### 📚 **RAG-Powered Documentation Search**
- Semantic documentation search
- Context-aware answer generation
- Knowledge base integration
- Internal wiki connectivity

### 🏢 **Multi-Tenant Architecture**
- Organization-level data isolation
- Role-based access control (planned)
- Custom branding and configuration
- Scalable infrastructure

### 📈 **Real-Time Analytics Dashboard**
- Live ticket processing metrics
- Cluster insights and trends
- Pain point frequency analysis
- Product impact visualization

---

## 🛠️ Tech Stack

### **Backend**
- **FastAPI** - High-performance async web framework
- **PostgreSQL** - Relational database with advanced features
- **pgvector** - Vector similarity search extension
- **SQLAlchemy 2.0** - Modern ORM with async support
- **Alembic** - Database migration management
- **OpenAI GPT-4o** - Advanced language model for analysis
- **Hugging Face Transformers** - Sentence embeddings
- **Supabase Auth** - Authentication and authorization

### **Frontend**
- **Next.js 15** - React framework with App Router
- **React 19** - Latest React features
- **TailwindCSS 4.x** - Utility-first styling
- **Radix UI** - Accessible component primitives
- **React Hook Form** - Form state management
- **Zod** - TypeScript-first schema validation

### **Infrastructure**
- **Docker** - Containerization
- **PostgreSQL** - Primary database
- **Vector Database** - Semantic search capabilities
- **Webhooks** - Real-time event processing

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Next.js Frontend                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ Dashboard   │  │   Clusters   │  │  Experiments  │   │
│  │ Analytics   │  │   Explorer   │  │   Manager     │   │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘   │
└─────────┼─────────────────┼───────────────────┼──────────┘
          │                 │                   │
          └─────────────────┼───────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│                   FastAPI Backend                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │   Ticket    │  │  Clustering  │  │  Integration  │   │
│  │  Analysis   │  │   Engine     │  │    Layer      │   │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘   │
└─────────┼─────────────────┼───────────────────┼──────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│   OpenAI     │  │ PostgreSQL + │  │    Zendesk API   │
│   GPT-4o     │  │   pgvector   │  │  GrowthBook API  │
└──────────────┘  └──────────────┘  └──────────────────┘
```

### Data Flow

1. **Ingestion**: Tickets synced from Zendesk via webhooks/API
2. **Embedding**: Text converted to vector embeddings using transformers
3. **Clustering**: Semantic similarity clustering with pgvector
4. **Analysis**: GPT-4o extracts pain points and generates insights
5. **Storage**: Results stored in PostgreSQL with vector indexing
6. **Visualization**: Dashboard displays clusters, trends, and insights
7. **Action**: Insights converted to GrowthBook experiments

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key
- Zendesk API credentials (optional)

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
# Add your API keys and database connection string

# Initialize database
alembic upgrade head

# Run the server
uvicorn main:app --reload --port 8000
```

API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Configure API endpoint

# Run development server
npm run dev
```

Application will open at `http://localhost:3000`

---

## 💡 Usage

### 1. Connect Zendesk

```python
# Configure Zendesk integration
POST /api/integrations/zendesk
{
  "subdomain": "your-company",
  "api_token": "your-token",
  "email": "admin@company.com"
}
```

### 2. Sync Tickets

```python
# Import tickets (automatic via webhooks or manual)
POST /api/tickets/sync
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### 3. Generate Clusters

```python
# Analyze and cluster tickets
POST /api/clusters/generate
{
  "organization_id": "org-123",
  "min_cluster_size": 5
}
```

### 4. View Insights

Navigate to the dashboard to see:
- Clustered ticket groups
- Pain point analysis
- Trending issues
- Recommended product improvements

---

## 📊 API Documentation

Once the server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tickets` | POST | Create or import tickets |
| `/api/clusters` | GET | Retrieve ticket clusters |
| `/api/analysis/{ticket_id}` | GET | Get AI analysis for ticket |
| `/api/search` | POST | Semantic documentation search |
| `/api/experiments` | POST | Create GrowthBook experiment |

---

## 🎓 Technical Highlights

### What Makes This Project Stand Out

1. **Advanced NLP & ML**
   - Transformer-based semantic embeddings
   - GPT-4o integration for analysis
   - Vector similarity search with pgvector
   - RAG (Retrieval-Augmented Generation) implementation

2. **Full-Stack Modern Architecture**
   - FastAPI async backend
   - Next.js 15 App Router
   - Server-side rendering and actions
   - Real-time webhook processing

3. **Enterprise-Grade Features**
   - Multi-tenant architecture
   - Scalable vector database
   - Third-party API integrations
   - Authentication and authorization

4. **Database Engineering**
   - PostgreSQL with advanced extensions
   - Vector indexing for similarity search
   - Database migration management
   - Optimized query performance

5. **System Integration**
   - Bi-directional Zendesk sync
   - GrowthBook A/B testing integration
   - Webhook event processing
   - RESTful API design

---

## 🗺️ Roadmap

### Current Features (Q1 2026)
- ✅ Semantic ticket clustering
- ✅ GPT-4o powered analysis
- ✅ Zendesk integration
- ✅ GrowthBook connectivity
- ✅ RAG documentation search
- ✅ Multi-tenant support

### Planned Features
- [ ] Jira integration for ticket management
- [ ] Slack notifications for critical insights
- [ ] Multi-language support (i18n)
- [ ] Role-based access control (RBAC)
- [ ] Custom ML model training
- [ ] Advanced analytics and reporting
- [ ] Export to CSV/Excel
- [ ] API rate limiting and caching

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

---

## 📁 Project Structure

```
Echolab/
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   ├── integrations/ # Zendesk, GrowthBook
│   │   └── utils/        # Helper functions
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test suite
│   └── requirements.txt  # Python dependencies
├── frontend/             # Next.js application
│   ├── app/             # App Router pages
│   ├── components/      # React components
│   ├── lib/             # Utilities and actions
│   └── public/          # Static assets
├── Embedding/           # Standalone embedding scripts
└── README.md           # This file
```

---

## 🔒 Security

- Supabase authentication with JWT
- Organization-level data isolation
- API key rotation support
- Secure webhook verification
- Environment variable configuration

---

## 📄 License

This project is open source and available under standard licensing terms.

---

## 👤 Author

**Bhavana Reddy**

- GitHub: [@bhavanareddy19](https://github.com/bhavanareddy19)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/YOUR_PROFILE)

---

## 🙏 Acknowledgments

- OpenAI for GPT-4o API
- Hugging Face for transformer models
- FastAPI and Next.js communities
- PostgreSQL and pgvector teams

---

<div align="center">

**Transform customer feedback into product excellence! 🔬✨**

[⬆ Back to Top](#-echolab---ai-powered-customer-feedback-intelligence)

</div>

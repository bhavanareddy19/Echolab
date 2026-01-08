import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import pandas as pd
from urllib.parse import urlparse
import warnings
import re
import numpy as np
import torch
import gc
from datetime import datetime
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from transformers import (
    BartTokenizer, BartForConditionalGeneration,
    T5Tokenizer, T5ForConditionalGeneration,
    AutoTokenizer, AutoModelForSeq2SeqLM
)
import json

# Load environment variables
load_dotenv()

# Suppress warnings
warnings.filterwarnings('ignore')

class SupabaseManager:
    """Supabase database manager using direct PostgreSQL connection"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """Connect to Supabase PostgreSQL database using the correct URL"""
        try:
            # Get the database URL from environment variables
            db_url = os.getenv("SUPABASE_DB_URL")
            if not db_url:
                raise Exception("SUPABASE_DB_URL not found in environment variables")
            
            # Parse the URL to extract connection parameters
            parsed = urlparse(db_url)
            
            # Extract connection parameters
            db_params = {
                'host': parsed.hostname,
                'port': parsed.port,
                'database': parsed.path[1:],  # Remove leading '/'
                'user': parsed.username,
                'password': parsed.password,
            }
            
            print(f"🔌 Connecting to Supabase PostgreSQL at {parsed.hostname}:{parsed.port}...")
            
            # Connect using psycopg2 (not asyncpg since this is a sync connection)
            self.connection = psycopg2.connect(**db_params)
            
            print("✅ Successfully connected to Supabase!")
            return True
            
        except Exception as e:
            print(f"❌ Supabase connection failed: {e}")
            self.connection = None
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("🔌 Database connection closed")

    def get_data(self, organization_id=None, limit=None):
        """Load data from TICKETS table (not pain_points_cluster) for processing"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")

        query = """
            SELECT id, subject, description, url, source, created_at, updated_at, 
                   type, priority, status, submitter_id, tags, rating, attachments, 
                   organization_id, feature, cluster, "Customer Problem", "Root Cause"
            FROM tickets 
        """
        params = []
        conditions = []

        if organization_id:
            conditions.append("organization_id = %s")
            params.append(organization_id)

        # Only get tickets that have been classified (have feature field populated)
        conditions.append("feature IS NOT NULL")

        # Only get tickets that have not been clustered yet
        conditions.append("clustered = FALSE")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        print(f"📊 Loading data from TICKETS table with query: {query}")
        print(f"📊 Parameters: {params}")

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()

        # Extract ticket IDs to update clustered status
        ticket_ids = [row['id'] for row in data]
        if ticket_ids:
            self.update_clustered_status(ticket_ids)

        print(f"📊 Loaded {len(data)} records from tickets table")
        return data

    def update_filtered_data(self, consolidated_data, organization_id):
        """Update only records for a specific organization"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")
            
        try:
            print(f"🔄 Updating records for organization {organization_id}...")
            
            with self.connection.cursor() as cursor:
                # First, delete existing records for this organization
                print(f"   Clearing existing records for organization {organization_id}...")
                cursor.execute("DELETE FROM pain_points_cluster WHERE organization_id = %s", (organization_id,))
                deleted_count = cursor.rowcount
                print(f"   ✅ Deleted {deleted_count} existing records")
                
                # Prepare data for insertion
                if not consolidated_data:
                    print("   No new data to insert")
                    self.connection.commit()
                    return True
                
                columns = list(consolidated_data[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                # Insert in batches
                batch_size = 50
                total_inserted = 0
                
                for i in range(0, len(consolidated_data), batch_size):
                    batch = consolidated_data[i:i + batch_size]
                    values = []
                    
                    for record in batch:
                        record_values = []
                        for col in columns:
                            value = record[col]
                            # Handle pandas/numpy data types
                            if pd.isna(value) if hasattr(pd, 'isna') else value is None:
                                record_values.append(None)
                            elif hasattr(value, 'item'):  # numpy types
                                record_values.append(value.item())
                            elif hasattr(value, 'isoformat'):  # datetime types
                                record_values.append(value.isoformat())
                            else:
                                record_values.append(value)
                        values.append(tuple(record_values))
                    
                    try:
                        # Build the INSERT query
                        query = f"INSERT INTO pain_points_cluster ({columns_str}) VALUES ({placeholders})"
                        cursor.executemany(query, values)
                        
                        total_inserted += len(batch)
                        print(f"   Inserted batch {i//batch_size + 1}: {total_inserted}/{len(consolidated_data)} records")
                        
                    except Exception as batch_error:
                        print(f"   ⚠️ Batch {i//batch_size + 1} failed: {batch_error}")
                        self.connection.rollback()
                        return False
                
                # Commit all changes
                self.connection.commit()
                        
            print(f"✅ Successfully updated {total_inserted} records for organization {organization_id}")
            return True
            
        except Exception as e:
            print(f"❌ Filtered update failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            print("✅ Database connection closed")
    
    def save_clusters_to_pain_points(self, clustered_data):
        """Save clustering results to pain_points_cluster table"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")
            
        try:
            print(f"💾 Saving {len(clustered_data)} clusters to pain_points_cluster table...")
            
            with self.connection.cursor() as cursor:
                # REMOVED: Delete statement - keeping historical data
                # No longer clearing existing records for organization
                
                # Insert new cluster summaries
                for cluster_data in clustered_data:
                    insert_query = """
                        INSERT INTO pain_points_cluster 
                        (body, hypothesis, tickets, num_of_tickets, status, organization_id, 
                         cluster_group, score, cluster_id, similarity_to_center, 
                         cluster_representative, cluster_size, cluster_theme, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # Convert data types properly - especially datetime handling
                    cursor.execute(insert_query, (
                        str(cluster_data.get('summary', '')),  # body - convert to string
                        None,  # hypothesis - keep as NULL
                        json.dumps(cluster_data.get('tickets', []), default=str),  # tickets JSONB - handle datetime serialization
                        int(cluster_data.get('ticket_count', 0)),  # num_of_tickets - ensure int
                        'processed',  # status
                        int(cluster_data.get('organization_id')),  # organization_id - ensure int
                        str(cluster_data.get('theme', '')),  # cluster_group - convert to string
                        float(cluster_data.get('confidence_score', 0.0)),  # score - ensure float
                        int(cluster_data.get('cluster_id')),  # cluster_id - ensure int
                        float(cluster_data.get('similarity_to_center', 0.0)),  # similarity_to_center - ensure float
                        bool(cluster_data.get('is_representative', False)),  # cluster_representative - ensure bool
                        int(cluster_data.get('cluster_size', 0)),  # cluster_size - ensure int
                        str(cluster_data.get('theme', '')),  # cluster_theme - convert to string
                        datetime.now()  # created_at
                    ))
        
            self.connection.commit()
            print(f"✅ Successfully saved {len(clustered_data)} cluster summaries to pain_points_cluster")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save clusters: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def update_clustered_status(self, ticket_ids: List[str]):
        """Update the clustered status of tickets to TRUE."""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")

        try:
            with self.connection.cursor() as cursor:
                query = """
                    UPDATE tickets
                    SET clustered = TRUE
                    WHERE id = ANY(%s::uuid[])
                """
                cursor.execute(query, (ticket_ids,))
                self.connection.commit()
                print(f"✅ Updated clustered status for {len(ticket_ids)} tickets.")
        except Exception as e:
            print(f"❌ Failed to update clustered status: {e}")
            self.connection.rollback()
            return False

class TextClustering:
    """Intelligent text clustering for customer support tickets"""
    
    def __init__(self, n_clusters=None, max_features=5000):
        self.n_clusters = n_clusters
        self.max_features = max_features
        self.vectorizer = None
        self.kmeans = None
        self.cluster_themes = {}
        
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        if not isinstance(text, str):
            return ""
        
        # Clean text
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = text.lower().strip()
        
        # Remove very short texts
        if len(text) < 10:
            return ""
            
        return text
    
    def determine_optimal_clusters(self, texts):
        """Determine optimal number of clusters"""
        if self.n_clusters:
            return self.n_clusters
            
        # Clean texts
        clean_texts = [self.preprocess_text(text) for text in texts]
        clean_texts = [t for t in clean_texts if len(t) > 10]
        
        if len(clean_texts) < 10:
            return min(5, len(clean_texts))
        
        # For customer support tickets, use rule of thumb: sqrt(n/2)
        optimal_k = int(np.sqrt(len(clean_texts) / 2))
        optimal_k = max(5, min(optimal_k, 20))  # Between 5 and 20 clusters
        
        return optimal_k
    
    def fit_predict(self, texts):
        """Cluster texts and return cluster assignments"""
        print("🔍 Analyzing customer support tickets for clustering...")
        
        # Clean texts
        clean_texts = [self.preprocess_text(text) for text in texts]
        valid_indices = [i for i, t in enumerate(clean_texts) if len(t) > 10]
        valid_texts = [clean_texts[i] for i in valid_indices]
        
        if len(valid_texts) < 3:
            print("⚠️ Too few valid texts for clustering")
            return [0] * len(texts)
        
        # Determine cluster count
        if not self.n_clusters:
            self.n_clusters = self.determine_optimal_clusters(valid_texts)
        
        print(f"   Creating {self.n_clusters} clusters from {len(valid_texts)} valid tickets")
        
        # Vectorize texts - optimized for customer support
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        X = self.vectorizer.fit_transform(valid_texts)
        
        # Cluster
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300
        )
        
        cluster_labels = self.kmeans.fit_predict(X)
        
        # Generate cluster themes
        self._generate_cluster_themes(valid_texts, cluster_labels)
        
        # Map back to original indices
        full_labels = [0] * len(texts)  # Default cluster for invalid texts
        for i, original_idx in enumerate(valid_indices):
            full_labels[original_idx] = cluster_labels[i]
        
        return full_labels
    
    def _generate_cluster_themes(self, texts, labels):
        """Generate descriptive themes for each cluster"""
        feature_names = self.vectorizer.get_feature_names_out()
        
        for cluster_id in range(self.n_clusters):
            # Get texts in this cluster
            cluster_texts = [texts[i] for i, label in enumerate(labels) if label == cluster_id]
            
            if not cluster_texts:
                self.cluster_themes[cluster_id] = f"General Support {cluster_id}"
                continue
            
            # Get top terms for this cluster
            cluster_center = self.kmeans.cluster_centers_[cluster_id]
            top_indices = cluster_center.argsort()[-10:][::-1]
            top_terms = [feature_names[i] for i in top_indices]
            
            # Generate theme based on top terms
            theme = self._create_theme_from_terms(top_terms, cluster_texts)
            self.cluster_themes[cluster_id] = theme
    
    def _create_theme_from_terms(self, terms, sample_texts):
        """Create descriptive theme from top terms"""
        # Customer support specific categories
        categories = {
            'support': 'Customer Support Requests',
            'customer': 'General Customer Inquiries', 
            'upgrade': 'Upgrade & Plan Requests',
            'guidance': 'Technical Guidance Requests',
            'integration': 'Integration Support',
            'digital': 'Digital Platform Support',
            'comprehensive': 'Comprehensive Support Requests',
            'campaign': 'Campaign & Marketing Support',
            'billing': 'Billing & Payment Support',
            'account': 'Account Management',
            'technical': 'Technical Support',
            'feature': 'Feature Requests',
            'api': 'API & Development Support',
            'training': 'Training & Education Requests',
            'consultation': 'Consultation Services'
        }
        
        # Find matching category
        terms_str = ' '.join(terms).lower()
        
        for keyword, theme in categories.items():
            if keyword in terms_str:
                return theme
        
        # Fallback to most common meaningful terms
        meaningful_terms = [t for t in terms[:3] if len(t) > 3 and t not in ['customer', 'support', 'request']]
        if meaningful_terms:
            return ' '.join(meaningful_terms[:2]).title() + " Support"
        
        return "General Customer Support"


class EnhancedSummarizer:
    """Enhanced AI summarizer with multiple model options for better results"""
    
    def __init__(self, model_choice='bart-large-cnn'):
        """
        Initialize with model choice:
        - 'bart-large-cnn': Best for detailed summaries (RECOMMENDED)
        - 'flan-t5-large': Good for instruction-following
        - 'led-base': Good for long documents
        - 'bart-large-xsum': More concise summaries
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_choice = model_choice
        
        print(f"🤖 Initializing Enhanced AI Summarizer...")
        print(f"   Device: {self.device}")
        print(f"   Model: {model_choice}")
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name()
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"   GPU: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            print(f"   Running on CPU (will be slower)")
        
        self._load_model()
    
    def _load_model(self):
        """Load the selected model and tokenizer"""
        try:
            model_configs = {
                'bart-large-cnn': {
                    'model_name': 'facebook/bart-large-cnn',
                    'tokenizer_class': BartTokenizer,
                    'model_class': BartForConditionalGeneration,
                    'max_input': 1024,
                    'max_output': 300
                },
                'flan-t5-large': {
                    'model_name': 'google/flan-t5-large',
                    'tokenizer_class': T5Tokenizer,
                    'model_class': T5ForConditionalGeneration,
                    'max_input': 512,
                    'max_output': 250
                },
                'led-base': {
                    'model_name': 'allenai/led-base-16384',
                    'tokenizer_class': AutoTokenizer,
                    'model_class': AutoModelForSeq2SeqLM,
                    'max_input': 4096,
                    'max_output': 512
                },
                'bart-large-xsum': {
                    'model_name': 'facebook/bart-large-xsum',
                    'tokenizer_class': BartTokenizer,
                    'model_class': BartForConditionalGeneration,
                    'max_input': 1024,
                    'max_output': 200
                }
            }
            
            config = model_configs.get(self.model_choice, model_configs['bart-large-cnn'])
            
            print(f"   📦 Loading tokenizer: {config['model_name']}...")
            self.tokenizer = config['tokenizer_class'].from_pretrained(config['model_name'])
            
            print(f"   📦 Loading model: {config['model_name']}...")
            self.model = config['model_class'].from_pretrained(config['model_name'])
            self.model.to(self.device)
            self.model.eval()
            
            self.max_input_length = config['max_input']
            self.max_output_length = config['max_output']
            
            print(f"✅ Model loaded successfully!")
            print(f"   Max input tokens: {self.max_input_length}")
            print(f"   Max output tokens: {self.max_output_length}")
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("💡 Make sure you have internet connection for first-time model download")
            raise
    
    def extract_pain_points(self, texts: List[str]) -> List[str]:
        """Extract key pain points and problems from tickets"""
        pain_point_keywords = [
            'problem', 'issue', 'error', 'cannot', 'unable', 'failed', 'broken',
            'not working', 'difficulty', 'trouble', 'frustrat', 'confus', 'stuck',
            'help', 'support', 'fix', 'resolve', 'solution', 'urgent', 'critical',
            'bug', 'crash', 'slow', 'missing', 'incorrect', 'wrong'
        ]
        
        pain_points = []
        for text in texts:
            if not text:
                continue
            text_lower = text.lower()
            
            # Find sentences containing pain point keywords
            sentences = text.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in pain_point_keywords):
                    cleaned = sentence.strip()
                    if len(cleaned) > 20:  # Meaningful sentence
                        pain_points.append(cleaned)
        
        # Deduplicate similar pain points
        unique_pain_points = []
        for point in pain_points:
            is_duplicate = False
            for unique_point in unique_pain_points:
                # Simple similarity check
                if len(set(point.split()) & set(unique_point.split())) > len(point.split()) * 0.6:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_pain_points.append(point)
        
        return unique_pain_points[:10]  # Return top 10 pain points
    
    def prepare_input_for_summary(self, texts: List[str], theme: str) -> str:
        """Prepare input text optimized for pain point summarization"""
        # Extract pain points first
        pain_points = self.extract_pain_points(texts)
        
        # Build structured input based on model type
        if 'flan-t5' in self.model_choice:
            # T5 models work better with instructions
            prompt = f"Summarize the main customer problems and pain points from these support tickets about {theme}:\n\n"
            
            # Add pain points
            if pain_points:
                prompt += "Key Issues:\n"
                for i, point in enumerate(pain_points[:5], 1):
                    prompt += f"{i}. {point}\n"
                prompt += "\n"
            
            # Add sample full tickets
            prompt += "Sample Tickets:\n"
            for i, text in enumerate(texts[:3], 1):
                if text and len(text) > 20:
                    preview = text[:200] + "..." if len(text) > 200 else text
                    prompt += f"Ticket {i}: {preview}\n"
            
            prompt += "\nSummary of main problems:"
            return prompt
            
        else:
            # BART and LED models - structure as article
            combined = f"Customer Support Tickets - {theme}\n\n"
            
            if pain_points:
                combined += "MAIN PROBLEMS IDENTIFIED:\n"
                for point in pain_points[:7]:
                    combined += f"• {point}\n"
                combined += "\n"
            
            combined += "DETAILED TICKETS:\n"
            for i, text in enumerate(texts[:5], 1):
                if text and len(text) > 20:
                    preview = text[:300] + "..." if len(text) > 300 else text
                    combined += f"[TICKET {i}]: {preview}\n\n"
            
            return combined
    
    def summarize_cluster(self, texts: List[str], theme: str, cluster_id: int) -> str:
        """Generate comprehensive summary of customer pain points in cluster"""
        if not texts:
            return f"Empty cluster: {theme}"

        # Combine all ticket descriptions
        combined_descriptions = " ".join([t for t in texts if t and len(t) > 20])
        if not combined_descriptions:
            return f"No sufficient content for {theme} (Cluster {cluster_id})"

        # Refine the prompt for better summarization
        refined_prompt = (
            f"Summarize the key pain points, actionable insights, and recurring issues "
            f"from the following customer support tickets related to {theme}:\n\n"
            f"{combined_descriptions}"
        )

        try:
            # Tokenize the refined prompt
            inputs = self.tokenizer(
                refined_prompt,
                max_length=self.max_input_length,
                return_tensors="pt",
                truncation=True,
                padding=True
            ).to(self.device)

            # Generate summary with optimized parameters
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs.get('attention_mask'),
                    max_length=self.max_output_length * 2,  # Allow longer summaries
                    min_length=100,  # Ensure a longer minimum length
                    num_beams=6,  # Use more beams for better quality
                    length_penalty=1.0,  # Neutral length penalty
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    do_sample=False
                )

            # Decode the generated summary
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            # Ensure theme context is included
            if theme.lower() not in summary.lower():
                summary = f"{theme}: {summary}"

            return summary

        except Exception as e:
            print(f"❌ Error during summarization: {e}")
            return f"Failed to generate summary for {theme} (Cluster {cluster_id})"
    
    def update_clustered_status(self, ticket_ids: List[str]):
        """Update the clustered status of tickets to TRUE."""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")

        try:
            with self.connection.cursor() as cursor:
                query = """
                    UPDATE tickets
                    SET clustered = TRUE
                    WHERE id = ANY(%s::uuid[])
                """
                cursor.execute(query, (ticket_ids,))
                self.connection.commit()
                print(f"✅ Updated clustered status for {len(ticket_ids)} tickets.")
        except Exception as e:
            print(f"❌ Failed to update clustered status: {e}")
            self.connection.rollback()
            return False

async def process_existing_supabase_data(organization_id=None, limit=None):
    """Main processing function - reads from tickets, writes to pain_points_cluster"""
    print("🚀 Enhanced AI Processing for Customer Support Tickets")
    print("=" * 65)
    
    if organization_id:
        print(f"🏢 Filtering by organization: {organization_id}")
    if limit:
        print(f"📊 Processing limit: {limit} tickets")
    
    # Initialize components
    db_manager = SupabaseManager()
    
    try:
        # Connect to database
        print("\n🔌 Connecting to Supabase...")
        db_manager.connect()
        
        # Load data from TICKETS table
        print("\n📊 Loading ticket data from TICKETS table...")
        raw_data = db_manager.get_data(organization_id=organization_id, limit=limit)
        
        if not raw_data:
            return {
                "message": "No classified tickets found for the specified criteria",
                "organization_id": organization_id,
                "total_tickets": 0,
                "clusters": []
            }
        
        # Process tickets for clustering - handle datetime serialization
        data = []
        for row in raw_data:
            # Combine text fields
            combined_text = ""
            if row.get('subject'):
                combined_text += str(row['subject']) + " "
            if row.get('description'):
                combined_text += str(row['description']) + " "
            if row.get('Customer Problem'):
                combined_text += str(row['Customer Problem']) + " "
            if row.get('Root Cause'):
                combined_text += str(row['Root Cause'])
            
            # Convert datetime objects to strings for JSON serialization
            created_at = row.get('created_at')
            if hasattr(created_at, 'isoformat'):
                created_at = created_at.isoformat()
            elif created_at:
                created_at = str(created_at)
            
            updated_at = row.get('updated_at')
            if hasattr(updated_at, 'isoformat'):
                updated_at = updated_at.isoformat()
            elif updated_at:
                updated_at = str(updated_at)
            
            data.append({
                'id': str(row['id']),  # Convert UUID to string
                'combined_text': combined_text.strip(),
                'subject': str(row.get('subject', '')),
                'description': str(row.get('description', '')),
                'feature': str(row.get('feature', '')),
                'customer_problem': str(row.get('Customer Problem', '')),
                'root_cause': str(row.get('Root Cause', '')),
                'organization_id': int(row.get('organization_id', 0)),  # Ensure int
                'created_at': created_at,  # Now serializable
                'updated_at': updated_at,  # Now serializable
                'priority': str(row.get('priority', '')),
                'status': str(row.get('status', '')),
                'tags': str(row.get('tags', '')),
                'url': str(row.get('url', '')),
                'source': str(row.get('source', '')),
                'type': str(row.get('type', '')),
                'rating': float(row.get('rating', 0)) if row.get('rating') else 0.0,
                'attachments': str(row.get('attachments', '')),
                'cluster': str(row.get('cluster', ''))
            })
        
        # Perform clustering
        print(f"\n🤖 Clustering {len(data)} tickets...")
        
        # Initialize clustering
        clustering = TextClustering()
        texts = [item['combined_text'] for item in data]
        cluster_labels = clustering.fit_predict(texts)
        
        # Initialize summarizer
        summarizer = EnhancedSummarizer(model_choice='bart-large-cnn')
        
        # Group by clusters
        clusters = {}
        for i, (item, cluster_id) in enumerate(zip(data, cluster_labels)):
            cluster_id = int(cluster_id)  # Ensure cluster_id is int
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    'cluster_id': cluster_id,
                    'tickets': [],
                    'texts': []
                }
            
            clusters[cluster_id]['tickets'].append(item)
            clusters[cluster_id]['texts'].append(item['combined_text'])
        
        # Generate summaries and prepare for saving
        cluster_results = []
        pain_points_data = []
        
        for cluster_id, cluster_data in clusters.items():
            theme = clustering.cluster_themes.get(cluster_id, f"Cluster {cluster_id}")
            
            # Generate AI summary
            if len(cluster_data['texts']) > 0:
                summary = summarizer.summarize_cluster(
                    cluster_data['texts'], 
                    theme, 
                    cluster_id
                )
            else:
                summary = "No summary available"
            
            # Prepare API response data (serializable)
            cluster_results.append({
                'cluster_id': int(cluster_id),  # Ensure int
                'theme': str(theme),
                'summary': str(summary),
                'ticket_count': int(len(cluster_data['tickets'])),
                'sample_tickets': cluster_data['tickets'][:3]
            })
            
            # Prepare database data with proper types and datetime handling
            pain_points_data.append({
                'cluster_id': int(cluster_id),
                'theme': str(theme),
                'summary': str(summary),
                'ticket_count': int(len(cluster_data['tickets'])),
                'tickets': cluster_data['tickets'],  # Datetime objects already converted to strings above
                'organization_id': int(organization_id),
                'cluster_size': int(len(cluster_data['tickets'])),
                'confidence_score': 0.85,
                'similarity_to_center': 0.75,
                'is_representative': cluster_id == 0,
                'hypothesis': {
                    'theme': str(theme),
                    'confidence': 0.85,
                    'key_features': [str(item['feature']) for item in cluster_data['tickets'][:5]],
                    'analysis_timestamp': datetime.now().isoformat()  # Convert to string
                }
            })
        
        # Sort by ticket count
        cluster_results.sort(key=lambda x: x['ticket_count'], reverse=True)
        
        # Save clustering results to pain_points_cluster table
        print(f"\n💾 Saving clustering results to pain_points_cluster table...")
        save_success = db_manager.save_clusters_to_pain_points(pain_points_data)
        
        return {
            "message": "Clustering completed successfully",
            "organization_id": str(organization_id),  # Convert to string for JSON
            "total_tickets": int(len(data)),
            "total_clusters": int(len(cluster_results)),
            "database_updated": bool(save_success),
            "clusters": cluster_results
        }
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        raise Exception(f"Clustering failed: {str(e)}")
        
    finally:
        db_manager.close()

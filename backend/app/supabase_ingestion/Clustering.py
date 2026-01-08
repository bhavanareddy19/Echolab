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
from sklearn.metrics.pairwise import cosine_similarity
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
        try:
            # Get individual connection parameters
            db_params = {
                'host': os.getenv("DB_HOST"),
                'port': os.getenv("DB_PORT"),
                'database': os.getenv("DB_NAME"),
                'user': os.getenv("DB_USER"),
                'password': os.getenv("DB_PASSWORD"),
            }
            
            # Check if all parameters are available
            if not all(db_params.values()):
                raise Exception("Missing database connection parameters")
            
            print(f"🔌 Connecting to Supabase PostgreSQL at {db_params['host']}:{db_params['port']}...")
            
            # Connect using psycopg2
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

    def get_unclustered_tickets(self, organization_id=None):
        """Load only unclustered tickets from TICKETS table"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")
            
        query = """
            SELECT t.id, t.subject, t.description, t.url, t.source, t.created_at, t.updated_at, 
                   t.type, t.priority, t.status, t.submitter_id, t.tags, t.rating, t.attachments, 
                   t.organization_id, t.feature, t.cluster, t."Customer Problem", t."Root Cause"
            FROM tickets t
            LEFT JOIN pain_points_cluster ppc ON t.id::text = ppc.ticket_id::text
            WHERE ppc.ticket_id IS NULL
            AND t.feature IS NOT NULL
        """
        params = []
        
        if organization_id:
            query += " AND t.organization_id = %s"
            params.append(organization_id)
            
        query += " ORDER BY t.created_at DESC"
        
        print(f"📊 Loading unclustered tickets from TICKETS table...")
        
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        
        print(f"📊 Loaded {len(data)} unclustered records from tickets table")
        return data

    def get_existing_clusters(self, organization_id=None):
        """Get existing clusters from pain_points_cluster table"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")
            
        query = """
            SELECT cluster_id, cluster_theme, array_agg(ticket_id) as ticket_ids, 
                   COUNT(*) as cluster_size, organization_id
            FROM pain_points_cluster
            WHERE cluster_id IS NOT NULL
        """
        params = []
        
        if organization_id:
            query += " AND organization_id = %s"
            params.append(organization_id)
            
        query += " GROUP BY cluster_id, cluster_theme, organization_id"
        
        print(f"📊 Loading existing clusters from pain_points_cluster table...")
        
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        
        print(f"📊 Loaded {len(data)} existing clusters")
        return data

    def get_cluster_representatives(self, organization_id=None):
        """Get representative tickets for each cluster"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")
            
        query = """
            SELECT cluster_id, body, cluster_theme
            FROM pain_points_cluster
            WHERE cluster_representative = true
        """
        params = []
        
        if organization_id:
            query += " AND organization_id = %s"
            params.append(organization_id)
            
        print(f"📊 Loading cluster representatives...")
        
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        
        print(f"📊 Loaded {len(data)} cluster representatives")
        return data

    def save_clusters_to_pain_points(self, clustered_data):
        """Save clustering results to pain_points_cluster table"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")
            
        try:
            print(f"💾 Saving {len(clustered_data)} clusters to pain_points_cluster table...")
            
            with self.connection.cursor() as cursor:
                # Insert new cluster summaries
                for cluster_data in clustered_data:
                    insert_query = """
                        INSERT INTO pain_points_cluster 
                        (ticket_id, body, tickets, num_of_tickets, status, organization_id, 
                         cluster_group, score, cluster_id, similarity_to_center, 
                         cluster_representative, cluster_size, cluster_theme, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # Convert data types properly - especially datetime handling
                    cursor.execute(insert_query, (
                        str(cluster_data.get('ticket_id', '')),  # ticket_id
                        str(cluster_data.get('summary', '')),  # body - convert to string
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

    def update_ticket_cluster_assignment(self, ticket_id, cluster_id, similarity, is_representative=False):
        """Update a ticket's cluster assignment"""
        if not self.connection:
            raise Exception("Database connection not established. Call connect() first.")
            
        try:
            with self.connection.cursor() as cursor:
                update_query = """
                    UPDATE pain_points_cluster 
                    SET cluster_id = %s, similarity_to_center = %s, cluster_representative = %s
                    WHERE ticket_id = %s
                """
                
                cursor.execute(update_query, (
                    int(cluster_id),
                    float(similarity),
                    bool(is_representative),
                    str(ticket_id)
                ))
        
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Failed to update ticket cluster assignment: {e}")
            if self.connection:
                self.connection.rollback()
            return False


class TextClustering:
    """Intelligent text clustering for customer support tickets with incremental clustering"""
    
    def __init__(self, n_clusters=None, max_features=5000, similarity_threshold=0.6):
        self.n_clusters = n_clusters
        self.max_features = max_features
        self.similarity_threshold = similarity_threshold
        self.vectorizer = None
        self.kmeans = None
        self.cluster_themes = {}
        self.cluster_centers = {}
        
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
    
    def incremental_cluster(self, new_texts, existing_clusters=None):
        """Incrementally cluster new texts, matching to existing clusters when possible"""
        print("🔍 Incremental clustering of new tickets...")
        
        # Clean new texts
        clean_new_texts = [self.preprocess_text(text) for text in new_texts]
        valid_indices = [i for i, t in enumerate(clean_new_texts) if len(t) > 10]
        valid_new_texts = [clean_new_texts[i] for i in valid_indices]
        
        if len(valid_new_texts) == 0:
            print("⚠️ No valid texts for clustering")
            return [0] * len(new_texts), {}
        
        # Initialize cluster assignments
        cluster_assignments = [-1] * len(new_texts)  # -1 means not yet assigned
        similarities = [0.0] * len(new_texts)
        
        # If we have existing clusters, try to match new texts to them
        if existing_clusters and len(existing_clusters) > 0:
            print(f"   Matching against {len(existing_clusters)} existing clusters...")
            
            # Vectorize new texts
            if not self.vectorizer:
                self.vectorizer = TfidfVectorizer(
                    max_features=self.max_features,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.8
                )
                # Fit on new texts (we don't have the original training data)
                self.vectorizer.fit(valid_new_texts)
            
            new_vectors = self.vectorizer.transform(valid_new_texts)
            
            # For each existing cluster, calculate similarity to its center
            for cluster_id, cluster_info in existing_clusters.items():
                if 'center' not in cluster_info:
                    continue
                    
                # Calculate cosine similarity
                cluster_similarities = cosine_similarity(new_vectors, cluster_info['center'])
                
                # Assign texts that are similar enough to this cluster
                for i, idx in enumerate(valid_indices):
                    if cluster_similarities[i] >= self.similarity_threshold and cluster_similarities[i] > similarities[idx]:
                        cluster_assignments[idx] = cluster_id
                        similarities[idx] = cluster_similarities[i]
                        print(f"      Text matched to cluster {cluster_id} (similarity: {cluster_similarities[i]:.3f})")
        
        # Find unassigned texts
        unassigned_indices = [i for i, cluster_id in enumerate(cluster_assignments) if cluster_id == -1]
        unassigned_texts = [new_texts[i] for i in unassigned_indices]
        
        # Cluster unassigned texts
        if len(unassigned_texts) > 0:
            print(f"   Clustering {len(unassigned_texts)} unassigned texts into new clusters...")
            
            # Determine cluster count for unassigned texts
            n_clusters = self.determine_optimal_clusters(unassigned_texts)
            self.n_clusters = n_clusters  # Set the instance variable
            print(f"   Creating {n_clusters} new clusters")
            
            # Vectorize unassigned texts
            if not self.vectorizer:
                self.vectorizer = TfidfVectorizer(
                    max_features=self.max_features,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.8
                )
            
            unassigned_vectors = self.vectorizer.fit_transform(unassigned_texts)
            
            # Cluster unassigned texts
            self.kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10,
                max_iter=300
            )
            
            new_cluster_labels = self.kmeans.fit_predict(unassigned_vectors)
            
            # Generate cluster themes
            self._generate_cluster_themes(unassigned_texts, new_cluster_labels)
            
            # Store cluster centers for future matching
            for cluster_id in range(n_clusters):
                cluster_indices = np.where(new_cluster_labels == cluster_id)[0]
                if len(cluster_indices) > 0:
                    self.cluster_centers[cluster_id] = {
                        'center': unassigned_vectors[cluster_indices].mean(axis=0),
                        'theme': self.cluster_themes.get(cluster_id, f"Cluster {cluster_id}")
                    }
            
            # Map back to original indices
            next_cluster_id = max(existing_clusters.keys()) + 1 if existing_clusters else 0
            for i, original_idx in enumerate(unassigned_indices):
                cluster_id = new_cluster_labels[i] + next_cluster_id
                cluster_assignments[original_idx] = cluster_id
                similarities[original_idx] = 1.0  # Default similarity for new clusters
        
        return cluster_assignments, self.cluster_centers
    
    def _generate_cluster_themes(self, texts, labels):
        """Generate descriptive themes for each cluster"""
        if self.n_clusters is None:
            print("⚠️ No clusters to generate themes for")
            return
            
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
        
        # Filter valid texts
        valid_texts = [t for t in texts if t and len(t) > 20]
        if not valid_texts:
            return f"No sufficient content for {theme} (Cluster {cluster_id})"
        
        # Prepare input
        prepared_input = self.prepare_input_for_summary(valid_texts, theme)
        
        # Truncate if needed
        if len(prepared_input) > self.max_input_length * 4:  # Rough char to token ratio
            prepared_input = prepared_input[:self.max_input_length * 3]
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                prepared_input,
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
                    max_length=self.max_output_length,
                    min_length=50,
                    num_beams=4,
                    length_penalty=1.5,  # Encourage longer summaries
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    do_sample=False,
                    temperature=1.0
                )
            
            # Decode summary
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            # Post-process summary
            if not summary.strip():
                # Fallback to extractive summary
                pain_points = self.extract_pain_points(valid_texts)
                if pain_points:
                    summary = f"Customers are experiencing the following issues with {theme}: "
                    summary += "; ".join(pain_points[:3])
                else:
                    summary = f"Multiple customer requests and issues related to {theme}"
            
            # Ensure theme context is included
            if theme.lower() not in summary.lower():
                summary = f"{theme}: {summary}"
            
            # Add structured metadata
            metadata_lines = [
                f"\n\n📊 CLUSTER ANALYSIS:",
                f"• Cluster ID: {cluster_id}",
                f"• Category: {theme}",
                f"• Total Tickets: {len(texts)}",
                f"• AI Model: {self.model_choice}",
                f"• Key Pain Points Identified: {len(self.extract_pain_points(valid_texts))}"
            ]
            
            return summary + "\n".join(metadata_lines)
            
        except Exception as e:
            print(f"⚠️ AI summarization failed for cluster {cluster_id}: {e}")
            
            # Enhanced fallback
            pain_points = self.extract_pain_points(valid_texts)
            if pain_points:
                fallback = f"{theme} - Customer Pain Points:\n"
                for i, point in enumerate(pain_points[:5], 1):
                    fallback += f"{i}. {point}\n"
            else:
                fallback = f"{theme}: Analysis of {len(texts)} customer support tickets"
            
            metadata = f"\n\n[Fallback summary | Cluster {cluster_id} | {len(texts)} tickets]"
            return fallback + metadata
    
    def cleanup(self):
        """Clean up GPU memory"""
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        print("🧹 GPU memory cleaned up")


def process_incremental_clustering(organization_id=None):
    """Main processing function for incremental clustering"""
    print("🚀 Incremental AI Clustering for Customer Support Tickets")
    print("=" * 65)
    
    if organization_id:
        print(f"🏢 Filtering by organization: {organization_id}")
    
    # Initialize components
    db_manager = SupabaseManager()
    
    try:
        # Connect to database
        print("\n🔌 Connecting to Supabase...")
        db_manager.connect()
        
        # Load unclustered tickets
        print("\n📊 Loading unclustered ticket data from TICKETS table...")
        raw_data = db_manager.get_unclustered_tickets(organization_id=organization_id)
        
        if not raw_data:
            return {
                "message": "No unclustered tickets found for the specified criteria",
                "organization_id": organization_id,
                "total_tickets": 0,
                "clusters_updated": 0
            }
        
        # Load existing clusters
        print("\n📊 Loading existing clusters for matching...")
        existing_clusters_data = db_manager.get_existing_clusters(organization_id)
        
        # Prepare existing clusters for matching
        existing_clusters = {}
        if existing_clusters_data:
            # Get cluster representatives for vectorization
            cluster_reps = db_manager.get_cluster_representatives(organization_id)
            
            # Create a simple mapping for now - in a real implementation, we'd need to store vector representations
            for cluster in existing_clusters_data:
                existing_clusters[cluster['cluster_id']] = {
                    'theme': cluster['cluster_theme'],
                    'size': cluster['cluster_size']
                }
        
        # Process tickets for clustering
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
        
        # Perform incremental clustering
        print(f"\n🤖 Incrementally clustering {len(data)} new tickets...")
        
        # Initialize clustering
        clustering = TextClustering(similarity_threshold=0.6)  # Adjust threshold as needed
        texts = [item['combined_text'] for item in data]
        
        # Perform incremental clustering
        cluster_labels, new_clusters = clustering.incremental_cluster(texts, existing_clusters)
        
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
            # Determine if this is an existing or new cluster
            is_existing = cluster_id in existing_clusters
            theme = existing_clusters[cluster_id]['theme'] if is_existing else f"Cluster {cluster_id}"
            
            # For new clusters, generate AI summary
            if not is_existing and len(cluster_data['texts']) > 0:
                summary = summarizer.summarize_cluster(
                    cluster_data['texts'], 
                    theme, 
                    cluster_id
                )
            else:
                summary = f"Added to existing cluster: {theme}"
            
            # Prepare API response data (serializable)
            cluster_results.append({
                'cluster_id': int(cluster_id),  # Ensure int
                'theme': str(theme),
                'summary': str(summary),
                'ticket_count': int(len(cluster_data['tickets'])),
                'is_new': not is_existing,
                'sample_tickets': cluster_data['tickets'][:3]
            })
            
            # Prepare database data with proper types and datetime handling
            for ticket in cluster_data['tickets']:
                pain_points_data.append({
                    'ticket_id': str(ticket['id']),
                    'cluster_id': int(cluster_id),
                    'theme': str(theme),
                    'summary': str(summary),
                    'ticket_count': int(len(cluster_data['tickets'])),
                    'tickets': [ticket],  # Single ticket for individual assignment
                    'organization_id': int(organization_id) if organization_id else int(ticket['organization_id']),
                    'cluster_size': int(len(cluster_data['tickets'])),
                    'confidence_score': 0.85,
                    'similarity_to_center': 0.75,  # Default value
                    'is_representative': False,  # Will set representative later
                })
        
        # Sort by ticket count
        cluster_results.sort(key=lambda x: x['ticket_count'], reverse=True)
        
        # Save clustering results to pain_points_cluster table
        print(f"\n💾 Saving clustering results to pain_points_cluster table...")
        save_success = db_manager.save_clusters_to_pain_points(pain_points_data)
        
        return {
            "message": "Incremental clustering completed successfully",
            "organization_id": str(organization_id),  # Convert to string for JSON
            "total_tickets": int(len(data)),
            "existing_clusters_matched": len([c for c in cluster_results if not c['is_new']]),
            "new_clusters_created": len([c for c in cluster_results if c['is_new']]),
            "database_updated": bool(save_success),
            "clusters": cluster_results
        }
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        raise Exception(f"Clustering failed: {str(e)}")
        
    finally:
        # Clean up
        if 'summarizer' in locals():
            summarizer.cleanup()
        db_manager.close()


# Example usage
if __name__ == "__main__":
    # Process incremental clustering for all unclustered tickets
    result = process_incremental_clustering()
    print(f"\n🎯 Clustering Result: {result['message']}")
    print(f"   Total tickets processed: {result['total_tickets']}")
    print(f"   Matched to existing clusters: {result['existing_clusters_matched']}")
    print(f"   New clusters created: {result['new_clusters_created']}")
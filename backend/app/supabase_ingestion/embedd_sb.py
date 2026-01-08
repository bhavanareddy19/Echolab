#!/usr/bin/env python3
"""
Automated Ticket Embedding Generator
Automatically generates embeddings for all tickets in the database
"""

import psycopg2
from psycopg2.extras import execute_batch
import os
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import time

# Load environment variables
load_dotenv()

# Configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64
EMBEDDING_DIMENSION = 384
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_TEXT_LENGTH = 512

# Database connection
DB_CONFIG = {
    'user': os.getenv('DB_USER') or os.getenv('user'),
    'password': os.getenv('DB_PASSWORD') or os.getenv('password'),
    'host': os.getenv('DB_HOST') or os.getenv('host'),
    'port': os.getenv('DB_PORT') or os.getenv('port') or '5432',
    'dbname': os.getenv('DB_NAME') or os.getenv('dbname') or 'postgres',
}

# Add SSL for Supabase
if DB_CONFIG['host'] and 'supabase' in DB_CONFIG['host'].lower():
    DB_CONFIG['sslmode'] = 'require'

def main():
    print("=" * 60)
    print("AUTOMATED TICKET EMBEDDING GENERATOR")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Device: {DEVICE}")
    print(f"Batch Size: {BATCH_SIZE}")
    
    # Load model
    print("\nLoading model...")
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Check embedding column
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'tickets' 
        AND column_name IN ('body_embedding', 'embedding')
        LIMIT 1
    """)
    result = cursor.fetchone()
    if not result:
        print("ERROR: No embedding column found!")
        return
    
    embedding_column = result[0]
    
    # Fetch all tickets
    print(f"Fetching tickets...")
    cursor.execute("""
        SELECT id, description, subject 
        FROM tickets 
        WHERE description IS NOT NULL OR subject IS NOT NULL
    """)
    tickets = cursor.fetchall()
    
    if not tickets:
        print("No tickets found!")
        return
    
    print(f"Found {len(tickets)} tickets")
    
    # Process in batches
    start_time = time.time()
    total_updated = 0
    
    for i in range(0, len(tickets), BATCH_SIZE):
        batch = tickets[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(tickets) + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Prepare texts
        texts = []
        ids = []
        for ticket_id, description, subject in batch:
            # Combine subject and description
            text_parts = []
            if subject:
                text_parts.append(f"Subject: {subject}")
            if description:
                text_parts.append(f"Description: {description}")
            
            text = " ".join(text_parts)[:MAX_TEXT_LENGTH * 4]
            if text:
                texts.append(text)
                ids.append(ticket_id)
        
        if not texts:
            continue
        
        # Generate embeddings
        print(f"Batch {batch_num}/{total_batches}: Processing {len(texts)} tickets...", end=' ')
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        
        # Update database
        update_query = f"""
            UPDATE tickets 
            SET {embedding_column} = %s, updated_at = %s
            WHERE id = %s
        """
        
        update_data = []
        for ticket_id, embedding in zip(ids, embeddings):
            embedding_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
            update_data.append((embedding_str, datetime.now(), ticket_id))
        
        execute_batch(cursor, update_query, update_data, page_size=100)
        conn.commit()
        total_updated += len(update_data)
        print(f"✓")
    
    # Final statistics
    elapsed = time.time() - start_time
    cursor.execute(f"SELECT COUNT(*) FROM tickets WHERE {embedding_column} IS NOT NULL")
    total_with_embeddings = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("COMPLETED")
    print("=" * 60)
    print(f"Processed: {total_updated} tickets")
    print(f"Time: {elapsed:.2f} seconds")
    print(f"Speed: {total_updated/elapsed:.2f} tickets/second")
    print(f"Total with embeddings: {total_with_embeddings}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
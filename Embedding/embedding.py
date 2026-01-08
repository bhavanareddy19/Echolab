import csv
import numpy as np
import os
from tqdm import tqdm
import torch
from sentence_transformers import SentenceTransformer

# Configuration
INPUT_CSV = 'b2b.csv'
OUTPUT_CSV = 'embedding_minilm_l6_v2.csv'
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64  # Adjust based on your GPU memory
EMBEDDING_DIMENSION = 384  # All-MiniLM-L6-v2 dimension
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def get_embeddings(model, texts):
    """Generate embeddings for a batch of texts using sentence-transformers"""
    try:
        # sentence-transformers handles batching and GPU automatically
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=BATCH_SIZE
        )
        return embeddings.astype(np.float32)
    
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        # Return empty embeddings for failed batch
        return np.zeros((len(texts), EMBEDDING_DIMENSION), dtype=np.float32)

def generate_embeddings():
    """Generate embeddings and save to CSV"""
    if os.path.exists(OUTPUT_CSV):
        print(f"{OUTPUT_CSV} already exists. Skipping embedding generation.")
        return
    
    print(f"Loading model: {MODEL_NAME}")
    print(f"Using device: {DEVICE}")
    
    # Load the sentence transformer model
    try:
        model = SentenceTransformer(MODEL_NAME, device=DEVICE)
        print(f"Model loaded successfully on {DEVICE}")
        
        # Print GPU memory info if using CUDA
        if DEVICE == "cuda":
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            print(f"GPU Memory Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Read IDs and bodies from CSV
    ids = []    
    bodies = []
    print(f"Reading data from {INPUT_CSV}...")
    
    try:
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in tqdm(reader, desc="Reading CSV"):
                if row['body'] and row['body'].strip():  # Skip empty bodies
                    ids.append(row['id'])
                    # Truncate text if too long (model has token limits)
                    body = row['body'][:512]  # All-MiniLM-L6-v2 has 512 token limit
                    bodies.append(body)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Found {len(bodies)} valid entries to process")

    # Process in batches and save to CSV
    print(f"Generating embeddings and saving to {OUTPUT_CSV}...")
    
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'body', 'embedding'])
            
            # Process all texts at once (sentence-transformers handles batching internally)
            print("Generating embeddings...")
            all_embeddings = model.encode(
                bodies, 
                convert_to_numpy=True, 
                show_progress_bar=True,
                batch_size=BATCH_SIZE
            )
            
            print("Writing embeddings to CSV...")
            for i, (id_val, body, embedding) in enumerate(tqdm(zip(ids, bodies, all_embeddings), total=len(ids))):
                try:
                    emb_str = "[" + ",".join(map(str, embedding.tolist())) + "]"
                    writer.writerow([id_val, body, emb_str])
                except Exception as e:
                    print(f"Error writing row {i}: {e}")
                    writer.writerow([id_val, body, ''])
    
    except Exception as e:
        print(f"Error during embedding generation: {e}")
        return

    print("Embedding generation complete!")
    print(f"Embeddings saved to: {OUTPUT_CSV}")
    
    # Print GPU memory usage if using CUDA
    if DEVICE == "cuda":
        print(f"Final GPU Memory Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")

# Main execution flow
if __name__ == "__main__":
    # Check for CUDA availability
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Input file {INPUT_CSV} not found!")
        exit(1)

    generate_embeddings()
    print("\nProcess completed successfully!")
    print(f"Your embeddings are saved in: {OUTPUT_CSV}")
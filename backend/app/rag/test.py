# search_tickets.py
import asyncio
import json
import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor
from datetime import datetime
from b2b_saas_table import get_all_records
from transformers import AutoTokenizer, AutoModel

print("🚀 Loading embedding model for search...")
MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"

# Use official implementation from model card
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, padding_side='left')
model = AutoModel.from_pretrained(MODEL_ID)
print("✅ Model loaded successfully!")

def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """Official implementation from Qwen model card"""
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

def get_detailed_instruct(task_description: str, query: str) -> str:
    """Official instruction format from model card"""
    return f'Instruct: {task_description}\nQuery:{query}'

# Task description for queries (not documents)
TASK_DESCRIPTION = 'Given a web search query, retrieve relevant passages that answer the query'

@torch.no_grad()
def embed_query(text: str, max_length=8192) -> np.ndarray:
    """Generate query embedding using official Qwen implementation"""
    # Format query with instruction (as per model card)
    formatted_query = get_detailed_instruct(TASK_DESCRIPTION, text)
    
    # Tokenize
    batch_dict = tokenizer(
        [formatted_query],
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    batch_dict.to(model.device)
    
    # Get embeddings
    outputs = model(**batch_dict)
    embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
    
    # Normalize
    embeddings = F.normalize(embeddings, p=2, dim=1)
    
    return embeddings[0].cpu().numpy()

@torch.no_grad()
def embed_document(text: str, max_length=8192) -> np.ndarray:
    """Generate document embedding (no instruction needed)"""
    # Documents don't need instruction formatting
    batch_dict = tokenizer(
        [text],
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    batch_dict.to(model.device)
    
    # Get embeddings
    outputs = model(**batch_dict)
    embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
    
    # Normalize
    embeddings = F.normalize(embeddings, p=2, dim=1)
    
    return embeddings[0].cpu().numpy()

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    try:
        vec1 = np.array(vec1).flatten()
        vec2 = np.array(vec2).flatten()
        
        if len(vec1) != len(vec2):
            print(f"⚠️ Vector length mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0
        
        # Since vectors are already normalized, dot product = cosine similarity
        similarity = float(np.dot(vec1, vec2))
        
        # Clamp to [-1, 1] range
        similarity = max(-1.0, min(1.0, similarity))
        
        return similarity
        
    except Exception as e:
        print(f"❌ Error in cosine_similarity: {e}")
        return 0.0

# Test the official implementation
def test_official_implementation():
    """Test with the exact example from model card"""
    print("\n🧪 TESTING OFFICIAL QWEN IMPLEMENTATION")
    print("="*60)
    
    # Exact example from model card
    task = 'Given a web search query, retrieve relevant passages that answer the query'
    
    queries = [
        get_detailed_instruct(task, 'What is the capital of China?'),
        get_detailed_instruct(task, 'Explain gravity')
    ]
    
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other."
    ]
    
    input_texts = queries + documents
    
    # Process all at once like in model card
    batch_dict = tokenizer(
        input_texts,
        padding=True,
        truncation=True,
        max_length=8192,
        return_tensors="pt",
    )
    
    outputs = model(**batch_dict)
    embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    
    # Calculate similarities
    scores = (embeddings[:2] @ embeddings[2:].T)
    print("Official example scores:", scores.tolist())
    print("Expected: [[0.7645, 0.1414], [0.1355, 0.5999]]")
    
    return embeddings

async def semantic_search(question, top_k=3):
    """
    Perform semantic search to find most relevant chunks for a question
    """
    print(f"🔍 Searching for: '{question}'")
    print("="*60)
    try:
        print("📊 Generating question embedding with instruction...")
        question_embedding = embed_query(question)
        print(f"✅ Question embedding shape: {question_embedding.shape}")

        print("📚 Fetching all stored chunks...")
        records = await get_all_records()
        if not records:
            print("❌ No records found in the database.")
            return []

        print(f"📄 Comparing against {len(records)} stored chunks...")
        similarities = []
        successful_comparisons = 0

        for i, record in enumerate(records):
            try:
                if record.embedding is not None and len(record.embedding) > 0:
                    sim = cosine_similarity(question_embedding, record.embedding)
                    if sim is not None and not np.isnan(sim):
                        similarities.append({
                            'record': record,
                            'similarity': float(sim),
                            'confidence': record.chunk_metadata.get('confidence_score', 0) if record.chunk_metadata else 0
                        })
                        successful_comparisons += 1
                else:
                    print(f"⚠️ Record {record.id} has no embedding or empty embedding")
            except Exception as e:
                print(f"❌ Error processing record {record.id}: {e}")
                continue

        print(f"✅ Successfully compared {successful_comparisons} chunks")
        if not similarities:
            print("❌ No valid similarities calculated.")
            return []

        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = similarities[:top_k]

        print(f"\n🎯 Top {len(top_results)} Results:")
        print("="*60)
        for i, result in enumerate(top_results, 1):
            record = result['record']
            sim = result['similarity']
            conf = result['confidence']
            print(f"\n#{i} Match (Similarity: {sim:.4f})")
            print("-" * 40)
            print(f"📝 Chunk ID: {record.id}")
            print(f"🔗 Source URL: {record.url}")
            print(f"📄 Title: {record.title}")
            print(f"🔢 Chunk Order: {record.chunk_order}")
            print(f"📊 Confidence: {conf:.3f}")
            print(f"📅 Created: {record.created_at}")
            if record.chunk_metadata and record.chunk_metadata.get('chunk_text'):
                chunk_text = record.chunk_metadata['chunk_text']
                preview = chunk_text[:300] + "..." if len(chunk_text) > 300 else chunk_text
                print(f"📖 Content Preview: {preview}")
            if record.chunk_metadata:
                metadata = record.chunk_metadata
                if metadata.get("tags"):
                    print(f"🏷️  Tags: {', '.join(metadata['tags'])}")
                if metadata.get("category"):
                    print(f"📂 Category: {metadata['category']}")
                if metadata.get("word_count"):
                    print(f"📊 Word Count: {metadata['word_count']}")

        return top_results

    except Exception as e:
        print(f"❌ Error during semantic search: {e}")
        import traceback; traceback.print_exc()
        return []


async def debug_embeddings():
    """Debug function to check embedding data"""
    print("🔧 Debugging embedding data...")
    try:
        records = await get_all_records()
        print(f"📄 Found {len(records)} records")
        for i, record in enumerate(records[:3]):
            print(f"\nRecord {i+1}:")
            print(f"  ID: {record.id}")
            print(f"  Embedding exists: {record.embedding is not None}")
            if record.embedding is not None and len(record.embedding) > 0:
                try:
                    emb_preview = list(record.embedding)[:5]  # works with memoryview/array
                    print(f"Embedding: {emb_preview}")
                except Exception as e:
                    print(f"⚠️ Could not preview embedding: {e}")
            else:
                print("Embedding: None")

        print("\n🔍 Testing question embedding...")
        test_question = "What is product-led growth?"
        question_emb = embed_query(test_question)
        print(f"Question embedding shape: {question_emb.shape}")
        print(f"Question embedding norm: {np.linalg.norm(question_emb):.4f}")

        if records and records[0].embedding:
            test_similarity = cosine_similarity(question_emb, records[0].embedding)
            print(f"Test similarity: {test_similarity:.4f}")

    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback; traceback.print_exc()


async def interactive_search():
    """Interactive search interface"""
    print("\n🤖 Interactive Semantic Search")
    print("=" * 50)
    print("Type your questions to search through stored content.")
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'debug' to run embedding diagnostics.\n")

    while True:
        try:
            question = input("❓ Enter your question: ").strip()
            if question.lower() in ['quit','exit','q']:
                print("👋 Goodbye!"); break
            if question.lower() == 'debug':
                await debug_embeddings(); continue
            if not question:
                print("⚠️ Please enter a question."); continue
            results = await semantic_search(question, top_k=3)
            if not results:
                print("😞 No relevant results found.")
            print("\n" + "="*60)
            print("Ready for next question...\n")
        except KeyboardInterrupt:
            print("\n👋 Search interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def view_all_data():
    """Fetch and display all records in the table"""
    print("\n" + "=" * 50)
    print("ALL RECORDS IN TABLE:")
    print("="*50)
    try:
        records = await get_all_records()
        if not records:
            print("No records found in the table."); return
        for record in records:
            print(f"\nID: {record.id}")
            print(f"URL: {record.url}")
            print(f"Title: {record.title}")
            print(f"Chunk Order: {record.chunk_order}")
            print(f"Created At: {record.created_at}")
            if record.embedding:
                print(f"Embedding: {record.embedding[:5]}... (showing first 5 values)")
            else:
                print("Embedding: None")
            print(
                f"Chunk Metadata: {json.dumps(record.chunk_metadata, indent=2) if record.chunk_metadata else 'None'}"
            )
            print("-" * 30)
    except Exception as e:
        print(f"Error fetching records: {e}")

async def debug_specific_search(question):
    """Debug a specific search to understand what's happening"""
    print(f"\n🔧 DEBUGGING SEARCH FOR: '{question}'")
    print("="*70)
    try:
        q_emb = embed_query(question)
        print(f"📊 Question embedding: shape {q_emb.shape}, norm {np.linalg.norm(q_emb):.3f}")

        records = await get_all_records()
        print(f"📄 Total records: {len(records)}")

        all_similarities = []
        for record in records:
            if record.embedding is not None:
                sim = cosine_similarity(q_emb, record.embedding)
                chunk_text = record.chunk_metadata.get('chunk_text', '') if record.chunk_metadata else ''
                all_similarities.append({
                    'id': record.id,
                    'similarity': sim,
                    'title': record.title,
                    'chunk_text': chunk_text[:200],
                    'embedding_norm': np.linalg.norm(record.embedding)
                })

        all_similarities.sort(key=lambda x: x['similarity'], reverse=True)

        print(f"\n📈 SIMILARITY DISTRIBUTION:")
        sims = [s['similarity'] for s in all_similarities]
        print(f"   Mean: {np.mean(sims):.3f}")
        print(f"   Median: {np.median(sims):.3f}")
        print(f"   Max: {np.max(sims):.3f}")
        print(f"   Min: {np.min(sims):.3f}")
        print(f"   Std Dev: {np.std(sims):.3f}")

        print(f"\n🔍 TOP 10 RESULTS WITH CONTENT PREVIEW:")
        print("-" * 70)
        for i, result in enumerate(all_similarities[:10], 1):
            print(f"\n{i}. ID: {result['id']} | Similarity: {result['similarity']:.4f}")
            print(f"   Title: {result['title']}")
            print(f"   Embedding norm: {result['embedding_norm']:.3f}")
            print(f"   Content: {result['chunk_text']}...")

        # simple keyword probe (optional)
        print(f"\n🔍 KEYWORD PROBE:")
        eureka_matches = [r for r in all_similarities if 'eureka' in r['chunk_text'].lower()]
        print(f"   Eureka matches: {len(eureka_matches)}")

        return all_similarities
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback; traceback.print_exc()
        return []

async def test_embedding_quality():
    """Sanity check: unrelated topics should NOT be highly similar now"""
    print(f"\n🧪 TESTING EMBEDDING QUALITY")
    print("="*50)
    test_queries = [
        "What is machine learning?",
        "How to cook pasta?",
        "Financial planning strategies",
        "User onboarding best practices"
    ]
    print("Testing similarity between very different topics:")
    embs = [embed_query(t) for t in test_queries]  # use query formatter so we test query space
    for i, q1 in enumerate(test_queries):
        for j, q2 in enumerate(test_queries[i+1:], i+1):
            sim = cosine_similarity(embs[i], embs[j])
            print(f"'{q1}' vs '{q2}': {sim:.3f}")
    print("\n🔍 Expected: Similarities should be much lower (<0.5-ish) for unrelated pairs.")

async def test_raw_similarities():
    """Compare fresh query embeddings vs stored doc embeddings"""
    print(f"\n🧪 TESTING RAW SIMILARITY CALCULATION")
    print("="*60)
    test_texts = [
        "What is the IKEA effect in action?",
        "User onboarding best practices",
        "How to cook pasta",
        "Machine learning algorithms"
    ]
    print("Testing fresh query embeddings:")
    q_embs = [embed_query(t) for t in test_texts]
    print("Cosines among queries (should be low for unrelated):")
    for i, t1 in enumerate(test_texts):
        for j, t2 in enumerate(test_texts[i+1:], i+1):
            sim = cosine_similarity(q_embs[i], q_embs[j])
            print(f"'{t1[:22]}...' vs '{t2[:22]}...': {sim:.3f}")

    print(f"\n🔍 Testing against database embeddings:")
    records = await get_all_records()
    if records:
        db_embedding = records[0].embedding
        fresh_embedding = embed_query("What is the IKEA effect?")
        print(f"Database embedding norm: {np.linalg.norm(db_embedding):.3f}")
        print(f"Fresh query embedding norm: {np.linalg.norm(fresh_embedding):.3f}")
        similarity = cosine_similarity(fresh_embedding, db_embedding)
        print(f"Fresh (query) vs DB (doc) similarity: {similarity:.3f}")

async def test_stored_vs_fresh_embeddings():
    """Test if stored embeddings match fresh ones"""
    print("\n🔍 TESTING STORED vs FRESH EMBEDDINGS")
    print("="*60)
    
    records = await get_all_records()
    if not records:
        print("❌ No records found")
        return
    
    # Get a record with text
    test_record = None
    for record in records:
        if record.chunk_metadata and record.chunk_metadata.get('chunk_text'):
            test_record = record
            break
    
    if not test_record:
        print("❌ No record with chunk text found")
        return
    
    chunk_text = test_record.chunk_metadata['chunk_text']
    print(f"📄 Testing with chunk: {chunk_text[:100]}...")
    
    # Generate fresh document embedding (correct way)
    fresh_embedding = embed_document(chunk_text)
    stored_embedding = np.array(test_record.embedding)
    
    print(f"📊 Fresh embedding shape: {fresh_embedding.shape}")
    print(f"📊 Stored embedding shape: {stored_embedding.shape}")
    print(f"📊 Fresh embedding norm: {np.linalg.norm(fresh_embedding):.4f}")
    print(f"📊 Stored embedding norm: {np.linalg.norm(stored_embedding):.4f}")
    
    # Compare them
    similarity = cosine_similarity(fresh_embedding, stored_embedding)
    print(f"🎯 Fresh vs Stored similarity: {similarity:.4f}")
    
    if similarity < 0.9:
        print("❌ EMBEDDINGS DON'T MATCH! Your stored embeddings are wrong.")
        print("🔧 You need to re-generate and re-upload your embeddings.")
    else:
        print("✅ Embeddings match - problem is elsewhere.")

async def main():
    print("🔍 RAG System Testing & Search Interface")
    print("="*50)
    while True:
        print("\nChoose an option:")
        print("1. View all stored data")
        print("2. Perform semantic search")
        print("3. Interactive search mode")
        print("4. Debug embeddings")
        print("5. Debug specific search")
        print("6. Test embedding quality")
        print("7. Test raw similarities")
        print("8. Test official implementation")
        print("9. Test stored vs fresh embeddings")  # Add this line
        print("10. Exit")  # Change Exit to 10
        choice = input("\nEnter your choice (1-10): ").strip()
        if choice == '1':
            await view_all_data()
        elif choice == '2':
            question = input("Enter your search question: ").strip()
            if question:
                await semantic_search(question, top_k=3)
            else:
                print("⚠️ Please enter a valid question.")
        elif choice == '3':
            await interactive_search()
        elif choice == '4':
            await debug_embeddings()
        elif choice == '5':
            question = input("Enter question to debug: ").strip()
            if question:
                await debug_specific_search(question)
        elif choice == '6':
            await test_embedding_quality()
        elif choice == '7':
            await test_raw_similarities()
        elif choice == '8':
            test_official_implementation()
        elif choice == '9':  # Add this new option
            await test_stored_vs_fresh_embeddings()
        elif choice == '10':  # Update exit choice
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-10.")

if __name__ == "__main__":
    asyncio.run(main())

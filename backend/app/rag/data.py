import asyncio
import openai
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from b2b_saas_table import create_record, get_all_records, search_similar, supabase

load_dotenv(".env")

# OpenAI setup (if using OpenAI embeddings)
openai.api_key = os.getenv("OPENAI_API_KEY")

class DataProcessor:
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"  # or your preferred model
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text"""
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return [0.0] * 1536  # Return zero vector as fallback
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            
            if end >= len(text):
                break
                
        return chunks
    
    async def process_and_store_document(
        self, 
        url: str, 
        content: str, 
        title: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Process a document: chunk, embed, and store in database"""
        
        # Chunk the content
        chunks = self.chunk_text(content)
        
        stored_records = []
        
        for chunk_order, chunk in enumerate(chunks):
            try:
                # Create embedding
                embedding = self.create_embedding(chunk)
                
                # Prepare data for database
                record_data = {
                    "url": url,
                    "title": title,
                    "chunk_order": chunk_order,
                    "embedding": embedding,
                    "metadata": {
                        "chunk_text": chunk,  # Store chunk text in metadata
                        "chunk_length": len(chunk),
                        **(metadata or {})
                    }
                }
                
                # Store in database using SQLAlchemy
                new_record = await create_record(record_data)
                stored_records.append(new_record)
                
                print(f"Stored chunk {chunk_order} for {url}")
                
            except Exception as e:
                print(f"Error processing chunk {chunk_order}: {e}")
                continue
        
        return stored_records
    
    async def bulk_insert_with_supabase_client(self, records: List[Dict]):
        """Alternative: Bulk insert using Supabase client for better performance"""
        try:
            response = supabase.table("b2b_saas_context").insert(records).execute()
            print(f"Bulk inserted {len(records)} records")
            return response.data
        except Exception as e:
            print(f"Error in bulk insert: {e}")
            return None
    
    def search_context(self, query: str, limit: int = 5):
        """Search for relevant context based on query"""
        # Create embedding for the query
        query_embedding = self.create_embedding(query)
        
        # Search for similar vectors
        results = search_similar(query_embedding, limit)
        
        return results
    
    async def get_all_stored_data(self):
        """Retrieve all stored data"""
        return await get_all_records()

# Example usage functions
async def process_example_documents():
    """Example of how to process and store documents"""
    processor = DataProcessor()
    
    # Example documents
    documents = [
        {
            "url": "https://example.com/doc1",
            "title": "B2B SaaS Marketing Guide",
            "content": "This is a comprehensive guide to B2B SaaS marketing strategies. It covers lead generation, customer acquisition, and retention tactics...",
            "metadata": {"source": "marketing_guide", "category": "marketing"}
        },
        {
            "url": "https://example.com/doc2", 
            "title": "Customer Success Best Practices",
            "content": "Customer success is crucial for B2B SaaS companies. This document outlines best practices for onboarding, support, and retention...",
            "metadata": {"source": "cs_guide", "category": "customer_success"}
        }
    ]
    
    # Process each document
    for doc in documents:
        await processor.process_and_store_document(
            url=doc["url"],
            content=doc["content"],
            title=doc["title"],
            metadata=doc["metadata"]
        )

async def search_example():
    """Example of how to search stored data"""
    processor = DataProcessor()
    
    query = "How to improve customer retention in SaaS?"
    results = processor.search_context(query, limit=3)
    
    print(f"Search results for: '{query}'")
    for result in results:
        print(f"- URL: {result.get('url')}")
        print(f"- Similarity: {result.get('similarity')}")
        print(f"- Content: {result.get('metadata', {}).get('chunk_text', '')[:100]}...")
        print()

# Main execution
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Example: Process documents
    asyncio.run(process_example_documents())
    
    # Example: Search
    # search_example()  # Uncomment to test search
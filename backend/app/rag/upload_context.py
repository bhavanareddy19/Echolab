import asyncio
import json
from datetime import datetime
from b2b_saas_table import create_record, get_all_records
from extract_pages import main as extract_pages_main
from extract_pages import main_from_url as extract_pages_from_url_main


async def create_sample_data():
    """Create sample records with test data for each column type"""
    link = "https://productled.com/book/product-led-growth#Content"
    
    # Fix 1: Use await instead of asyncio.run() since we're already in an async function
    embeddings_info = await extract_pages_from_url_main(link)

    created_records = []  # Track all created records

    for i, embedding_data in enumerate(embeddings_info):  # Changed variable name for clarity
        # Sample metadata (JSONB) - should be unique per chunk
        sample_metadata = {
            "source": link,
            "category": "B2B SaaS Industry", 
            "author": "",
            "tags": ["Low Activation", "AHA Moment"],
            "chunk_text": embedding_data.get('chunk_text'),  # Use embedding_data instead of embeddings_info[i]
            "confidence_score": embedding_data.get('confidence'),  # Use embedding_data instead of embeddings_info[i]
            "processed_date": datetime.now().isoformat(),
            "chunk_index": i  # Fix 2: Removed trailing comma
        }
        
        # Test record
        test_record = {
            "url": link,
            "title": "Product-Led Institute case studies (open PDFs)",
            "chunk_order": i,
            "embedding": embedding_data.get('embedding'),  # Use embedding_data instead of embeddings_info[i]
            "chunk_metadata": sample_metadata
        }
        
        try:
            new_record = await create_record(test_record)
            # Fix 3: Use embeddings_info (the list) for length, not embeddings (undefined variable)
            print(f"✅ Created record: ID={new_record.id}, Chunk={i+1}/{len(embeddings_info)}")
            created_records.append(new_record)
        except Exception as e:
            print(f"❌ Error creating record {i+1}: {e}")
    
    print(f"\n🎉 Created {len(created_records)} records total!")
    return created_records

async def view_all_data():
    """Fetch and display all records in the table"""
    print("\n" + "="*50)
    print("ALL RECORDS IN TABLE:")
    print("="*50)
    
    try:
        records = await get_all_records()
        
        if not records:
            print("No records found in the table.")
            return
        
        for record in records:
            print(f"\nID: {record.id}")
            print(f"URL: {record.url}")
            print(f"Title: {record.title}")
            print(f"Chunk Order: {record.chunk_order}")
            print(f"Created At: {record.created_at}")
            print(f"Embedding: {record.embedding[:5]}... (showing first 5 values)")
            print(f"Chunk Metadata: {json.dumps(record.chunk_metadata, indent=2) if record.chunk_metadata else 'None'}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error fetching records: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting database test...")
    
    # Create sample data
    await create_sample_data()
    
    # View all data
    #await view_all_data()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
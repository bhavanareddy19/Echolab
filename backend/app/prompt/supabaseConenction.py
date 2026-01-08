from dotenv import load_dotenv
import os
from supabase import create_client

# Load environment variables
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

# Fetech Data from Tickets Table

def fetch_ticket_data(limit=20):
    try:
        response = (
            supabase
            .table("tickets")
            .select("id, subject, description")  # id will be included automatically
            .is_("feature", None) # Fetch rows where feature is NULL
            .order("id", desc=False)  # oldest first
            .limit(limit)
            .execute()
        )
        return response.data  # List of ticket dictionaries
    except Exception as e:
        print("Error fetching data:", e)
        return []

def update_ticket_data(ticket_id: str, classification: dict):
    # Update a single ticket with classification results
    try:
        supabase.table("tickets").update({
            "feature": classification.get("Classification"),
            "cluster": classification.get("Cluster"),
            "customer_problem": classification.get("Customer Problem"),
            "root_cause": classification.get("Root Cause")
        }).eq("id", ticket_id).execute()
        print(f"✅ Updated ticket {ticket_id}")
    except Exception as e:
        print(f"❌ Failed to update ticket {ticket_id}: {repr(e)}")

def upsert_ticket_batch(batch):
    """Upsert a batch of tickets into Supabase safely"""
    if not batch:
        return
    try:
        supabase.table("tickets").upsert(batch, on_conflict="id").execute()
        print(f"✅ Upserted batch of {len(batch)} tickets")
    except Exception as e:
        print(f"❌ Batch upsert failed: {repr(e)}")
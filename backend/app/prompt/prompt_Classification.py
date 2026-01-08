from dotenv import load_dotenv
import os
import json
import time
from openai import OpenAI
from ..prompt.supabaseConenction import fetch_ticket_data, upsert_ticket_batch

# Load environment variables from the .env file
load_dotenv()

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
MODEL_NAME=os.getenv("MODEL_NAME", "gpt-4o")

client = OpenAI(
#     api_version=API_VERSION,
#     azure_endpoint=ENDPOINT,
    api_key=OPENAI_API_KEY
)


def classify_tickets(ticket_subject: str, ticket_description: str):
    start_time = time.time()
    
    role = """
    You are an AI Product Analyst. 
    Your task is to transform raw customer support tickets into actionable 
    Cluster & Classification insights.
    """
    
    prompt = f"""
    TASK: Cluster & Classification  

    Instructions:
    - **Classification**: Label as either "Bug" or "Feature Improvement". 
    - **Customer Problem**: 
        - Express the issue/request directly, without mentioning the requester.  
        - Strip out meta-phrases such as:  
            "The customer is", "Request for", "Requesting", "Seeking", "Interested in", "They need", "They require", etc.  
        - Start with the subject matter itself.
        - Write in a concise form optimized for vector similarity (no pleasantries, no generic intros).  
    - **Root Cause**: Only if Classification = "Bug" AND ≥99% confident, provide the most likely technical or logical cause. Otherwise, leave blank.  

    INPUT:  
    Subject: {ticket_subject}  
    Description: {ticket_description}  

    OUTPUT (strict JSON format):  
    {{
    "Classification": "Bug | Feature Improvement",
    "Customer Problem": "string",
    "Root Cause": "string or blank"
    }}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages= [
            {"role": "system", "content": role, },
            {"role": "user","content": prompt,}
        ],
        max_tokens=4096,
        temperature=0
    )
    elapsed_time = time.time() - start_time
    print(f"Extraction Time: {elapsed_time:.2f} seconds")

    output_text = response.choices[0].message.content
    try:
        # Extract JSON block from the output
        json_start = output_text.find("{")
        json_end = output_text.rfind("}") + 1
        json_str = output_text[json_start:json_end]
        output_json = json.loads(json_str)

        return output_json
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Raw output:", output_text)
        return None

def test_tickets():
    tickets = fetch_ticket_data(limit=20)

    expected_classification = {
        "0002aaa9-def9-54bd-90ec-efd9d7dd747b": "Feature Improvement",
        "0003d477-b61d-59e6-9a92-ccb4f82a4ee4": "Bug",
        "00077e7c-1e0f-5dfa-9ffd-cdfa96ba2dbd": "Bug",
        "0008c106-92c4-5258-bf66-6496290d4598": "Bug",
        "000f1a93-ddf7-54c0-b1d2-7165fb4b92d9": "Bug",
        "0011110d-b6af-55f9-b1ff-741601295df0": "Bug",
        "0013878c-7ac1-5959-8ca6-0d65ac627d68": "Bug", 
        "0022becc-1421-57b6-b805-434536a89a06": "Bug",
        "00238c07-dd23-5bc9-b8ac-b4555c132610": "Feature Improvement",
        "002daf38-6e85-5027-8ed2-350d1a06d624": "Bug",
        "00301fa5-b730-59ee-8780-37e7b10568ed": "Bug",
        "0035ae2f-795b-5cc6-b25a-2beb89954e22": "Feature Improvement",
        "00390ecb-f689-5903-9fea-b3e011d4e74a": "Bug",
        "003c6248-545d-55a2-ac68-a895647f3b4a": "Bug",
        "003cb4af-1af8-571c-a5e1-ccc9790533c3": "Bug",
        "003e91a0-6be5-557c-acfb-c16c1cb6120a": "Feature Improvement",
        "00467a77-749d-5069-92e0-82402109b954": "Bug",
        "00492e6d-0547-5188-93be-128869bc5c2f": "Bug",
        "00499576-74b6-578c-a0a6-e009679bcaeb": "Feature Improvement",
        "004a5b0d-3bfb-5e1d-8364-d68fe996921d": "Bug"
    }

    for idx, ticket in enumerate(tickets, start=1):
        ticket_id = ticket.get("id", None)
        subject = ticket.get("subject", "")
        description = ticket.get("description", "")
        
        # print(f"Subject: {subject}")
        predicted = classify_tickets(subject, description)
        print(f"{idx}, Classification: {predicted['Classification']}, Customer Problem: {predicted['Customer Problem']}, Root Cause: {predicted['Root Cause']} ")
        
        # if predicted["Classification"] == expected_classification[ticket_id]:
        #     print(f"Test Case {idx} Passed")
        # else:
        #     print(f"Test Case {idx} Failed.")
        # print(f"Ticket ID {idx}: {ticket_id}, Expected Classification: {expected_classification[ticket_id]}, Predicted Classification: {predicted['Classification']}")


def classify_and_store(limit=500, batch_size=50, sleep_between=2):
    """Classify tickets and store results back in Supabase in batches"""
    tickets = fetch_ticket_data(limit=limit)
    total = len(tickets)
    print(f"📥 Fetched {total} tickets")

    batch = []
    success, failed = 0, 0

    for idx, ticket in enumerate(tickets, start=1):
        ticket_id = ticket.get("id")
        subject = ticket.get("subject", "")
        description = ticket.get("description", "")

        print(f"[{idx}/{total}] Classifying ticket {ticket_id}...")

        classification = classify_tickets(subject, description)

        if classification:
            batch.append({
                "id": ticket_id,
                "feature": classification.get("Classification"),
                "Customer Problem": classification.get("Customer Problem"),
                "Root Cause": classification.get("Root Cause"),
                "clustered": False  # Set clustered column to False
            })
            success += 1
        else:
            print(f"⚠️ Skipped ticket {ticket_id} (classification error)")
            failed += 1

        # If batch is full, upsert it
        if len(batch) >= batch_size:
            upsert_ticket_batch(batch)
            print(f"🔍 Batch data: {batch}")
            batch = []
            time.sleep(sleep_between)

    # Upsert any remaining tickets
    if batch:
        upsert_ticket_batch(batch)

    print("\n📊 Summary:")
    print(f"   Processed : {total}")
    print(f"   Classified: {success}")
    print(f"   Failed    : {failed}")


# test_tickets(tickets, expected_classification)

if __name__ == "__main__":
    classify_and_store(limit=50, batch_size=50, sleep_between=2)
    # test_tickets()
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os
from datetime import datetime
from dotenv import load_dotenv
import uuid
import re
import json

# Load environment variables
load_dotenv()

# Database connection parameters with SSL enforcement
DB_CONFIG = {
    'user': os.getenv('user'),
    'password': os.getenv('password'),
    'host': os.getenv('host'),
    'port': os.getenv('port'),
    'dbname': os.getenv('dbname'),
    'sslmode': 'require',  # Enforce SSL connection
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 5
}

def clean_text(text):
    """Remove control characters that cause database/Excel issues"""
    if text is None:
        return None
    if isinstance(text, str):
        # Remove control characters except newline/tab
        return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    return str(text)  # Convert non-strings to string

def connect_to_db():
    """Establish secure connection to the database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_hugging_face_organization(conn):
    """Create or get Hugging Face organization with ID 1"""
    try:
        cursor = conn.cursor()
        
        # Check if organization with ID 1 exists
        cursor.execute("SELECT id, company FROM organizations WHERE id = 1")
        existing_org = cursor.fetchone()
        
        if existing_org:
            print(f"Organization already exists: ID={existing_org[0]}, Company={existing_org[1]}")
            # Update to Hugging Face if different
            if existing_org[1] != 'Hugging Face':
                cursor.execute("""
                    UPDATE organizations 
                    SET company = 'Hugging Face', 
                        updated_at = %s
                    WHERE id = 1
                """, (datetime.now(),))
                conn.commit()
                print("Updated organization to Hugging Face")
            return 1
        else:
            # Create new organization with ID 1
            cursor.execute("""
                INSERT INTO organizations (
                    id, company, domain_names, name_of_representative, 
                    role, email, created_at, updated_at
                ) VALUES (
                    1, 'Hugging Face', %s, NULL, NULL, 'support@huggingface.co', %s, %s
                )
                RETURNING id;
            """, (
                json.dumps(['huggingface.co']),  # domain_names as JSON
                datetime.now(),
                datetime.now()
            ))
            
            org_id = cursor.fetchone()[0]
            conn.commit()
            print(f"Created Hugging Face organization with ID: {org_id}")
            return org_id
            
    except Exception as e:
        print(f"Error creating organization: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()

def create_default_user(conn, organization_id):
    """Create a default user for Hugging Face organization"""
    try:
        cursor = conn.cursor()
        
        # Check if default user exists
        cursor.execute("""
            SELECT id FROM users 
            WHERE email = 'support@huggingface.co'
        """)
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"Default user already exists: {existing_user[0]}")
            return existing_user[0]
        else:
            # Create new default user
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (
                    id, name, email, phone, role, active, verified, 
                    organization_id, created_at, updated_at
                ) VALUES (
                    %s, 'Hugging Face Support', 'support@huggingface.co', 
                    NULL, 'support', true, true, %s, %s, %s
                )
                RETURNING id;
            """, (
                user_id,
                organization_id,
                datetime.now(),
                datetime.now()
            ))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            print(f"Created default user with ID: {user_id}")
            return user_id
            
    except Exception as e:
        print(f"Error creating default user: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()

def process_tags(row):
    """Process tag columns from CSV and combine them"""
    tags = []
    for i in range(1, 9):  # tag_1 through tag_8
        tag_col = f'tag_{i}'
        if tag_col in row:
            tag_value = row[tag_col]
            # Check if not NaN and has actual content
            if pd.notna(tag_value) and tag_value != '':
                # Convert to string and clean
                tag_str = clean_text(str(tag_value))
                if tag_str:  # Only add non-empty strings
                    tags.append(tag_str)
    
    return ','.join(tags) if tags else None

def process_b2b_csv(csv_file, organization_id, default_user_id):
    """Read and process b2b.csv data"""
    try:
        # Read CSV
        df = pd.read_csv(csv_file, low_memory=False)
        print(f"Loaded {len(df)} rows from {csv_file}")
        
        tickets_data = []
        
        for idx, row in df.iterrows():
            # Generate unique UUID for each ticket
            ticket_id = str(uuid.uuid4())
            
            # Process subject field - handle NaN and non-string types
            subject = row.get('subject')
            if pd.isna(subject):
                subject = None
            else:
                subject = str(subject)  # Convert to string first
                subject = clean_text(subject)
                # Truncate if too long
                if subject and len(subject) > 255:
                    subject = subject[:255]
            
            # Process body field - handle NaN and non-string types
            body = row.get('body')
            if pd.isna(body):
                body = None
            else:
                body = str(body)  # Convert to string first
                body = clean_text(body)
                # Truncate if too long
                if body and len(body) > 10000:
                    body = body[:10000]
            
            # Process answer field - handle NaN and non-string types
            answer = row.get('answer')
            if pd.isna(answer):
                answer = None
            else:
                answer = str(answer)  # Convert to string first
                answer = clean_text(answer)
            
            # Process tags
            tags = process_tags(row)
            
            # Map priority (ensure it's a valid value or NULL)
            priority = row.get('priority')
            if pd.notna(priority):
                priority = str(priority).lower()
                # Validate priority values (typical: low, normal, high, urgent)
                if priority not in ['low', 'normal', 'high', 'urgent']:
                    priority = 'normal'  # Default to normal
            else:
                priority = 'normal'
            
            # Map type
            ticket_type = row.get('type')
            if pd.isna(ticket_type):
                ticket_type = None
            else:
                ticket_type = str(ticket_type)
                ticket_type = clean_text(ticket_type)
            
            # Map status - default to 'open' since CSV doesn't have status
            status = 'open'
            
            # Handle cluster as a custom field (store in description or as tag)
            cluster = row.get('cluster')
            if pd.notna(cluster):
                cluster_info = f"\n\n[Cluster: {cluster}]"
                if body:
                    body = body + cluster_info
                else:
                    body = cluster_info
            
            tickets_data.append({
                'id': ticket_id,
                'url': None,  # No URL in b2b.csv
                'source': 'Hugging Face',  # Fixed source
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'type': ticket_type,
                'subject': subject,
                'description': body,
                'priority': priority,
                'status': status,
                'submitter_id': default_user_id,
                'tags': tags,
                'rating': None,
                'attachments': None,
                'organization_id': organization_id,
                'feature': None,
                'body_embedding': None,
                'cluster': str(cluster) if pd.notna(cluster) else None,
                'Customer Problem': None,  # Using quoted column name
                'Root Cause': None,  # Using quoted column name
                'body': answer,  # Store answer in body field
                'embedding': None
            })
        
        return tickets_data
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        import traceback
        traceback.print_exc()
        return None

def insert_tickets_batch(conn, tickets_data):
    """Insert tickets in batches"""
    try:
        cursor = conn.cursor()
        
        # First, check which columns actually exist in the tickets table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tickets' 
            AND table_schema = 'public';
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing columns in tickets table: {existing_columns}")
        
        # Build insert query based on existing columns
        columns_to_insert = []
        placeholders = []
        
        # Define column mapping
        column_mapping = {
            'id': 'id',
            'url': 'url',
            'source': 'source',
            'created_at': 'created_at',
            'updated_at': 'updated_at',
            'type': 'type',
            'subject': 'subject',
            'description': 'description',
            'priority': 'priority',
            'status': 'status',
            'submitter_id': 'submitter_id',
            'tags': 'tags',
            'rating': 'rating',
            'attachments': 'attachments',
            'organization_id': 'organization_id',
            'feature': 'feature',
            'cluster': 'cluster',
            'body': 'body'
        }
        
        # Only include columns that exist in the table
        for key, db_column in column_mapping.items():
            if db_column in existing_columns:
                columns_to_insert.append(db_column)
                placeholders.append(f'%({key})s')
        
        # Handle special columns with spaces (if they exist)
        if 'Customer Problem' in existing_columns:
            columns_to_insert.append('"Customer Problem"')
            placeholders.append('%(Customer Problem)s')
        
        if 'Root Cause' in existing_columns:
            columns_to_insert.append('"Root Cause"')
            placeholders.append('%(Root Cause)s')
        
        # Build the insert query
        insert_query = f"""
            INSERT INTO tickets ({', '.join(columns_to_insert)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT (id) DO UPDATE SET
                {', '.join([f'{col} = EXCLUDED.{col}' for col in columns_to_insert if col != 'id'])}
        """
        
        print(f"Insert query prepared for {len(columns_to_insert)} columns")
        
        # Filter ticket data to only include existing columns
        filtered_tickets = []
        for ticket in tickets_data:
            filtered_ticket = {}
            for key in ticket:
                db_column = column_mapping.get(key, key)
                if db_column in existing_columns or db_column in ['"Customer Problem"', '"Root Cause"']:
                    filtered_ticket[key] = ticket[key]
            filtered_tickets.append(filtered_ticket)
        
        total = len(filtered_tickets)
        print(f"Inserting {total} tickets...")
        
        # Insert in batches of 100
        batch_size = 100
        for i in range(0, total, batch_size):
            batch = filtered_tickets[i:i+batch_size]
            try:
                execute_batch(cursor, insert_query, batch, page_size=batch_size)
                conn.commit()
                print(f"Inserted {min(i+batch_size, total)} of {total} tickets")
            except Exception as batch_error:
                print(f"Error inserting batch {i//batch_size + 1}: {batch_error}")
                conn.rollback()
                
                # Try inserting individually for this batch
                for j, ticket in enumerate(batch):
                    try:
                        cursor.execute(insert_query, ticket)
                        conn.commit()
                    except Exception as row_error:
                        print(f"Failed to insert ticket {i+j+1}: {row_error}")
                        conn.rollback()
        
        print("Ticket insertion completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error inserting tickets: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()

def main():
    """Main function to process b2b.csv and insert into Supabase"""
    csv_file = 'supabase_ingestion/b2b.csv'
    
    print(f"Starting import process for {csv_file}")
    print("=" * 50)
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        print("Failed to connect to database. Exiting.")
        return
    
    try:
        # Step 1: Create Hugging Face organization
        print("\nStep 1: Creating Hugging Face organization...")
        org_id = create_hugging_face_organization(conn)
        if not org_id:
            print("Failed to create organization. Exiting.")
            return
        
        # Step 2: Create default user
        print("\nStep 2: Creating default user...")
        user_id = create_default_user(conn, org_id)
        if not user_id:
            print("Failed to create default user. Exiting.")
            return
        
        # Step 3: Process CSV file
        print(f"\nStep 3: Processing {csv_file}...")
        tickets_data = process_b2b_csv(csv_file, org_id, user_id)
        
        if tickets_data:
            # Print summary of data to be inserted
            print(f"\nData Summary:")
            print(f"- Total tickets to insert: {len(tickets_data)}")
            
            # Count non-null subjects
            subjects_count = sum(1 for t in tickets_data if t['subject'] is not None)
            print(f"- Tickets with subjects: {subjects_count}")
            
            # Count non-null descriptions
            descriptions_count = sum(1 for t in tickets_data if t['description'] is not None)
            print(f"- Tickets with descriptions: {descriptions_count}")
            
            # Count tickets with tags
            tags_count = sum(1 for t in tickets_data if t['tags'] is not None)
            print(f"- Tickets with tags: {tags_count}")
            
            # Step 4: Insert tickets
            print(f"\nStep 4: Inserting {len(tickets_data)} tickets...")
            insert_tickets_batch(conn, tickets_data)
            
            # Verify insertion
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE source = 'Hugging Face'")
            count = cursor.fetchone()[0]
            cursor.close()
            
            print(f"\n✅ Import completed! Total Hugging Face tickets in database: {count}")
        else:
            print("No data to insert")
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
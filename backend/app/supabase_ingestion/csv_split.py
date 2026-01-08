import pandas as pd
import math

# Configuration
input_csv = 'github_issues_tickets.csv'
output_prefix = 'github_issues_tickets_part_'
num_files = 4

def split_csv_to_csv(input_file, output_prefix, num_files):
    # Define dtype specification
    dtype_spec = {
        'user_id': 'Int64',
        'id': 'Int64',
        'created_at': 'str',
        'updated_at': 'str'
    }
    
    # Read CSV
    print(f"Reading CSV file: {input_file}")
    df = pd.read_csv(input_file, dtype=dtype_spec, low_memory=False)
    total_rows = len(df)
    print(f"Total rows: {total_rows}")
    
    # Calculate rows per file (rounded up)
    rows_per_file = math.ceil(total_rows / num_files)
    print(f"Splitting into {num_files} files with ~{rows_per_file} rows each")
    
    # Split and save each portion
    for i in range(num_files):
        start_idx = i * rows_per_file
        end_idx = min((i + 1) * rows_per_file, total_rows)
        
        # Create subset
        subset = df.iloc[start_idx:end_idx]
        
        # Output filename
        output_file = f"{output_prefix}{i+1}.csv"
        
        print(f"Creating {output_file} with rows {start_idx+1} to {end_idx}")
        subset.to_csv(output_file, index=False)
    
    print("\nProcess completed successfully!")
    print(f"Created {num_files} CSV files with prefix '{output_prefix}'")

if __name__ == "__main__":
    split_csv_to_csv(input_csv, output_prefix, num_files)
import httpx
import pandas as pd
import argparse
import sys

def fetch_ho_clues(limit=10, source=None, reviewed_only=False, output_file="ho_clues_sample.csv"):
    """
    Fetches professional clues from the George Ho Datasette API and saves to CSV.
    """
    # VERIFIED: Database name is 'data', Table is 'clues'
    BASE_URL = "https://cryptics.georgeho.org/data/clues.json"
    
    # Use _shape=array to get a clean list of dictionaries
    params = {
        "_shape": "array",
        "_size": limit,
    }
    # Only add the parameter if explicitly requested
    if reviewed_only:
        params["is_reviewed"] = 1

    if source:
        params["source"] = source

    print(f"Connecting to: {BASE_URL}")
    
    try:
        # verify=False handles local SSL certificate issues
        with httpx.Client(verify=False, follow_redirects=True) as client:
            response = client.get(BASE_URL, params=params, timeout=20.0)
            response.raise_for_status()
            
            # Since _shape=array is used, data is a list of dicts
            data = response.json()
            
            if not data:
                print("No clues found matching your filters.")
                return

            # Directly load the list of dictionaries into a DataFrame
            df = pd.DataFrame(data)
            
            # Select and order only the relevant columns for the pipeline
            cols_to_keep = ['clue', 'answer', 'definition', 'source', 'source_url', 'puzzle_date']
            df = df[[c for c in cols_to_keep if c in df.columns]]
            
            # Save the DataFrame to CSV
            df.to_csv(output_file, index=False)
            print(f"Successfully saved {len(df)} professional clues to {output_file}")
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch professional clues")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--source", type=str, help="e.g., times_xwd_times")
    # CHANGE 3: Update CLI to allow toggling reviewed status
    parser.add_argument("--reviewed", action="store_true", help="Only fetch human-reviewed clues")
    
    args = parser.parse_args()
    fetch_ho_clues(limit=args.limit, source=args.source, reviewed_only=args.reviewed)
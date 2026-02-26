"""
fetch_ho_clues.py - George Ho Dataset Fetcher

This script fetches professional cryptic crossword clues from George Ho's Datasette API
(https://cryptics.georgeho.org/) and saves them to a file for processing by ho_processor.py.

Supports fetching up to ~500,000 rows with pagination and exports to CSV, Parquet, or DuckDB formats.

USAGE:
    # Fetch 10 clues to CSV (default)
    python fetch_ho_clues.py

    # Fetch 50 clues
    python fetch_ho_clues.py --limit 50

    # Fetch ALL clues (~500k rows) to Parquet
    python fetch_ho_clues.py --format parquet

    # Filter by source (e.g., Times crossword)
    python fetch_ho_clues.py --limit 1000 --source times_xwd_times

    # Filter by multiple sources (comma-separated)
    python fetch_ho_clues.py --source times_xwd_times,fifteensquared

    # Filter by specific date
    python fetch_ho_clues.py --date 2017-08-25

    # Combine filters to DuckDB database
    python fetch_ho_clues.py --source guardian --date 2020-01-15 --format duckdb

    # Fetch large batch with custom output name
    python fetch_ho_clues.py --limit 50000 --output ho_clues_large --format parquet

    # Fetch all clues with pagination (may take several minutes)
    python fetch_ho_clues.py --source times_xwd_times,fifteensquared --limit 0 --output ho_all --format duckdb

ARGUMENTS:
    --limit NUM         Maximum number of clues to fetch (default: 10, omit or use 0 for all rows)
    --source NAME       Filter by publication source (comma-separated allowed)
    --date YYYY-MM-DD   Filter by exact puzzle date (e.g., '2017-08-25')
    --format FORMAT     Output format: 'csv' (default), 'parquet', or 'duckdb'
    --output NAME       Output filename base (default: 'ho_clues_sample', extension auto-added)
    --batch-size NUM    Rows per API request for pagination (default: 1000)
    --no-resume         Disable DuckDB resume checkpointing

OUTPUT FORMATS:
    - csv:      Comma-separated values file (default, best for <100k rows)
    - parquet:  Compressed columnar format (efficient for large datasets)
    - duckdb:   DuckDB database file with 'clues' table (queryable SQL database)

OUTPUT COLUMNS:
    - clue: The cryptic clue text
    - answer: The answer word/phrase
    - definition: Extracted definition (if available)
    - source: Publication source
    - source_url: Link to original puzzle
    - puzzle_date: Date of publication

WORKFLOW:
    1. Run this script to fetch clues → ho_clues_sample.{csv,parquet,duckdb}
    2. Process with: python ho_processor.py ho_clues_sample.csv
    3. Get enriched output → ho_enriched_TIMESTAMP.json

EXAMPLES:
    # Quick test with 5 clues
    python fetch_ho_clues.py --limit 5

    # Fetch all Times clues to efficient Parquet format
    python fetch_ho_clues.py --source times_xwd_times --format parquet

    # Get all clues from a specific date
    python fetch_ho_clues.py --date 2019-12-25 --output xmas_2019

    # Full database dump to DuckDB (may take several minutes)
    python fetch_ho_clues.py --source times_xwd_times,fifteensquared --limit 0 --output ho_all --format duckdb --timeout 120 --retries 5

NOTES:
    - The API may have SSL certificate warnings (handled automatically)
    - Not all clues have a 'definition' field populated
    - Large fetches (>100k rows) automatically use pagination with progress indicator
    - Available sources: times_xwd_times, guardian, telegraph, ft, independent, etc.
    - For analyzing large exports, DuckDB format allows SQL queries without loading into memory
"""

import httpx
import pandas as pd
import argparse
import sys
import time
import json
import os
from typing import Optional

def normalize_for_duckdb(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize string-like columns to object dtype for DuckDB compatibility."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
            df[col] = df[col].astype(object)
    return df

def fetch_ho_clues(
    limit: Optional[int] = 10,
    source: Optional[str] = None,
    date: Optional[str] = None,
    output_file: str = "ho_clues_sample",
    format: str = "csv",
    batch_size: int = 1000,
    timeout_seconds: float = 60.0,
    max_retries: int = 3,
    resume: bool = True
):
    """
    Fetches professional clues from the George Ho Datasette API with pagination support.
    
    Args:
        limit: Maximum number of clues to fetch (None or 0 = fetch all available)
        source: Filter by publication source (comma-separated list supported)
        date: Filter by exact puzzle_date (format: 'YYYY-MM-DD')
        output_file: Output filename base (extension added based on format)
        format: Output format - 'csv', 'parquet', or 'duckdb'
        batch_size: Number of rows to fetch per API request (default: 1000)
        resume: Resume DuckDB exports using a checkpoint file (default: True)
    """
    # VERIFIED: Database name is 'data', Table is 'clues'
    BASE_URL = "https://cryptics.georgeho.org/data/clues.json"
    
    # Determine if we're fetching all rows
    fetch_all = (limit is None or limit == 0)
    
    # Build initial parameters
    params = {
        "_shape": "objects",
        "_size": batch_size,  # Fetch in chunks for pagination
    }
    
    # Note: We'll filter results client-side after fetching, as Datasette JSON API
    # may not support WHERE clauses reliably across all deployments

    print(f"Connecting to: {BASE_URL}")
    if fetch_all:
        print("Fetching ALL available rows (this may take several minutes)...")
    else:
        print(f"Fetching up to {limit:,} rows...")
    
    use_duckdb = (format == "duckdb")
    all_data = []
    total_fetched = 0
    total_written = 0
    next_url = None
    duckdb_con = None
    checkpoint_path = f"{output_file}.checkpoint.json"
    resume_enabled = (use_duckdb and resume)
    resume_mode = False
    duckdb_table_exists = False

    if use_duckdb:
        try:
            import duckdb
        except ImportError:
            print("ERROR: duckdb not installed. Install with: pip install duckdb")
            sys.exit(1)
        output_path = f"{output_file}.duckdb"
        duckdb_con = duckdb.connect(output_path)
        duckdb_table_exists = (
            duckdb_con.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'main' AND table_name = 'clues'"
            ).fetchone()[0]
            > 0
        )

        if resume_enabled and os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    checkpoint = json.load(f)
                expected = {
                    "source": source,
                    "date": date,
                    "batch_size": batch_size,
                    "output_file": output_file,
                }
                if checkpoint.get("settings") == expected and checkpoint.get("next_url"):
                    next_url = checkpoint.get("next_url")
                    resume_mode = True
                    print(f"Resuming from checkpoint: {next_url}")
                else:
                    print("Checkpoint settings do not match current run. Starting fresh.")
            except (OSError, json.JSONDecodeError):
                print("Checkpoint file is invalid. Starting fresh.")

        if not resume_mode:
            duckdb_con.execute("DROP TABLE IF EXISTS clues")
            duckdb_table_exists = False
            if resume_enabled and os.path.exists(checkpoint_path):
                try:
                    os.remove(checkpoint_path)
                except OSError:
                    pass
    
    try:
        with httpx.Client(verify=False, follow_redirects=True, timeout=timeout_seconds) as client:
            while True:
                # Use next_url if available (pagination), otherwise use BASE_URL with params
                request_url = next_url or BASE_URL
                request_params = None if next_url else params

                for attempt in range(1, max_retries + 1):
                    try:
                        response = client.get(request_url, params=request_params)
                        response.raise_for_status()
                        break
                    except httpx.ReadTimeout:
                        if attempt == max_retries:
                            raise
                        backoff_seconds = 2 ** (attempt - 1)
                        print(f"Read timeout. Retrying in {backoff_seconds}s (attempt {attempt}/{max_retries})...")
                        time.sleep(backoff_seconds)
                    except httpx.RequestError as exc:
                        if attempt == max_retries:
                            raise
                        backoff_seconds = 2 ** (attempt - 1)
                        print(
                            f"Network error ({exc.__class__.__name__}). Retrying in {backoff_seconds}s "
                            f"(attempt {attempt}/{max_retries})..."
                        )
                        time.sleep(backoff_seconds)
                    except httpx.HTTPStatusError as exc:
                        status_code = exc.response.status_code
                        if status_code >= 500 or status_code == 429:
                            if attempt == max_retries:
                                raise
                            backoff_seconds = 2 ** (attempt - 1)
                            print(
                                f"Server error {status_code}. Retrying in {backoff_seconds}s "
                                f"(attempt {attempt}/{max_retries})..."
                            )
                            time.sleep(backoff_seconds)
                        else:
                            raise
                
                # Parse response based on shape
                json_data = response.json()
                
                # Handle both array and object shapes
                if isinstance(json_data, dict):
                    rows = json_data.get('rows', [])
                    # Check for next page URL (Datasette returns 'next')
                    next_url = json_data.get('next') or json_data.get('next_url')
                    if next_url and not next_url.startswith('http'):
                        # Make relative URLs absolute
                        next_url = f"https://cryptics.georgeho.org{next_url}"
                else:
                    # Direct array response (no pagination info)
                    rows = json_data
                    next_url = None
                
                if not rows:
                    break

                reached_limit = False
                if not fetch_all and (total_fetched + len(rows)) > limit:
                    allowed = max(0, limit - total_fetched)
                    rows = rows[:allowed]
                    reached_limit = True

                if not use_duckdb:
                    all_data.extend(rows)

                total_fetched += len(rows)

                # Progress indicator
                print(f"Fetched {total_fetched:,} rows...", end='\r')

                if use_duckdb:
                    # Convert to DataFrame for this batch
                    df = pd.DataFrame(rows)

                    # Apply client-side filters to the batch
                    if source:
                        source_list = [s.strip() for s in source.split(",") if s.strip()]
                        if source_list:
                            df = df[df['source'].isin(source_list)]

                    if date:
                        df = df[df['puzzle_date'] == date]

                    if len(df) > 0:
                        cols_to_keep = ['clue', 'answer', 'definition', 'source', 'source_url', 'puzzle_date']
                        if 'rowid' in df.columns:
                            cols_to_keep = ['rowid'] + cols_to_keep
                        df = df[[c for c in cols_to_keep if c in df.columns]]
                        df = normalize_for_duckdb(df)
                        duckdb_con.register("df", df)
                        if not duckdb_table_exists:
                            duckdb_con.execute("CREATE TABLE clues AS SELECT * FROM df")
                            duckdb_table_exists = True
                        else:
                            if 'rowid' in df.columns:
                                duckdb_con.execute(
                                    "INSERT INTO clues SELECT * FROM df WHERE rowid NOT IN (SELECT rowid FROM clues)"
                                )
                            else:
                                duckdb_con.execute("INSERT INTO clues SELECT * FROM df")
                        total_written += len(df)

                    if resume_enabled:
                        try:
                            with open(checkpoint_path, "w", encoding="utf-8") as f:
                                json.dump(
                                    {
                                        "next_url": next_url,
                                        "settings": {
                                            "source": source,
                                            "date": date,
                                            "batch_size": batch_size,
                                            "output_file": output_file,
                                        },
                                    },
                                    f,
                                )
                        except OSError:
                            pass

                # Check if we've reached the limit
                if reached_limit:
                    print(f"\nReached limit of {limit:,} rows.")
                    break

                # Check if there's more data to fetch
                if not next_url:
                    print(f"\nReached end of dataset at {total_fetched:,} rows.")
                    break

            if use_duckdb:
                if total_written == 0:
                    print("No clues match your filters after filtering.")
                    if not fetch_all:
                        print("Tip: Try removing --limit or setting --limit 0 to search the full dataset.")
                    return
                row_count = duckdb_con.execute("SELECT COUNT(*) FROM clues").fetchone()[0]
                if row_count == 0:
                    print("No clues match your filters after filtering.")
                    if not fetch_all:
                        print("Tip: Try removing --limit or setting --limit 0 to search the full dataset.")
                    return
                if resume_enabled and not next_url and os.path.exists(checkpoint_path):
                    try:
                        os.remove(checkpoint_path)
                    except OSError:
                        pass
                duckdb_con.close()
                print(f"Successfully saved {row_count:,} clues to {output_path} (DuckDB format)")
                print(f"Query with: duckdb {output_path} -c 'SELECT * FROM clues LIMIT 10'")
                return

            if not all_data:
                print("\nNo clues found matching your filters.")
                return

            print(f"\nTotal rows fetched: {len(all_data):,}")

            # Convert to DataFrame
            df = pd.DataFrame(all_data)

            # Apply client-side filters
            original_count = len(df)
            if source:
                source_list = [s.strip() for s in source.split(",") if s.strip()]
                if source_list:
                    df = df[df['source'].isin(source_list)]
                    print(f"Filtered by sources {source_list}: {len(df):,} rows")

            if date:
                df = df[df['puzzle_date'] == date]
                print(f"Filtered by date '{date}': {len(df):,} rows")

            if len(df) == 0:
                print("No clues match your filters after filtering.")
                if not fetch_all:
                    print("Tip: Try removing --limit or setting --limit 0 to search the full dataset.")
                return

            if original_count != len(df):
                print(f"Final filtered count: {len(df):,} rows")

            # Select and order only the relevant columns for the pipeline
            cols_to_keep = ['clue', 'answer', 'definition', 'source', 'source_url', 'puzzle_date']
            df = df[[c for c in cols_to_keep if c in df.columns]]
            
            # Save based on format
            if format == "csv":
                output_path = f"{output_file}.csv"
                df.to_csv(output_path, index=False)
                print(f"Successfully saved {len(df):,} clues to {output_path} (CSV format)")
                
            elif format == "parquet":
                try:
                    import pyarrow
                    output_path = f"{output_file}.parquet"
                    df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)
                    print(f"Successfully saved {len(df):,} clues to {output_path} (Parquet format)")
                except ImportError:
                    print("ERROR: pyarrow not installed. Install with: pip install pyarrow")
                    sys.exit(1)
                    
            elif format == "duckdb":
                print(f"ERROR: DuckDB export is handled during fetch. Use --format csv or --format parquet to export after fetch.")
                sys.exit(1)
            else:
                print(f"ERROR: Unknown format '{format}'. Use 'csv', 'parquet', or 'duckdb'.")
                sys.exit(1)
            
    except Exception as e:
        print(f"\nError fetching data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch professional cryptic crossword clues from George Ho's dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--limit", type=int, default=10, 
                       help="Max clues to fetch (default: 10, use 0 for all)")
    parser.add_argument("--source", type=str, 
                       help="Filter by source (comma-separated, e.g., times_xwd_times,guardian)")
    parser.add_argument("--date", type=str, 
                       help="Filter by exact date (format: YYYY-MM-DD, e.g., 2017-08-25)")
    parser.add_argument("--format", type=str, default="csv", choices=["csv", "parquet", "duckdb"],
                       help="Output format (default: csv)")
    parser.add_argument("--output", type=str, default="ho_clues_sample",
                       help="Output filename base (default: ho_clues_sample)")
    parser.add_argument("--batch-size", type=int, default=1000,
                       help="Rows per API request (default: 1000)")
    parser.add_argument("--timeout", type=float, default=60.0,
                       help="HTTP timeout in seconds (default: 60)")
    parser.add_argument("--retries", type=int, default=3,
                       help="Max retries on read timeout (default: 3)")
    parser.add_argument("--no-resume", action="store_true",
                       help="Disable DuckDB resume checkpointing")
    
    args = parser.parse_args()
    
    fetch_ho_clues(
        limit=args.limit if args.limit > 0 else None,
        source=args.source,
        date=args.date,
        output_file=args.output,
        format=args.format,
        batch_size=args.batch_size,
        timeout_seconds=args.timeout,
        max_retries=args.retries,
        resume=not args.no_resume
    )
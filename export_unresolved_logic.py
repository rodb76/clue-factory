import argparse
import os
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Export unresolved logic rows for investigation")
    parser.add_argument("-i", "--input", default="all_enriched.csv", help="Input enriched CSV")
    parser.add_argument("--outdir", default=".", help="Output directory")
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    if "logic" not in df.columns:
        raise ValueError("Input file does not contain a 'logic' column")

    logic_series = df["logic"]
    logic_as_str = logic_series.fillna("").astype(str)

    empty_mask = logic_series.isna() | logic_as_str.str.strip().eq("")
    not_found_mask = logic_as_str.eq("Logic not found")

    empty_df = df[empty_mask].copy()
    not_found_df = df[not_found_mask].copy()
    unresolved_df = df[empty_mask | not_found_mask].copy()

    os.makedirs(args.outdir, exist_ok=True)

    empty_path = os.path.join(args.outdir, "all_enriched_empty_logic.csv")
    not_found_path = os.path.join(args.outdir, "all_enriched_logic_not_found.csv")
    unresolved_path = os.path.join(args.outdir, "all_enriched_unresolved_logic.csv")

    empty_df.to_csv(empty_path, index=False)
    not_found_df.to_csv(not_found_path, index=False)
    unresolved_df.to_csv(unresolved_path, index=False)

    print("Export complete")
    print(f"Input rows: {len(df):,}")
    print(f"Empty logic rows: {len(empty_df):,}")
    print(f"Logic not found rows: {len(not_found_df):,}")
    print(f"Combined unresolved rows: {len(unresolved_df):,}")
    print(f"Wrote: {empty_path}")
    print(f"Wrote: {not_found_path}")
    print(f"Wrote: {unresolved_path}")


if __name__ == "__main__":
    main()

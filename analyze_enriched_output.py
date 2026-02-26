import argparse
import pandas as pd


def pct(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return (part / whole) * 100.0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze enriched clue CSV and report Logic-not-found stats"
    )
    parser.add_argument(
        "-i",
        "--input",
        default="all_enriched.csv",
        help="Path to enriched CSV file (default: all_enriched.csv)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    if "logic" not in df.columns:
        raise ValueError("Input file does not contain a 'logic' column")

    total_rows = len(df)
    logic_not_found_mask = df["logic"].fillna("").eq("Logic not found")
    logic_not_found_rows = int(logic_not_found_mask.sum())

    empty_logic_mask = df["logic"].isna() | df["logic"].astype(str).str.strip().eq("")
    empty_logic_rows = int(empty_logic_mask.sum())

    found_rows = total_rows - logic_not_found_rows - empty_logic_rows

    print("=== Enriched Output Summary ===")
    print(f"File: {args.input}")
    print(f"Total rows: {total_rows:,}")
    print(f"Rows with logic found: {found_rows:,} ({pct(found_rows, total_rows):.2f}%)")
    print(
        f"Rows with 'Logic not found': {logic_not_found_rows:,} "
        f"({pct(logic_not_found_rows, total_rows):.2f}%)"
    )
    print(f"Rows with empty/null logic: {empty_logic_rows:,} ({pct(empty_logic_rows, total_rows):.2f}%)")

    if "source" in df.columns:
        print("\n=== By Source ===")
        grouped = (
            df.assign(
                logic_not_found=logic_not_found_mask,
                empty_logic=empty_logic_mask,
            )
            .groupby("source", dropna=False)
            .agg(
                total=("logic", "size"),
                not_found=("logic_not_found", "sum"),
                empty=("empty_logic", "sum"),
            )
            .reset_index()
        )

        for _, row in grouped.iterrows():
            source = row["source"]
            total = int(row["total"])
            not_found = int(row["not_found"])
            empty = int(row["empty"])
            found = total - not_found - empty
            print(
                f"{source}: total={total:,}, found={found:,} ({pct(found, total):.2f}%), "
                f"not_found={not_found:,} ({pct(not_found, total):.2f}%), "
                f"empty={empty:,} ({pct(empty, total):.2f}%)"
            )


if __name__ == "__main__":
    main()

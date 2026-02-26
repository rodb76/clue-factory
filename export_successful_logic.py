import argparse
import os
import pandas as pd


def pct(part: int, whole: int) -> float:
    return 0.0 if whole == 0 else (part / whole) * 100.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Export rows where logic was successfully found")
    parser.add_argument("-i", "--input", default="all_enriched.csv", help="Input enriched CSV")
    parser.add_argument("--outdir", default=".", help="Output directory")
    parser.add_argument("--chunksize", type=int, default=100000, help="Chunk size for streaming export")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    successful_path = os.path.join(args.outdir, "all_enriched_successful_logic.csv")

    total_rows = 0
    success_rows = 0
    not_found_rows = 0
    empty_rows = 0
    source_counts = {}

    first_write = True

    reader = pd.read_csv(args.input, chunksize=args.chunksize)
    for idx, chunk in enumerate(reader, start=1):
        if "logic" not in chunk.columns:
            raise ValueError("Input file does not contain a 'logic' column")

        logic_series = chunk["logic"]
        logic_as_str = logic_series.fillna("").astype(str)

        empty_mask = logic_series.isna() | logic_as_str.str.strip().eq("")
        not_found_mask = logic_as_str.eq("Logic not found")
        successful_mask = ~(empty_mask | not_found_mask)

        successful_chunk = chunk[successful_mask]

        successful_chunk.to_csv(
            successful_path,
            mode="w" if first_write else "a",
            header=first_write,
            index=False,
        )
        first_write = False

        total_rows += len(chunk)
        success_rows += int(successful_mask.sum())
        not_found_rows += int(not_found_mask.sum())
        empty_rows += int(empty_mask.sum())

        if "source" in successful_chunk.columns and len(successful_chunk) > 0:
            counts = successful_chunk.groupby("source", dropna=False).size()
            for source, count in counts.items():
                source_counts[source] = source_counts.get(source, 0) + int(count)

        print(
            f"Processed chunk {idx}: total={total_rows:,}, successful={success_rows:,}, "
            f"not_found={not_found_rows:,}, empty={empty_rows:,}"
        )

    print("\nExport complete")
    print(f"Input rows: {total_rows:,}")
    print(f"Successful logic rows: {success_rows:,} ({pct(success_rows, total_rows):.2f}%)")
    print(f"Logic not found rows: {not_found_rows:,} ({pct(not_found_rows, total_rows):.2f}%)")
    print(f"Empty/null logic rows: {empty_rows:,} ({pct(empty_rows, total_rows):.2f}%)")
    print(f"Wrote: {successful_path}")

    if source_counts:
        print("\nSuccessful rows by source:")
        for source, count in sorted(source_counts.items(), key=lambda item: item[1], reverse=True):
            print(f"  {source}: {count:,}")


if __name__ == "__main__":
    main()

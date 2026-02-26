import pandas as pd

df = pd.read_csv('ho_enriched_updated.csv')
dynasty_rows = df[df['answer'] == 'DYNASTY']

for idx, row in dynasty_rows.iterrows():
    print(f"Row {idx}:")
    print(f"  Answer: {row['answer']}")
    print(f"  Logic: {repr(row['tftt_logic'])}")
    print()

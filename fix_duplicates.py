import pandas as pd

files = [
    "data/cleaned/credit_cleaned.csv",
    "data/engineered/credit_features.csv"
]

for path in files:
    df = pd.read_csv(path)
    before = len(df)
    dupes  = df.duplicated().sum()
    df     = df.drop_duplicates(keep='first').reset_index(drop=True)
    df.to_csv(path, index=False)
    print(f"{path}")
    print(f"  Before: {before:,}  Duplicates: {dupes:,}  After: {len(df):,}")
    print(f"  Remaining dupes: {df.duplicated().sum()}")
    print()

print("Done!")

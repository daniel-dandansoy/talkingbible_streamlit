import pandas as pd
import glob

# Listahan ng files
files = glob.glob("*.csv")

all_verses = []

print("Starting merge...")

for file in files:
    # Kunin ang pangalan ng version (hal. ASV.csv -> ASV)
    version_name = file.replace(".csv", "")
    
    print(f"Reading {file} as version: {version_name}")
    
    try:
        # Basahin ang CSV
        df = pd.read_csv(file)
        
        # I-add ang 'version' column
        # Siguraduhin na may column na 'version' ang dataframe
        df['version'] = version_name
        
        all_verses.append(df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

# I-combine lahat
if all_verses:
    final_df = pd.concat(all_verses, ignore_index=True)
    
    # I-save
    final_df.to_csv("bible_full.csv", index=False)
    print(f"\n✅ SUCCESS! Created 'bible_full.csv' with {len(final_df)} verses.")
else:
    print("\n❌ No CSV files found or error occurred.")
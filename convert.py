import pandas as pd
import glob
import os

# Hanapin lahat ng .xlsx files
excel_files = glob.glob("*.xlsx")

for file in excel_files:
    print(f"Converting {file}...")
    try:
        df = pd.read_excel(file)
        # I-save as CSV
        output_filename = file.replace(".xlsx", ".csv")
        df.to_csv(output_filename, index=False)
        print(f"✅ Saved: {output_filename}")
    except Exception as e:
        print(f"❌ Error sa {file}: {e}")

print("\nDone! Check na lang ang folder mo.")
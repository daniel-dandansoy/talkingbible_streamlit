import pandas as pd
import sqlite3
import os

# ============================================================
# PARTNER: ITO ANG 6 NA VERSIONS NA NAKALIST MO
# Siguraduhin na tugma ang pangalan ng .xlsx files dito!
# ============================================================
version_list = [
    {'file': 'ASV.xlsx',              'name': 'ASV'},
    {'file': 'AV.xlsx',               'name': 'AV'},
    {'file': 'JewishPubSociety.xlsx', 'name': 'Jewish Pub Society'},
    {'file': 'KJV.xlsx',              'name': 'KJV'},  # <<-- DEFAULT VERSION
    {'file': 'Webster.xlsx',          'name': 'Webster'},
    {'file': 'WordEnglishBible.xlsx', 'name': 'Word English Bible'}
]

def convert_to_sqlite():
    print("Starting conversion... Partner, hinintay ko lang.")
    
    # 1. Kumonekta sa SQLite Database
    # Lilikha ng 'bible.db' file
    conn = sqlite3.connect('bible.db')
    cursor = conn.cursor()

    # 2. Gumawa ng Modern Table Schema
    # Isang table lang para sa lahat ng version para mabilis ang search
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bible_verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            book_title TEXT,
            chapter INTEGER,
            verse INTEGER,
            text TEXT,
            version TEXT
        )
    ''')

    # 3. I-process ang bawat Excel file sa listahan
    for item in version_list:
        filename = item['file']
        version_name = item['name']
        
        if not os.path.exists(filename):
            print(f"WARNING: Hindi mahanap ang {filename}. Iskip muna.")
            continue

        print(f"Reading {filename} ({version_name})...")
        
        try:
            # Basahin ang Excel
            df = pd.read_excel(filename)
            
            # I-rename ang columns para standardized sa Database
            # Base sa mo: Book, BookTitle, Chapter, Verse, TextData
            df = df.rename(columns={
                'Book': 'book_id',
                'BookTitle': 'book_title',
                'Chapter': 'chapter',
                'Verse': 'verse',
                'TextData': 'text'
            })
            
            # Idagdag ang Version column (KJV, ASV, etc.)
            df['version'] = version_name
            
            # Save sa SQLite
            df.to_sql('bible_verses', conn, if_exists='append', index=False)
            print(f"Success: {len(df)} rows na-add for {version_name}.")
            
        except Exception as e:
            print(f"Error sa {filename}: {e}")

    # 4. Create Index para super fast ang Search
    print("Creating index...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_search ON bible_verses (book_title, chapter, verse, version)')
    
    conn.commit()
    conn.close()
    print("\nDONE! Nabuo na ang 'bible.db'. Kasama na lahat ng 6 versions.")

if __name__ == "__main__":
    convert_to_sqlite()
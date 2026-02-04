# ==========================================
# CONFIGURATION (Direct Connection)
# ==========================================
import streamlit as st
import pandas as pd
import re
import difflib
from supabase import create_client, Client

# Ito ang credentials na binigay mo kanina
# Siguraduhin na correct ito
url = "https://osolprafwnjroxtfooem.supabase.co"
key = "sb_publishable_nEZK1UTE237qgFhJE4KuZg_E5DOvZJ2"

# Initialize Supabase
supabase: Client = create_client(url, key)

st.set_page_config(
    page_title="Talking Bible (AI Search)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .verse-text { font-size: 18px; line-height:1.6; }
    .section-header {
        border-bottom: 2px solid #ddd;
        padding-bottom: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
        color: #2c3e50;
    }
    .book-divider {
        border-top: 4px solid #3498db;
        margin-top: 40px;
        margin-bottom: 20px;
    }
    /* Highlight sa corrections */
    .highlight {
        color: red;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# VB6 CHAPTERS MAP
# ==========================================
VB_MAX_CHAPTERS = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
    "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
    "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36,
    "Ezra": 10, "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150,
    "Proverbs": 31, "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66,
    "Jeremiah": 52, "Lamentations": 5, "Ezekiel": 48, "Daniel": 12,
    "Hosea": 14, "Joel": 3, "Amos": 9, "Obadiah": 1, "Jonah": 4,
    "Micah": 7, "Nahum": 3, "Habakkuk": 3, "Zephania": 3, "Haggai": 2,
    "Zechariah": 14, "Malachi": 4, "Matthew": 28, "Mark": 16, "Luke": 24,
    "John": 21, "Acts": 28, "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13,
    "Galatians": 6, "Ephesians": 6, "Philippians": 4, "Colossians": 4,
    "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4,
    "Titus": 3, "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5,
    "2 Peter": 3, "1 John": 5, "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22
}

# ==========================================
# DATABASE FUNCTIONS (Supabase Version)
# ==========================================
def get_versions():
    response = supabase.table('bible_verses').select('version').execute()
    versions = list(set([d['version'] for d in response.data]))
    versions.sort()
    return versions

def get_books():
    response = supabase.table('bible_verses').select('book_title').execute()
    books = list(set([d['book_title'] for d in response.data]))
    books.sort()
    return books

def get_verses(version, book, chapter=None, start_verse=None, end_verse=None):
    query = supabase.table('bible_verses').select("*").eq('version', version).eq('book_title', book)
    if chapter:
        query = query.eq('chapter', chapter)
        if start_verse and end_verse:
            query = query.gte('verse', start_verse).lte('verse', end_verse)
        elif start_verse:
            query = query.eq('verse', start_verse)
    response = query.order('verse').execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df = df.sort_values(by=['chapter', 'verse'])
    return df

def search_keyword(keyword, version=None):
    if version:
        response = supabase.table('bible_verses').select("*").ilike('text', f'%{keyword}%').eq('version', version).limit(50).execute()
    else:
        response = supabase.table('bible_verses').select("*").ilike('text', f'%{keyword}%').limit(50).execute()
    df = pd.DataFrame(response.data)
    return df

# ==========================================
# AI LOGIC: FUZZY MATCH
# ==========================================
def fuzzy_find_book(input_word, available_books):
    # 1. Exact Match
    input_word_clean = input_word.strip().lower()
    for book in available_books:
        if book.lower() == input_word_clean:
            return book, 1.0 # 100% match
            
    # 2. Close Match (difflib)
    # Cutoff 0.6 means 60% similarity or higher
    matches = difflib.get_close_matches(input_word_clean, available_books, n=1, cutoff=0.6)
    if matches:
        return matches[0], 0.8 # High confidence
        
    return None, 0

# ==========================================
# TAGALOG / TYPO MAP (Expanded)
# ==========================================
TAGALOG_MAP = {
    "genesis": "Genesis", "exodo": "Exodus", "levitico": "Leviticus",
    "numeros": "Numbers", "deuteronomio": "Deuteronomy", "josue": "Joshua",
    "hukom": "Judges", "ruth": "Ruth", "1 samuel": "1 Samuel", "2 samuel": "2 Samuel",
    "1 hari": "1 Kings", "2 hari": "2 Kings", "1 kronika": "1 Chronicles", 
    "2 kronika": "2 Chronicles", "esdras": "Ezra", "nehemias": "Nehemiah",
    "ester": "Esther", "job": "Job", "salmo": "Psalms", "kawikaan": "Proverbs",
    "mangangaral": "Ecclesiastes", "kantikil ng salomo": "Song of Solomon", "isaias": "Isaiah",
    "jeremias": "Jeremiah", "panaghoy": "Lamentations", "esekiel": "Ezekiel",
    "daniel": "Daniel", "oseas": "Hosea", "joel": "Joel", "amos": "Amos",
    "abdias": "Obadiah", "jonas": "Jonah", "mikas": "Micah", "nahum": "Nahum",
    "habacuc": "Habakkuk", "sofonias": "Zephaniah", "hageo": "Haggai",
    "zacarias": "Zechariah", "malakias": "Malachi", "mateo": "Matthew",
    "marcos": "Mark", "lucas": "Luke", "juan": "John",
    "gawa": "Acts", "roma": "Romans", "corinto": "Corinthians",
    "galacia": "Galatians", "efeso": "Ephesians", "filipos": "Philippians",
    "colosas": "Colossians", "tesalonica": "Thessalonians", "timoteo": "Timothy",
    "tito": "Titus", "filemon": "Philemon", "hebreo": "Hebrews",
    "santiago": "James", "pedro": "Peter", "jude": "Jude",
    "apocalipsis": "Revelation", "PAHAYAG": "Revelation", "pahayag": "Revelation",
    # SUPER TYP MAP
    "juana": "Juan", # Female name typo
    "juna": "Juan",
    "juam": "Juan",
    "mate": "Mateo",
    "mark": "Marcos",
    "luk": "Lucas",
    "john": "Juan",
    "peter": "Pedro",
    "santiag": "Santiago",
    "coritho": "Corinto"
}

FILLER_WORDS = {"i", "a", "ang", "sa", "ni", "kay", "si", "at"}

# ==========================================
# SUPER PARSER (CLEAN + FUZZY)
# ==========================================
def parse_multi_query(input_str, available_books):
    
    temp_input = input_str
    
    # 1. TAGALOG MAP FIRST
    for tagalog, english in TAGALOG_MAP.items():
        temp_input = re.sub(r'\b' + tagalog + r'\b', english, temp_input, flags=re.IGNORECASE)

    # 2. SPLIT INTO CHUNKS (by numbers roughly) or just split by spaces
    # Since we don't know where the book ends, let's use a sliding window approach for keywords
    # Simplified: Split by space, clean fillers, find books, extract numbers around them.
    
    # Heuristic: Remove filler words
    words = re.findall(r'\b[\w\d]+\b', temp_input)
    
    # Clean List
    clean_words = [w for w in words if w.lower() not in FILLER_WORDS]
    
    # Find Books in Clean Words
    queries = []
    
    current_book = None
    current_nums = []
    
    for word in clean_words:
        # Check if Word is a Book (Exact or Fuzzy)
        is_book = False
        
        # Try exact
        potential_book = next((b for b in available_books if b.lower() == word.lower()), None)
        if potential_book:
            is_book = True
            current_book = potential_book
        else:
            # Try Fuzzy
            match, score = fuzzy_find_book(word, available_books)
            if match:
                is_book = True
                current_book = match
        
        if is_book:
            # If we found a book, and we have accumulated numbers before it, that's the reference
            # BUT, in "corinto 2 4", the numbers are AFTER. 
            # So we flush when we find NEXT book or END of string.
            pass 
        
        # Collect Numbers
        if word.isdigit():
            current_nums.append(int(word))
            
        # FLUSH LOGIC: If we have a book AND numbers, AND next word is NOT a number, 
        # then we assume this query is complete? No, tricky.
        # Let's use simple logic: If current_word is book, look ahead for numbers.
    
    # Better Logic: Iterate with Index
    i = 0
    while i < len(clean_words):
        word = clean_words[i]
        
        # Check Book
        book_match = None
        # Check exact
        if next((b for b in available_books if b.lower() == word.lower()), None):
            book_match = next((b for b in available_books if b.lower() == word.lower()), None)
        else:
            # Check Tagalog Map
            tag_english = TAGALOG_MAP.get(word.lower())
            if tag_english and tag_english in available_books:
                book_match = tag_english
            else:
                # Check Fuzzy
                match, score = fuzzy_find_book(word, available_books)
                if match:
                    book_match = match
                    st.toast(f"Corrected '{word}' to '{match}'", icon="✨")
        
        if book_match:
            # Look ahead for numbers
            j = i + 1
            nums_found = []
            while j < len(clean_words) and clean_words[j].isdigit():
                nums_found.append(int(clean_words[j]))
                j += 1
            
            # If found numbers, assign
            if nums_found:
                if len(nums_found) == 1:
                    # Just Chapter
                    queries.append({'book': book_match, 'chapter': nums_found[0], 'start_verse': None, 'end_verse': None})
                elif len(nums_found) == 2:
                    # Chapter and Verse
                    queries.append({'book': book_match, 'chapter': nums_found[0], 'start_verse': nums_found[1], 'end_verse': None})
                elif len(nums_found) >= 3:
                    # Range
                    queries.append({'book': book_match, 'chapter': nums_found[0], 'start_verse': nums_found[1], 'end_verse': nums_found[-1]})
            else:
                # Whole Book
                queries.append({'book': book_match, 'chapter': None, 'start_verse': None, 'end_verse': None})
            
            i = j # Skip processed numbers
        else:
            i += 1
            
    return queries

def get_verses(version, book, chapter=None, start_verse=None, end_verse=None):
    conn = get_connection()
    base_query = "SELECT verse, text FROM bible_verses WHERE version = ? AND book_title = ?"
    params = [version, book]
    
    if chapter:
        base_query += " AND chapter = ?"
        params.append(chapter)
        if start_verse and end_verse:
            base_query += " AND verse BETWEEN ? AND ?"
            params.append(start_verse)
            params.append(end_verse)
        elif start_verse:
            base_query += " AND verse = ?"
            params.append(start_verse)
            
    base_query += " ORDER BY chapter, verse"
    df = pd.read_sql(base_query, conn, params=params)
    conn.close()
    return df

def search_keyword(keyword, version=None):
    conn = get_connection()
    if version:
        query = "SELECT book_title, chapter, verse, text FROM bible_verses WHERE text LIKE ? AND version = ? LIMIT 50"
        df = pd.read_sql(query, conn, params=(f'%{keyword}%', version))
    else:
        query = "SELECT book_title, chapter, verse, text FROM bible_verses WHERE text LIKE ? LIMIT 50"
        df = pd.read_sql(query, conn, params=(f'%{keyword}%',))
    conn.close()
    return df

# ==========================================
# UI LAYOUT
# ==========================================
st.title("🤖 Talking Bible (AI Smart)")

with st.sidebar:
    st.header("🎤 Speaker / Pastor")
    uploaded_file = st.file_uploader("Upload Picture", type=['jpg', 'png', 'jpeg'])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Today's Speaker", width=200, use_column_width=False)
        st.success("Speaker Activated!")
    else:
        st.info("No picture uploaded.")
    
    st.divider()
    
    st.header("Settings")
    versions = get_versions()
    default_idx = versions.index('KJV') if 'KJV' in versions else 0
    selected_version = st.selectbox("Choose Version", versions, index=default_idx)
    st.divider()
    
    st.caption("✨ AI Fuzzy Textbox")
    smart_search_input = st.text_input("Mag-type kahit sablay!", placeholder="i corinto 2 4 juana 3 5...")
    st.markdown("""
    <small>
    Examples:<br>
    - <b>i corinto 2 4</b><br>
    - <b>juana 3 5</b> (Auto-correct to Juan)<br>
    - <b>mateo 1 5</b>
    </small>
    """, unsafe_allow_html=True)
    st.divider()

    st.caption("Or use Dropdowns:")
    books = get_books()
    selected_book = st.selectbox("Search Book", books, index=0) 
    selected_chapter = st.number_input("Chapter", min_value=1, value=1, step=1)

tab1, tab2 = st.tabs(["📖 Read Passage", "🔍 Keyword Search"])

with tab1:
    use_smart = False
    queries_list = []
    
    if smart_search_input.strip():
        queries_list = parse_multi_query(smart_search_input, books)
        if queries_list:
            use_smart = True
        else:
            st.warning("Could not understand. Using Dropdowns instead.")
    
    if not use_smart:
        queries_list = [{
            'book': selected_book,
            'chapter': selected_chapter,
            'start_verse': None,
            'end_verse': None
        }]

    for i, q in enumerate(queries_list):
        display_book = q['book']
        display_chapter = q['chapter']
        start_v = q['start_verse']
        end_v = q['end_verse']
        
        if display_chapter:
            if start_v and end_v:
                header_text = f"{display_book} CHAPTER {display_chapter} (Verses {start_v}-{end_v})"
            elif start_v:
                header_text = f"{display_book} CHAPTER {display_chapter}:{start_v}"
            else:
                header_text = f"{display_book} CHAPTER {display_chapter}"
        else:
            max_chap = VB_MAX_CHAPTERS.get(display_book, "?")
            header_text = f"{display_book} (Chapters 1-{max_chap})"
            
        st.markdown(f"<h3 class='section-header'>{header_text}</h3>", unsafe_allow_html=True)
        
        verses_df = get_verses(selected_version, display_book, display_chapter, start_v, end_v)
        
        if not verses_df.empty:
            for index, row in verses_df.iterrows():
                verse_num = row['verse']
                verse_text = row['text']
                
                st.markdown(f"""
                <div class='verse-text'>
                    <sup><b>{verse_num}</b></sup> {verse_text}
                </div>
                <br>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"No verses found for {display_book} {display_chapter}.")
            
        if i < len(queries_list) - 1:
            st.markdown("<div class='book-divider'></div>", unsafe_allow_html=True)

with tab2:
    st.subheader("Search the Bible")
    keyword = st.text_input("Enter word or phrase (e.g., 'love', 'faith'):")
    search_scope = st.checkbox("Search only in current version", value=True)
    
    if st.button("Search"):
        if keyword:
            with st.spinner("Searching..."):
                if search_scope:
                    results = search_keyword(keyword, selected_version)
                else:
                    results = search_keyword(keyword)
                
                if not results.empty:
                    for index, row in results.iterrows():
                        st.markdown(f"**{row['book_title']} {row['chapter']}:{row['verse']}**")
                        st.write(row['text'])
                        st.divider()
                else:
                    st.info("No results found.")
        else:
            st.warning("Please enter a keyword.")

st.markdown("---")
st.caption("🤍 Freely shared, never for sale. Spreading His Word to everyone.")
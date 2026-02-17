from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME

from whoosh.analysis import StemmingAnalyzer, StandardAnalyzer

from datetime import datetime, timedelta, timezone

from search_engine import SearchEngine

if __name__ == "__main__":
    # Define some sample documents.
    # Notice we include 'extra' fields that aren't specifically in the search schema.
    # These will still be preserved because SearchEngine pickles the entire input dict.
    docs = [
        {
            "id": "1",
            "title": "First document",
            "description": "This is the first document we've added in San Francisco!",
            "tags": ["foo", "bar"],
            "date": datetime.now(timezone.utc) - timedelta(days=0),
            "extra": "kittens and cats",
        },
        {
            "id": "2",
            "title": "Second document",
            "description": "The second one is even more interesting!",
            "tags": ["alice"],
            "date": datetime.now(timezone.utc) - timedelta(days=1),
            "extra": "foals and horses",
        },
        {
            "id": "3",
            "title": "Third document",
            "description": "The third one is less interesting!",
            "tags": ["bob"],
            "date": datetime.now(timezone.utc) - timedelta(days=2),
            "extra": "bunny and rabbit",
        },
    ]

    # Define the search schema.
    # - ID: Unindexed value that can be retrieved quickly.
    # - TEXT: Indexed (searchable) text.
    # - StandardAnalyzer: Tokenizes text using standard rules (e.g., splits on whitespace and punctuation).
    # - KEYWORD: Space-separated keywords, indexed as a single unit or individually.
    # - DATETIME: Indexed as a date for range queries.
    schema = Schema(
        id=ID(stored=True),
        title=TEXT(stored=True),
        description=TEXT(stored=True, analyzer=StandardAnalyzer(), spelling=True),
        tags=KEYWORD(stored=True, lowercase=True, commas=True),
        date=DATETIME(stored=True),
    )

    print("--- Schema Configuration ---")
    for k, v in schema.items():
        print(f"Field '{k}': {v.__class__.__name__}")
    print(f"Total searchable fields: {schema.names()}")
    print("-" * 28 + "\n")

    # Initialize and index
    engine = SearchEngine(schema)
    engine.index_documents(docs)

    print(f"Successfully indexed {engine.get_index_size()} documents.\n")

    # demonstrate simple keyword queries
    print("--- Keyword Searching ---")
    # Whoosh is case-insensitive by default with most analyzers.
    for q in ["first", "second", "THIRD", "bob", "alice"]:
        print(f"\nQuery: '{q}'")
        engine.search(q, limit=10, print_only=True)

    # demonstrate phrase search and multifield search
    print("\n--- Phrase and Multi-field Searching ---")
    # 'san francisco' will match because it's in the description.
    # 'kittens' will match because SearchEngine searches all fields (except 'raw').
    # Note: 'kittens' is in the 'extra' field of doc 1.
    # BUT WAIT: 'extra' isn't in the schema, so it won't be indexed for search!
    # The 'pickle' trick allows us to SEE 'extra' in the results,
    # but it doesn't make 'extra' searchable unless we add it to the schema.
    for q in ["san francisco", "kittens"]:
        print(f"\nQuery: '{q}'")
        engine.search(q, limit=10, print_only=True)

    # demonstrate complex boolean logic
    print("\n--- Boolean Logic Searching ---")
    q = "San Francisco OR (tags:alice AND description:interesting)"
    print(f"Query: '{q}'")
    engine.search(q, limit=10, print_only=True)

    # demonstrate date range queries
    print("\n--- Date Range Searching ---")
    # Syntax: [YYYYMMDD TO YYYYMMDD]
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    q = f"date:[{yesterday.strftime('%Y%m%d')} TO {today.strftime('%Y%m%d')}]"
    print(f"Searching for documents from {yesterday} to {today}...")
    print(f"Query: '{q}'")
    engine.search(q, limit=10, print_only=True)

    # demonstrate spelling suggestions
    print("\n--- Spelling Suggestions ---")
    q = "fransisco"  # misspelled
    print(f"Query: '{q}'")
    engine.search(q, limit=5, print_only=True)

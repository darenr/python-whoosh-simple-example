from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME

from whoosh.analysis import StemmingAnalyzer

from datetime import datetime, timedelta, timezone

from search_engine import SearchEngine

if __name__ == "__main__":
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

    schema = Schema(
        id=ID(stored=True),
        title=TEXT(stored=True),
        description=TEXT(stored=True, analyzer=StemmingAnalyzer(), spelling=True),
        tags=KEYWORD(stored=True),
        date=DATETIME(stored=True),
    )

    for k, v in schema.items():
        print(f"{k}: {v.__class__.__name__}")

    engine = SearchEngine(schema)
    engine.index_documents(docs)

    print(f"indexed {engine.get_index_size()} documents")

    fields_to_search = ["title", "description", "tags"]

    print("\nPerforming some simple keyword queries...")
    for q in ["first", "second", "THIRD", "kittens", "bob", "alice", "san francisco"]:
        engine.show_results(q, fields_to_search)

    # now an example of a query that matches on the description field but not the title field
    print("\nPerforming a query that matches on description but not title...")
    q = "san francisco"
    engine.show_results(q, fields_to_search)

    # now a complex query that matches on multiple fields
    q = "San Francisco OR (tags:alice AND description:interesting)"
    engine.show_results(q, fields_to_search)

    # now a query showing date ranges, any document from today or yesterday
    print("\nPerforming a query that matches on date range...")
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    q = f"date:[{yesterday.strftime('%Y%m%d')} TO {today.strftime('%Y%m%d')}]"

    engine.show_results(q, fields_to_search)

from typing import Dict, List, Sequence

from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, STORED
from whoosh.qparser import MultifieldParser

from whoosh.filedb.filestore import RamStorage
from whoosh.analysis import StemmingAnalyzer

import pickle
from datetime import datetime, timedelta, timezone


class SearchEngine:
    def __init__(self, schema):
        self.schema = schema
        schema.add("raw", STORED())
        self.ix = RamStorage().create_index(self.schema)

    def index_documents(self, docs: Sequence):
        writer = self.ix.writer()
        for doc in docs:
            d = {k: v for k, v in doc.items() if k in self.schema.stored_names()}
            d["raw"] = pickle.dumps(doc)
            writer.add_document(**d)
        writer.commit(optimize=True)

    def get_index_size(self) -> int:
        return self.ix.doc_count_all()

    def _query(self, q: str, fields: Sequence) -> List[Dict]:
        search_results = []
        with self.ix.searcher() as searcher:
            corrector = searcher.corrector("description")

            results = searcher.search(MultifieldParser(fields, schema=self.schema).parse(q))
            if results.is_empty():
                print(f"No results found for query: {q}")
                suggestions = corrector.suggest(q, limit=3)
                if suggestions:
                    print(f"Did you mean: {', '.join(suggestions)}?")
                else:
                    print("No suggestions available.")
            else:
                for r in results:
                    d = pickle.loads(r["raw"])
                    search_results.append(d)

        return search_results

    def search(self, q: str, fields: Sequence) -> str:
        return self._query(q, fields)

    def show_results(self, q: str, fields: Sequence) -> str:
        results = self._query(q, fields)
        for r in results:
            row = {
                k: v
                for k, v in r.items()
                if k != "raw" and isinstance(v, (str, list, datetime))
            }
            print(f"query: {q}\n\t{row}")


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

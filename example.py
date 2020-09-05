from typing import Dict, List, Sequence

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import MultifieldParser
from whoosh.filedb.filestore import RamStorage
from whoosh.analysis import StemmingAnalyzer

#
# Simple example indexing to an in-memory index and performing a search
# across multiple fields and returning an array of highlighted results
#


class SearchEngine:

    def __init__(self, schema):
        self.ix = RamStorage().create_index(schema)

    def index_documents(self, docs: Sequence):
        writer = self.ix.writer()
        for doc in docs:
            writer.add_document(**doc)
        writer.commit(optimize=True)

    def get_index_size(self) -> int:
        return self.ix.doc_count_all()

    def query(self, q: str, fields: Sequence, highlight: bool=True) -> List[Dict]:
        search_results = []
        with self.ix.searcher() as searcher:
            results = searcher.search(MultifieldParser(fields, schema=schema).parse(q))
            for r in results:
                d = {k:v for k, v in r.items()}
                if highlight:
                    for f in fields:
                        if r[f] and isinstance(r[f], str):
                            d[f] = r.highlights(f) or r[f]

                search_results.append(d)

        return search_results

if __name__ == '__main__':

    docs = [
        {
            "id": "1",
            "title": "First document banana",
            "description": "This is the first document we've added!",
            "tags": ['foo', 'bar']
        },
        {
            "id": "2",
            "title": "Second document hatstand",
            "description": "The second one is even more interesting!",
            "tags": ['alice']
        },
        {
            "id": "3",
            "title": "Third document slug",
            "description": "The third one is less interesting!",
            "tags": ['bob']
        },
    ]

    schema = Schema(
        id=ID(stored=True),
        title=TEXT(stored=True),
        description=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        tags=KEYWORD(stored=True)
    )

    engine = SearchEngine(schema)
    engine.index_documents(docs)

    print(f"indexed {engine.get_index_size()} documents")

    fields_to_search = ["title", "description", "tags"]

    for q in ["hatstand", "banana", "first", "second", "alice", "bob"]:
        print(f"Query:: {q}")
        print("\t", engine.query(q, fields_to_search, highlight=True))
        print("-"*70)

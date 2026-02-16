from typing import Dict, List, Sequence

from whoosh.fields import STORED
from whoosh.qparser import MultifieldParser

from whoosh.filedb.filestore import RamStorage

import pickle
from datetime import datetime


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

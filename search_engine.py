from typing import Dict, List, Sequence

from whoosh.fields import COLUMN, TEXT
from whoosh.qparser import MultifieldParser

from whoosh.filedb.filestore import RamStorage

import pickle

from rich.pretty import pprint


class SearchEngine:
    def __init__(self, schema):
        self.schema = schema
        schema.add("raw", COLUMN())
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

    def _query(self, q: str, limit: int) -> List[Dict]:
        search_results = []
        with self.ix.searcher() as searcher:
            corrector = searcher.corrector("description")
            fields_to_search = [x for x in self.schema.names() if x != "raw"]
            results = searcher.search(
                MultifieldParser(fields_to_search, schema=self.schema).parse(q), limit=limit
            )
            if results.is_empty():
                print(f"No results found for query: {q}")
                suggestions = corrector.suggest(q, limit=3)
                if suggestions:
                    print(f"Did you mean: {', '.join(suggestions)}?")
                else:
                    print("No suggestions available.")
            else:
                for r in results:
                    # restore the whole object not just the stored fields, using pickle to preserve datatypes
                    d = pickle.loads(r["raw"])
                    search_results.append(d)

        return search_results

    def search(self, q: str, limit: int, print_only=False) -> str:
        results = self._query(q, limit=limit)
        if print_only:
            for row in results:
                pprint(row)
        else:
            return results

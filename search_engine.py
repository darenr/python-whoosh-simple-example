from typing import Dict, List, Sequence

from whoosh.fields import COLUMN
from whoosh.qparser import MultifieldParser

from whoosh.filedb.filestore import RamStorage

import pickle

from rich.pretty import pprint


class SearchEngine:
    """
    A simple wrapper around the Whoosh library to provide an easy-to-use search engine interface.
    
    It features in-memory indexing, automatic schema management for full object retrieval 
    using pickle, and search suggestions for failed queries.
    """

    def __init__(self, schema):
        """
        Initialize the SearchEngine with a Whoosh schema.
        
        Args:
            schema: A whoosh.fields.Schema object defining the indexable fields.
        """
        self.schema = schema
        # Add a HIDDEN column to store the original raw object as a byte sequence.
        # This allows us to retrieve the original data types even if they aren't 
        # fully represented in the text-based search index.
        self.schema.add("raw", COLUMN())
        self.ix = RamStorage().create_index(self.schema)

    def index_documents(self, docs: Sequence):
        """
        Add multiple documents to the search index.
        
        Args:
            docs: A sequence of dictionaries representing documents.
        """
        writer = self.ix.writer()
        for doc in docs:
            # Filter incoming dictionary to only include fields defined in the schema
            d = {k: v for k, v in doc.items() if k in self.schema.stored_names()}
            # Store the entire original document using pickle in a hidden field
            d["raw"] = pickle.dumps(doc)
            writer.add_document(**d)
        
        # We call commit with optimize=True to merge segments for better query performance.
        # This is especially useful for small, relatively static indices.
        writer.commit(optimize=True)

    def get_index_size(self) -> int:
        """Return the number of documents in the index."""
        return self.ix.doc_count_all()

    def _query(self, q: str, limit: int) -> List[Dict]:
        """
        Internal method to execute a search query against the index.
        
        Args:
            q: The search query string.
            limit: Maximum number of results to return.
            
        Returns:
            A list of the original document dictionaries.
        """
        search_results = []
        with self.ix.searcher() as searcher:
            # Corrector helps provide 'Did you mean?' suggestions for misspellings.
            # Here it defaults to searching the 'description' field.
            corrector = searcher.corrector("description")
            
            # We search all fields defined in the schema except for our internal 'raw' field.
            fields_to_search = [x for x in self.schema.names() if x != "raw"]
            
            # Parse the query and search
            parser = MultifieldParser(fields_to_search, schema=self.schema)
            results = searcher.search(parser.parse(q), limit=limit)
            
            if results.is_empty():
                print(f"No results found for query: {q}")
                suggestions = corrector.suggest(q, limit=3)
                if suggestions:
                    print(f"Did you mean: {', '.join(suggestions)}?")
                else:
                    print("No suggestions available.")
            else:
                for r in results:
                    # Retrieve the whole original object from the hidden 'raw' column
                    # This bypasses the schema's indexed text and returns the original types.
                    d = pickle.loads(r["raw"])
                    search_results.append(d)

        return search_results

    def search(self, q: str, limit: int, print_only=False) -> str:
        """
        Public search interface.
        
        Args:
            q: The search query string.
            limit: Maximum results to return.
            print_only: If True, prints formatted results instead of returning them.
            
        Returns:
            The list of results if print_only is False, otherwise returns None.
        """
        results = self._query(q, limit=limit)
        if print_only:
            for row in results:
                print("-" * 20)
                pprint(row)
        else:
            return results

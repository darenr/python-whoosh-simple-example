# python-whoosh-simple-example
An example of how to use whoosh to index and search documents

```
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
  ```

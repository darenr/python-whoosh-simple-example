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

produces the following output:

```
indexed 3 documents
Query:: hatstand
	 [{'description': 'The second one is even more interesting!', 'id': '2', 'tags': ['alice'], 'title': 'Second document <b class="match term0">hatstand</b>'}]
----------------------------------------------------------------------
Query:: banana
	 [{'description': "This is the first document we've added!", 'id': '1', 'tags': ['foo', 'bar'], 'title': 'First document <b class="match term0">banana</b>'}]
----------------------------------------------------------------------
Query:: first
	 [{'description': 'This is the <b class="match term1">first</b> document we\'ve added', 'id': '1', 'tags': ['foo', 'bar'], 'title': '<b class="match term0">First</b> document banana'}]
----------------------------------------------------------------------
Query:: second
	 [{'description': 'The <b class="match term1">second</b> one is even more interesting', 'id': '2', 'tags': ['alice'], 'title': '<b class="match term0">Second</b> document hatstand'}]
----------------------------------------------------------------------
Query:: alice
	 [{'description': 'The second one is even more interesting!', 'id': '2', 'tags': ['alice'], 'title': 'Second document hatstand'}]
----------------------------------------------------------------------
Query:: bob
	 [{'description': 'The third one is less interesting!', 'id': '3', 'tags': ['bob'], 'title': 'Third document slug'}]
```

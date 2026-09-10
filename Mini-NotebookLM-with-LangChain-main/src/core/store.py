from __future__ import annotations

import truststore
truststore.inject_into_ssl()

import os
import uuid
from dataclasses import dataclass, field

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_cohere import CohereEmbeddings
from langchain_core.documents import Document

from core.sources import chunk_source

EMBEDDINGS_MODEL = CohereEmbeddings(
    cohere_api_key=os.getenv("COHERE_API_KEY"), model="embed-multilingual-v3.0"
)


@dataclass
class Source:
    id: str
    name: str
    content: str
    active: bool = True


@dataclass
class SourceStore:
    _sources: dict[str, Source] = field(default_factory=dict)
    _vector_store: InMemoryVectorStore | None = None
    _vector_ids_by_source:dict[str,list[str]] = field(default_factory=dict)

    def list(self) -> list[Source]:
        return list(self._sources.values())

    def get(self, source_id: str) -> Source | None:
        return self._sources.get(source_id)

    def active_ids(self) -> set[str]:
        return {s.id for s in self._sources.values() if s.active}

    # add
    def add(self, name: str, content: str) -> Source:
        source = Source(id=uuid.uuid4().hex[:8], name=name, content=content)
        self._sources[source.id] = source
        chunks = chunk_source(source.id, source.name, source.content)
        if self._vector_store is None:
            self._vector_store = InMemoryVectorStore(EMBEDDINGS_MODEL)
        vector_ids = self._vector_store.add_documents(chunks)
        self._vector_ids_by_source[source.id] = vector_ids
        return source

    # remove
    def remove(self, source_id: str) -> bool:
        source = self._sources.pop(source_id, None)
        if source is None:
            return False
        ids = self._vector_ids_by_source[source.id]
        if ids and self._vector_store is not None:
            self._vector_store.delete(ids=ids)
        return True

    def set_active(self, source_id: str, active: bool) -> Source | None:
        source = self._sources.get(source_id)
        if source is not None:
            source.active = active
        return source

    def search(self, query: str, k: int | None = None) -> list[Document]:
        active_sources = self.active_ids()
        if not active_sources:
            return []

        results = self._vector_store.similarity_search(
            query=query,
            k=k or 4,
            filter=lambda doc: doc.metadata.get("source_id") in active_sources,
        )

        print("SEARCH QUERY:", query)
        print("RESULTS:", len(results))

        for r in results:
            print("----")
            print(r.page_content[:300])

        return results

store = SourceStore()
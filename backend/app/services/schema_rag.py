from __future__ import annotations

import os
from typing import Dict, List

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TRANSFORMERS_NO_FLAX", "1")
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")

import math
import re
from typing import Callable, List

import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.types import EmbeddingFunction, Embeddings

from app.core.config import settings


class SchemaRag:
    def __init__(self, persist_path: str, model_name: str) -> None:
        self._client = chromadb.PersistentClient(path=persist_path)
        self._model_name = model_name
        self._embed_fn = None
        self._collection = None

    def _ensure_collection(self) -> None:
        if self._collection is not None:
            return

        self._embed_fn = self._build_embedding_function()
        self._collection = self._client.get_or_create_collection(
            name="schema_context",
            embedding_function=self._embed_fn,
        )

    def _build_embedding_function(self) -> Callable[[list[str]], list[list[float]]]:
        try:
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self._model_name
            )
        except Exception:
            return HashEmbeddingFunction()

    def rebuild(self, schema: Dict[str, List[str]]) -> None:
        self._ensure_collection()

        existing = self._collection.get(include=["ids"])
        existing_ids = existing.get("ids", [])
        if existing_ids:
            self._collection.delete(ids=existing_ids)

        documents: List[str] = []
        metadatas: List[dict[str, str]] = []
        ids: List[str] = []

        for table_name, columns in schema.items():
            documents.append(f"Table: {table_name}\nColumns: {', '.join(columns)}")
            metadatas.append({"table": table_name})
            ids.append(table_name)

        if documents:
            self._collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def retrieve(self, query: str, top_k: int) -> str:
        if not query.strip():
            return ""

        self._ensure_collection()

        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas"],
        )

        documents = results.get("documents", [[]])[0]
        if not documents:
            return ""

        return "\n\n".join(documents)


schema_rag = SchemaRag(persist_path=settings.chroma_path, model_name=settings.embedding_model)


class HashEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: List[str]) -> Embeddings:
        vectors: list[list[float]] = []
        for text in input:
            tokens = re.findall(r"[a-z0-9_]+", text.lower())
            size = 256
            vec = [0.0] * size
            for token in tokens:
                idx = hash(token) % size
                vec[idx] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vectors.append([v / norm for v in vec])
        return vectors

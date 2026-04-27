import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from loguru import logger

root_path = str(Path(__file__).parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from src.embedding.embedder import Embedder

load_dotenv()

class Retriever:
    """
    Classe responsável pela busca semântica no banco vetorial Qdrant.
    """
    def __init__(self, collection_name="aneel_chunks"):
        self.collection_name = collection_name
        self.embedder = Embedder()
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )

    def search(self, query: str, limit: int = 5, year: str = None):
        """
        Busca os trechos mais relevantes para uma pergunta.
        """
        logger.info(f"🔍 Buscando contextos para: '{query[:50]}...'")
        
        query_vector = self.embedder.get_embeddings([query])[0]

        query_filter = None
        if year:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="year",
                        match=models.MatchValue(value=str(year))
                    )
                ]
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        results = []
        for hit in response.points:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "chunk": hit.payload.get("texto"),
                "file": hit.payload.get("nome_arquivo"),
                "year": hit.payload.get("ano")
            })

        return results, query_vector

def retrieve_context(query: str, limit: int = 5, year: str = None):
    """
    Função auxiliar para ser chamada diretamente pelo Back-end.
    Exemplo: from src.retrieval.retriever import retrieve_context
    """
    retriever = Retriever()
    return retriever.search(query, limit=limit, year=year)

if __name__ == "__main__":
    pergunta = "Quais documentos subsidiam a revisão tarifária?"
    contextos, query_vector = retrieve_context(pergunta, limit=2)
    
    for c in contextos:
        print(f"\n[{c['file']}] (Score: {c['score']:.4f})\n{c['chunk'][:200]}...")

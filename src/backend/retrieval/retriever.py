import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from loguru import logger
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Ajuste de path para permitir importações internas se o script for rodado diretamente
root_path = str(Path(__file__).parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)


# Carrega variáveis do .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Embedder:
    def __init__(self, model="text-embedding-3-small"):
        self.model = model

    @retry(
        stop=stop_after_attempt(8), # Aumentado para 8 tentativas
        wait=wait_exponential(multiplier=2, min=5, max=60), # Espera mais agressiva (até 60s)
        reraise=True
    )
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Gera embeddings para uma lista de textos.
        Utiliza retentativas automáticas para lidar com rate limits ou instabilidades.
        """
        try:
            # Limpeza básica de textos (remover quebras de linha excessivas melhora o embedding)
            texts = [t.replace("\n", " ") for t in texts]
            
            response = client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            # Extrai os vetores da resposta
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Erro ao gerar embeddings: {e}")
            raise e

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
            timeout=60  # Aumentado para 60 segundos
        )

    def search(self, query: str, limit: int = 5, year: str = None):
        """
        Busca os trechos mais relevantes para uma pergunta.
        """
        logger.info(f"🔍 Buscando contextos para: '{query[:50]}...'")
        
        # 1. Gera embedding da pergunta
        query_vector = self.embedder.get_embeddings([query])[0]

        # 2. Filtro por ano (opcional)
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

        # 3. Busca no Qdrant com Retry manual
        max_retries = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True
                )
                break # Sucesso
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Tentativa {attempt + 1} de busca falhou. Tentando novamente...")
                    import time
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"❌ Erro definitivo na busca: {e}")
                    raise e

        # 4. Formata os resultados
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

# Função de conveniência para o Back-end
def retrieve_context(query: str, limit: int = 5, year: str = None):
    """
    Função auxiliar para ser chamada diretamente pelo Back-end.
    Exemplo: from src.retrieval.retriever import retrieve_context
    """
    retriever = Retriever()
    return retriever.search(query, limit=limit, year=year)

if __name__ == "__main__":
    # Teste rápido
    pergunta = "Quais documentos subsidiam a revisão tarifária?"
    contextos, query_vector = retrieve_context(pergunta, limit=2)
    
    for c in contextos:
        print(f"\n[{c['file']}] (Score: {c['score']:.4f})\n{c['chunk'][:200]}...")

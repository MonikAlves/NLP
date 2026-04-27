import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class VectorDB:
    def __init__(self, collection_name="aneel_chunks"):
        self.collection_name = collection_name
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60,
        )

    def ensure_collection(self, vector_size=1536):
        """
        Garante que a coleção exista no Qdrant com as configurações corretas.
        """
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            logger.info(f"🚀 Criando coleção '{self.collection_name}' no Qdrant...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                ),
            )
            logger.success(f"✅ Coleção '{self.collection_name}' criada com sucesso.")
        else:
            logger.info(f"📚 Coleção '{self.collection_name}' já existe.")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=20),
        reraise=True
    )
    def upsert_chunks(self, points: list[PointStruct]):
        """
        Insere ou atualiza um lote de vetores e metadados no Qdrant.
        """
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao fazer upsert no Qdrant: {e}")
            return False

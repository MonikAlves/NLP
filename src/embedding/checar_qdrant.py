import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def checar_qdrant():
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    collection_name = "aneel_chunks"

    try:
        info = client.get_collection(collection_name=collection_name)
        logger.info(f"📊 Coleção: {collection_name}")
        logger.info(f"🔢 Total de pontos (chunks) no banco: {info.points_count}")

        logger.info("🔍 Inspecionando os últimos registros inseridos...")
        records, _ = client.scroll(
            collection_name=collection_name,
            limit=3,
            with_payload=True,
            with_vectors=False
        )

        for i, record in enumerate(records, 1):
            print(f"\n--- Amostra {i} ---")
            print(f"ID: {record.id}")
            print(f"Arquivo: {record.payload.get('nome_arquivo')}")
            print(f"Ano: {record.payload.get('ano')}")
            print(f"Texto (primeiros 100 caracteres): {record.payload.get('texto')[:100]}...")

    except Exception as e:
        logger.error(f"❌ Erro ao acessar o Qdrant: {e}")

if __name__ == "__main__":
    checar_qdrant()

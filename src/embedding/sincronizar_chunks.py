import sqlite3
import os
from google.cloud import storage
from loguru import logger

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(ROOT_DIR, "chave.json")
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"

def sincronizar_chunks():
    logger.info("☁️  Listando arquivos JSONL no bucket (aneel/chunks/) para sincronizar status...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    arquivos_no_gcp = set()
    for blob in bucket.list_blobs(prefix="aneel/chunks/"):
        if blob.name.endswith(".jsonl"):
            nome = blob.name.split("/")[-1].replace(".jsonl", ".pdf")
            arquivos_no_gcp.add(nome)

    logger.info(f"☁️  {len(arquivos_no_gcp)} chunks encontrados no GCP.")

    if not arquivos_no_gcp:
        logger.warning("Nenhum chunk encontrado.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    nomes_placeholders = ",".join(["?"] * len(arquivos_no_gcp))
    query = f"""
        UPDATE arquivos 
        SET status = 8 
        WHERE nome_arquivo IN ({nomes_placeholders}) AND status < 8
    """
    
    cursor.execute(query, list(arquivos_no_gcp))
    marcados = cursor.rowcount
    conn.commit()
    conn.close()

    logger.success(f"✅ {marcados} arquivos marcados como status=8 (Prontos para Embedding)!")

if __name__ == "__main__":
    sincronizar_chunks()

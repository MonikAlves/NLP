"""
Verifica quais arquivos já existem no GCP bucket e marca status=3 no banco.
Roda após o migrar.py para não precisar baixar de novo o que já está lá.
"""
import sqlite3
import os
from google.cloud import storage
from loguru import logger

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(ROOT_DIR, "chave.json")
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"
PREFIXOS = ["aneel/pdfs/", "aneel/htmls/", "aneel/zips/"]


def sincronizar():
    logger.info("☁️  Listando arquivos no GCP bucket...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    arquivos_no_gcp = set()
    for prefixo in PREFIXOS:
        for blob in bucket.list_blobs(prefix=prefixo):
            nome = blob.name.split("/")[-1]
            if nome:
                arquivos_no_gcp.add(nome)

    logger.info(f"☁️  {len(arquivos_no_gcp)} arquivos encontrados no GCP.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome_arquivo FROM arquivos WHERE status = 0")
    pendentes = cursor.fetchall()
    logger.info(f"📋 {len(pendentes)} registros com status=0 (pendente) no banco.")

    marcados = 0
    for arquivo_id, nome_arquivo in pendentes:
        if nome_arquivo in arquivos_no_gcp:
            cursor.execute(
                "UPDATE arquivos SET status = 3 WHERE id = ?", (arquivo_id,)
            )
            marcados += 1

    conn.commit()
    conn.close()

    logger.success(f"✅ {marcados} arquivos marcados como status=3 (já no GCP).")
    logger.info(f"   {len(pendentes) - marcados} ainda precisam ser baixados.")


if __name__ == "__main__":
    sincronizar()

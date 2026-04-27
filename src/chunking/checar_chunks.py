import os
from google.cloud import storage
from loguru import logger

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
cred_path = os.path.join(ROOT_DIR, "chave.json")
if os.path.exists(cred_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
BUCKET_NAME = "dados_bruto_nlp"

def checar_chunks():
    logger.info("☁️  Contando arquivos JSONL no bucket do GCP...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    count = 0
    anos = set()

    for blob in bucket.list_blobs(prefix="aneel/chunks/"):
        if blob.name.endswith(".jsonl"):
            count += 1
            
            partes = blob.name.split("/")
            if len(partes) > 3:
                ano = partes[-2]
                anos.add(ano)

            if count % 5000 == 0:
                logger.info(f"Já contei {count} arquivos...")

    logger.success(f"🎉 Total de arquivos JSONL na pasta aneel/chunks/: {count}")
    logger.info(f"📅 Anos encontrados: {sorted(list(anos))}")

if __name__ == "__main__":
    checar_chunks()

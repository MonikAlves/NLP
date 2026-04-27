import sqlite3
import os
from google.cloud import storage
from loguru import logger

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
cred_path = os.path.join(ROOT_DIR, "chave.json")
if os.path.exists(cred_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"

def sincronizar():
    logger.info("☁️  Listando markdowns no GCP bucket (aneel/markdowns/)...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    # Coleta arquivos do GCP (nome base e ano)
    gcp_files = []
    for blob in bucket.list_blobs(prefix="aneel/markdowns/"):
        if blob.name.endswith(".md"):
            partes = blob.name.split("/")
            nome = partes[-1].replace(".md", ".pdf")
            # Extrair ano do caminho se existir ex: aneel/markdowns/2016/arquivo.md
            ano = partes[-2] if len(partes) > 3 else ""
            gcp_files.append((nome, ano))

    logger.info(f"☁️  {len(gcp_files)} markdowns encontrados no GCP.")

    if not gcp_files:
        logger.warning("Nenhum markdown encontrado.")
        return

    # Conecta no banco
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Busca todos os arquivos que já existem no banco
    cursor.execute("SELECT nome_arquivo FROM arquivos")
    arquivos_db = {row[0] for row in cursor.fetchall()}

    marcados_update = 0
    inseridos_novos = 0

    logger.info("Sincronizando com o banco de dados...")
    
    for nome, ano in gcp_files:
        if nome in arquivos_db:
            # Já existe, vamos garantir que o status seja 6 (se for menor que 6)
            cursor.execute("UPDATE arquivos SET status = 6 WHERE nome_arquivo = ? AND status < 6", (nome,))
            marcados_update += cursor.rowcount
        else:
            # Não existe! Vamos forçar a injeção no banco para não dependermos do banco original
            cursor.execute(
                "INSERT INTO arquivos (nome_arquivo, ano, status) VALUES (?, ?, 6)",
                (nome, ano)
            )
            inseridos_novos += 1

    conn.commit()
    conn.close()

    logger.success(f"✅ {marcados_update} arquivos atualizados para status=6.")
    logger.success(f"✅ {inseridos_novos} novos arquivos INJETADOS à força no banco com status=6.")
    logger.success(f"🎉 Total de arquivos prontos para chunking (status=6): {marcados_update + inseridos_novos}")

if __name__ == "__main__":
    sincronizar()

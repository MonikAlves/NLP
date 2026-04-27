import sqlite3
import asyncio
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from loguru import logger
from typing import Optional, Tuple
from google.cloud import storage

from migrar import migrar
from downloader import Downloader

# --- 1. CONFIGURAÇÕES ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(ROOT_DIR, "chave.json")
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"
MAX_WORKERS = 15


# --- 3. FUNÇÕES DO WORKER ---
def get_next_task(conn) -> Optional[Tuple]:
    cursor = conn.cursor()
    while True:
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor.execute("SELECT rowid, url, nome_arquivo FROM arquivos WHERE status IN (0, 2) LIMIT 1")
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE arquivos SET status = 1 WHERE rowid = ?", (row[0],))
            conn.commit()
            return row
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                time.sleep(random.uniform(0.05, 0.2))
            else:
                conn.rollback()
                raise

async def worker_loop(worker_id: int):
    logger.info(f"👷 Worker {worker_id} iniciado!")
    conn = sqlite3.connect(DB_NAME, timeout=60.0)
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    downloader = Downloader()

    try:
        while True:
            task = get_next_task(conn)
            if not task: break

            rowid, url, filename = task
            cursor = conn.cursor()

            # Determina o Content-Type para o Google Cloud Storage
            if filename.lower().endswith(('.html', '.htm')):
                c_type = "text/html"
                folder = "aneel/htmls"
            elif filename.lower().endswith('.zip'):
                c_type = "application/zip"
                folder = "aneel/zips"
            else:
                c_type = "application/pdf"
                folder = "aneel/pdfs"

            logger.info(f"📥 Worker {worker_id}: Baixando {filename}...")
            
            # --- DOWNLOAD ---
            _, content, erro_log = await downloader.download_file(url)

            # --- UPLOAD ---
            if content:
                try:
                    blob_name = f"{folder}/{filename}"
                    blob = bucket.blob(blob_name)
                    # Upload usando o content_type correto definido acima
                    blob.upload_from_string(content, content_type=c_type)
                    
                    cursor.execute("UPDATE arquivos SET status = 3, erro_log = NULL WHERE rowid = ?", (rowid,))
                    logger.success(f"✅ Worker {worker_id}: Sucesso - {filename}")
                except Exception as e:
                    logger.error(f"❌ Worker {worker_id}: Erro GCS - {e}")
                    cursor.execute("UPDATE arquivos SET status = 2, erro_log = ? WHERE rowid = ?", (f"Erro GCS: {str(e)[:50]}", rowid))
            else:
                logger.error(f"❌ Worker {worker_id}: Falha download - {erro_log}")
                novo_status = 4 if "404" in (erro_log or "") else 2
                cursor.execute("UPDATE arquivos SET status = ?, erro_log = ? WHERE rowid = ?", (novo_status, erro_log, rowid))

            conn.commit()
            
    finally:
        await downloader.close()
        conn.close()

def run_worker(worker_id: int):
    asyncio.run(worker_loop(worker_id))

if __name__ == "__main__":
    migrar.migrar("resource/2016.json")
    migrar.migrar("resource/2021json")
    migrar.migrar("resource/2022.json")

    print("🚀 Iniciando Motor (PDF + HTML + ZIP) Multi-Processos...")
    try:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(run_worker, i) for i in range(MAX_WORKERS)]
            for future in futures:
                future.result() 
        print("\n🛑 Processamento finalizado.")
    except KeyboardInterrupt:
        print("\n🛑 Parada manual.")

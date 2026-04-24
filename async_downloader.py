import sqlite3
import asyncio
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from curl_cffi.requests import AsyncSession
from loguru import logger
from typing import Optional, Tuple
from google.cloud import storage

# --- 1. CONFIGURAÇÕES ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "chave.json"
DB_NAME = "controle_downloads.db"
BUCKET_NAME = "dados_bruto_nlp"
MAX_WORKERS = 15 

# --- 2. CLASSE DE DOWNLOAD ---
class AsyncPDFDownloader:
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> AsyncSession:
        current_loop = asyncio.get_running_loop()
        async with self._lock:
            if self._session is None or self._session.loop != current_loop:
                if self._session:
                    try: await self._session.close()
                    except: pass
                self._session = AsyncSession(impersonate="chrome120", verify=False)
            return self._session

    async def close(self):
        async with self._lock:
            if self._session:
                await self._session.close()
                self._session = None

    async def download_file(self, url: str) -> Tuple[str, Optional[bytes], Optional[str]]:
        # Limpeza de URL (Removendo espaços e garantindo https)
        url = url.strip().replace("http://", "https://")
        
        await asyncio.sleep(random.uniform(0.3, 1.0))

        for attempt in range(3):
            try:
                session = await self.get_session()
                # Aumentei o timeout para 60 para aguentar HTMLs maiores ou ZIPs
                resp = await session.get(url, timeout=60, allow_redirects=True)
                
                if resp.status_code == 200:
                    return url, resp.content, None
                
                if resp.status_code == 404:
                    return url, None, "Erro 404"
                
                await asyncio.sleep(2 ** (attempt + 1))
            except Exception as e:
                logger.error(f"Erro inesperado {url}: {e}")
                await asyncio.sleep(2)

        return url, None, "Falha definitiva"

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
    downloader = AsyncPDFDownloader()

    try:
        while True:
            task = get_next_task(conn)
            if not task: break

            rowid, url, filename = task
            cursor = conn.cursor()

            # --- NOVO FILTRO DE EXTENSÃO ---
            # Removido o pulo de HTML. Agora ele só pula o arquivo específico que você pediu.
            if filename.lower().endswith('aprt20164000_1.pdf'):
                logger.info(f"⏩ Worker {worker_id}: Pulando arquivo bloqueado {filename}")
                cursor.execute("UPDATE arquivos SET status = 4 WHERE rowid = ?", (rowid,))
                conn.commit()
                continue

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
    print("🚀 Iniciando Motor (PDF + HTML + ZIP) Multi-Processos...")
    try:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(run_worker, i) for i in range(MAX_WORKERS)]
            for future in futures:
                future.result() 
        print("\n🛑 Processamento finalizado.")
    except KeyboardInterrupt:
        print("\n🛑 Parada manual.")
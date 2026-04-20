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
MAX_WORKERS = 10  # Número de processos em paralelo

# --- 2. CLASSE DE DOWNLOAD (Sua versão adaptada) ---
class AsyncPDFDownloader:
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> AsyncSession:
        current_loop = asyncio.get_running_loop()
        
        async with self._lock:
            if self._session is None or self._session.loop != current_loop:
                if self._session:
                    try:
                        await self._session.close()
                    except:
                        pass
                
                self._session = AsyncSession(impersonate="chrome120", verify=False)
            return self._session

    async def close(self):
        async with self._lock:
            if self._session:
                await self._session.close()
                self._session = None

    async def download_pdf(self, url: str) -> Tuple[str, Optional[bytes], Optional[str]]:
        url = url.replace("http://", "https://")
        
        # Delay leve para simular humano e evitar Rate Limit
        await asyncio.sleep(random.uniform(0.5, 1.5))

        for attempt in range(3):
            try:
                session = await self.get_session()
                resp = await session.get(url, timeout=30, allow_redirects=True)
                
                if resp.status_code == 200:
                    return url, resp.content, None
                
                if resp.status_code == 404:
                    return url, None, "Erro 404 - Not Found"
                    
                if resp.status_code == 403:
                    logger.warning(f"403 Forbidden em {url}. Backoff tentativa {attempt+1}...")
                else:
                    logger.warning(f"Erro {resp.status_code} em {url} na tentativa {attempt+1}")
                
                await asyncio.sleep(2 ** (attempt + 1))
                
            except Exception as e:
                logger.error(f"Erro inesperado {url}: {e}")
                await asyncio.sleep(2)

        return url, None, "Falha definitiva após 3 tentativas"

# --- 3. FUNÇÕES DO WORKER (Rodam em paralelo) ---
def get_next_task(conn) -> Optional[Tuple]:
    """Busca o próximo arquivo no DB e o marca como 'em andamento' (status 1) de forma segura."""
    cursor = conn.cursor()
    while True:
        try:
            # BEGIN IMMEDIATE trava o banco para escrita momentaneamente, evitando que 2 workers peguem a mesma linha
            conn.execute("BEGIN IMMEDIATE")
            cursor.execute("SELECT rowid, url, nome_arquivo FROM arquivos WHERE status IN (0, 2) LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                cursor.execute("UPDATE arquivos SET status = 1 WHERE rowid = ?", (row[0],))
            
            conn.commit()
            return row
        except sqlite3.OperationalError as e:
            # Se o banco estiver travado por outro worker, espera uma fração de segundo e tenta de novo
            if "locked" in str(e):
                time.sleep(random.uniform(0.05, 0.2))
            else:
                conn.rollback()
                raise

async def worker_loop(worker_id: int):
    """Loop principal de cada processo paralelo."""
    logger.info(f"👷 Worker {worker_id} iniciado!")
    
    # Cada processo precisa de sua própria conexão com o DB e GCS
    conn = sqlite3.connect(DB_NAME, timeout=60.0)
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    downloader = AsyncPDFDownloader()

    try:
        while True:
            task = get_next_task(conn)
            if not task:
                logger.info(f"🎉 Worker {worker_id}: Fim da fila!")
                break

            rowid, url, filename = task
            cursor = conn.cursor()

            # --- FILTRO DE HTML/PULAR ---
            if filename.lower().endswith(('.html', '.htm')) or filename.lower().endswith('aprt20164000_1.pdf'):
                logger.info(f"⏩ Worker {worker_id}: Pulando {filename}")
                cursor.execute("UPDATE arquivos SET status = 4 WHERE rowid = ?", (rowid,))
                conn.commit()
                continue

            logger.info(f"📥 Worker {worker_id}: Baixando {filename}...")
            
            # --- DOWNLOAD ---
            _, content, erro_log = await downloader.download_pdf(url)

            # --- UPLOAD PARA O BUCKET E ATUALIZAÇÃO DO DB ---
            if content:
                try:
                    # Faz o upload DIRETAMENTE da memória (bytes) para o GCP. Muito mais rápido!
                    blob_name = f"aneel/pdfs/{filename}"
                    blob = bucket.blob(blob_name)
                    blob.upload_from_string(content, content_type="application/pdf")
                    
                    cursor.execute("UPDATE arquivos SET status = 3, erro_log = NULL WHERE rowid = ?", (rowid,))
                    logger.success(f"✅ Worker {worker_id}: Sucesso - {filename}")
                except Exception as e:
                    logger.error(f"❌ Worker {worker_id}: Erro no upload do GCS - {e}")
                    cursor.execute("UPDATE arquivos SET status = 2, erro_log = ? WHERE rowid = ?", (f"Erro GCS: {str(e)[:50]}", rowid))
            else:
                logger.error(f"❌ Worker {worker_id}: Falha no download - {erro_log}")
                # Status 4 se for 404, senão status 2 (Erro)
                novo_status = 4 if "404" in (erro_log or "") else 2
                cursor.execute("UPDATE arquivos SET status = ?, erro_log = ? WHERE rowid = ?", (novo_status, erro_log, rowid))

            conn.commit()
            
    except Exception as e:
        logger.error(f"⚠️ Worker {worker_id} falhou criticamente: {e}")
    finally:
        await downloader.close()
        conn.close()

def run_worker(worker_id: int):
    """Função ponte para iniciar o asyncio dentro de um processo do ProcessPoolExecutor."""
    asyncio.run(worker_loop(worker_id))

# --- 4. MOTOR PRINCIPAL ---
if __name__ == "__main__":
    print("🚀 Iniciando Motor Multi-Processos (curl_cffi + GCS Direto)...")
    
    try:
        # Cria um pool com 10 processos independentes
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Dispara os 10 workers, passando um ID (de 0 a 9) para cada um
            futures = [executor.submit(run_worker, i) for i in range(MAX_WORKERS)]
            
            # Aguarda todos terminarem
            for future in futures:
                future.result() 
                
        print("\n🛑 Processamento finalizado com sucesso.")
    except KeyboardInterrupt:
        print("\n🛑 Parada manual solicitada pelo usuário.")
import os
import json
import sqlite3
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from google.cloud import storage
from qdrant_client.models import PointStruct
import uuid

from embedder import Embedder
from vector_db import VectorDB

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT_DIR, "controle_downloads.db")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(ROOT_DIR, "chave.json")

BUCKET_NAME = "dados_bruto_nlp"

STATUS_CHUNKEADO = 8
STATUS_EMBEDDANDO = 10
STATUS_EMBEDDADO = 11
STATUS_ERRO_EMBEDDING = 12

def process_single_file(arq_info, embedder, vector_db):
    arquivo_id, nome_arquivo, ano = arq_info
    nome_jsonl = nome_arquivo.replace(".pdf", ".jsonl")
    blob_path = f"aneel/chunks/{ano}/{nome_jsonl}"
    
    for _ in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("UPDATE arquivos SET status = ? WHERE id = ?", (STATUS_EMBEDDANDO, arquivo_id))
            conn.commit()
            conn.close()
            break
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                import time
                import random
                time.sleep(random.uniform(0.1, 0.5))
                continue
            raise e
    else:
        logger.error(f"Não foi possível desbloquear o banco para o arquivo {nome_arquivo}")
        return False

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)
        
        if not blob.exists():
            logger.error(f"Arquivo {blob_path} não encontrado no GCP.")
            return False
            
        content = blob.download_as_string().decode("utf-8")
        
        chunks = []
        for line in content.splitlines():
            if line.strip():
                chunks.append(json.loads(line))
        
        if not chunks:
            logger.warning(f"Arquivo {nome_jsonl} está vazio.")
            return True

        texts = [c["texto"] for c in chunks]
        embeddings = embedder.get_embeddings(texts)
        
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{nome_arquivo}_{i}"))
            
            payload = {
                "nome_arquivo": nome_arquivo,
                "texto": chunk["texto"],
                "ano": str(chunk.get("ano", ano)),
                "chunk_index": i
            }
            
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        if vector_db.upsert_chunks(points):
            for _ in range(5):
                try:
                    conn = sqlite3.connect(DB_PATH, timeout=30.0)
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("UPDATE arquivos SET status = ? WHERE id = ?", (STATUS_EMBEDDADO, arquivo_id))
                    conn.commit()
                    conn.close()
                    break
                except sqlite3.OperationalError as e:
                    if "locked" in str(e):
                        import time
                        import random
                        time.sleep(random.uniform(0.1, 0.5))
                        continue
                    raise e
            return True
        else:
            raise Exception("Falha no Upsert do Qdrant")

    except Exception as e:
        logger.error(f"❌ Erro ao processar embeddings de {nome_arquivo}: {e}")

        for _ in range(5):
            try:
                conn = sqlite3.connect(DB_PATH, timeout=30.0)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("UPDATE arquivos SET status = ? WHERE id = ?", (STATUS_ERRO_EMBEDDING, arquivo_id))
                conn.commit()
                conn.close()
                break
            except:
                import time
                time.sleep(0.2)
        return False

def main():
    parser = argparse.ArgumentParser(description="Pipeline de Embedding e Carga no Qdrant")
    parser.add_argument("--limit", type=int, default=None, help="Limita o número de arquivos para teste.")
    parser.add_argument("--workers", type=int, default=10, help="Número de threads simultâneas.")
    args = parser.parse_args()

    logger.info("🎬 Iniciando Pipeline de Embedding...")
    
    embedder = Embedder()
    vector_db = VectorDB()
    vector_db.ensure_collection()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"SELECT id, nome_arquivo, ano FROM arquivos WHERE status = {STATUS_CHUNKEADO}"

    if args.limit:
        query += f" LIMIT {args.limit}"
    
    cursor.execute(query)
    arquivos_pendentes = cursor.fetchall()
    conn.close()

    if not arquivos_pendentes:
        logger.success("✅ Nenhum arquivo pendente de embedding!")
        return

    logger.info(f"📋 Encontrados {len(arquivos_pendentes)} arquivos para processar.")

    sucessos = 0
    erros = 0
    total_geral = len(arquivos_pendentes)
    
    MICRO_BATCH = 50
    COOLDOWN_BATCH = 500
    
    for i in range(0, total_geral, COOLDOWN_BATCH):
        bloco_500 = arquivos_pendentes[i : i + COOLDOWN_BATCH]
        
        logger.info(f"📦 Iniciando Grande Bloco: {i+1} até {min(i + COOLDOWN_BATCH, total_geral)}")

        for j in range(0, len(bloco_500), MICRO_BATCH):
            sub_lote = bloco_500[j : j + MICRO_BATCH]
            
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = {executor.submit(process_single_file, arq, embedder, vector_db): arq for arq in sub_lote}
                for future in as_completed(futures):
                    if future.result():
                        sucessos += 1
                    else:
                        erros += 1
            
            logger.info(f"🚀 Sub-lote concluído ({j + len(sub_lote)}/{len(bloco_500)}) | Total: {sucessos + erros}/{total_geral}")
            
            if j + MICRO_BATCH < len(bloco_500):
                time.sleep(5)

        if i + COOLDOWN_BATCH < total_geral:
            logger.warning(f"⏳ Bloco de 500 concluído. Pausando por 60s para resetar limites...")
            time.sleep(60)

    logger.success(f"🏁 Pipeline finalizado! Sucessos: {sucessos}, Erros: {erros}")

if __name__ == "__main__":
    main()

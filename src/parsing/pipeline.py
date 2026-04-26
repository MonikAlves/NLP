import sqlite3
import os
import sys
import time
import random
from concurrent.futures import ProcessPoolExecutor
from loguru import logger
from google.cloud import storage

# Caminhos absolutos — funciona independente de onde o script for rodado
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(ROOT_DIR, "chave.json")
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"
MAX_WORKERS = 16

# Importa módulos do mesmo pacote
sys.path.insert(0, os.path.dirname(__file__))
from extractor import extract_pages
from enricher import enrich_page
from chunker import chunk_pages

# Status usados na tabela arquivos
STATUS_BAIXADO = 3       # já no GCP, pronto para parsing
STATUS_PARSEANDO = 5     # worker reservou o arquivo
STATUS_PARSEADO = 6      # parsing concluído com sucesso
STATUS_ERRO_PARSE = 7    # erro durante parsing

# Filtro de ano (opcional): ex. python pipeline.py 2021
ANO_FILTRO = int(sys.argv[1]) if len(sys.argv) > 1 else None


# ---------------------------------------------------------------------------
# Controle de fila (mesmo padrão do async_downloader)
# ---------------------------------------------------------------------------

def get_next_task(conn, ano_filtro=None) -> tuple | None:
    """
    Pega o próximo arquivo com status=3 que ainda não foi parseado.
    Usa BEGIN IMMEDIATE para evitar que dois workers peguem o mesmo arquivo.
    Se ano_filtro for passado, processa apenas arquivos daquele ano.
    """
    cursor = conn.cursor()
    while True:
        try:
            conn.execute("BEGIN IMMEDIATE")
            if ano_filtro:
                cursor.execute("""
                    SELECT id, nome_arquivo, titulo, ementa, assunto, autor,
                           data_assinatura, data_publicacao, ano, situacao
                    FROM arquivos
                    WHERE status = ? AND ano = ?
                    LIMIT 1
                """, (STATUS_BAIXADO, ano_filtro))
            else:
                cursor.execute("""
                    SELECT id, nome_arquivo, titulo, ementa, assunto, autor,
                           data_assinatura, data_publicacao, ano, situacao
                    FROM arquivos
                    WHERE status = ?
                    LIMIT 1
                """, (STATUS_BAIXADO,))
            row = cursor.fetchone()
            if row:
                conn.execute(
                    "UPDATE arquivos SET status = ? WHERE id = ?",
                    (STATUS_PARSEANDO, row[0]),
                )
            conn.commit()
            return row
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                time.sleep(random.uniform(0.05, 0.2))
            else:
                conn.rollback()
                raise


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def save_chunks(conn, arquivo_id: int, chunks: list[dict]):
    """Insere todos os chunks de um arquivo no banco."""
    rows = []
    for c in chunks:
        rows.append((
            arquivo_id,
            c.get("nome_arquivo"),
            c.get("pagina"),
            c.get("chunk_index"),
            c.get("texto"),
            c.get("metodo"),           # método de extração (pymupdf/ocr/ocr_falhou)
            c.get("titulo"),
            c.get("ementa"),
            c.get("assunto"),
            c.get("autor"),
            c.get("data_assinatura"),
            c.get("data_publicacao"),
            c.get("ano"),
            c.get("situacao"),
            c.get("artigos"),
            c.get("paragrafos"),
            c.get("normas_ref"),
            c.get("valores_monetarios"),
            c.get("cnpj"),
            c.get("datas_no_texto"),
        ))

    conn.executemany("""
        INSERT INTO chunks (
            arquivo_id, nome_arquivo, pagina, chunk_index, texto,
            metodo_extracao, titulo, ementa, assunto, autor,
            data_assinatura, data_publicacao, ano, situacao,
            artigos, paragrafos, normas_ref, valores_monetarios, cnpj, datas_no_texto
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def worker_loop(worker_id: int, ano_filtro=None):
    """Loop principal de cada processo paralelo."""
    logger.info(f"🔧 Worker {worker_id} iniciado! (ano={ano_filtro or 'todos'})")

    conn = sqlite3.connect(DB_NAME, timeout=60.0)
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    try:
        while True:
            task = get_next_task(conn, ano_filtro)
            if not task:
                logger.info(f"✅ Worker {worker_id}: Fila vazia, encerrando.")
                break

            (arquivo_id, nome_arquivo, titulo, ementa, assunto, autor,
             data_assinatura, data_publicacao, ano, situacao) = task

            doc_metadata = {
                "nome_arquivo": nome_arquivo,
                "titulo": titulo,
                "ementa": ementa,
                "assunto": assunto,
                "autor": autor,
                "data_assinatura": data_assinatura,
                "data_publicacao": data_publicacao,
                "ano": ano,
                "situacao": situacao,
            }

            logger.info(f"📄 Worker {worker_id}: {nome_arquivo}")

            # 1. Baixa o PDF do GCP em memória (nunca salva em disco)
            try:
                blob = bucket.blob(f"aneel/pdfs/{nome_arquivo}")
                pdf_bytes = blob.download_as_bytes()
            except Exception as e:
                logger.error(f"❌ Worker {worker_id}: Erro ao baixar {nome_arquivo}: {e}")
                conn.execute(
                    "UPDATE arquivos SET status = ?, erro_log = ? WHERE id = ?",
                    (STATUS_ERRO_PARSE, f"Erro GCP: {str(e)[:100]}", arquivo_id),
                )
                conn.commit()
                continue

            # 2. Extrai páginas (PyMuPDF → OCR fallback)
            try:
                pages = extract_pages(pdf_bytes, nome_arquivo)
                if not pages:
                    raise ValueError("Nenhuma página extraída")
            except Exception as e:
                logger.error(f"❌ Worker {worker_id}: Erro na extração de {nome_arquivo}: {e}")
                conn.execute(
                    "UPDATE arquivos SET status = ?, erro_log = ? WHERE id = ?",
                    (STATUS_ERRO_PARSE, f"Erro extração: {str(e)[:100]}", arquivo_id),
                )
                conn.commit()
                continue

            # 3. Enriquece cada página (metadados do banco + Regex)
            enriched = [enrich_page(p, doc_metadata) for p in pages]

            # 4. Gera chunks
            chunks = chunk_pages(enriched)

            # 5. Salva no banco
            try:
                save_chunks(conn, arquivo_id, chunks)
                conn.execute(
                    "UPDATE arquivos SET status = ? WHERE id = ?",
                    (STATUS_PARSEADO, arquivo_id),
                )
                conn.commit()
                logger.success(
                    f"✅ Worker {worker_id}: {nome_arquivo} → "
                    f"{len(pages)} págs, {len(chunks)} chunks"
                )
            except Exception as e:
                logger.error(f"❌ Worker {worker_id}: Erro ao salvar chunks de {nome_arquivo}: {e}")
                conn.execute(
                    "UPDATE arquivos SET status = ?, erro_log = ? WHERE id = ?",
                    (STATUS_ERRO_PARSE, f"Erro save: {str(e)[:100]}", arquivo_id),
                )
                conn.commit()

    finally:
        conn.close()


def run_worker(args):
    """Ponto de entrada para cada processo (necessário para o ProcessPoolExecutor)."""
    worker_id, ano_filtro = args
    worker_loop(worker_id, ano_filtro)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    filtro_msg = f"ano={ANO_FILTRO}" if ANO_FILTRO else "todos os anos"
    print(f"🚀 Iniciando Pipeline de Parsing ({MAX_WORKERS} workers, {filtro_msg})...")
    print(f"📂 Banco: {DB_NAME}")
    try:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            args = [(i, ANO_FILTRO) for i in range(MAX_WORKERS)]
            futures = [executor.submit(run_worker, a) for a in args]
            for future in futures:
                future.result()
        print("\n🛑 Parsing finalizado.")
    except KeyboardInterrupt:
        print("\n🛑 Parada manual.")

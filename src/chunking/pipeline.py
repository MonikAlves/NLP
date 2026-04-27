import os
import json
import sqlite3
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from google.cloud import storage
from tenacity import retry, stop_after_attempt, wait_exponential

from parser import extract_metadata_and_text
from chunker import generate_chunks

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
cred_path = os.path.join(ROOT_DIR, "chave.json")
if os.path.exists(cred_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

DB_PATH = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"

STATUS_PARSEADO = 6     # Arquivo pronto para o chunking
STATUS_CHUNKEANDO = 7   # Em processamento de chunking (para evitar duplicidade caso tenhamos multiplas maquinas)
STATUS_CHUNKS_OK = 8    # Chunking concluído com sucesso
STATUS_CHUNKS_ERRO = 9  # Erro na etapa de chunking

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def update_db_status(arquivo_id: int, status: int, erro_log: str = None):
    """Atualiza o status do arquivo no banco de dados SQLite."""
    try:
        with sqlite3.connect(DB_PATH, timeout=60.0) as conn:
            if erro_log:
                conn.execute("UPDATE arquivos SET status = ?, erro_log = ? WHERE id = ?", (status, erro_log, arquivo_id))
            else:
                conn.execute("UPDATE arquivos SET status = ? WHERE id = ?", (status, arquivo_id))
            conn.commit()
    except Exception as e:
        logger.error(f"Erro ao atualizar status do arquivo {arquivo_id} para {status}: {e}")

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def download_and_process(nome_arquivo: str, ano: str) -> list[dict]:
    """Baixa o arquivo do GCP e gera os chunks (com retentativa automática)."""
    base_name = nome_arquivo.rsplit('.', 1)[0]
    md_filename = f"{base_name}.md"
    
    blob_path = f"aneel/markdowns/{ano}/{md_filename}"
    blob = bucket.blob(blob_path)
    
    if not blob.exists():
        blob_path = f"aneel/markdowns/{md_filename}"
        blob = bucket.blob(blob_path)
        if not blob.exists():
            raise FileNotFoundError(f"Arquivo Markdown não encontrado no GCP: {md_filename}")
            
    content = blob.download_as_string().decode("utf-8")
    metadata, clean_text = extract_metadata_and_text(content)
    
    if "nome_arquivo" not in metadata:
        metadata["nome_arquivo"] = nome_arquivo
    if "ano" not in metadata and ano:
        metadata["ano"] = ano
        
    return generate_chunks(clean_text, metadata)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def upload_chunks(ano: str, nome_arquivo: str, chunks: list[dict]):
    """Faz upload da lista de chunks como um arquivo .jsonl isolado no GCP (com retentativa automática)."""
    base_name = nome_arquivo.rsplit('.', 1)[0]
    
    ano_folder = ano if ano else "sem_ano"
    upload_path = f"aneel/chunks/{ano_folder}/{base_name}.jsonl"
    
    jsonl_content = ""
    for chunk in chunks:
        jsonl_content += json.dumps(chunk, ensure_ascii=False) + "\n"
        
    blob = bucket.blob(upload_path)
    blob.upload_from_string(jsonl_content, content_type="application/jsonl")

def process_single_file(arquivo) -> bool:
    """Orquestra o download, chunking e upload de um único arquivo."""
    arquivo_id, nome_arquivo, ano = arquivo
    
    update_db_status(arquivo_id, STATUS_CHUNKEANDO)
    
    try:
        chunks = download_and_process(nome_arquivo, ano)
        
        if chunks:
            upload_chunks(ano, nome_arquivo, chunks)
        
        update_db_status(arquivo_id, STATUS_CHUNKS_OK)
        return True
        
    except Exception as e:
        logger.error(f"❌ Falha persistente no arquivo {nome_arquivo}: {e}")
        update_db_status(arquivo_id, STATUS_CHUNKS_ERRO, f"Erro Chunking: {str(e)[:100]}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Pipeline de Chunking Resiliente (1-para-1) com SQLite e Retries")
    parser.add_argument("--limit", type=int, default=None, help="Limita o número de arquivos processados para testes.")
    parser.add_argument("--workers", type=int, default=50, help="Número de threads simultâneas.")
    args = parser.parse_args()

    logger.info("Iniciando pipeline de Chunking...")
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome_arquivo, ano FROM arquivos WHERE status = ?", (STATUS_PARSEADO,))
        arquivos_pendentes = cursor.fetchall()
        
    if not arquivos_pendentes:
        logger.success("Nenhum arquivo pendente de chunking! Todos estão processados ou com status diferente de 6.")
        return
        
    logger.info(f"Encontrados {len(arquivos_pendentes)} arquivos prontos para chunking (status=6).")
    
    if args.limit:
        logger.info(f"Limitando para processar apenas os {args.limit} primeiros arquivos.")
        arquivos_pendentes = arquivos_pendentes[:args.limit]
        
    sucessos = 0
    erros = 0
    total = len(arquivos_pendentes)
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_arq = {executor.submit(process_single_file, arq): arq for arq in arquivos_pendentes}
        
        for idx, future in enumerate(as_completed(future_to_arq), 1):
            if future.result():
                sucessos += 1
            else:
                erros += 1
                
            if idx % 100 == 0 or idx == total:
                logger.info(f"Progresso: {idx}/{total} (Sucesso: {sucessos} | Erros: {erros})")
                
    logger.success(f"Pipeline finalizado! Sucessos: {sucessos} | Erros: {erros}")

if __name__ == "__main__":
    main()

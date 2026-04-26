import sqlite3
import os
from google.cloud import storage
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Define a credencial do GCP se existir na raiz
cred_path = os.path.join(ROOT_DIR, "chave.json")
if os.path.exists(cred_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

DB_PATH = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"

def export_worker(arquivo):
    arquivo_id, nome_arquivo, ano = arquivo
    
    # Cada thread abre sua própria conexão com o SQLite (leitura apenas)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT texto 
        FROM chunks 
        WHERE arquivo_id = ? 
        ORDER BY pagina ASC, chunk_index ASC
    ''', (arquivo_id,))
    
    chunks = cursor.fetchall()
    conn.close()
    
    if not chunks:
        return
        
    # Constrói o texto completo em Markdown
    full_markdown = f"# Documento: {nome_arquivo}\nAno: {ano}\n\n"
    for (texto,) in chunks:
        full_markdown += texto + "\n\n"
        
    # Envia diretamente para o Cloud Storage
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        
        # Troca a extensão para .md
        base_name = nome_arquivo.rsplit('.', 1)[0]
        blob_path = f"aneel/markdowns/{ano}/{base_name}.md"
        
        blob = bucket.blob(blob_path)
        blob.upload_from_string(full_markdown, content_type="text/markdown")
        logger.success(f"✅ {nome_arquivo} → {blob_path}")
    except Exception as e:
        logger.error(f"❌ Erro ao exportar {nome_arquivo}: {e}")

def main():
    logger.info("📥 Conectando ao banco de dados para exportação...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome_arquivo, ano FROM arquivos WHERE status = 6")
    arquivos = cursor.fetchall()
    conn.close()
    
    total = len(arquivos)
    logger.info(f"🚀 Encontrados {total} arquivos parseados. Iniciando upload para o GCS...")
    
    # Usamos Threads porque o gargalo é o Upload via Internet (I/O Bound)
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(export_worker, arquivos)
        
    logger.info("🎉 Exportação de todos os Markdowns concluída com sucesso!")

if __name__ == "__main__":
    main()

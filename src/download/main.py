import sqlite3
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from google.cloud import storage

# --- 1. CONFIGURAÇÕES ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(ROOT_DIR, "chave.json")
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")
BUCKET_NAME = "dados_bruto_nlp"
DOWNLOAD_DIR = os.path.join(ROOT_DIR, "temp_pdfs")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# --- 2. CONFIGURAÇÃO DO NAVEGADOR ---
chrome_options = Options()
# chrome_options.add_argument("--headless") # Descomente para rodar sem janela
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True 
}
chrome_options.add_experimental_option("prefs", prefs)

def limpar_pasta_temp():
    for f in os.listdir(DOWNLOAD_DIR):
        try:
            os.remove(os.path.join(DOWNLOAD_DIR, f))
        except:
            pass

def processar_definitivo():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    conn = sqlite3.connect(DB_NAME)
    
    print("🚀 Motor iniciado. Monitorando integridade dos downloads...")

    while True:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, url, nome_arquivo FROM arquivos WHERE status IN (0, 2) LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            print("🎉 Fim da fila!")
            break

        rowid, url, filename = row
        
        # --- FILTRO DE HTML (PULA OS < 100 ARQUIVOS) ---
        if filename.lower().endswith('.html') or filename.lower().endswith('.htm') or filename.lower().endswith('aprt20164000_1.pdf'):
            print(f"⏩ Pulando HTM/L: {filename}")
            cursor.execute("UPDATE arquivos SET status = 4 WHERE rowid = ?", (rowid,))
            conn.commit()
            continue

        print(f"\n📥 Alvo: {filename}")
        limpar_pasta_temp()

        try:
            driver.get(url)
            
            # --- FILTRO 404 (Link quebrado no servidor) ---
            if "404.0 - Not Found" in driver.page_source or "404 - Not Found" in driver.page_source:
                print(f"⚠️ Erro 404: Arquivo não existe no servidor, pulando...")
                cursor.execute("UPDATE arquivos SET status = 4, erro_log = 'Erro 404' WHERE rowid = ?", (rowid,))
                conn.commit()
                continue
            
            file_path = None
            sucesso_download = False
            
            # Espera até 60 segundos
            for i in range(60):
                todos_arquivos = os.listdir(DOWNLOAD_DIR)
                
                # Critério de Integridade: Não pode ter extensões temporárias
                tem_temporario = any(
                    f.endswith('.crdownload') or 
                    f.endswith('.tmp') or 
                    f.endswith('.temp') or
                    '.com.google.Chrome' in f 
                    for f in todos_arquivos
                )
                
                # Filtra apenas o que é arquivo final
                arquivos_finais = [
                    f for f in todos_arquivos 
                    if not f.endswith('.crdownload') 
                    and not f.endswith('.tmp')
                    and not f.endswith('.temp')
                    and not f.startswith('.com.google')
                ]

                # SÓ SEGUE SE: Tiver arquivo final E não tiver nenhum temporário rodando
                if arquivos_finais and not tem_temporario:
                    temp_name = os.path.join(DOWNLOAD_DIR, arquivos_finais[0])
                    extensao_real = os.path.splitext(arquivos_finais[0])[1]
                    
                    # Garante que o nome no bucket seja consistente
                    nome_final = os.path.splitext(filename)[0] + extensao_real
                    file_path = os.path.join(DOWNLOAD_DIR, nome_final)
                    
                    os.rename(temp_name, file_path)
                    sucesso_download = True
                    break
                
                time.sleep(1)
                if i % 15 == 0 and i > 0:
                    print(f"   ...aguardando conclusão real ({i}s)")

            if sucesso_download and file_path:
                # Upload definitivo
                blob = bucket.blob(f"aneel/pdfs/{os.path.basename(file_path)}")
                blob.upload_from_filename(file_path)
                
                cursor.execute("UPDATE arquivos SET status = 3, erro_log = NULL WHERE rowid = ?", (rowid,))
                os.remove(file_path)
                print(f"✅ Sucesso íntegro: {os.path.basename(file_path)}")
            else:
                print(f"❌ Timeout: O arquivo não finalizou a tempo.")
                cursor.execute("UPDATE arquivos SET status = 2, erro_log = 'Timeout/Incompleto' WHERE rowid = ?", (rowid,))

        except Exception as e:
            print(f"⚠️ Erro: {str(e)[:50]}")
            cursor.execute("UPDATE arquivos SET status = 2, erro_log = ? WHERE rowid = ?", (str(e), rowid))
        
        conn.commit()
        time.sleep(random.uniform(1, 2))
    
    driver.quit()
    conn.close()

if __name__ == "__main__":
    try:
        processar_definitivo()
    except KeyboardInterrupt:
        print("\n🛑 Parada solicitada.")
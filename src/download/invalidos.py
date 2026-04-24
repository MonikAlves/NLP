import sqlite3
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def resetar_e_limpar_pdfs():
    # Conecta ao banco
    conn = sqlite3.connect(os.path.join(ROOT_DIR, 'controle_downloads.db'))
    cursor = conn.cursor()

    print("🔍 Iniciando limpeza e reset de PDFs com erro...")

    # O SQL faz tudo: 
    # 1. TRIM(url) remove espaços no início e fim
    # 2. SET status = 0 coloca de volta na fila
    # 3. Filtra apenas status 4 que sejam PDF
    cursor.execute("""
        UPDATE arquivos 
        SET 
            url = TRIM(url), 
            status = 0, 
            erro_log = NULL 
        WHERE 
            status = 4 
            AND url LIKE '%.pdf%'
    """)
    
    # OBS: Usei '%.pdf%' (com % no fim) para garantir que pegue 
    # URLs que tenham espaços ou parâmetros após o .pdf
    
    linhas_afetadas = cursor.rowcount
    conn.commit()
    conn.close()

    if linhas_afetadas > 0:
        print(f"✅ Sucesso: {linhas_afetadas} PDFs foram limpos e voltaram para a fila (status 0).")
    else:
        print("ℹ️ Nenhum PDF com status 4 encontrado para resetar.")

if __name__ == "__main__":
    resetar_e_limpar_pdfs()
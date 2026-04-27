import sqlite3
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def resetar_e_limpar_pdfs():
    conn = sqlite3.connect(os.path.join(ROOT_DIR, 'controle_downloads.db'))
    cursor = conn.cursor()

    print("🔍 Iniciando limpeza e reset de PDFs com erro...")

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
    
    linhas_afetadas = cursor.rowcount
    conn.commit()
    conn.close()

    if linhas_afetadas > 0:
        print(f"✅ Sucesso: {linhas_afetadas} PDFs foram limpos e voltaram para a fila (status 0).")
    else:
        print("ℹ️ Nenhum PDF com status 4 encontrado para resetar.")

if __name__ == "__main__":
    resetar_e_limpar_pdfs()
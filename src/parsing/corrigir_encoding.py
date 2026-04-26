import sqlite3
import os
from loguru import logger
import ftfy

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT_DIR, "controle_downloads.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    logger.info("🔍 Buscando todos os textos no banco de dados...")
    cursor.execute("SELECT id, texto FROM chunks")
    rows = cursor.fetchall()
    
    updates = []
    logger.info(f"⚙️ Analisando {len(rows)} blocos de texto para correção de encoding...")
    
    for row_id, texto in rows:
        if not texto: continue
        
        # A mágica acontece aqui: o ftfy detecta mojibake e arruma
        texto_corrigido = ftfy.fix_text(texto)
        
        # Só atualiza se realmente mudou algo
        if texto_corrigido != texto:
            updates.append((texto_corrigido, row_id))
            
    if updates:
        logger.info(f"⏳ Aplicando correção em {len(updates)} blocos. Isso pode levar um minutinho...")
        # Atualiza em lote para ser super rápido
        cursor.executemany("UPDATE chunks SET texto = ? WHERE id = ?", updates)
        conn.commit()
        logger.success(f"✅ Sucesso! {len(updates)} textos foram consertados no banco.")
    else:
        logger.info("👍 Nenhum texto precisava de correção.")
        
    conn.close()

if __name__ == "__main__":
    main()

import sqlite3

def corrigir_protocolos():
    # Conectar ao banco
    conn = sqlite3.connect('controle_downloads.db')
    cursor = conn.cursor()

    print("🔍 Analisando banco de dados...")

    # 1. Conta quantos serão afetados para te dar um feedback
    cursor.execute("SELECT COUNT(*) FROM arquivos WHERE url LIKE 'http://%'")
    total_http = cursor.fetchone()[0]

    if total_http == 0:
        print("✅ Nenhuma URL com 'http://' encontrada. Tudo limpo!")
        conn.close()
        return

    print(f"found {total_http} URLs com protocolo inseguro. Corrigindo...")

    # 2. Executa o UPDATE usando lógica de string do SQLite
    # SUBSTR(url, 8) remove os 7 caracteres de 'http://' e concatena com 'https://'
    # Isso garante que não mexeremos em 'http' que apareça no meio da URL por erro
    cursor.execute("""
        UPDATE arquivos 
        SET 
            url = 'https://' || SUBSTR(url, 8),
            status = 0,
            erro_log = NULL
        WHERE 
            url LIKE 'http://%'
            AND status IN (4)
    """)

    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()

    print("-" * 30)
    print(f"🚀 SUCESSO!")
    print(f"🔄 URLs convertidas: {rows_affected}")
    print(f"📥 Status resetado para 0 (fila de download)")
    print("-" * 30)

if __name__ == "__main__":
    corrigir_protocolos()
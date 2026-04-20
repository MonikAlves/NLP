import sqlite3

conn = sqlite3.connect('controle_downloads.db')
cursor = conn.cursor()

# Usamos LIKE '%404%' para garantir que pegamos qualquer variação de erro 404
# E fazemos o UPDATE diretamente no SQL para performance máxima
cursor.execute("""
    UPDATE arquivos 
    SET 
        url = REPLACE(url, 'http://', 'https://'),
        status = 0,
        erro_log = NULL
    WHERE 
        status = 4 
""")

rows_affected = cursor.rowcount
conn.commit()
conn.close()

if rows_affected > 0:
    print(f"✅ {rows_affected} URLs corrigidas (HTTP -> HTTPS) e resetadas para status 0!")
else:
    print("⚠️ Nenhum registro encontrado com status 4 e erro contendo '404'.")
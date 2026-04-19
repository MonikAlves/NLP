import sqlite3

conn = sqlite3.connect('controle_downloads.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT rowid, url 
    FROM arquivos 
    WHERE status = 4 AND erro_log = 'Erro 404'
""")

registros = cursor.fetchall()
a =0
for rowid, url in registros:
    if url.startswith("http://"):
        nova_url = url.replace("http://", "https://", 1)

        cursor.execute("""
            UPDATE arquivos 
            SET url = ?, status = 0, erro_log = NULL
            WHERE rowid = ?
        """, (nova_url, rowid))
        a = a+1
        print(f"🔄 {url} -> {nova_url} | status resetado")

conn.commit()
conn.close()

print(f"✅ {a} URLs corrigidas e prontas para retry!")
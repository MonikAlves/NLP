import json
import sqlite3

def migrar():
    # 1. Carregar o arquivo JSON
    with open('dado.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # 2. Conectar ao SQLite (vai criar o arquivo se não existir)
    conn = sqlite3.connect('controle_downloads.db')
    cursor = conn.cursor()

    # 3. Criar a tabela com a estrutura otimizada
    # status: 0=nada, 1=progresso, 2=erro, 3=baixado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_registro TEXT,
            titulo TEXT,
            url TEXT UNIQUE,
            nome_arquivo TEXT,
            status INTEGER DEFAULT 0,
            tentativas INTEGER DEFAULT 0,
            erro_log TEXT
        )
    ''')

    registros_inseridos = 0

    # 4. Iterar sobre o JSON e inserir no banco
    for data, conteudo in dados.items():
        for registro in conteudo.get('registros', []):
            for pdf in registro.get('pdfs', []):
                try:
                    cursor.execute('''INSERT OR IGNORE INTO arquivos 
                        (data_registro, titulo, url, nome_arquivo, status)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        data,
                        registro.get('titulo'),
                        pdf.get('url'),
                        pdf.get('arquivo'),
                        0 # status inicial
                    ))
                    if cursor.rowcount > 0:
                        registros_inseridos += 1
                except Exception as e:
                    print(f"Erro ao inserir {pdf.get('arquivo')}: {e}")

    conn.commit()
    conn.close()
    print(f"Migração concluída! {registros_inseridos} novos arquivos prontos para processamento.")

if __name__ == "__main__":
    migrar()

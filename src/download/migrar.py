import json
import sqlite3
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def limpar_campo(valor):
    if not valor:
        return None
    if ':' in valor:
        return valor.split(':', 1)[1].strip()
    return valor.strip()

def migrar():
    # 1. Carregar o arquivo JSON (aceita caminho via argumento ou usa dado.json)
    json_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT_DIR, 'dado.json')
    print(f"📂 Lendo {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # 2. Conectar ao SQLite (vai criar o arquivo se não existir)
    conn = sqlite3.connect(os.path.join(ROOT_DIR, 'controle_downloads.db'))
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
            erro_log TEXT,
            ano INTEGER,
            numeracao_item TEXT,
            autor TEXT,
            material TEXT,
            esfera TEXT,
            situacao TEXT,
            assinatura TEXT,
            publicacao TEXT,
            assunto TEXT,
            ementa TEXT
        )
    ''')

    registros_inseridos = 0

    # 4. Iterar sobre o JSON e inserir no banco
    for data, conteudo in dados.items():
        for registro in conteudo.get('registros', []):
            for pdf in registro.get('pdfs', []):
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO arquivos (
                            data_registro, titulo, url, nome_arquivo, status,
                            ano, numeracao_item, autor, material, esfera,
                            situacao, data_assinatura, data_publicacao, assunto, ementa
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data,
                        registro.get('titulo'),
                        pdf.get('url'),
                        pdf.get('arquivo'),
                        0,
                        int(data[:4]),
                        registro.get('numeracaoItem'),
                        registro.get('autor'),
                        registro.get('material'),
                        limpar_campo(registro.get('esfera')),
                        limpar_campo(registro.get('situacao')),
                        limpar_campo(registro.get('assinatura')),
                        limpar_campo(registro.get('publicacao')),
                        limpar_campo(registro.get('assunto')),
                        registro.get('ementa')
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

import sqlite3
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")


def criar_tabela_chunks():
    conn = sqlite3.connect(DB_NAME)

    # Adiciona colunas faltantes na tabela arquivos (se não existirem)
    colunas_novas = [
        ("ementa", "TEXT"),
        ("assunto", "TEXT"),
        ("autor", "TEXT"),
        ("material", "TEXT"),
        ("esfera", "TEXT"),
        ("situacao", "TEXT"),
        ("data_assinatura", "TEXT"),
        ("data_publicacao", "TEXT"),
    ]
    for col, tipo in colunas_novas:
        try:
            conn.execute(f"ALTER TABLE arquivos ADD COLUMN {col} {tipo}")
            print(f"  ✅ Coluna '{col}' adicionada à tabela arquivos.")
        except Exception:
            pass  # já existe

    # Cria tabela de chunks
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_id INTEGER,
            nome_arquivo TEXT,
            pagina INTEGER,
            chunk_index INTEGER,
            texto TEXT,
            metodo_extracao TEXT,
            titulo TEXT,
            ementa TEXT,
            assunto TEXT,
            autor TEXT,
            data_assinatura TEXT,
            data_publicacao TEXT,
            ano INTEGER,
            situacao TEXT,
            artigos TEXT,
            paragrafos TEXT,
            normas_ref TEXT,
            valores_monetarios TEXT,
            cnpj TEXT,
            datas_no_texto TEXT,
            status INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Tabela 'chunks' criada (ou já existia).")
    print("✅ Migração concluída.")


if __name__ == "__main__":
    criar_tabela_chunks()

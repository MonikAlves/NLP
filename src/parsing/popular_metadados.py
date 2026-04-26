import json
import sqlite3
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_NAME = os.path.join(ROOT_DIR, "controle_downloads.db")

# Aceita caminho do JSON como argumento; padrão = dado.json na raiz
JSON_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT_DIR, "dado.json")


def limpar_campo(valor: str | None) -> str | None:
    """Remove prefixos como 'Assunto:', 'Situação:' dos campos do JSON."""
    if not valor:
        return None
    if ":" in valor:
        return valor.split(":", 1)[1].strip()
    return valor.strip()


def popular_metadados():
    print(f"📂 Lendo {JSON_PATH}...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        dados = json.load(f)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    atualizados = 0
    erros = 0
    total = 0

    print("🔄 Atualizando metadados no banco...")

    for data_registro, conteudo in dados.items():
        for registro in conteudo.get("registros", []):
            ementa         = registro.get("ementa")
            assunto        = limpar_campo(registro.get("assunto"))
            autor          = registro.get("autor")
            material       = registro.get("material")
            esfera         = limpar_campo(registro.get("esfera"))
            situacao       = limpar_campo(registro.get("situacao"))
            data_assinatura = limpar_campo(registro.get("assinatura"))
            data_publicacao = limpar_campo(registro.get("publicacao"))

            for pdf in registro.get("pdfs", []):
                url = pdf.get("url")
                if not url:
                    continue
                total += 1
                try:
                    cursor.execute("""
                        UPDATE arquivos
                        SET
                            ementa          = ?,
                            assunto         = ?,
                            autor           = ?,
                            material        = ?,
                            esfera          = ?,
                            situacao        = ?,
                            data_assinatura = ?,
                            data_publicacao = ?
                        WHERE url = ?
                    """, (
                        ementa, assunto, autor, material,
                        esfera, situacao, data_assinatura, data_publicacao,
                        url,
                    ))
                    if cursor.rowcount > 0:
                        atualizados += 1
                except Exception as e:
                    print(f"  ⚠️ Erro em {url}: {e}")
                    erros += 1

    conn.commit()
    conn.close()

    print(f"\n✅ Concluído!")
    print(f"   Total no JSON:   {total}")
    print(f"   Atualizados:     {atualizados}")
    print(f"   Sem match no DB: {total - atualizados - erros}")
    print(f"   Erros:           {erros}")


if __name__ == "__main__":
    popular_metadados()

import sqlite3
import time
import os

def conferir_status():
    conn = sqlite3.connect('controle_downloads.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM arquivos")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM arquivos WHERE status = 0")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM arquivos WHERE status = 2")
    erros = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM arquivos WHERE status = 3")
    concluidos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM arquivos WHERE status = 1")
    processando = cursor.fetchone()[0]

    conn.close()

    return total, pendentes, erros, concluidos, processando


def limpar_tela():
    os.system('clear')  # Linux (sua VM)


def monitorar():
    while True:
        total, pendentes, erros, concluidos, processando = conferir_status()

        limpar_tela()

        print("-" * 30)
        print("📊 RESUMO DO BANCO DE DADOS")
        print("-" * 30)
        print(f"✅ Concluídos:   {concluidos}")
        print(f"⏳ Pendentes:     {pendentes}")
        print(f"❌ Erros:         {erros}")
        print(f"🔄 Processando:   {processando}")
        print("-" * 30)
        print(f"📦 Total Geral:   {total}")

        if total > 0:
            progresso = (concluidos / total) * 100
            print(f"📈 Progresso:     {progresso:.2f}%")

        print("-" * 30)
        print("🔄 Atualizando em 5 segundos...")

        time.sleep(5)


if __name__ == "__main__":
    monitorar()
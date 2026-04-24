import sqlite3
import time
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def conferir_status():
    conn = sqlite3.connect(os.path.join(ROOT_DIR, 'controle_downloads.db'))
    cursor = conn.cursor()

    query = """
    SELECT 
        IFNULL(ano, 'Sem Ano') as ano_ref,
        COUNT(*) as total,
        SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pendentes,
        SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as processando,
        SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as erros,
        SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) as concluidos,
        SUM(CASE WHEN status = 4 THEN 1 ELSE 0 END) as invalidos
    FROM arquivos
    GROUP BY ano_ref
    ORDER BY ano_ref DESC
    """
    
    try:
        cursor.execute(query)
        resumo = cursor.fetchall()
    except sqlite3.OperationalError:
        resumo = []
    
    conn.close()
    return resumo

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def monitorar():
    while True:
        resumo = conferir_status()
        limpar_tela()

        # --- CÁLCULOS TOTAIS ---
        total_v = sum(row[1] for row in resumo)
        concluidos_v = sum(row[5] for row in resumo)

        print("-" * 40)
        print("🌍 RESUMO TOTAL (TODOS OS ANOS)")
        print("-" * 40)
        print(f"📦 Total Geral:   {total_v}")
        print(f"✅ Concluídos:    {concluidos_v}")
        if total_v > 0:
            prog_g = (concluidos_v / total_v) * 100
            print(f"📈 Progresso:     {prog_g:.2f}%")
        print("-" * 40)

        # --- DETALHAMENTO POR ANO ---
        for ano_data in resumo:
            ano, total, pend, proc, err, ok, inv = ano_data
            
            # Cálculo de porcentagem do ano específico
            prog_ano = (ok / total * 100) if total > 0 else 0
            
            print(f"\n📅 ANO: {ano}")
            print(f"📈 Progresso:     {prog_ano:.2f}%")
            print(f"✅ Concluídos:     {ok}")
            print(f"⏳ Pendentes:      {pend}")
            print(f"❌ Erros:          {err}")
            print(f"❓ Inválidos:      {inv}")
            print(f"🔄 Processando:    {proc}")
            print(f"小 Total Ano:      {total}")
            print("." * 20)

        print(f"\n🔄 Atualizando em 1 segundos...")
        time.sleep(1)

if __name__ == "__main__":
    try:
        monitorar()
    except KeyboardInterrupt:
        print("\n👋 Monitoramento encerrado.")
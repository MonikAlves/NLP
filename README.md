# ANEEL Intelligence RAG System 🧠⚖️

Este projeto é um sistema de **RAG (Retrieval-Augmented Generation)** de larga escala projetado para processar, indexar e permitir buscas inteligentes em mais de 26.000 documentos da ANEEL (Agência Nacional de Energia Elétrica).

## 🚀 Estrutura do Projeto

O sistema é dividido em 4 etapas principais, localizadas na pasta `src/`:

1.  **Download**: Captura automatizada de PDFs e metadados do portal da ANEEL.
2.  **Parsing**: Conversão de PDFs/HTMLs para Markdown e geração de pedaços de texto (chunks).
3.  **Embedding**: Vetorização dos textos usando IA (OpenAI) e armazenamento no **Qdrant Cloud**.
4.  **Retrieval**: Motor de busca semântica para encontrar os trechos mais relevantes para qualquer pergunta.

---

## 🛠️ Pré-requisitos

*   **Python 3.10+**
*   **Contas e Chaves**:
    *   Google Cloud Platform (Bucket Storage)
    *   OpenAI API (Model: `text-embedding-3-small`)
    *   Qdrant Cloud (Cluster Vector Database)

---

## ⚙️ Configuração Inicial

### 1. Clonar e Instalar
```bash
git clone https://github.com/MonikAlves/NLP.git
cd NLP
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:
```ini
OPENAI_API_KEY=sua_chave_aqui
QDRANT_URL=sua_url_do_cluster
QDRANT_API_KEY=sua_chave_do_qdrant
```

### 3. Credenciais GCP
Coloque o arquivo `chave.json` (Service Account do Google Cloud) na raiz do projeto para permitir o acesso ao Bucket de arquivos.

---

## 🔌 Ordem de Execução (Passo a Passo)

### Passo 1: Download de Documentos
Sincroniza os metadados dos arquivos JSON e inicia o download via Selenium.
```bash
python src/download/pipeline.py
```
*O sistema gerencia automaticamente a integridade dos PDFs e faz o upload para o GCP.*

### Passo 2: Parsing e Chunking (GCP)
Transforma os PDFs brutos em arquivos `.jsonl` com o texto limpo e dividido. Este passo geralmente é executado em uma VM para alta performance.
```bash
python src/parsing/pipeline.py
```

### Passo 3: Geração de Embeddings
Esta é a etapa mais massiva. Ela lê os chunks do GCP, gera os vetores na OpenAI e salva no Qdrant Cloud.
```bash
python src/embedding/pipeline.py --workers 10
```
*Nota: O script possui um sistema de "cool-down" automático para não estourar o Rate Limit da OpenAI.*

### Passo 4: Busca Semântica (Retrieval)
Agora você pode fazer perguntas ao seu banco de dados!
```bash
python src/retrieval/retriever.py
```

---

## 🖥️ Gerenciamento da VM (GCP)

Se precisar rodar o processamento pesado na nuvem:

```bash
# Conectar na VM
gcloud compute ssh nlp-parser --zone=southamerica-east1-a

# Rodar processo em segundo plano (evita queda se a conexão cair)
screen -S embedding
python src/embedding/pipeline.py --workers 15
# Pressione Ctrl+A+D para sair do screen sem matar o processo
```

---

## 📊 Comandos de Monitoramento

*   **Verificar progresso no SQLite**:
    ```bash
    sqlite3 controle_downloads.db "SELECT status, COUNT(*) FROM arquivos GROUP BY status;"
    ```
*   **Verificar dados no Qdrant**:
    ```bash
    python src/embedding/checar_qdrant.py
    ```

---

## 📝 Legenda de Status (Banco de Dados)
*   `0`: Pendente
*   `3`: Download/Upload concluído
*   `6`: Markdown gerado
*   `8`: Pronto para Embedding
*   `11`: Processo completo (Indexado no Qdrant)

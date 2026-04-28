# ANEEL Intelligence RAG System 🧠⚖️

Este projeto é um sistema de **RAG (Retrieval-Augmented Generation)** de larga escala projetado para processar, indexar e permitir buscas inteligentes em mais de 26.000 documentos da ANEEL (Agência Nacional de Energia Elétrica).

## 🚀 Estrutura do Projeto

O sistema é dividido em 4 etapas principais, localizadas na pasta `src/`:

1.  **Download**: Captura automatizada de PDFs e metadados do portal da ANEEL.
2.  **Parsing**: Extração do conteúdo dos PDFs/HTMLs e conversão para Markdown.
3.  **Chunking**: Geração dos blocos de texto (chunks) a partir do Markdown dos arquivos.
4.  **Embedding**: Vetorização dos textos usando o modelo de embedding da OpenAI e armazenamento no **Qdrant Cloud**.
5.  **Retrieval**: Motor de busca semântica para encontrar os trechos mais relevantes para qualquer pergunta.

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
Coloque o arquivo `chave.json` (Service Account do Google Cloud) na raiz do projeto para permitir o acesso ao Bucket de arquivos, chamado de `dados_bruto_nlp`.

---

## 🔌 Ordem de Execução (Passo a Passo)

### Passo 1: Download de Documentos
Sincroniza os metadados dos arquivos JSON e inicia o download dos arquivos.
```bash
python src/download/pipeline.py
```

### Passo 2: Parsing
Transforma os PDFs/HTMLs brutos em arquivos `.jsonl` com o texto limpo no formato Markdown
```bash
python src/parsing/pipeline.py
```

### Passo 3: Chunking
Transforma os PDFs brutos em arquivos `.jsonl` com o texto limpo e dividido.
```bash
python src/parsing/pipeline.py --workers 20
```

### Passo 4: Geração de Embeddings
Esta é a etapa mais massiva. Ela lê os chunks do GCP, gera os vetores na OpenAI e salva no Qdrant Cloud.
```bash
python src/embedding/pipeline.py --workers 10
```

### Passo 5: Busca Semântica (Retrieval)
Agora você pode fazer perguntas ao seu banco de dados!
```bash
python src/retrieval/retriever.py
```

*Nota: Em cada etapa o sistema gerencia automaticamente a integridade dos arquivos e faz o upload para o GCP, mantendo uma arquitetura medalhão dos dados.*

---

## 🖥️ Execução na VM do Google Cloud (GCP)

Todas as etapas anteriores podem ser executadas localmente na máquina do usuário, entretanto é recomendável usar a VM do Google para acelerar a execução e diminuir a latência da rede. Para executar o processamento pesado na nuvem, basta:

1. iniciar uma instância da VM no Google na mesma região do bucket.
2. Executar todos os passos anteriores no Google Cloud Shell da VM.

## 📱 Aplicação

O sistema possui uma interface web para interação.

### Backend (API)

Para rodar o servidor backend, certifique-se de que o `.env` está configurado corretamente e o arquivo `chave.json` está na raiz.

```bash
cd src/backend
pip install -r requirements.txt
python main.py
```

O servidor estará disponível em `http://localhost:8000`. Você pode acessar a documentação interativa (Swagger) em `http://localhost:8000/docs`.

### Frontend

Para executar o front-end da aplicação, primeiro instalamos as dependências:

```bash
cd src/frontend
npm install
```

E para executar em modo de desenvolvimento:

```bash
npm run dev
```
#!/bin/bash
# 1. Prepara a máquina do Google
apt-get update && apt-get install -y python3-pip python3-venv git sqlite3

# 2. Baixa o código de vocês
git clone https://github.com/seu-usuario/meu-projeto-rag.git /opt/rag
cd /opt/rag

# 3. Cria o ambiente e instala as dependências corretas
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Inicia a Fase de Download
cd src/stage1_download

# O pulo do gato: baixar o dado.json de um bucket GCS para que o migrar.py funcione!
gsutil cp gs://seu-bucket-de-config/dado.json .

python3 migrar.py
python3 async_downloader.py

# 5. Inicia a Fase de Processamento (Que faremos a seguir)
# cd ../stage2_processing
# python3 pdf_to_json_parser.py

# Opcional: Desligar a máquina automaticamente quando terminar para não gerar custos!
shutdown -h now
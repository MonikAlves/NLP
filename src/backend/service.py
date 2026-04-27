from typing import Dict, Optional, List, Any
import os
import sys
from pathlib import Path
from openai import OpenAI

# Ajuste de path para importar módulos do src
root_path = str(Path(__file__).parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from src.retrieval.retriever import retrieve_context
from src.embedding.embedder import Embedder
from dotenv import load_dotenv

# Carrega variáveis do arquivo '.env' na raiz
load_dotenv(os.path.join(root_path, ".env"))

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("OPEN_ROUTER")
)
embedder = Embedder()

PROMPT_TEMPLATE = """
Você é um assistente especialista em documentos da ANEEL.
Use os contextos abaixo para responder à pergunta do usuário de forma precisa.
Se não souber a resposta com base no contexto, diga que não encontrou informações específicas.

Contextos:
{context_text}

Pergunta: {pergunta}
Resposta:
"""

def completion(pergunta: str, debug: bool = False) -> Dict[str, Any]:
    """
    Função principal de conversa que utiliza RAG.
    """
    # 1. Recuperar contexto (RAG)
    contextos = retrieve_context(pergunta, limit=5)
    
    # 2. Preparar o contexto para o prompt
    context_text = "\n\n".join([f"Documento: {c['file']}\nTrecho: {c['chunk']}" for c in contextos])
    
    # 3. Montar o prompt usando o template do cabeçalho
    prompt = PROMPT_TEMPLATE.format(context_text=context_text, pergunta=pergunta)

    # 4. Chamar a LLM via OpenRouter usando o modelo do .env
    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {"role": "system", "content": "Você é um assistente útil e preciso."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    resposta_final = response.choices[0].message.content

    # 5. Se debug for False, retorna apenas a resposta
    if not debug:
        return {"resposta": resposta_final}

    # 6. Se debug for True, monta o retorno detalhado
    # Obtém o embedding para o preview (6-7 primeiros valores)
    embedding_full = embedder.get_embeddings([pergunta])[0]
    embedding_preview = embedding_full[:7]

    # Formata os documentos do retriever conforme solicitado
    docs_retriever = []
    for c in contextos:
        docs_retriever.append({
            "id": c.get("id", "N/A"),
            "name": c.get("file", "N/A"),
            "score": round(c.get("score", 0), 4),
            "chunk": c.get("chunk", "")
        })

    return {
        "resposta": resposta_final,
        "debug": {
            "documentos_retriever": docs_retriever,
            "embedding_da_pergunta": {
                "embedding_preview": embedding_preview,
                "dimension": len(embedding_full)
            }
        }
    }

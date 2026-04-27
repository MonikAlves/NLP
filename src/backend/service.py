from typing import Dict, Optional, List, Any
import os
import sys
from pathlib import Path
from openai import OpenAI

# Ajuste de path para importar módulos do src
root_path = str(Path(__file__).parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

# Agora importa tudo do novo arquivo unificado dentro da pasta do backend
from retrieval.retriever import retrieve_context, Embedder
from dotenv import load_dotenv

# Carrega variáveis do arquivo '.env' na raiz
load_dotenv(os.path.join(root_path, ".env"))

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("OPEN_ROUTER")
)
embedder = Embedder()

PROMPT_TEMPLATE = """
Você é um Assistente Especialista em Regulação da ANEEL (Agência Nacional de Energia Elétrica).
Seu objetivo é analisar perguntas de usuários e fornecer respostas precisas, claras e fundamentadas exclusivamente nos documentos oficiais fornecidos no contexto.

DIRETRIZES FUNDAMENTAIS (Siga rigorosamente):
1. ANCORAGEM NO CONTEXTO: Baseie sua resposta **estritamente** nos trechos de contexto fornecidos abaixo. Não utilize conhecimentos prévios externos, não especule e não invente dados (zero alucinação).
2. TRATAMENTO DE INFORMAÇÃO AUSENTE: Se o contexto fornecido não contiver as informações necessárias para responder à pergunta de forma completa ou parcial, declare honestamente: "Com base nos documentos recuperados, não encontrei informações específicas para responder a esta pergunta." Não tente preencher lacunas com informações de fora.
3. CITAÇÃO DE FONTES: Para cada afirmação de impacto ou regra regulatória citada, faça referência direta ao documento de origem (utilize a tag 'Documento:' fornecida nos contextos).
4. CLAREZA TÉCNICA: Os documentos da ANEEL (Resoluções, Módulos do PRODIST, etc.) costumam ser densos. Traduza a linguagem técnica governamental para uma resposta compreensível e direta, mas sem perder a precisão jurídica/regulatória.
5. ESTRUTURA E FORMATAÇÃO: 
   - Utilize formatação em Markdown.
   - Destaque termos técnicos ou prazos importantes em **negrito**.
   - Use listas (bullet points) para enumerar regras, requisitos ou passos.
   - Seja conciso e direto ao ponto.
Contextos:
{context_text}

Pergunta: {pergunta}
Resposta:
"""

def completion(pergunta: str, debug: bool = False) -> Dict[str, Any]:
    """
    Função principal de conversa que utiliza RAG.
    """
    # 1. Recuperar contexto (RAG) - Agora retorna (contextos, query_vector)
    contextos, query_vector_full = retrieve_context(pergunta, limit=5)
    
    # 2. Preparar o contexto para o prompt de forma segura
    context_text = ""
    for c in contextos:
        # Tenta acessar como dicionário, se falhar pula ou trata como erro
        try:
            name = c.get('file', 'Desconhecido')
            texto = c.get('chunk', 'Trecho não encontrado')
            context_text += f"Documento: {name}\nTrecho: {texto}\n\n"
        except (AttributeError, TypeError):
            continue
    
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
    # Usamos o query_vector que já veio da busca para o preview
    embedding_preview = query_vector_full[:7]

    # Formata os documentos do retriever conforme solicitado
    docs_retriever = []
    for c in contextos:
        try:
            docs_retriever.append({
                "id": c.get("id", "N/A"),
                "name": c.get("file", "N/A"),
                "score": round(c.get("score", 0), 4),
                "chunk": c.get("chunk", "")
            })
        except (AttributeError, TypeError):
            continue

    return {
        "resposta": resposta_final,
        "debug": {
            "documentos_retriever": docs_retriever,
            "embedding_da_pergunta": {
                "embedding_preview": embedding_preview,
                "dimension": len(query_vector_full)
            }
        }
    }

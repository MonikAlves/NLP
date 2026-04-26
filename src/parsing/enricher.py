import re
import json

# Padrões Regex para documentos da ANEEL
PATTERNS = {
    "artigos": re.compile(
        r'\bArt\.?\s*\d+[º°]?(?:\s*[-–]\s*[A-Z])?', re.IGNORECASE
    ),
    "paragrafos": re.compile(r'§\s*\d+[º°]?'),
    "normas_ref": re.compile(
        r'(?:RN|RD|DSP|RE|Portaria|Resolução Normativa|Resolução de Diretoria)'
        r'\s*(?:n[º°]?\s*)?\d+(?:/\d+)?',
        re.IGNORECASE,
    ),
    "valores_monetarios": re.compile(
        r'R\$\s*[\d.,]+(?:\s*(?:mil|milhões|bilhões))?'
    ),
    "cnpj": re.compile(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'),
    "datas_no_texto": re.compile(r'\d{2}/\d{2}/\d{4}'),
    "artigos_lei": re.compile(
        r'Lei\s+(?:n[º°]?\s*)?\d+(?:\.\d+)?(?:/\d+)?', re.IGNORECASE
    ),
}


def enrich_page(page: dict, doc_metadata: dict) -> dict:
    """
    Combina os metadados do documento (vindos do SQLite) com a página extraída
    e adiciona campos extraídos via Regex no texto.

    doc_metadata deve conter: nome_arquivo, titulo, ementa, assunto, autor,
    data_assinatura, data_publicacao, ano, situacao.
    """
    texto = page.get("texto", "")

    # Metadados do banco entram diretamente no dict da página
    enriched = {**page, **doc_metadata}

    # Regex aplicados ao texto da página
    for campo, pattern in PATTERNS.items():
        matches = list(dict.fromkeys(pattern.findall(texto)))  # dedup com ordem
        enriched[campo] = json.dumps(matches, ensure_ascii=False) if matches else None

    return enriched

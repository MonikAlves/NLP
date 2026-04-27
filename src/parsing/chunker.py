SEPARATORS = ["\n## ", "\n### ", "\n#### ", "\nArt.", "\n\n", "\n", ". ", " ", ""]

CHUNK_SIZE = 4000
OVERLAP = 400


def chunk_pages(enriched_pages: list[dict]) -> list[dict]:
    """
    Recebe páginas enriquecidas e retorna lista de chunks.
    Usa divisão recursiva com hierarquia de separadores (estilo RecursiveCharacterTextSplitter).
    Cada chunk herda todos os metadados da página de origem.
    """
    all_chunks = []

    for page in enriched_pages:
        texto = page.get("texto", "").strip()
        if not texto:
            continue

        parts = _recursive_split(texto, CHUNK_SIZE, OVERLAP, SEPARATORS)

        for idx, part in enumerate(parts):
            part = part.strip()
            if part:
                all_chunks.append({**page, "chunk_index": idx, "texto": part})

    return all_chunks


def _recursive_split(text: str, size: int, overlap: int, separators: list[str]) -> list[str]:
    """
    Divide texto recursivamente usando separadores em ordem de prioridade.
    Se o texto cabe num chunk, retorna direto.
    Tenta cada separador até conseguir dividir, então subdivide partes grandes recursivamente.
    """
    if len(text) <= size:
        return [text]

    for sep in separators:
        if sep and sep in text:
            return _split_and_merge(text, sep, size, overlap, separators)

    return _split_by_size(text, size, overlap)


def _split_and_merge(
    text: str, sep: str, size: int, overlap: int, separators: list[str]
) -> list[str]:
    """
    Divide pelo separador e reagrupa fragmentos pequenos até atingir o tamanho alvo.
    Aplica overlap: o início de cada chunk começa com o final do chunk anterior.
    """
    raw_parts = text.split(sep)
    merged = []
    current = ""

    for part in raw_parts:
        candidate = (current + sep + part) if current else part
        if len(candidate) > size and current:
            merged.append(current)
            tail = current[-overlap:] if overlap else ""
            current = (tail + sep + part) if tail else part
        else:
            current = candidate

    if current:
        merged.append(current)

    result = []
    remaining_seps = separators[separators.index(sep) + 1:] if sep in separators else separators[1:]
    for chunk in merged:
        if len(chunk) > size:
            result.extend(_recursive_split(chunk, size, overlap, remaining_seps))
        else:
            result.append(chunk)

    return result


def _split_by_size(text: str, size: int, overlap: int) -> list[str]:
    """
    Divide em blocos de tamanho fixo com overlap.
    Nunca corta no meio de uma palavra (procura o espaço mais próximo).
    """
    if not text:
        return []

    parts = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))

        if end < len(text) and text[end] not in (" ", "\n"):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space

        parts.append(text[start:end])

        if end == len(text):
            break

        start = end - overlap

    return parts

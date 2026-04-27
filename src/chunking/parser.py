def extract_metadata_and_text(markdown_text: str) -> tuple[dict, str]:
    """Extrai metadados do cabeçalho e retorna o resto do texto limpo."""
    lines = markdown_text.split('\n')
    
    metadata = {}
    content_start_idx = 0
    
    # Procura no início do arquivo
    for i, line in enumerate(lines[:10]):  # busca apenas nas primeiras 10 linhas
        if line.startswith("# Documento:"):
            metadata["nome_arquivo"] = line.replace("# Documento:", "").strip()
        elif line.startswith("Ano:"):
            try:
                metadata["ano"] = int(line.replace("Ano:", "").strip())
            except ValueError:
                metadata["ano"] = None
        elif not line.strip() and "nome_arquivo" in metadata:
            # Encontrou a linha em branco após os metadados
            content_start_idx = i + 1
            break
            
    # Se não encontrou cabeçalho esperado, pega tudo
    if content_start_idx == 0 and "nome_arquivo" not in metadata:
        return {}, markdown_text
        
    content_text = "\n".join(lines[content_start_idx:])
    return metadata, content_text.strip()

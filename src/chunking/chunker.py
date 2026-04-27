from langchain_text_splitters import MarkdownTextSplitter

def generate_chunks(text: str, metadata: dict, chunk_size: int = 3000, chunk_overlap: int = 300) -> list[dict]:
    """
    Divide o texto em chunks respeitando o formato Markdown.
    Retorna uma lista de dicionários contendo o texto do chunk e os metadados.
    """
    if not text:
        return []
        
    splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    chunks = splitter.create_documents([text])
    
    results = []
    for i, doc in enumerate(chunks):
        # Cada doc da langchain tem page_content
        chunk_dict = {
            "chunk_index": i,
            "texto": doc.page_content,
            **metadata
        }
        results.append(chunk_dict)
        
    return results

import fitz
import pymupdf4llm
from loguru import logger
import pandas as pd
from bs4 import BeautifulSoup
import io

MIN_CHARS = 50

def extract_pages(file_bytes: bytes, nome_arquivo: str) -> list[dict]:
    """
    Extrator Universal: Detecta extensão e extrai texto de PDF, HTML ou Excel.
    Retorna lista de dicts: {pagina, texto, metodo}
    """
    ext = nome_arquivo.split('.')[-1].lower()
    
    if ext == 'pdf':
        return _extract_pdf(file_bytes, nome_arquivo)
    elif ext in ['html', 'htm']:
        return _extract_html(file_bytes, nome_arquivo)
    elif ext in ['xlsx', 'xls']:
        return _extract_excel(file_bytes, nome_arquivo)
    else:
        logger.warning(f"❓ {nome_arquivo}: Extensão '{ext}' não suportada.")
        return []

def _extract_pdf(pdf_bytes: bytes, nome_arquivo: str) -> list[dict]:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"❌ {nome_arquivo}: Erro ao abrir PDF: {e}")
        return []

    pages = []
    num_pages = len(doc)

    try:
        md_text = pymupdf4llm.to_markdown(doc)
        page_texts = md_text.split("\n-----\n")
        while len(page_texts) < num_pages:
            page_texts.append("")
    except Exception as e:
        logger.warning(f"⚠️ {nome_arquivo}: pymupdf4llm falhou: {e}")
        page_texts = [""] * num_pages

    for i in range(num_pages):
        page_num = i + 1
        texto = page_texts[i].strip() if i < len(page_texts) else ""

        if len(texto) >= MIN_CHARS:
            pages.append({"pagina": page_num, "texto": texto, "metodo": "pymupdf4llm"})
        else:
            texto_ocr = _ocr_page(doc[i], nome_arquivo, page_num)
            if len(texto_ocr) >= MIN_CHARS:
                pages.append({"pagina": page_num, "texto": texto_ocr, "metodo": "ocr"})
            else:
                pages.append({"pagina": page_num, "texto": texto_ocr or texto, "metodo": "ocr_falhou"})

    doc.close()
    return pages

def _extract_html(html_bytes: bytes, nome_arquivo: str) -> list[dict]:
    try:
        # Tenta decodificar (muitos arquivos ANEEL usam latin-1 ou utf-8)
        try:
            content = html_bytes.decode('utf-8')
        except:
            content = html_bytes.decode('latin-1')
            
        soup = BeautifulSoup(content, 'lxml')
        
        # Remove scripts e estilos
        for script in soup(["script", "style"]):
            script.extract()
            
        texto = soup.get_text(separator='\n').strip()
        return [{"pagina": 1, "texto": texto, "metodo": "beautifulsoup"}]
    except Exception as e:
        logger.error(f"❌ {nome_arquivo}: Erro no HTML: {e}")
        return []

def _extract_excel(excel_bytes: bytes, nome_arquivo: str) -> list[dict]:
    try:
        df_dict = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=None)
        pages = []
        for sheet_name, df in df_dict.items():
            if df.empty: continue
            # Converte tabela para Markdown
            md_table = df.to_markdown(index=False)
            pages.append({
                "pagina": sheet_name, 
                "texto": f"## Planilha: {sheet_name}\n\n{md_table}", 
                "metodo": "pandas"
            })
        return pages
    except Exception as e:
        logger.error(f"❌ {nome_arquivo}: Erro no Excel: {e}")
        return []

def _ocr_page(page, nome_arquivo: str, page_num: int) -> str:
    try:
        import pytesseract
        from PIL import Image
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return pytesseract.image_to_string(img, lang="por").strip()
    except Exception as e:
        return ""

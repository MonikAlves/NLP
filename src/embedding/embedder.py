import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from loguru import logger

# Carrega variáveis do .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Embedder:
    def __init__(self, model="text-embedding-3-small"):
        self.model = model

    @retry(
        stop=stop_after_attempt(8), # Aumentado para 8 tentativas
        wait=wait_exponential(multiplier=2, min=5, max=60), # Espera mais agressiva (até 60s)
        reraise=True
    )
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Gera embeddings para uma lista de textos.
        Utiliza retentativas automáticas para lidar com rate limits ou instabilidades.
        """
        try:
            # Limpeza básica de textos (remover quebras de linha excessivas melhora o embedding)
            texts = [t.replace("\n", " ") for t in texts]
            
            response = client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            # Extrai os vetores da resposta
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Erro ao gerar embeddings: {e}")
            raise e
